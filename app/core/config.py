from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # OpenRouter
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./chat_history.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 3600
    
    # Application
    app_name: str = "Agent LLM POC"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    
    # Model
    default_model: str = "moonshotai/kimi-k2:free"  # OpenRouter 무료 Agent 최적화 모델
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # Agent Configuration
    agent_timeout: int = 300
    max_agents: int = 10
    
    # Model Fallback Configuration
    fallback_enabled: bool = True
    fallback_free_only: bool = True
    fallback_models: str = "deepseek/deepseek-chat-v3-0324:free,google/gemini-2.0-flash-exp:free,qwen/qwen3-235b-a22b-07-25:free"
    
    @property
    def fallback_models_list(self) -> List[str]:
        """Fallback models as a list"""
        return [model.strip() for model in self.fallback_models.split(",") if model.strip()]


settings = Settings()