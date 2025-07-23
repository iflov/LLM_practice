# LLM Agent Backend Server POC

FastAPI 기반 LLM Agent 시스템 POC - OpenRouter와 LangChain을 활용한 Tool Calling 지원 백엔드 서버

## 특징

- **OpenRouter Integration**: 다양한 LLM 모델 사용 가능
- **Tool Calling**: Calculator, Weather, Search 등의 도구 사용
- **Session Management**: Redis를 사용한 세션 관리
- **Chat History**: SQLite를 사용한 대화 기록 저장
- **RESTful API**: FastAPI로 구현된 깔끔한 API

## 설치

1. 의존성 설치
```bash
pip install -r requirements.txt
# 또는 uv 사용시
uv pip install -r requirements.txt
```

2. 환경 설정
```bash
cp .env.example .env
# .env 파일에서 OPENROUTER_API_KEY 설정
```

3. Redis 실행 (Docker 사용시)
```bash
docker run -d -p 6379:6379 redis:alpine
```

## 실행

```bash
python main.py
```

서버가 실행되면:
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 사용법

### 1. 세션 생성
```bash
POST /api/chat/session
```

### 2. 메시지 전송
```bash
POST /api/chat/message
Headers: X-Session-ID: {session_id}
Body: {
    "message": "What's the weather in Seoul?",
    "use_tools": true
}
```

### 3. 대화 기록 조회
```bash
GET /api/chat/history/{session_id}
```

### 4. 사용 가능한 도구 목록
```bash
GET /api/chat/tools
```

## 테스트

```bash
python test_api.py
```

## 프로젝트 구조

```
app/
├── core/           # 설정 및 핵심 모듈
├── models/         # 데이터베이스 모델
├── services/       # 외부 서비스 연동
├── routers/        # API 엔드포인트
├── agents/         # Agent 로직
└── tools/          # Tool 구현
```

## 사용 가능한 도구

1. **Calculator**: 수학 계산
2. **Weather**: 날씨 정보 조회 (Mock)
3. **Search**: 웹 검색 (Mock)

## 환경 변수

- `OPENROUTER_API_KEY`: OpenRouter API 키 (필수)
- `DATABASE_URL`: SQLite 데이터베이스 경로
- `REDIS_URL`: Redis 연결 URL
- `DEFAULT_MODEL`: 기본 LLM 모델

## 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   FastAPI   │────▶│    Agent    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                     │
                           ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Redis    │     │ OpenRouter  │
                    │  (Session)  │     │ (LLM + Tools)│
                    └─────────────┘     └─────────────┘
                           │                     
                           ▼                     
                    ┌─────────────┐
                    │   SQLite    │
                    │  (History)  │
                    └─────────────┘
```

## 📖 추가 문서

프로젝트를 더 잘 이해하려면 다음 문서들을 참고하세요:

- **[빠른 참조 가이드](QUICK_REFERENCE.md)** - 자주 사용하는 명령어와 API
- **[프로젝트 구조 상세](PROJECT_STRUCTURE.md)** - 전체 디렉토리 구조와 각 파일 설명
- **[아키텍처 개요](ARCHITECTURE_OVERVIEW.md)** - 시스템 설계와 데이터 플로우
- **[개발 가이드](DEVELOPMENT_GUIDE.md)** - 새 기능 추가 및 커스터마이징 방법

## 🔥 현재 설정

- **모델**: `deepseek/deepseek-chat-v3-0324:free` (Tool Calling 지원)
- **세션 저장**: Redis (TTL 1시간)
- **대화 기록**: SQLite (`chat_history.db`)
- **포트**: 8000
