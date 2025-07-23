import redis.asyncio as redis
import json
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
import uuid


class SessionManager:
    def __init__(self):
        self.redis_client = None
        
    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def create_session(self) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        session_data = {
            "created_at": datetime.utcnow().isoformat(),
            "messages": [],
            "context": {}
        }
        await self.redis_client.setex(
            f"session:{session_id}",
            settings.redis_session_ttl,
            json.dumps(session_data)
        )
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        data = await self.redis_client.get(f"session:{session_id}")
        if data:
            # Refresh TTL on access
            await self.redis_client.expire(f"session:{session_id}", settings.redis_session_ttl)
            return json.loads(data)
        return None
    
    async def update_session(self, session_id: str, session_data: Dict[str, Any]):
        """Update session data"""
        await self.redis_client.setex(
            f"session:{session_id}",
            settings.redis_session_ttl,
            json.dumps(session_data)
        )
    
    async def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to session history"""
        session_data = await self.get_session(session_id)
        if not session_data:
            return False
            
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        session_data["messages"].append(message)
        
        # Keep only last 20 messages in Redis (full history is in SQLite)
        if len(session_data["messages"]) > 20:
            session_data["messages"] = session_data["messages"][-20:]
            
        await self.update_session(session_id, session_data)
        return True
    
    async def get_messages(self, session_id: str, limit: int = 10):
        """Get recent messages from session"""
        session_data = await self.get_session(session_id)
        if not session_data:
            return []
        
        messages = session_data.get("messages", [])
        return messages[-limit:] if limit else messages
    
    async def update_context(self, session_id: str, context: Dict[str, Any]):
        """Update session context (for maintaining state between requests)"""
        session_data = await self.get_session(session_id)
        if not session_data:
            return False
            
        session_data["context"].update(context)
        await self.update_session(session_id, session_data)
        return True


# Global instance
# session_manager = SessionManager()

# Redis가 없을 때 Mock 사용
from app.services.session_manager_mock import session_manager