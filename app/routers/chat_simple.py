"""
Tool 없이도 작동하는 간단한 Chat Router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.agents.simple_agent import simple_agent_manager
from app.services.session_manager import session_manager
from app.models.database import save_message
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/simple", tags=["simple-chat"])


class ChatMessage(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    success: bool
    response: str
    reasoning_steps: List[str] = []
    model_used: str


@router.post("/chat", response_model=ChatResponse)
async def simple_chat(request: ChatMessage):
    """Tool 없이 대화하기"""
    try:
        # 세션 확인
        session_data = await session_manager.get_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Agent 가져오기
        agent = simple_agent_manager.get_or_create_agent(request.session_id)
        
        # 메시지 처리
        result = await agent.process(request.message)
        
        # 대화 저장
        await save_message(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
        
        await save_message(
            session_id=request.session_id,
            role="assistant",
            content=result["response"],
            metadata={
                "model": result.get("model_used", "unknown"),
                "reasoning_steps": result.get("reasoning_steps", [])
            }
        )
        
        # Redis에도 저장
        await session_manager.add_message(
            request.session_id, 
            "user", 
            request.message
        )
        await session_manager.add_message(
            request.session_id, 
            "assistant", 
            result["response"],
            {"model": result.get("model_used")}
        )
        
        return ChatResponse(
            success=result["success"],
            response=result["response"],
            reasoning_steps=result.get("reasoning_steps", []),
            model_used=result.get("model_used", "unknown")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo")
async def demo_agent():
    """Agent 데모 - 세션 생성부터 대화까지"""
    try:
        # 세션 생성
        session_id = await session_manager.create_session()
        
        # Agent 생성
        agent = simple_agent_manager.get_or_create_agent(session_id)
        
        # 데모 대화
        demo_messages = [
            "Hello! What is an AI agent?",
            "Can you explain the key components?",
            "How does memory work in agents?"
        ]
        
        responses = []
        for msg in demo_messages:
            result = await agent.process(msg)
            responses.append({
                "user": msg,
                "agent": result["response"],
                "reasoning": result.get("reasoning_steps", [])
            })
        
        return {
            "session_id": session_id,
            "demo_conversation": responses,
            "model_used": settings.default_model,
            "note": "This is a simple agent without external tools"
        }
        
    except Exception as e:
        logger.error(f"Demo error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))