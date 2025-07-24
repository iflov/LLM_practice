"""
Model Fallback System
여러 모델을 등록하고 장애 시 자동으로 대체 모델로 전환
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import httpx
from datetime import datetime, timedelta
import asyncio
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class ModelStatus(Enum):
    AVAILABLE = "available"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ModelConfig:
    id: str
    name: str
    supports_tools: bool
    is_free: bool
    priority: int  # 낮을수록 우선순위 높음
    context_length: int
    rate_limit_retry_after: Optional[datetime] = None
    consecutive_errors: int = 0
    status: ModelStatus = ModelStatus.AVAILABLE


class ModelManager:
    """모델 관리 및 Fallback 시스템"""
    
    def __init__(self):
        # 모델 우선순위 순으로 등록
        self.models = [
            ModelConfig(
                id="deepseek/deepseek-chat-v3-0324:free",
                name="DeepSeek V3 Chat (Free)",
                supports_tools=True,
                is_free=True,
                priority=1,
                context_length=32768
            ),
            ModelConfig(
                id="google/gemini-flash-1.5-8b",
                name="Gemini Flash 1.5 8B",
                supports_tools=True,
                is_free=False,  # 무료 티어 있지만 제한적
                priority=2,
                context_length=1000000
            ),
            ModelConfig(
                id="qwen/qwen-2-7b-instruct:free",
                name="Qwen 2 7B (Free)",
                supports_tools=False,  # Tool 미지원
                is_free=True,
                priority=3,
                context_length=32768
            ),
            ModelConfig(
                id="meta-llama/llama-3.2-3b-instruct:free",
                name="Llama 3.2 3B (Free)",
                supports_tools=False,
                is_free=True,
                priority=4,
                context_length=131072
            ),
            ModelConfig(
                id="openai/gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                supports_tools=True,
                is_free=False,
                priority=5,
                context_length=16385
            ),
        ]
        
        # 모델 ID로 빠른 조회를 위한 딕셔너리
        self.model_dict = {model.id: model for model in self.models}
        
    def get_available_models(self, require_tools: bool = False) -> List[ModelConfig]:
        """사용 가능한 모델 목록 반환"""
        now = datetime.now()
        available_models = []
        
        for model in self.models:
            # 상태 확인
            if model.status == ModelStatus.DISABLED:
                continue
                
            # Rate limit 확인
            if model.rate_limit_retry_after and model.rate_limit_retry_after > now:
                continue
                
            # Tool 지원 필요 시
            if require_tools and not model.supports_tools:
                continue
                
            # 연속 에러가 5회 이상이면 일시적으로 제외
            if model.consecutive_errors >= 5:
                continue
                
            available_models.append(model)
            
        # 우선순위 순으로 정렬
        return sorted(available_models, key=lambda m: m.priority)
    
    def get_best_model(self, require_tools: bool = False, prefer_free: bool = True) -> Optional[ModelConfig]:
        """최적의 모델 선택"""
        available = self.get_available_models(require_tools)
        
        if not available:
            return None
            
        # 무료 모델 우선 선택 옵션
        if prefer_free:
            free_models = [m for m in available if m.is_free]
            if free_models:
                return free_models[0]
                
        return available[0]
    
    def mark_model_error(self, model_id: str, error: Exception):
        """모델 에러 기록"""
        if model_id not in self.model_dict:
            return
            
        model = self.model_dict[model_id]
        model.consecutive_errors += 1
        
        error_msg = str(error).lower()
        
        # Rate limit 에러 처리
        if "rate" in error_msg and "limit" in error_msg:
            model.status = ModelStatus.RATE_LIMITED
            model.rate_limit_retry_after = datetime.now() + timedelta(minutes=5)
            logger.warning(f"Model {model_id} rate limited, retry after 5 minutes")
            
        # 기타 에러
        elif model.consecutive_errors >= 5:
            model.status = ModelStatus.ERROR
            logger.error(f"Model {model_id} marked as error after {model.consecutive_errors} failures")
            
    def mark_model_success(self, model_id: str):
        """모델 성공 기록"""
        if model_id not in self.model_dict:
            return
            
        model = self.model_dict[model_id]
        model.consecutive_errors = 0
        model.status = ModelStatus.AVAILABLE
        model.rate_limit_retry_after = None
        
    def reset_model_status(self, model_id: str):
        """모델 상태 초기화"""
        if model_id not in self.model_dict:
            return
            
        model = self.model_dict[model_id]
        model.consecutive_errors = 0
        model.status = ModelStatus.AVAILABLE
        model.rate_limit_retry_after = None
        

class OpenRouterClientWithFallback:
    """Fallback 기능이 있는 OpenRouter 클라이언트"""
    
    def __init__(self):
        self.model_manager = ModelManager()
        self.base_url = settings.openrouter_base_url
        self.api_key = settings.openrouter_api_key
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        use_tools: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Fallback이 적용된 채팅 완료 요청"""
        
        # 사용 가능한 모델 가져오기
        models = self.model_manager.get_available_models(require_tools=use_tools)
        
        if not models:
            raise Exception("No available models found")
            
        last_error = None
        
        # 각 모델로 시도
        for model in models:
            try:
                logger.info(f"Trying model: {model.id}")
                
                # API 요청
                result = await self._make_request(
                    model_id=model.id,
                    messages=messages,
                    tools=tools if use_tools else None
                )
                
                # 성공 시 모델 상태 업데이트
                self.model_manager.mark_model_success(model.id)
                
                # 결과에 사용된 모델 정보 추가
                result["model_used"] = model.id
                result["model_info"] = {
                    "id": model.id,
                    "name": model.name,
                    "is_free": model.is_free,
                    "supports_tools": model.supports_tools
                }
                
                return result
                
            except Exception as e:
                last_error = e
                logger.error(f"Model {model.id} failed: {str(e)}")
                
                # 에러 기록
                self.model_manager.mark_model_error(model.id, e)
                
                # 다음 모델로 시도
                continue
                
        # 모든 모델 실패
        raise Exception(f"All models failed. Last error: {str(last_error)}")
        
    async def _make_request(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """실제 API 요청"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "LLM Agent POC"
        }
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens
        }
        
        if tools:
            payload["tools"] = tools
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
                
            return response.json()


# 싱글톤 인스턴스
model_manager = ModelManager()
openrouter_client = OpenRouterClientWithFallback()