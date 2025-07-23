# 프로젝트 구조 상세 설명

## 📂 전체 디렉토리 구조

```
LLM_practice/
│
├── app/                        # 메인 애플리케이션 코드
│   ├── __init__.py
│   ├── agents/                 # Agent 구현체들
│   │   ├── __init__.py
│   │   ├── chat_agent.py       # 기본 Chat Agent 구현
│   │   └── langchain_agent.py  # LangChain 기반 Agent
│   ├── core/                   # 핵심 설정 및 유틸리티
│   │   ├── __init__.py
│   │   └── config.py           # 환경 설정 (pydantic-settings)
│   ├── models/                 # 데이터베이스 모델
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy 설정
│   │   └── llm_models.py       # ORM 모델 정의
│   ├── routers/                # API 엔드포인트
│   │   ├── __init__.py
│   │   └── chat.py             # 채팅 관련 API
│   ├── services/               # 외부 서비스 연동
│   │   ├── __init__.py
│   │   ├── openrouter_client.py # OpenRouter API 클라이언트
│   │   └── session_manager.py   # Redis 세션 관리
│   └── tools/                  # Agent가 사용할 도구들
│       ├── __init__.py
│       ├── base_tool.py        # Tool 기본 클래스
│       ├── calculator.py       # 계산기 도구
│       ├── search.py           # 검색 도구 (Mock)
│       └── weather.py          # 날씨 도구 (Mock)
│
├── src/                        # 추가 POC 코드 (초기 실험용)
│   ├── __init__.py
│   ├── agents/                 # 간단한 Agent 구현
│   │   └── simple_agent.py
│   ├── api/                    # API 라우터
│   │   └── chat.py
│   ├── core/                   # 설정 및 로깅
│   │   ├── config.py
│   │   └── logging.py
│   └── services/               # OpenRouter 클라이언트
│       └── openrouter_client.py
│
├── docs/                       # 문서화
│   ├── quick-start-guide.md    # 빠른 시작 가이드
│   └── ...
│
├── tests/                      # 테스트 코드
│   ├── unit/                   # 단위 테스트
│   └── integration/            # 통합 테스트
│
├── main.py                     # 메인 서버 진입점
├── main_poc.py                 # POC 버전 서버
├── test_api.py                 # API 테스트 스크립트
├── test_deepseek_tools.py      # DeepSeek 모델 테스트
│
├── requirements.txt            # Python 의존성
├── requirements-minimal.txt    # 최소 의존성
├── pyproject.toml             # 프로젝트 메타데이터
│
├── .env                        # 환경 변수 (Git 제외)
├── .env.example               # 환경 변수 예제
├── .gitignore
│
└── chat_history.db            # SQLite 데이터베이스 (자동 생성)
```

## 🏗️ 핵심 컴포넌트 설명

### 1. **FastAPI 애플리케이션** (`main.py`)
- 서버의 진입점
- 미들웨어 설정 (CORS)
- 라우터 등록
- 생명주기 관리 (startup/shutdown)

### 2. **Agent 시스템** (`app/agents/`)
- **chat_agent.py**: 기본 Agent 인터페이스
- **langchain_agent.py**: LangChain을 활용한 고급 Agent
  - Tool calling 지원
  - 메모리 관리 (대화 기록)
  - 프롬프트 템플릿

### 3. **도구 (Tools)** (`app/tools/`)
- **base_tool.py**: 모든 도구의 기본 클래스
  ```python
  class BaseTool:
      name: str
      description: str
      parameters: List[Parameter]
      async def run(self, **kwargs) -> str
  ```
- **구현된 도구들**:
  - Calculator: 수학 계산
  - Weather: 날씨 정보 (Mock)
  - Search: 웹 검색 (Mock)

### 4. **데이터 저장소**
- **Redis**: 활성 세션 관리
  - 세션 ID
  - 최근 메시지 (최대 20개)
  - 세션 컨텍스트
  - TTL: 1시간
- **SQLite**: 영구 대화 기록
  - 전체 대화 내용
  - 사용된 도구 정보
  - 모델 정보
  - 토큰 사용량 및 비용

### 5. **API 구조** (`app/routers/chat.py`)
```
POST /api/chat/session          # 세션 생성
POST /api/chat/message          # 메시지 전송
GET  /api/chat/history/{id}     # 대화 기록 조회
GET  /api/chat/tools            # 도구 목록
```

## 🔄 요청 처리 흐름

```
1. 클라이언트 요청
   ↓
2. FastAPI 라우터 (chat.py)
   ↓
3. 세션 검증 (Redis)
   ↓
4. Agent 처리 (langchain_agent.py)
   ├─ 프롬프트 분석
   ├─ 도구 필요성 판단
   ├─ 도구 실행 (필요시)
   └─ 응답 생성
   ↓
5. OpenRouter API 호출
   ↓
6. 결과 저장
   ├─ Redis (세션 업데이트)
   └─ SQLite (영구 저장)
   ↓
7. 클라이언트 응답
```

## 🔧 환경 설정 (`app/core/config.py`)

```python
class Settings(BaseSettings):
    # OpenRouter
    openrouter_api_key: str
    openrouter_base_url: str
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    redis_session_ttl: int
    
    # Model
    default_model: str  # 현재: deepseek/deepseek-chat-v3-0324:free
    max_tokens: int
    temperature: float
```

## 📦 주요 의존성

- **FastAPI**: 웹 프레임워크
- **LangChain**: Agent 프레임워크
- **SQLAlchemy**: ORM
- **Redis**: 세션 관리
- **httpx**: HTTP 클라이언트
- **pydantic**: 데이터 검증

## 🔌 확장 포인트

1. **새로운 도구 추가**: `app/tools/`에 새 파일 생성
2. **새로운 Agent 타입**: `app/agents/`에 구현
3. **API 확장**: `app/routers/`에 새 라우터 추가
4. **모델 변경**: `.env`의 `DEFAULT_MODEL` 수정

## 💡 개발 팁

1. **로깅**: `structlog`를 사용하여 JSON 형식으로 로그 출력
2. **에러 처리**: 모든 예외는 API 레벨에서 처리
3. **비동기**: 모든 I/O 작업은 `async/await` 사용
4. **타입 힌트**: 코드 가독성과 IDE 지원을 위해 적극 활용