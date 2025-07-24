from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, AsyncGenerator
import json
import asyncio
from app.agents.chat_agent import ChatAgent
from app.services.session_manager import session_manager
from app.tools import get_all_tools
from app.core.config import settings
from app.core.model_config import AVAILABLE_MODELS, get_fallback_models


router = APIRouter(prefix="/api/chat", tags=["chat"])
chat_agent = ChatAgent(use_fallback=settings.fallback_enabled)


class ChatRequest(BaseModel):
    message: str
    use_tools: bool = True
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    response: str
    tools_used: List[Dict[str, Any]]
    session_id: str
    model_used: str


class SessionResponse(BaseModel):
    session_id: str


@router.post("/session")
async def create_session() -> SessionResponse:
    """Create a new chat session"""
    session_id = await session_manager.create_session()
    return SessionResponse(session_id=session_id)


@router.post("/message")
async def send_message(request: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    """Send a message to the chat agent"""
    
    # Get or create session
    session_id = request.session_id
    if not session_id:
        session_id = await session_manager.create_session()
    else:
        # Check if session exists
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            # Create new session if not found
            session_id = await session_manager.create_session()
    
    try:
        # Process message with agent
        result = await chat_agent.process_message(
            session_id=session_id,
            user_message=request.message,
            use_tools=request.use_tools
        )
        
        # Format tool usage information
        tools_used = []
        for tool_call in result.get("tool_calls", []):
            tools_used.append({
                "tool": tool_call["tool_name"],
                "args": tool_call["tool_args"],
                "result": tool_call["result"]
            })
        
        return ChatResponse(
            response=result["content"],
            tools_used=tools_used,
            session_id=session_id,
            model_used=result.get("model_used", "unknown")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get chat history for a session"""
    
    # Check if session exists
    session_data = await session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get history from database
    history = await chat_agent.get_chat_history(session_id, limit)
    return history


@router.get("/tools")
async def list_available_tools() -> Dict[str, List[Dict[str, Any]]]:
    """List all available tools"""
    tools = get_all_tools()
    
    tool_list = []
    for name, tool in tools.items():
        tool_list.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "required": param.required
                }
                for param in tool.parameters
            ]
        })
    
    return {"tools": tool_list}


@router.get("/models")
async def list_available_models() -> Dict[str, Any]:
    """List all available models and fallback configuration"""
    
    # Fallback 모델 리스트
    fallback_models = get_fallback_models(
        require_tools=True,
        free_only=settings.fallback_free_only
    )
    
    return {
        "default_model": settings.default_model,
        "fallback_enabled": settings.fallback_enabled,
        "fallback_free_only": settings.fallback_free_only,
        "available_models": [
            {
                "id": model.id,
                "name": model.name,
                "supports_tools": model.supports_tools,
                "is_free": model.is_free,
                "context_length": model.context_length,
                "priority": model.priority
            }
            for model in AVAILABLE_MODELS
        ],
        "fallback_order": [model.id for model in fallback_models]
    }


@router.post("/message/stream")
async def send_message_stream(request: ChatRequest):
    """Send a message to the chat agent with streaming response"""
    
    # Get or create session
    session_id = request.session_id
    if not session_id:
        session_id = await session_manager.create_session()
    else:
        # Check if session exists
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            session_id = await session_manager.create_session()
    
    async def generate() -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        try:
            # Send initial metadata
            yield f"data: {json.dumps({'type': 'metadata', 'session_id': session_id})}\n\n"
            
            # Process message with streaming
            async for chunk in chat_agent.process_message_stream(
                session_id=session_id,
                user_message=request.message,
                use_tools=request.use_tools
            ):
                if chunk["type"] == "token":
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk['content']})}\n\n"
                elif chunk["type"] == "tool_call":
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': chunk['tool'], 'args': chunk['args']})}\n\n"
                elif chunk["type"] == "tool_result":
                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': chunk['tool'], 'result': chunk['result']})}\n\n"
                elif chunk["type"] == "done":
                    yield f"data: {json.dumps({'type': 'done', 'model_used': chunk.get('model_used', 'unknown')})}\n\n"
                    
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )