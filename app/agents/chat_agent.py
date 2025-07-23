from typing import List, Dict, Any, Optional
from app.services.openrouter_client import OpenRouterClient
from app.services.openrouter_fallback_client import OpenRouterFallbackClient
from app.services.session_manager import session_manager
from app.models.database import ChatHistory, AsyncSessionLocal
from app.core.config import settings
from sqlalchemy import select
import json


class ChatAgent:
    def __init__(self, use_fallback: bool = True):
        # Fallback 지원 여부에 따라 클라이언트 선택
        if use_fallback:
            self.openrouter_client = OpenRouterFallbackClient()
        else:
            self.openrouter_client = OpenRouterClient()
        
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
        
        # Get response from OpenRouter
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
        
        # Save to database
        await self._save_to_database(
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
        )
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "usage": usage,
            "model_used": model_used
        }
    
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
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ChatHistory)
                .where(ChatHistory.session_id == session_id)
                .order_by(ChatHistory.created_at.desc())
                .limit(limit)
            )
            
            history = []
            for chat in result.scalars():
                history.append({
                    "id": chat.id,
                    "user_message": chat.user_message,
                    "assistant_message": chat.assistant_message,
                    "tools_used": chat.tools_used,
                    "created_at": chat.created_at.isoformat(),
                    "metadata": chat.metadata
                })
            
            # Reverse to get chronological order
            return history[::-1]