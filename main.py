from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# ASGI 서버 - FastAPI 앱을 실행하기 위한 서버
import uvicorn
# 설정 관리 - 환경변수와 설정값들을 중앙에서 관리
from src.core.config import settings
# 구조화된 로깅 - JSON 형태로 로그를 남겨 모니터링과 디버깅을 용이하게 함
from src.core.logging import setup_logging, get_logger

setup_logging(settings.log_level)
logger = get_logger(__name__)

# Lifespan context manager - FastAPI의 새로운 lifecycle 관리 방식
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting LLM Agent Server", 
                app_name=settings.app_name,
                environment=settings.app_env)
    
    # Initialize Agent Manager
    from src.agents.manager import get_agent_manager
    agent_manager = await get_agent_manager()
    logger.info("Agent Manager initialized")
    
    # TODO: 여기에 DB 연결, Redis 연결 등 초기화 작업 추가 예정
    
    yield  # 애플리케이션 실행
    
    # Shutdown - 서버 종료 시 실행
    logger.info("Shutting down LLM Agent Server")
    
    # Cleanup Agent Manager
    if agent_manager:
        await agent_manager.shutdown()
    
    # TODO: 여기에 DB 연결 해제, 열린 연결 정리 등 정리 작업 추가 예정


# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title=settings.app_name,  # API 문서에 표시될 제목
    version="0.1.0",  # API 버전 관리
    description="LLM Agent Backend Server with OpenRouter integration",  # API 설명
    lifespan=lifespan  # lifespan 이벤트 핸들러 등록
)

# CORS 설정 - 프론트엔드(예: React)에서 API 호출할 수 있도록 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 허용할 프론트엔드 도메인 목록
    allow_credentials=True,  # 쿠키/인증 정보 포함 허용
    allow_methods=["*"],  # 모든 HTTP 메소드 허용 (GET, POST, PUT, DELETE 등)
    allow_headers=["*"],  # 모든 헤더 허용
)

# API 라우터 등록
from src.api.chat import router as chat_router
app.include_router(chat_router)


# 헬스체크 엔드포인트 - 서버가 정상 작동하는지 확인용
# 로드밸런서나 쿠버네티스 등에서 서버 상태 모니터링에 사용
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env
    }


# 직접 실행 시에만 작동 (python main.py)
# 프로덕션에서는 보통 gunicorn이나 다른 ASGI 서버를 사용
if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # 실행할 앱 경로 (모듈명:앱인스턴스)
        host=settings.app_host,  # 서버가 바인딩할 호스트 (0.0.0.0 = 모든 인터페이스)
        port=settings.app_port,  # 서버 포트
        reload=settings.app_env == "development"  # 개발 환경에서만 코드 변경 시 자동 재시작
    ) 