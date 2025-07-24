"""
Model Management API endpoints
모델 목록 조회 및 관리
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from app.services.model_manager import model_manager, ModelStatus

router = APIRouter(prefix="/api/models", tags=["models"])


class ModelInfo(BaseModel):
    id: str
    name: str
    supports_tools: bool
    is_free: bool
    priority: int
    context_length: Optional[int] = None
    status: Optional[str] = None
    consecutive_errors: Optional[int] = None
    rate_limit_retry_after: Optional[str] = None


class ModelsListResponse(BaseModel):
    total: int
    models: List[ModelInfo]


class AvailableModelsResponse(BaseModel):
    total: int
    require_tools: bool
    models: List[ModelInfo]


class CurrentModelResponse(BaseModel):
    id: str
    name: str
    supports_tools: bool
    is_free: bool
    context_length: int
    selection_criteria: Dict[str, Any]


class ModelStatusUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    model_id: str
    action: str  # "enable", "disable", "reset"


@router.get("/list", response_model=ModelsListResponse)
async def list_all_models() -> ModelsListResponse:
    """등록된 모든 모델 목록 조회"""
    models_info = []
    
    for model in model_manager.models:
        models_info.append(ModelInfo(
            id=model.id,
            name=model.name,
            supports_tools=model.supports_tools,
            is_free=model.is_free,
            priority=model.priority,
            context_length=model.context_length,
            status=model.status.value,
            consecutive_errors=model.consecutive_errors,
            rate_limit_retry_after=model.rate_limit_retry_after.isoformat() if model.rate_limit_retry_after else None
        ))
    
    return ModelsListResponse(
        total=len(models_info),
        models=sorted(models_info, key=lambda x: x.priority)
    )


@router.get("/available", response_model=AvailableModelsResponse)
async def get_available_models(require_tools: bool = False) -> AvailableModelsResponse:
    """현재 사용 가능한 모델 목록"""
    available = model_manager.get_available_models(require_tools=require_tools)
    
    models_info = []
    for model in available:
        models_info.append(ModelInfo(
            id=model.id,
            name=model.name,
            supports_tools=model.supports_tools,
            is_free=model.is_free,
            priority=model.priority,
            context_length=model.context_length
        ))
    
    return AvailableModelsResponse(
        total=len(models_info),
        require_tools=require_tools,
        models=models_info
    )


@router.get("/current", response_model=CurrentModelResponse)
async def get_current_model(require_tools: bool = False, prefer_free: bool = True) -> CurrentModelResponse:
    """현재 선택될 최적 모델 정보"""
    model = model_manager.get_best_model(require_tools=require_tools, prefer_free=prefer_free)
    
    if not model:
        raise HTTPException(status_code=503, detail="No available models found")
    
    return CurrentModelResponse(
        id=model.id,
        name=model.name,
        supports_tools=model.supports_tools,
        is_free=model.is_free,
        context_length=model.context_length,
        selection_criteria={
            "require_tools": require_tools,
            "prefer_free": prefer_free
        }
    )


@router.post("/status")
async def update_model_status(update: ModelStatusUpdate) -> Dict[str, str]:
    """모델 상태 업데이트"""
    
    if update.model_id not in model_manager.model_dict:
        raise HTTPException(status_code=404, detail=f"Model {update.model_id} not found")
    
    model = model_manager.model_dict[update.model_id]
    
    if update.action == "enable":
        model.status = ModelStatus.AVAILABLE
        model.consecutive_errors = 0
        model.rate_limit_retry_after = None
        message = f"Model {update.model_id} enabled"
        
    elif update.action == "disable":
        model.status = ModelStatus.DISABLED
        message = f"Model {update.model_id} disabled"
        
    elif update.action == "reset":
        model_manager.reset_model_status(update.model_id)
        message = f"Model {update.model_id} reset"
        
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {update.action}")
    
    return {"message": message, "status": model.status.value}


@router.get("/test-fallback")
async def test_fallback_scenario() -> Dict[str, Any]:
    """Fallback 시나리오 테스트"""
    
    # 모든 모델의 현재 상태 저장
    original_states = {}
    for model_id, model in model_manager.model_dict.items():
        original_states[model_id] = {
            "status": model.status,
            "errors": model.consecutive_errors
        }
    
    # 테스트 시나리오
    test_results = []
    
    # 1. 정상 상황
    best_model = model_manager.get_best_model(require_tools=True)
    test_results.append({
        "scenario": "Normal - Tool required",
        "selected_model": best_model.id if best_model else None
    })
    
    # 2. 첫 번째 모델 비활성화
    if best_model:
        model_manager.model_dict[best_model.id].status = ModelStatus.DISABLED
        second_model = model_manager.get_best_model(require_tools=True)
        test_results.append({
            "scenario": f"First model ({best_model.id}) disabled",
            "selected_model": second_model.id if second_model else None
        })
    
    # 3. Tool 미지원 시나리오
    best_no_tools = model_manager.get_best_model(require_tools=False)
    test_results.append({
        "scenario": "No tools required",
        "selected_model": best_no_tools.id if best_no_tools else None
    })
    
    # 원상태 복구
    for model_id, state in original_states.items():
        model_manager.model_dict[model_id].status = state["status"]
        model_manager.model_dict[model_id].consecutive_errors = state["errors"]
    
    return {
        "test_results": test_results,
        "note": "Models have been restored to original state"
    }