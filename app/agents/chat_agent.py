from typing import List, Dict, Any, Optional, AsyncGenerator
from app.services.openrouter_client import OpenRouterClient
from app.services.openrouter_fallback_client import OpenRouterFallbackClient
from app.services.mock_client import MockOpenRouterClient
from app.services.session_manager import session_manager
from app.models.database import ChatHistory, AsyncSessionLocal
from app.core.config import settings
from sqlalchemy import select
import json
import logging
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class ChatAgent:
    def __init__(self, use_fallback: bool = True):
        # Fallback 지원 여부에 따라 클라이언트 선택
        if use_fallback:
            self.openrouter_client = OpenRouterFallbackClient()
        else:
            self.openrouter_client = OpenRouterClient()
        
        # Mock 클라이언트 (Rate limit 시 사용)
        self.mock_client = MockOpenRouterClient()
        self.use_mock_mode = False
        
    async def process_message(
        self,
        session_id: str,
        user_message: str,
        use_tools: bool = True
    ) -> Dict[str, Any]:
        """Process a user message and return response with tool usage info"""
        
        # Save user message to session FIRST
        await session_manager.add_message(
            session_id,
            "user",
            user_message
        )
        
        # Get session context (now includes the new message)
        messages = await session_manager.get_messages(session_id, limit=10)
        
        # Convert to OpenAI format
        chat_messages = []
        
        # Add system message first
        chat_messages.append({
            "role": "system",
            "content": "You are a helpful AI assistant with access to various tools. Remember the conversation context and user information shared in previous messages."
        })
        
        # Add conversation history
        for msg in messages:
            if msg["role"] in ["user", "assistant"]:
                chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Get response from OpenRouter (with rate limit handling)
        response = None
        
        # Mock 모드가 활성화된 경우
        if self.use_mock_mode:
            logger.info("Using mock client due to rate limits")
            response = await self.mock_client.chat_completion_with_fallback(
                messages=chat_messages,
                use_tools=use_tools
            )
        else:
            try:
                if isinstance(self.openrouter_client, OpenRouterFallbackClient):
                    # Fallback client 사용
                    response = await self.openrouter_client.chat_completion_with_fallback(
                        messages=chat_messages,
                        use_tools=use_tools
                    )
                else:
                    # 기존 client 사용
                    if use_tools:
                        response = await self.openrouter_client.chat_completion_with_tools(
                            messages=chat_messages
                        )
                    else:
                        response = await self.openrouter_client.simple_chat_completion(
                            messages=chat_messages
                        )
                
                # Rate limit 감지
                if response and response.get("content", ""):
                    content = response["content"]
                    if "Rate limit exceeded" in content or "All models failed" in content:
                        logger.warning("Rate limit detected, switching to mock mode")
                        self.use_mock_mode = True
                        response = await self.mock_client.chat_completion_with_fallback(
                            messages=chat_messages,
                            use_tools=use_tools
                        )
                        
            except Exception as e:
                error_msg = str(e)
                if "Rate limit exceeded" in error_msg or "429" in error_msg:
                    logger.warning("Rate limit exception, switching to mock mode")
                    self.use_mock_mode = True
                    response = await self.mock_client.chat_completion_with_fallback(
                        messages=chat_messages,
                        use_tools=use_tools
                    )
                else:
                    raise
        
        # Safely extract content and tool_calls
        content = response.get("content", "") if response else ""
        tool_calls = response.get("tool_calls", []) if response else []
        usage = response.get("usage", {}) if response else {}
        model_used = response.get("model_used", settings.default_model) if response else settings.default_model
        
        await session_manager.add_message(
            session_id,
            "assistant",
            content,
            metadata={
                "tool_calls": tool_calls,
                "usage": usage,
                "model_used": model_used
            }
        )
        
        # 백그라운드로 DB 저장 (성능 향상)
        asyncio.create_task(self._save_to_database(
            session_id=session_id,
            user_message=user_message,
            assistant_message=content,
            tools_used=[tc.get("tool_name", "") for tc in tool_calls if isinstance(tc, dict)],
            metadata={
                "content": content,
                "tool_calls": tool_calls,
                "usage": usage,
                "model": model_used
            }
        ))
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "usage": usage,
            "model_used": model_used
        }
    
    async def process_message_stream(
        self,
        session_id: str,
        user_message: str,
        use_tools: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a user message with streaming response"""
        
        # Save user message to session FIRST
        await session_manager.add_message(
            session_id,
            "user",
            user_message
        )
        
        # Get session context (now includes the new message)
        messages = await session_manager.get_messages(session_id, limit=10)
        
        # Convert to OpenAI format
        chat_messages = []
        
        # Add system message first
        chat_messages.append({
            "role": "system",
            "content": "You are a helpful AI assistant with access to various tools. Remember the conversation context and user information shared in previous messages."
        })
        
        # Add conversation history
        for msg in messages:
            if msg["role"] in ["user", "assistant"]:
                chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        try:
            # Stream response from client
            if self.use_mock_mode:
                # Mock doesn't support streaming yet, so simulate it
                response = await self.mock_client.chat_completion_with_fallback(
                    messages=chat_messages,
                    use_tools=use_tools
                )
                # Simulate streaming
                content = response.get("content", "")
                for i in range(0, len(content), 10):  # Stream in chunks of 10 chars
                    yield {"type": "token", "content": content[i:i+10]}
                    await asyncio.sleep(0.01)  # Small delay to simulate streaming
                
                for tool_call in response.get("tool_calls", []):
                    yield {"type": "tool_call", "tool": tool_call.get("tool_name"), "args": tool_call.get("tool_args")}
                    yield {"type": "tool_result", "tool": tool_call.get("tool_name"), "result": tool_call.get("result")}
                
                yield {"type": "done", "model_used": response.get("model_used", "unknown")}
                
                # Save to session and DB in background
                asyncio.create_task(self._save_stream_result(
                    session_id, content, response.get("tool_calls", []), 
                    response.get("usage", {}), response.get("model_used", "unknown")
                ))
            else:
                # Real streaming from OpenRouter
                if isinstance(self.openrouter_client, OpenRouterFallbackClient):
                    # Streaming with fallback
                    async for chunk in self.openrouter_client.stream_chat_completion_with_fallback(
                        messages=chat_messages,
                        use_tools=use_tools
                    ):
                        yield chunk
                else:
                    # Direct streaming (not implemented yet in base client)
                    # Fall back to non-streaming for now
                    response = await self.openrouter_client.chat_completion_with_tools(
                        messages=chat_messages
                    ) if use_tools else await self.openrouter_client.simple_chat_completion(
                        messages=chat_messages
                    )
                    
                    content = response.get("content", "")
                    for i in range(0, len(content), 10):
                        yield {"type": "token", "content": content[i:i+10]}
                        await asyncio.sleep(0.01)
                    
                    yield {"type": "done", "model_used": response.get("model_used", settings.default_model)}
                    
        except Exception as e:
            yield {"type": "error", "error": str(e)}
    
    async def _save_stream_result(
        self,
        session_id: str,
        content: str,
        tool_calls: List[Dict],
        usage: Dict,
        model_used: str
    ):
        """Save streaming result to session and database"""
        await session_manager.add_message(
            session_id,
            "assistant",
            content,
            metadata={
                "tool_calls": tool_calls,
                "usage": usage,
                "model_used": model_used
            }
        )
        
        # Save to database
        await self._save_to_database(
            session_id=session_id,
            user_message="",  # Already saved
            assistant_message=content,
            tools_used=[tc.get("tool_name", "") for tc in tool_calls if isinstance(tc, dict)],
            metadata={
                "content": content,
                "tool_calls": tool_calls,
                "usage": usage,
                "model": model_used
            }
        )
    
    async def _save_to_database(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        tools_used: List[str],
        metadata: Dict[str, Any]
    ):
        """Save chat history to database"""
        async with AsyncSessionLocal() as db:
            chat_history = ChatHistory(
                session_id=session_id,
                user_message=user_message,
                assistant_message=assistant_message,
                tools_used=tools_used,
                model_used=metadata.get("model", "unknown"),
                tokens_used=metadata.get("usage", {}).get("total_tokens"),
                metadata=metadata
            )
            db.add(chat_history)
            await db.commit()
    
    async def get_chat_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get chat history from database"""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(ChatHistory)
                    .where(ChatHistory.session_id == session_id)
                    .order_by(ChatHistory.created_at.desc())
                    .limit(limit)
                )
                
                history = []
                for chat in result.scalars():
                    # Safely handle metadata
                    metadata = chat.metadata if chat.metadata else {}
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    
                    # Safely handle tools_used
                    tools_used = chat.tools_used if chat.tools_used else []
                    if isinstance(tools_used, str):
                        try:
                            tools_used = json.loads(tools_used)
                        except:
                            tools_used = []
                    
                    history.append({
                        "id": chat.id,
                        "user_message": chat.user_message or "",
                        "assistant_message": chat.assistant_message or "",
                        "tools_used": tools_used,
                        "model_used": chat.model_used or "unknown",
                        "created_at": chat.created_at.isoformat() if chat.created_at else "",
                        "metadata": metadata
                    })
                
                # Reverse to get chronological order
                return history[::-1]
                
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return []