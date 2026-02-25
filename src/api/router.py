from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from src.models.schemas import ChatRequest, ChatResponse
from src.services.graph_service import graph
from src.services.llm_service import get_chat_stream
from src.services.memory_service import memory_service
from src.core.config import settings # Added for system rules
from src.core.logging_config import get_logger

from src.api.auth import router as auth_router
from src.api.sessions import router as sessions_router
from src.services.tasks import process_chat_task
from celery.result import AsyncResult
from src.core.celery_app import celery_app

logger = get_logger(__name__)
router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])

@router.get("/chat/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Check the status of a chat processing task.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    result = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.ready():
        result["result"] = task_result.result
        
    return result

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 10, skip: int = 0):
    logger.info(f"API: get /chat/history - Session: {session_id}, limit: {limit}, skip: {skip}")
    try:
        # User requested 10 messages at a time
        history = await memory_service.get_history(session_id, limit=limit, skip=skip)
        return history
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    logger.info("##################### Incoming Async Chat Request ################################")
    logger.info(f"API: post /chat - Session: {request.session_id}")
    try:
        # Trigger Celery Task instead of direct processing
        task = process_chat_task.delay(request.model_dump())
        
        return {
            "task_id": task.id,
            "status": "pending",
            "message": "Chat request queued successfully"
        }
    except Exception as e:
        logger.error(f"API: post /chat - Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    # Streaming is now handled asynchronously via the queue.
    # The client will poll for updates.
    logger.info("##################### Incoming Async Chat Stream Request ################################")
    return await chat_endpoint(request)
