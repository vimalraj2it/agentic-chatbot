import litellm
from typing import List, Dict, Any, AsyncGenerator
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def get_chat_completion(
    messages: List[Dict[str, Any]], 
    model: str = None,
    stream: bool = False
) -> Any:
    logger.info("Entering get_chat_completion")
    try:
        selected_model = model or settings.DEFAULT_MODEL
        api_base = settings.LITELLM_PROXY_URL if settings.USE_LITELLM_SERVER else None
        
        logger.info(f"Using model  {selected_model} with api_base: {api_base} ")
        logger.info(f"Messages : {messages}")
        # LiteLLM already supports OpenAI-style multi-modal content blocks
        response = await litellm.acompletion(
            model=selected_model,
            messages=messages,
            stream=stream,
            api_base=api_base,
            api_key=settings.LITELLM_MASTER_KEY
        )
        logger.info("Exiting get_chat_completion successfully")
        return response
    except Exception as e:
        logger.error(f"Error in get_chat_completion: {e}")
        raise

async def get_chat_stream(
    messages: List[Dict[str, Any]], 
    model: str = None
) -> AsyncGenerator[str, None]:
    logger.info("Entering get_chat_stream")
    try:
        selected_model = model or settings.DEFAULT_MODEL
        api_base = settings.LITELLM_PROXY_URL if settings.USE_LITELLM_SERVER else None
        logger.info(f"Using model  {selected_model} with api_base: {api_base} ")
        logger.info(f"Stream Messages : {messages}")
        response = await litellm.acompletion(
            model=selected_model,
            messages=messages,
            stream=True,
            api_base=api_base,
            api_key=settings.LITELLM_MASTER_KEY
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content
        logger.info("Exiting get_chat_stream successfully")
    except Exception as e:
        logger.error(f"Error in get_chat_stream: {e}")
        raise
