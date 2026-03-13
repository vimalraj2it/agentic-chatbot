from src.core.celery_app import celery_app
from src.services.graph_service import graph
from src.services.memory_service import memory_service
from src.services.redis_stream import redis_stream_service
from src.core.logging_config import get_logger, log_execution
from src.graphs.inventory_monitor import inventory_monitor_task
import asyncio

logger = get_logger(__name__)

async def process_chat_logic(request_data: dict):
    """
    Core async logic to process a chat request.
    """
    session_id = request_data["session_id"]
    try:
        # Notify frontend that processing started
        await redis_stream_service.publish_status(session_id, "processing")

        initial_state = {
            "session_id": session_id,
            "user_id": request_data["user_id"],
            "user_message": request_data["message"],
            "model": request_data.get("model"),
            "streaming": request_data.get("streaming", True),
            "app_state": request_data.get("app_state"),
            "referenced_data": request_data.get("referenced_data"),
            "files": request_data.get("files"),
            "response_format": request_data.get("response_format")
        }
        
        # Invoke the graph with streaming support if enabled
        assistant_response = ""
        
        if initial_state["streaming"]:
            # Stream logs/tokens via astream
            async for chunk in graph.astream(initial_state, stream_mode="updates"):
                for node_name, node_state in chunk.items():
                    if "assistant_response" in node_state:
                        partial = node_state["assistant_response"]
                        if partial and len(partial) > len(assistant_response):
                            new_text = partial[len(assistant_response):]
                            assistant_response = partial
                            await redis_stream_service.publish_token(session_id, new_text)
            
            # Full result for persistence
            result = await graph.ainvoke(initial_state)
        else:
            # Direct invocation
            result = await graph.ainvoke(initial_state)
            assistant_response = result["assistant_response"]
        
        # Persist messages
        await memory_service.add_message(session_id, "user", request_data["message"])
        await memory_service.add_message(session_id, "assistant", assistant_response)
        
        # Notify frontend that processing is completed
        await redis_stream_service.publish_status(session_id, "completed", {"response": assistant_response})

        return {
            "status": "completed",
            "response": assistant_response,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error in process_chat_logic: {e}")
        await redis_stream_service.publish_status(session_id, "error", {"message": str(e)})
        return {"status": "error", "message": str(e)}

@celery_app.task(name="process_chat_task")
@log_execution
def process_chat_task(request_data: dict):
    """
    Background task to process a chat request (Celery entry point).
    """
    logger.info(f"Task: process_chat_task started for session {request_data.get('session_id')}")
    
    # Run the async logic in a sync wrapper for Celery
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(process_chat_logic(request_data))
