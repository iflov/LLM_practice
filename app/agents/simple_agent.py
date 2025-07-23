"""
Tool 없이 작동하는 간단한 Agent
무료 모델로도 Agent의 핵심 기능을 구현할 수 있습니다.
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SimpleAgent:
    """Tool 없이 작동하는 간단한 Agent"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # OpenRouter를 통한 모델 설정
        self.llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.default_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )
        
        # Agent의 시스템 프롬프트
        self.system_prompt = """You are a helpful AI assistant with the following capabilities:

1. **Memory**: I can remember our conversation context
2. **Reasoning**: I can analyze problems step by step
3. **Planning**: I can break down complex tasks into steps
4. **Expertise**: I have knowledge in various domains

Although I don't have access to external tools in this session, I can:
- Provide detailed explanations
- Help with problem-solving
- Offer creative solutions
- Maintain context across our conversation

How can I assist you today?"""
    
    async def process(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력 처리"""
        try:
            # 메시지 준비
            messages = [SystemMessage(content=self.system_prompt)]
            
            # 대화 기록 추가
            for message in self.memory.chat_memory.messages:
                messages.append(message)
            
            # 현재 사용자 입력 추가
            messages.append(HumanMessage(content=user_input))
            
            # LLM 호출
            response = await self.llm.ainvoke(messages)
            
            # 메모리에 저장
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(response.content)
            
            # Agent의 "추론 과정" 시뮬레이션
            reasoning_steps = self._simulate_reasoning(user_input)
            
            return {
                "success": True,
                "response": response.content,
                "reasoning_steps": reasoning_steps,
                "model_used": settings.default_model
            }
            
        except Exception as e:
            logger.error(f"Agent processing error: {str(e)}")
            return {
                "success": False,
                "response": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                "reasoning_steps": [],
                "model_used": settings.default_model
            }
    
    def _simulate_reasoning(self, user_input: str) -> List[str]:
        """Agent의 추론 과정 시뮬레이션 (교육 목적)"""
        steps = []
        
        # 간단한 키워드 기반 추론 단계 생성
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ["what", "why", "how", "explain"]):
            steps.append("질문 유형 분석: 설명 요청")
            steps.append("관련 지식 검색 중...")
            steps.append("답변 구조화...")
        
        elif any(word in input_lower for word in ["calculate", "compute", "math"]):
            steps.append("작업 유형: 계산 요청")
            steps.append("수식 분석 중...")
            steps.append("단계별 계산 수행...")
        
        elif any(word in input_lower for word in ["summarize", "summary"]):
            steps.append("작업 유형: 요약 요청")
            steps.append("이전 대화 컨텍스트 분석...")
            steps.append("핵심 포인트 추출...")
        
        else:
            steps.append("입력 분석 중...")
            steps.append("응답 생성 중...")
        
        return steps
    
    def get_conversation_history(self) -> List[Any]:
        """대화 기록 반환"""
        return self.memory.chat_memory.messages


class SimpleAgentManager:
    """Agent 인스턴스 관리"""
    
    def __init__(self):
        self.agents: Dict[str, SimpleAgent] = {}
    
    def get_or_create_agent(self, session_id: str) -> SimpleAgent:
        """세션별 Agent 인스턴스 가져오기 또는 생성"""
        if session_id not in self.agents:
            self.agents[session_id] = SimpleAgent(session_id)
            logger.info(f"New simple agent created for session: {session_id}")
        
        return self.agents[session_id]
    
    def remove_agent(self, session_id: str):
        """Agent 인스턴스 제거"""
        if session_id in self.agents:
            del self.agents[session_id]
            logger.info(f"Agent removed for session: {session_id}")


# 글로벌 Agent Manager 인스턴스
simple_agent_manager = SimpleAgentManager()