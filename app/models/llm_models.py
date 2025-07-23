"""
OpenRouter에서 사용 가능한 무료 LLM 모델 정보
"""

# OpenRouter 무료 모델 목록 (2024년 기준)
FREE_MODELS = {
    "meta-llama/llama-3-8b-instruct:free": {
        "name": "Llama 3 8B Instruct (Free)",
        "provider": "Meta",
        "context_length": 8192,
        "description": "Meta의 Llama 3 8B 인스트럭션 튜닝 모델 (무료)"
    },
    "mistralai/mistral-7b-instruct:free": {
        "name": "Mistral 7B Instruct (Free)", 
        "provider": "Mistral AI",
        "context_length": 8192,
        "description": "Mistral AI의 7B 인스트럭션 모델 (무료)"
    },
    "google/gemma-7b-it:free": {
        "name": "Gemma 7B Instruct (Free)",
        "provider": "Google",
        "context_length": 8192,
        "description": "Google의 Gemma 7B 인스트럭션 모델 (무료)"
    },
    "nousresearch/nous-capybara-7b:free": {
        "name": "Nous Capybara 7B (Free)",
        "provider": "NousResearch",
        "context_length": 4096,
        "description": "NousResearch의 Capybara 7B 모델 (무료)"
    },
    "openchat/openchat-7b:free": {
        "name": "OpenChat 3.5 (Free)",
        "provider": "OpenChat",
        "context_length": 8192,
        "description": "OpenChat 3.5 7B 모델 (무료)"
    },
    "gryphe/mythomist-7b:free": {
        "name": "MythoMist 7B (Free)",
        "provider": "Gryphe",
        "context_length": 8192,
        "description": "Gryphe의 MythoMist 7B 모델 (무료)"
    },
    "undi95/toppy-m-7b:free": {
        "name": "Toppy M 7B (Free)",
        "provider": "Undi95",
        "context_length": 4096,
        "description": "Undi95의 Toppy M 7B 모델 (무료)"
    }
}

# 작업별 추천 무료 모델
RECOMMENDED_FREE_MODELS = {
    "general": "meta-llama/llama-3-8b-instruct:free",
    "coding": "mistralai/mistral-7b-instruct:free",
    "creative": "gryphe/mythomist-7b:free",
    "analysis": "google/gemma-7b-it:free",
    "chat": "openchat/openchat-7b:free"
}

def get_free_model_info(model_id: str) -> dict:
    """무료 모델 정보 반환"""
    return FREE_MODELS.get(model_id, {
        "name": "Unknown Model",
        "provider": "Unknown",
        "context_length": 4096,
        "description": "Model information not available"
    })

def list_free_models() -> list:
    """사용 가능한 무료 모델 목록 반환"""
    return [
        {
            "id": model_id,
            **model_info
        }
        for model_id, model_info in FREE_MODELS.items()
    ]