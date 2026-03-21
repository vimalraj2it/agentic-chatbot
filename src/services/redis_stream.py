"""
Redis Streaming Service — Handles pub/sub for real-time LLM token delivery via SSE.
"""

import redis.asyncio as redis
import json
import asyncio
from typing import AsyncGenerator
from src.core.config import settings
from src.core.logging_config import get_logger, log_execution

logger = get_logger(__name__)

class RedisStreamService:
    """
    Manages publishing and subscribing to Redis channels for real-time updates.
    """

    def __init__(self):
        self._redis: redis.Redis = None

    async def get_redis(self) -> redis.Redis:
        if self._redis is None:
            try:
                # Lazy-load redis_url from settings
                redis_url = settings.REDIS_URL
                self._redis = redis.from_url(redis_url, decode_responses=True)
                # Quick ping to verify connectivity
                await self._redis.ping()
            except Exception as e:
                logger.warning(f"Failed to connect to Redis at {settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else 'N/A'}: {e}")
                self._redis = None
                raise e
        return self._redis

    @log_execution
    async def publish_token(self, session_id: str, token: str):
        """Publish a single token to the session's channel."""
        r = await self.get_redis()
        channel = f"stream:{session_id}"
        message = json.dumps({"type": "token", "content": token})
        await r.publish(channel, message)

    @log_execution
    async def publish_status(self, session_id: str, status: str, data: dict = None):
        """Publish a status update or event (e.g., 'completed', 'error')."""
        r = await self.get_redis()
        channel = f"stream:{session_id}"
        message = json.dumps({
            "type": "status", 
            "content": status,
            "data": data or {}
        })
        await r.publish(channel, message)

    async def subscribe(self, session_id: str) -> AsyncGenerator[str, None]:
        """
        Subscribe to a session's channel and yield messages as they arrive.
        Used by the SSE endpoint.
        """
        r = await self.get_redis()
        pubsub = r.pubsub()
        channel = f"stream:{session_id}"
        
        await pubsub.subscribe(channel)
        logger.info(f"Subscribed to Redis channel: {channel}")
        
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    yield message["data"]
                await asyncio.sleep(0.01) # Yield control
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel)
            logger.info(f"Unsubscribed from Redis channel: {channel}")
            raise
        except Exception as e:
            logger.error(f"Error in Redis subscription: {e}")
            await pubsub.unsubscribe(channel)
            raise

# Singleton
redis_stream_service = RedisStreamService()
