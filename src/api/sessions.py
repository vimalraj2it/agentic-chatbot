from fastapi import APIRouter, HTTPException, Depends
from typing import List
from src.models.schemas import SessionCreate, SessionInfo, SessionListResponse
from src.services.memory_service import memory_service
from src.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/{user_id}", response_model=SessionListResponse)
async def list_user_sessions(user_id: str):
    logger.info(f"Listing sessions for user: {user_id}")
    sessions = await memory_service.list_sessions(user_id)
    
    session_list = [
        SessionInfo(
            id=s["id"],
            title=s["title"],
            updated_at=s["updated_at"]
        ) for s in sessions
    ]
    
    return SessionListResponse(sessions=session_list)

@router.post("/{user_id}", response_model=SessionInfo)
async def create_user_session(user_id: str, request: SessionCreate):
    logger.info(f"Creating session for user: {user_id}")
    session_id = await memory_service.create_session(user_id, request.title)
    
    # Return basic info (we could fetch again but create_session uses SessionDoc internally)
    from datetime import datetime
    return SessionInfo(
        id=session_id,
        title=request.title or "New Chat",
        updated_at=datetime.utcnow()
    )
