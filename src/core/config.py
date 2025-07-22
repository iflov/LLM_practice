from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    app_name: str = Field(default="llm-agent-server")
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")
    
    # OpenRouter
    openrouter_api_key: str = Field(default="")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_cache_ttl: int = Field(default=3600)
    
    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./llm_agent.db")
    
    # Agent Configuration
    default_model: str = Field(default="anthropic/claude-3-opus")
    max_agents: int = Field(default=10)
    agent_timeout: int = Field(default=300)
    
    # Security
    api_key_header: str = Field(default="X-API-Key")
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
    
    # SSE Configuration
    sse_retry_timeout: int = Field(default=3000)
    sse_ping_interval: int = Field(default=30)


settings = Settings()