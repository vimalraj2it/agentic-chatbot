from src.core.celery_app import celery_app
from src.services.graph_service import graph
from src.services.memory_service import memory_service
from src.core.logging_config import get_logger
import asyncio

logger = get_logger(__name__)

@celery_app.task(name="process_chat_task")
def process_chat_task(request_data: dict):
    """
    Background task to process a chat request using LangGraph.
    """
    logger.info(f"Task: process_chat_task started for session {request_data.get('session_id')}")
    
    # Run the async graph invocation in a sync wrapper for Celery
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    async def run_process():
        try:
            initial_state = {
                "session_id": request_data["session_id"],
                "user_id": request_data["user_id"],
                "user_message": request_data["message"],
                "model": request_data.get("model"),
                "streaming": False,
                "app_state": request_data.get("app_state"),
                "referenced_data": request_data.get("referenced_data"),
                "files": request_data.get("files"),
                "response_format": request_data.get("response_format")
            }
            
            # Invoke the graph
            result = await graph.ainvoke(initial_state)
            
            # Persist messages
            await memory_service.add_message(request_data["session_id"], "user", request_data["message"])
            await memory_service.add_message(request_data["session_id"], "assistant", result["assistant_response"])
            
            return {
                "status": "completed",
                "response": result["assistant_response"],
                "session_id": request_data["session_id"]
            }
        except Exception as e:
            logger.error(f"Error in process_chat_task: {e}")
            return {"status": "error", "message": str(e)}

    return loop.run_until_complete(run_process())
