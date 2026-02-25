from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from src.models.schemas import ChatRequest
from src.services.tasks import process_chat_task
from src.core.celery_app import celery_app
from src.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/status/{task_id}")
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

@router.post("")
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

@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    # Streaming is now handled asynchronously via the queue.
    # The client will poll for updates.
    logger.info("##################### Incoming Async Chat Stream Request ################################")
    return await chat_endpoint(request)
