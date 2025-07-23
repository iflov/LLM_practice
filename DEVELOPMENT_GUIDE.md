# 개발 가이드

## 🚀 빠른 시작

### 1. 개발 환경 설정
```bash
# 1. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일에서 OPENROUTER_API_KEY 수정

# 4. Redis 실행
docker run -d -p 6379:6379 redis

# 5. 서버 실행
python main.py
```

### 2. 첫 번째 요청 보내기
```python
import httpx
import asyncio

async def first_chat():
    async with httpx.AsyncClient() as client:
        # 세션 생성
        resp = await client.post("http://localhost:8000/api/chat/session")
        session_id = resp.json()["session_id"]
        
        # 메시지 전송
        resp = await client.post(
            "http://localhost:8000/api/chat/message",
            json={
                "session_id": session_id,
                "message": "Calculate 25 * 4",
                "use_tools": True
            }
        )
        print(resp.json())

asyncio.run(first_chat())
```

## 🛠️ 새로운 도구 추가하기

### 1. 도구 클래스 생성
```python
# app/tools/translator.py
from app.tools.base_tool import BaseTool, Parameter

class TranslatorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="Translator",
            description="Translate text between languages",
            parameters=[
                Parameter(
                    name="text",
                    type="string",
                    description="Text to translate",
                    required=True
                ),
                Parameter(
                    name="target_language",
                    type="string", 
                    description="Target language (e.g., 'ko', 'ja', 'es')",
                    required=True
                )
            ]
        )
    
    async def run(self, text: str, target_language: str) -> str:
        # 실제 번역 API 호출 또는 Mock 응답
        translations = {
            "ko": f"[Korean] {text}의 한국어 번역",
            "ja": f"[Japanese] {text}の日本語訳",
            "es": f"[Spanish] Traducción de {text}"
        }
        return translations.get(target_language, f"Translation of '{text}' to {target_language}")
```

### 2. 도구 등록
```python
# app/tools/__init__.py에 추가
from app.tools.translator import TranslatorTool

def get_all_tools():
    return {
        "Calculator": CalculatorTool(),
        "Weather": WeatherTool(),
        "Search": SearchTool(),
        "Translator": TranslatorTool()  # 새 도구 추가
    }
```

## 🤖 Agent 커스터마이징

### 1. 프롬프트 수정
```python
# app/agents/langchain_agent.py
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant.
    
특별 지시사항:
- 한국어 질문에는 한국어로 답변
- 계산 결과는 단계별로 설명
- 도구 사용 전 사용자에게 알림

Available tools: {tools}
"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])
```

### 2. 메모리 설정 변경
```python
# 대화 기록 크기 조정
self.memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    k=10  # 최근 10개 메시지만 유지
)
```

## 📝 API 엔드포인트 추가

### 1. 새 라우터 생성
```python
# app/routers/admin.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/stats")
async def get_statistics():
    """시스템 통계 조회"""
    return {
        "total_sessions": await get_total_sessions(),
        "active_sessions": await get_active_sessions(),
        "total_messages": await get_total_messages()
    }
```

### 2. 라우터 등록
```python
# main.py
from app.routers import chat, admin

app.include_router(chat.router)
app.include_router(admin.router)  # 새 라우터 추가
```

## 🧪 테스트 작성

### 1. 도구 테스트
```python
# tests/unit/test_calculator.py
import pytest
from app.tools.calculator import CalculatorTool

@pytest.mark.asyncio
async def test_calculator_addition():
    calc = CalculatorTool()
    result = await calc.run(expression="2 + 2")
    assert "4" in result

@pytest.mark.asyncio
async def test_calculator_complex():
    calc = CalculatorTool()
    result = await calc.run(expression="(10 * 5) + 20")
    assert "70" in result
```

### 2. API 테스트
```python
# tests/integration/test_chat_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_session(client: AsyncClient):
    response = await client.post("/api/chat/session")
    assert response.status_code == 200
    assert "session_id" in response.json()
```

## 🐛 디버깅 팁

### 1. 로깅 활성화
```python
# 상세 로그 보기
import logging
logging.basicConfig(level=logging.DEBUG)

# LangChain 디버그 모드
import langchain
langchain.verbose = True
```

### 2. 데이터베이스 확인
```bash
# SQLite 데이터 조회
sqlite3 chat_history.db

# 최근 대화 확인
SELECT * FROM chat_history ORDER BY created_at DESC LIMIT 5;

# 특정 세션 추적
SELECT * FROM chat_history WHERE session_id = 'your-session-id';
```

### 3. Redis 모니터링
```bash
# Redis CLI 접속
redis-cli

# 모든 세션 키 확인
KEYS session:*

# 특정 세션 내용 확인
GET session:your-session-id
```

## 🚀 성능 최적화

### 1. 비동기 처리 개선
```python
# 동시 도구 실행
import asyncio

async def execute_multiple_tools(tools_to_run):
    tasks = [tool.run(**params) for tool, params in tools_to_run]
    results = await asyncio.gather(*tasks)
    return results
```

### 2. 캐싱 구현
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_result(tool_name: str, params: str):
    # 자주 사용되는 도구 결과 캐싱
    pass
```

## 📚 추가 학습 자료

1. **LangChain 심화**
   - [LangChain Cookbook](https://github.com/langchain-ai/langchain/tree/master/cookbook)
   - [Agent Types](https://python.langchain.com/docs/modules/agents/agent_types/)

2. **OpenRouter 활용**
   - [Model Comparison](https://openrouter.ai/models)
   - [API Documentation](https://openrouter.ai/docs)

3. **FastAPI 고급**
   - [Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
   - [Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

## 🤝 기여 가이드라인

1. **코드 스타일**: Black formatter 사용
2. **타입 힌트**: 모든 함수에 타입 힌트 추가
3. **문서화**: Docstring 작성 필수
4. **테스트**: 새 기능에는 테스트 추가