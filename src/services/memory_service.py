from typing import List, Dict, Optional
from datetime import datetime
from src.core.database import db
from src.core.logging_config import get_logger
from src.models.mongodb import MessageDoc

logger = get_logger(__name__)

class MemoryService:
    @property
    def sessions_col(self):
        return db.db["sessions"]

    async def get_history(self, session_id: str, limit: int = 5, skip: int = 0) -> List[Dict[str, str]]:
        """
        Retrieves history for a session with pagination support.
        - limit: Number of messages to return.
        - skip: Number of messages to skip from the end (most recent).
        Default limit=5 (for LLM context). limit=0 means return ALL messages.
        """
        logger.info(f"Retrieving persistent history for session: {session_id}, limit: {limit}, skip: {skip}")
        session = await self.sessions_col.find_one({"id": session_id})
        if not session:
            return []
        
        # Messages are stored in order: [oldest, ..., newest]
        messages = session.get("messages", [])
        total_count = len(messages)
        
        if limit == 0:
            # Return all messages (historical behavior)
            history = messages
        else:
            # Slice from the end
            start = max(0, total_count - skip - limit)
            end = total_count - skip
            if end <= 0:
                history = []
            else:
                history = messages[start:end]
        
        return [{"id": m.get("id"), "role": m["role"], "content": m["content"]} for m in history]

    async def add_message(self, session_id: str, role: str, content: str) -> MessageDoc:
        logger.info(f"Adding persistent message to session: {session_id}, role: {role}")
        message = MessageDoc(role=role, content=content)
        
        await self.sessions_col.update_one(
            {"id": session_id},
            {
                "$push": {"messages": message.model_dump()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return message

    async def create_session(self, user_id: str, title: str = "New Chat") -> str:
        from src.models.mongodb import SessionDoc
        logger.info(f"Creating new persistent session for user: {user_id}")
        session = SessionDoc(user_id=user_id, title=title)
        await self.sessions_col.insert_one(session.model_dump())
        return session.id

    async def list_sessions(self, user_id: str) -> List[Dict]:
        logger.info(f"Listing sessions for user: {user_id}")
        cursor = self.sessions_col.find({"user_id": user_id}).sort("updated_at", -1)
        sessions = await cursor.to_list(length=100)
        return sessions

memory_service = MemoryService()
