---
tags:
  - project-structure
  - llm-agent
  - backend
  - poc
created: 2025-07-22
updated: 2025-07-22
aliases:
  - 프로젝트 구조
  - LLM Agent 프로젝트 구조
description: LLM Agent 백엔드 서버 POC 프로젝트의 구조와 구성 요소
status: draft
category: reference
---

# LLM Agent 백엔드 서버 프로젝트 구조

> [!info] 개요
> LLM Agent 백엔드 서버 POC 프로젝트의 전체 구조와 각 구성 요소에 대한 설명입니다.

## 📑 목차

- [[#🏗️ 프로젝트 디렉토리 구조]]
- [[#📦 의존성 관리]]
- [[#⚙️ 환경 설정]]
- [[#💻 핵심 모듈]]
- [[#🚀 메인 애플리케이션]]

---

## 🏗️ 프로젝트 디렉토리 구조

```
LLM_practice/
├── src/                    # 소스 코드 디렉토리
│   ├── __init__.py
│   ├── api/               # API 엔드포인트
│   ├── agents/            # Agent 관련 로직
│   ├── core/              # 핵심 설정 및 유틸리티
│   │   ├── config.py      # 애플리케이션 설정
│   │   └── logging.py     # 로깅 설정
│   ├── db/                # 데이터베이스 관련
│   ├── services/          # 비즈니스 로직
│   └── utils/             # 유틸리티 함수
├── tests/                 # 테스트 코드
│   ├── unit/              # 단위 테스트
│   └── integration/       # 통합 테스트
├── docs/                  # 문서
├── main.py                # 애플리케이션 진입점
├── requirements.txt       # Python 의존성
├── .env.example          # 환경 변수 예제
├── .gitignore            # Git 무시 파일
├── architecture.pdf      # 아키텍처 설계 문서
└── CLAUDE.local.md       # 프로젝트 컨텍스트
```

---

## 📦 의존성 관리

### requirements.txt 구성

> [!note] 핵심 의존성
> ```txt
> # Core dependencies
> fastapi==0.104.1           # 웹 프레임워크
> uvicorn[standard]==0.24.0  # ASGI 서버
> python-dotenv==1.0.0       # 환경 변수 관리
> pydantic==2.5.0           # 데이터 검증
> pydantic-settings==2.1.0   # 설정 관리
> 
> # SSE support
> sse-starlette==1.8.2      # Server-Sent Events
> 
> # OpenRouter API client
> httpx==0.25.2             # HTTP 클라이언트
> aiohttp==3.9.1            # 비동기 HTTP
> 
> # Database
> sqlalchemy==2.0.23        # ORM
> aiosqlite==0.19.0         # 비동기 SQLite
> 
> # Redis
> redis==5.0.1              # Redis 클라이언트
> aioredis==2.0.1           # 비동기 Redis
> 
> # JSON-RPC
> jsonrpclib-pelix==0.4.3   # JSON-RPC 프로토콜
> 
> # Logging and monitoring
> structlog==23.2.0         # 구조화된 로깅
> prometheus-client==0.19.0  # 모니터링 메트릭
> ```

---

## ⚙️ 환경 설정

### .env.example 파일

> [!example] 환경 변수 설정
> ```env
> # Application Configuration
> APP_NAME=llm-agent-server
> APP_ENV=development
> APP_HOST=0.0.0.0
> APP_PORT=8000
> LOG_LEVEL=INFO
> 
> # OpenRouter Configuration
> OPENROUTER_API_KEY=your_openrouter_api_key_here
> OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
> 
> # Redis Configuration
> REDIS_URL=redis://localhost:6379/0
> REDIS_CACHE_TTL=3600
> 
> # Database Configuration
> DATABASE_URL=sqlite+aiosqlite:///./llm_agent.db
> 
> # Agent Configuration
> DEFAULT_MODEL=anthropic/claude-3-opus
> MAX_AGENTS=10
> AGENT_TIMEOUT=300
> 
> # Security
> API_KEY_HEADER=X-API-Key
> CORS_ORIGINS=["http://localhost:3000"]
> 
> # SSE Configuration
> SSE_RETRY_TIMEOUT=3000
> SSE_PING_INTERVAL=30
> ```

---

## 💻 핵심 모듈

### src/core/config.py

> [!note] 설정 관리 모듈
> Pydantic Settings를 사용하여 환경 변수를 타입 안전하게 관리합니다.

```python
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
    
    # ... (다른 설정들)

settings = Settings()
```

### src/core/logging.py

> [!note] 로깅 설정 모듈
> Structlog를 사용하여 구조화된 JSON 로깅을 구현합니다.

```python
import structlog
from structlog.stdlib import filter_by_level
import logging
import sys


def setup_logging(log_level: str = "INFO"):
    """Configure structured logging for the application"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # ... 프로세서 설정
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

---

## 🚀 메인 애플리케이션

### main.py

> [!example] FastAPI 애플리케이션 진입점
> ```python
> from fastapi import FastAPI
> from fastapi.middleware.cors import CORSMiddleware
> import uvicorn
> from src.core.config import settings
> from src.core.logging import setup_logging, get_logger
> 
> # Setup logging
> setup_logging(settings.log_level)
> logger = get_logger(__name__)
> 
> # Create FastAPI app
> app = FastAPI(
>     title=settings.app_name,
>     version="0.1.0",
>     description="LLM Agent Backend Server with OpenRouter integration"
> )
> 
> # Configure CORS
> app.add_middleware(
>     CORSMiddleware,
>     allow_origins=settings.cors_origins,
>     allow_credentials=True,
>     allow_methods=["*"],
>     allow_headers=["*"],
> )
> 
> @app.get("/health")
> async def health_check():
>     return {
>         "status": "healthy",
>         "app": settings.app_name,
>         "environment": settings.app_env
>     }
> ```

---

## 📚 참고자료

- [[technical-terms|기술 용어 설명]]
- [[architecture|아키텍처 설계]]
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [OpenRouter API 문서](https://openrouter.ai/docs)