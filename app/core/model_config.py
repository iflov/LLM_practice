"""
Model configuration with fallback support
"""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """모델 설정"""
    id: str
    name: str
    supports_tools: bool
    is_free: bool
    context_length: int
    priority: int = 0  # 낮을수록 우선순위 높음


# OpenRouter에서 사용 가능한 무료 모델들 (Tool 지원 여부 포함)
AVAILABLE_MODELS = [
    # Tool Calling 지원 모델들 (우선순위 높음)
    ModelConfig(
        id="moonshotai/kimi-k2:free",
        name="Moonshot Kimi K2",
        supports_tools=True,
        is_free=True,
        context_length=65536,
        priority=0  # 가장 높은 우선순위
    ),
    ModelConfig(
        id="deepseek/deepseek-chat-v3-0324:free",
        name="DeepSeek Chat V3",
        supports_tools=True,
        is_free=True,
        context_length=32768,
        priority=1
    ),
    ModelConfig(
        id="google/gemini-flash-1.5-8b",
        name="Gemini Flash 1.5 8B",
        supports_tools=True,
        is_free=True,
        context_length=1000000,
        priority=2
    ),
    ModelConfig(
        id="openai/gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        supports_tools=True,
        is_free=False,  # 유료
        context_length=16385,
        priority=10
    ),
    
    # Tool Calling 미지원 모델들 (fallback용)
    ModelConfig(
        id="meta-llama/llama-3.3-70b-instruct:free",
        name="Llama 3.3 70B",
        supports_tools=False,
        is_free=True,
        context_length=8192,
        priority=3
    ),
    ModelConfig(
        id="qwen/qwen3-235b-a22b-07-25:free",
        name="Qwen3 235B",
        supports_tools=False,
        is_free=True,
        context_length=262144,
        priority=4
    ),
    ModelConfig(
        id="tngtech/deepseek-r1t2-chimera:free",
        name="DeepSeek R1T2 Chimera",
        supports_tools=False,
        is_free=True,
        context_length=32768,
        priority=5
    ),
]


def get_fallback_models(require_tools: bool = False, free_only: bool = True) -> List[ModelConfig]:
    """
    우선순위에 따라 정렬된 fallback 모델 리스트 반환
    
    Args:
        require_tools: Tool calling이 필요한 경우 True
        free_only: 무료 모델만 사용할 경우 True
    """
    models = []
    
    for model in AVAILABLE_MODELS:
        # 필터링
        if free_only and not model.is_free:
            continue
        if require_tools and not model.supports_tools:
            continue
            
        models.append(model)
    
    # 우선순위에 따라 정렬
    models.sort(key=lambda x: x.priority)
    
    return models


def get_model_by_id(model_id: str) -> ModelConfig:
    """ID로 모델 찾기"""
    for model in AVAILABLE_MODELS:
        if model.id == model_id:
            return model
    return None