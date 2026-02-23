from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from src.models.schemas import ChatRequest, ChatResponse
from src.services.graph_service import graph
from src.services.llm_service import get_chat_stream
from src.services.memory_service import memory_service
from src.core.logging_config import get_logger

from src.api.auth import router as auth_router
from src.api.sessions import router as sessions_router

logger = get_logger(__name__)
router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])

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

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    logger.info("##################### Incoming Chat Request ################################")
    logger.info(f"API: post /chat - Session: {request.session_id}")
    try:
        # Get last 5 messages for LLM context
        history = await memory_service.get_history(request.session_id, limit=5)
        
        initial_state = {
            "session_id": request.session_id,
            "user_message": request.message,
            "model": request.model,
            "history": history
        }
        result = await graph.ainvoke(initial_state)
        
        # Persist messages
        user_msg = await memory_service.add_message(request.session_id, "user", request.message)
        assistant_msg = await memory_service.add_message(request.session_id, "assistant", result["assistant_response"])
        
        return ChatResponse(
            response=result["assistant_response"],
            user_id=user_msg.id,
            assistant_id=assistant_msg.id
        )
    except Exception as e:
        logger.error(f"API: post /chat - Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    logger.info("##################### Incoming Chat Stream Request ################################")
    logger.info(f"API: post /chat/stream - Session: {request.session_id}")
    try:
        history = await memory_service.get_history(request.session_id, limit=5)
        messages = history + [{"role": "user", "content": request.message}]
        
        async def event_generator():
            full_response = ""
            try:
                async for chunk in get_chat_stream(messages, request.model):
                    full_response += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                user_msg = await memory_service.add_message(request.session_id, "user", request.message)
                assistant_msg = await memory_service.add_message(request.session_id, "assistant", full_response)
                
                # Send metadata with IDs
                yield f"data: {json.dumps({'user_id': user_msg.id, 'assistant_id': assistant_msg.id})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"API: post /chat/stream - Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
