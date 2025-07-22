# LLM Agent POC 빠른 시작 가이드

## 🎯 POC 개발 전략

### 1단계: 최소 기능 Agent (1-2일)
```python
# 간단한 Agent 구조 예제
class SimpleAgent:
    def __init__(self, model, tools):
        self.model = model
        self.tools = tools
    
    async def run(self, prompt):
        # 1. 프롬프트 분석
        # 2. Tool 선택
        # 3. 실행 및 응답
        pass
```

### 2단계: Tool Calling 구현 (1일)
- Calculator, WebSearch, Database Query 등 간단한 도구들
- OpenRouter의 function calling 기능 활용

### 3단계: Agent 라우팅 (1-2일)
- 프롬프트 분류기 (Intent Classification)
- 적절한 Agent로 라우팅
- 응답 병합

## 🔧 추천 기술 스택 (간소화)

```python
# 최소한의 의존성
langchain==0.1.0  # Agent 프레임워크
openai==1.12.0    # OpenRouter 호출용
fastapi==0.104.1  # API 서버
```

## 📖 핵심 학습 포인트

1. **Prompt Engineering**
   - System prompts로 Agent 역할 정의
   - Few-shot examples 활용

2. **Tool Definition**
   ```python
   tools = [
       {
           "name": "search",
           "description": "Search for information",
           "parameters": {...}
       }
   ]
   ```

3. **Agent Loop**
   - Observe → Think → Act → Observe 패턴
   - ReAct (Reasoning + Acting) 방식

## 🚀 빠른 프로토타입 예제

```python
# src/agents/base_agent.py
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser

class BaseAgent:
    def __init__(self, llm, tools, system_prompt):
        self.llm = llm
        self.tools = tools
        self.system_prompt = system_prompt
        
    async def execute(self, user_input: str):
        # Agent 실행 로직
        pass
```

## 📚 추천 학습 순서

1. **OpenAI Function Calling 이해** (2-3시간)
   - [공식 문서](https://platform.openai.com/docs/guides/function-calling)
   
2. **LangChain Agent 튜토리얼** (1일)
   - [Agent 개념](https://python.langchain.com/docs/modules/agents/)
   
3. **실제 구현** (2-3일)
   - 단일 Agent → Tool 추가 → Multi-Agent

## 💡 POC 팁

- 복잡한 기능보다는 동작하는 프로토타입에 집중
- 하드코딩된 예제로 시작해서 점진적으로 개선
- 로깅을 충분히 추가해서 Agent의 사고 과정 추적
- OpenRouter의 다양한 모델로 실험 (비용 최적화)

## 🔗 유용한 리소스

- [Awesome LLM Agents](https://github.com/hyp1231/awesome-llm-agents)
- [LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/)
- [Building LLM Agents Tutorial](https://www.youtube.com/watch?v=DWUdGhRrv2c)