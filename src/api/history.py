from fastapi import APIRouter, HTTPException
from src.services.memory_service import memory_service
from src.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/{session_id}")
async def get_chat_history(session_id: str, limit: int = 10, skip: int = 0):
    logger.info(f"API: get /chat/history - Session: {session_id}, limit: {limit}, skip: {skip}")
    try:
        # User requested 10 messages at a time
        history = await memory_service.get_history(session_id, limit=limit, skip=skip)
        return history
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
