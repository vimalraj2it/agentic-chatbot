import litellm
import json
from typing import List, Dict, Any, AsyncGenerator
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

def clean_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Standardizes messages for LiteLLM/OpenAI API by:
    - Retaining only 'role' and 'content' fields.
    - Removing extra fields like 'id' from persistent history.
    """
    cleaned = []
    for msg in messages:
        cleaned.append({
            "role": msg.get("role"),
            "content": msg.get("content")
        })
    return cleaned

async def get_chat_completion(
    messages: List[Dict[str, Any]], 
    model: str = None,
    stream: bool = False
) -> Any:
    logger.info("Entering get_chat_completion")
    try:
        selected_model = model or settings.DEFAULT_MODEL
        api_base = settings.LITELLM_PROXY_URL if settings.USE_LITELLM_SERVER else None

        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": stream,
            "api_base": api_base,
            "api_key": settings.LITELLM_MASTER_KEY
        }
        logger.info("=== Full Request Payload ===")
        logger.info(json.dumps(payload, indent=2))

        # LiteLLM already supports OpenAI-style multi-modal content blocks
        response = await litellm.acompletion(**payload)
        
        # Log Token Usage and Cost
        usage = getattr(response, "usage", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_tokens", 0)
            completion_tokens = getattr(usage, "completion_tokens", 0)
            total_tokens = getattr(usage, "total_tokens", 0)
            
            # Extract cached tokens if available
            cached_tokens = 0
            prompt_tokens_details = getattr(usage, "prompt_tokens_details", None)
            if prompt_tokens_details:
                cached_tokens = getattr(prompt_tokens_details, "cached_tokens", 0)
            
            try:
                cost = litellm.completion_cost(completion_response=response)
            except Exception:
                cost = 0.0

            logger.info(
                f"LLM Metadata | Model: {selected_model} | "
                f"Input Tokens: {prompt_tokens} (Cached: {cached_tokens}) | "
                f"Output Tokens: {completion_tokens} | Total Tokens: {total_tokens} | "
                f"Estimated Cost: ${cost:.6f}"
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
        
        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": True,
            "api_base": api_base,
            "api_key": settings.LITELLM_MASTER_KEY,
            "stream_options": {"include_usage": True}
        }
        logger.info("=== Full Request Payload ===")
        logger.info(json.dumps(payload, indent=2))

        # LiteLLM already supports OpenAI-style multi-modal content blocks
        response = await litellm.acompletion(**payload)
        
        last_chunk = None
        async for chunk in response:
            last_chunk = chunk
            if len(chunk.choices) > 0:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        
        # Log Token Usage and Cost for stream
        if last_chunk and hasattr(last_chunk, "usage") and last_chunk.usage:
            usage = last_chunk.usage
            prompt_tokens = getattr(usage, "prompt_tokens", 0)
            completion_tokens = getattr(usage, "completion_tokens", 0)
            total_tokens = getattr(usage, "total_tokens", 0)
            
            cached_tokens = 0
            if hasattr(usage, "prompt_tokens_details") and usage.prompt_tokens_details:
                cached_tokens = getattr(usage.prompt_tokens_details, "cached_tokens", 0)
            
            try:
                cost = litellm.completion_cost(completion_response=last_chunk)
            except Exception:
                cost = 0.0

            logger.info(
                f"LLM Stream Metadata | Model: {selected_model} | "
                f"Input Tokens: {prompt_tokens} (Cached: {cached_tokens}) | "
                f"Output Tokens: {completion_tokens} | Total Tokens: {total_tokens} | "
                f"Estimated Cost: ${cost:.6f}"
            )

        logger.info("Exiting get_chat_stream successfully")
    except Exception as e:
        logger.error(f"Error in get_chat_stream: {e}")
        raise
