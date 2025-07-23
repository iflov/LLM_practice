"""
LangChain 기반 Agent 구현
OpenRouter의 무료 Llama 모델 사용
"""
from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool, StructuredTool
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.schema import BaseMessage

from app.core.config import settings
from app.core.model_config import model_manager
from app.tools.calculator import CalculatorTool
from app.tools.search import SearchTool
from app.tools.weather import WeatherTool
from app.tools.web_search import WebSearchTool
import logging
import httpx

logger = logging.getLogger(__name__)


class LangChainAgent:
    """LangChain을 사용한 Agent 구현"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Model Manager에서 현재 사용 가능한 모델 가져오기
        self.current_model = model_manager.get_current_model()
        logger.info(f"Using model: {self.current_model.id}")
        
        # OpenRouter를 통한 LLM 설정 (OpenAI 호환 API 사용)
        self.llm = self._create_llm(self.current_model.id)
        
        # Tools 초기화
        self.tools = self._initialize_tools()
        
        # Agent 생성
        self.agent_executor = self._create_agent()
        
    def _create_llm(self, model_id: str):
        """LLM 인스턴스 생성"""
        return ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=model_id,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )
        
    def _initialize_tools(self) -> List[Tool]:
        """도구들을 초기화"""
        tools = []
        
        # Calculator Tool
        calc_tool = CalculatorTool()
        tools.append(Tool(
            name="Calculator",
            description="Useful for mathematical calculations",
            func=calc_tool.run
        ))
        
        # Search Tool
        search_tool = SearchTool()
        tools.append(Tool(
            name="Search",
            description="Useful for searching information on the internet",
            func=search_tool.run
        ))
        
        # Weather Tool  
        weather_tool = WeatherTool()
        tools.append(Tool(
            name="Weather",
            description="Get current weather information for a city",
            func=weather_tool.run
        ))
        
        # Web Search Tool
        web_search_tool = WebSearchTool()
        tools.append(Tool(
            name="WebSearch",
            description="Search the web using DuckDuckGo for real-time information and current events",
            func=web_search_tool.run
        ))
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Agent 생성"""
        # Prompt Template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant powered by Llama model.
You have access to the following tools:

{tools}

Use tools when necessary to answer questions accurately.
Always think step by step before using a tool.
If you don't need to use a tool, just respond normally.

Current conversation:
{chat_history}
"""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Agent 생성
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # AgentExecutor 생성
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
        
        return agent_executor
    
    async def process(self, user_input: str, use_tools: bool = True) -> Dict[str, Any]:
        """사용자 입력 처리 (자동 모델 폴백 지원)"""
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Agent 실행
                result = await self.agent_executor.ainvoke({
                    "input": user_input
                })
                
                # 성공 시 실패 카운트 감소
                model_manager.mark_success(self.current_model.id)
                
                return {
                    "success": True,
                    "response": result.get("output", ""),
                    "tools_used": self._extract_tools_used(result),
                    "model_used": self.current_model.id
                }
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Rate limit 에러 감지
                if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                    logger.warning(f"Rate limit hit for model {self.current_model.id}")
                    model_manager.mark_failure(self.current_model.id, "rate_limit")
                    
                    # 다음 사용 가능한 모델로 전환
                    new_model = model_manager.get_next_available_model(require_tools=use_tools)
                    if new_model.id != self.current_model.id:
                        logger.info(f"Switching from {self.current_model.id} to {new_model.id}")
                        self.current_model = new_model
                        self.llm = self._create_llm(new_model.id)
                        self.agent_executor = self._create_agent()
                        continue
                
                # 기타 에러
                logger.error(f"Agent processing error: {str(e)}")
                model_manager.mark_failure(self.current_model.id, "error")
        
        # 모든 재시도 실패
        return {
            "success": False,
            "response": f"죄송합니다. 처리 중 오류가 발생했습니다. (마지막 에러: {str(last_error)})",
            "tools_used": [],
            "model_used": self.current_model.id
        }
    
    def _extract_tools_used(self, result: Dict[str, Any]) -> List[str]:
        """사용된 도구 목록 추출"""
        # LangChain의 intermediate_steps에서 도구 사용 정보 추출
        tools_used = []
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if isinstance(step, tuple) and len(step) > 0:
                    action = step[0]
                    if hasattr(action, "tool"):
                        tools_used.append(action.tool)
        return tools_used
    
    def get_conversation_history(self) -> List[BaseMessage]:
        """대화 기록 반환"""
        return self.memory.chat_memory.messages


class LangChainAgentManager:
    """Agent 인스턴스 관리"""
    
    def __init__(self):
        self.agents: Dict[str, LangChainAgent] = {}
    
    def get_or_create_agent(self, session_id: str) -> LangChainAgent:
        """세션별 Agent 인스턴스 가져오기 또는 생성"""
        if session_id not in self.agents:
            self.agents[session_id] = LangChainAgent(session_id)
            logger.info(f"New LangChain agent created for session: {session_id}")
        
        return self.agents[session_id]
    
    def remove_agent(self, session_id: str):
        """Agent 인스턴스 제거"""
        if session_id in self.agents:
            del self.agents[session_id]
            logger.info(f"Agent removed for session: {session_id}")


# 글로벌 Agent Manager 인스턴스
agent_manager = LangChainAgentManager()