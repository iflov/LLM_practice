# 빠른 참조 가이드

## 🎯 프로젝트 한눈에 보기

**목적**: LLM Agent 개발 학습을 위한 POC
**핵심**: OpenRouter + LangChain + Tool Calling
**현재 모델**: `deepseek/deepseek-chat-v3-0324:free`

## 🚀 30초 시작하기

```bash
# 1. Redis 실행
docker run -d -p 6379:6379 redis

# 2. 서버 실행
python main.py

# 3. API 문서 확인
open http://localhost:8000/docs
```

## 📡 주요 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/chat/session` | POST | 세션 생성 |
| `/api/chat/message` | POST | 메시지 전송 |
| `/api/chat/history/{id}` | GET | 대화 기록 |
| `/api/chat/tools` | GET | 도구 목록 |

## 🛠️ 사용 가능한 도구

| 도구 | 기능 | 예제 |
|------|------|------|
| Calculator | 수학 계산 | "What is 25 * 4?" |
| Weather | 날씨 정보 | "Weather in Seoul?" |
| Search | 웹 검색 | "Search Python async" |

## 📂 핵심 파일 위치

| 파일 | 용도 |
|------|------|
| `main.py` | 서버 진입점 |
| `.env` | 환경 설정 |
| `app/agents/langchain_agent.py` | Agent 로직 |
| `app/tools/` | 도구 구현 |
| `app/routers/chat.py` | API 엔드포인트 |
| `chat_history.db` | 대화 기록 DB |

## 🔍 디버깅 명령어

```bash
# 로그 확인
tail -f logs/app.log

# DB 확인
sqlite3 chat_history.db "SELECT * FROM chat_history ORDER BY created_at DESC LIMIT 5;"

# Redis 확인
redis-cli KEYS "session:*"

# 프로세스 확인
ps aux | grep python
```

## 💡 자주 사용하는 코드 스니펫

### Python으로 API 호출
```python
import httpx
async with httpx.AsyncClient() as client:
    # 세션 생성
    r = await client.post("http://localhost:8000/api/chat/session")
    session_id = r.json()["session_id"]
    
    # 메시지 전송
    r = await client.post(
        "http://localhost:8000/api/chat/message",
        json={"session_id": session_id, "message": "Hello", "use_tools": True}
    )
```

### curl로 테스트
```bash
# 세션 생성
curl -X POST http://localhost:8000/api/chat/session

# 메시지 전송
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SESSION_ID","message":"Hello","use_tools":true}'
```

## ⚙️ 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OPENROUTER_API_KEY` | - | 필수 |
| `DEFAULT_MODEL` | deepseek/deepseek-chat-v3-0324:free | LLM 모델 |
| `REDIS_URL` | redis://localhost:6379/0 | Redis 주소 |
| `DATABASE_URL` | sqlite+aiosqlite:///./chat_history.db | DB 경로 |

## 🐛 일반적인 문제 해결

| 문제 | 해결 방법 |
|------|----------|
| "No module named 'greenlet'" | `pip install greenlet` |
| "Address already in use" | `lsof -i :8000` → `kill -9 PID` |
| "Redis connection refused" | Redis 서버 실행 확인 |
| "Invalid API key" | `.env` 파일의 OPENROUTER_API_KEY 확인 |

## 📚 더 알아보기

- **전체 구조**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- **아키텍처**: [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)
- **개발 가이드**: [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)