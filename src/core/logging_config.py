import logging
import sys
import functools
import json
import time
from typing import Any, Callable, TypeVar, cast
from src.core.config import settings

T = TypeVar("T", bound=Callable[..., Any])

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str):
    return logging.getLogger(name)

def log_execution(func: T) -> T:
    """
    Decorator to log the start and end of a method, including inputs and outputs.
    Automatically handles both synchronous and asynchronous functions.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Log input
        logger.info(f"START: {func_name} | Inputs: args={args}, kwargs={kwargs}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            # Log output
            logger.info(f"RETURN: {func_name} | Duration: {duration:.4f}s | Output: {result}")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"ERROR: {func_name} | Duration: {duration:.4f}s | Exception: {str(e)}")
            raise

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Log input
        logger.info(f"START: {func_name} | Inputs: args={args}, kwargs={kwargs}")
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            # Log output
            logger.info(f"RETURN: {func_name} | Duration: {duration:.4f}s | Output: {result}")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"ERROR: {func_name} | Duration: {duration:.4f}s | Exception: {str(e)}")
            raise

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return cast(T, async_wrapper)
    return cast(T, wrapper)
