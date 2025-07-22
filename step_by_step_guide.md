# 🎯 LLM Agent POC 단계별 가이드

## 지금 당장 할 수 있는 것들

### 1️⃣ 가장 간단한 예제부터 실행 (5분)
```bash
# 개념 이해를 위한 간단한 예제 실행
python simple_example.py
```

이 예제로 Agent의 기본 개념을 이해:
- Agent가 뭔지
- Tool이 뭔지
- 어떻게 동작하는지

### 2️⃣ 실제 서버 띄워보기 (10분)
```bash
# 1. 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 패키지 설치
pip install fastapi uvicorn httpx sse-starlette pydantic

# 3. 서버 실행
python main.py
```

서버가 뜨면 http://localhost:8000/docs 에서 API 문서 확인

### 3️⃣ API 테스트해보기 (5분)
```bash
# 다른 터미널에서
python test_api.py
```

실제로 Agent가 어떻게 응답하는지 확인

## 🚀 다음 단계: 실제 LLM 연결하기

### OpenRouter 설정 (15분)
1. https://openrouter.ai 가입
2. API 키 발급
3. `.env` 파일에 키 설정
   ```
   OPENROUTER_API_KEY=sk-or-v1-xxxxx
   ```

### 간단한 LLM 호출 테스트
```python
# test_openrouter.py
import asyncio
from src.services.openrouter_client import OpenRouterClient

async def test():
    client = OpenRouterClient()
    result = await client.chat_completion(
        messages=[{"role": "user", "content": "안녕?"}],
        model="anthropic/claude-3-haiku-20240307"  # 가장 저렴
    )
    print(result)

asyncio.run(test())
```

## 💡 Agent 개발의 핵심 포인트

### 1. Agent = 역할 + 도구
```python
class MyAgent:
    role = "Python 코딩 도우미"
    tools = ["code_executor", "web_search", "file_reader"]
```

### 2. Tool = 함수
```python
def web_search(query: str) -> str:
    """웹에서 정보를 검색합니다"""
    # 실제 검색 로직
    return "검색 결과"
```

### 3. Orchestration = 조율
```python
# 사용자 입력 → Agent 선택 → Tool 실행 → 응답 생성
user_input → select_agent() → use_tools() → generate_response()
```

## 📚 학습 순서 추천

### Week 1: 기초
1. **Prompt Engineering** (2일)
   - System prompt 작성법
   - Few-shot examples
   
2. **Function Calling** (2일)
   - OpenAI 문서 읽기
   - 간단한 도구 만들기

3. **간단한 Agent** (3일)
   - 단일 Agent 구현
   - 2-3개 도구 추가

### Week 2: 심화
1. **Multi-Agent** (3일)
   - Agent 간 협업
   - 작업 분배

2. **Memory 추가** (2일)
   - 대화 맥락 유지
   - Redis 활용

3. **실제 서비스** (2일)
   - Error handling
   - Rate limiting

## 🛠️ 추천 도구/라이브러리

### 초보자용
- **LangChain** - 가장 문서화가 잘됨
- **Instructor** - Pydantic 기반 구조화된 출력

### 중급자용
- **CrewAI** - 멀티 에이전트
- **AutoGen** - Microsoft의 에이전트 프레임워크

### 실험용
- **MemGPT** - 메모리 관리
- **AgentGPT** - 웹 기반 자율 에이전트

## ❓ 자주 하는 질문

**Q: Agent랑 일반 챗봇이랑 뭐가 달라?**
A: Agent는 도구를 사용하고, 계획을 세우고, 자율적으로 행동할 수 있음

**Q: 꼭 OpenRouter를 써야 해?**
A: 아니요. OpenAI API, Anthropic API 직접 사용 가능

**Q: 비용이 많이 들어?**
A: 모델 선택이 중요. Haiku나 GPT-3.5는 저렴함

## 🎬 지금 바로 시작하기

```bash
# 1. 예제 실행
python simple_example.py

# 2. 서버 실행
python main.py

# 3. 브라우저에서 확인
open http://localhost:8000/docs

# 4. API 테스트
python test_api.py
```

막막하신가요? 가장 간단한 것부터 하나씩 실행해보세요! 🚀