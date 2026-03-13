from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
from celery.result import AsyncResult
from typing import AsyncGenerator
import uuid

from src.models.schemas import ChatRequest
from src.services.tasks import process_chat_task, process_chat_logic
from src.services.redis_stream import redis_stream_service
from src.core.celery_app import celery_app
from src.core.logging_config import get_logger, log_execution
from src.core.config import settings

logger = get_logger(__name__)
router = APIRouter()

@router.get("/status/{task_id}")
@log_execution
async def get_task_status(task_id: str):
    """
    Check the status of a chat processing task.
    """
    if not settings.USE_CELERY:
        # In non-celery mode, we don't track background tasks via AsyncResult
        # Status is essentially managed via SSE stream
        return {
            "task_id": task_id,
            "status": "N/A (Celery Disabled)",
            "info": "Streaming status via SSE is recommended"
        }

    task_result = AsyncResult(task_id, app=celery_app)
    result = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.ready():
        result["result"] = task_result.result
        
    return result

@router.post("")
@log_execution
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    logger.info(f"API: post /chat - Session: {request.session_id} (Celery: {settings.USE_CELERY})")
    try:
        if settings.USE_CELERY:
            # Trigger Celery Task
            task = process_chat_task.delay(request.model_dump())
            task_id = task.id
        else:
            # Run without Celery: use FastAPI BackgroundTasks
            task_id = str(uuid.uuid4())
            background_tasks.add_task(process_chat_logic, request.model_dump())
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Chat request processing started"
        }
    except Exception as e:
        logger.error(f"API: post /chat - Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stream/{session_id}")
async def stream_endpoint(request: Request, session_id: str):
    """
    SSE endpoint for receiving real-time updates for a session.
    """
    async def event_generator() -> AsyncGenerator[dict, None]:
        async for message in redis_stream_service.subscribe(session_id):
            # Check for client disconnect
            if await request.is_disconnected():
                logger.info(f"SSE client disconnected for session: {session_id}")
                break
            
            yield {
                "event": "message",
                "data": message
            }

    return EventSourceResponse(event_generator())
