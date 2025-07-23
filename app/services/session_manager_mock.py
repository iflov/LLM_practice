"""
Mock Session Manager - Redis 없이 메모리에서 동작
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class MockSessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
    async def connect(self):
        """Mock connect - 아무것도 하지 않음"""
        pass
        
    async def disconnect(self):
        """Mock disconnect - 아무것도 하지 않음"""
        pass
    
    async def create_session(self) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        session_data = {
            "created_at": datetime.utcnow().isoformat(),
            "messages": [],
            "context": {}
        }
        self.sessions[session_id] = session_data
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.sessions.get(session_id)
    
    async def update_session(self, session_id: str, session_data: Dict[str, Any]):
        """Update session data"""
        self.sessions[session_id] = session_data
    
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
        
        # Keep only last 20 messages
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
        """Update session context"""
        session_data = await self.get_session(session_id)
        if not session_data:
            return False
            
        session_data["context"].update(context)
        await self.update_session(session_id, session_data)
        return True


# Global instance
session_manager = MockSessionManager()