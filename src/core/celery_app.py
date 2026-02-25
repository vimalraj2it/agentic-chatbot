from celery import Celery
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Redis URL from environment or use default
redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "chat_app",
    broker=redis_url,
    backend=redis_url,
    include=["src.services.tasks"]
)

from celery.signals import worker_process_init
import asyncio

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300, # 5 minutes
)

@worker_process_init.connect
def init_worker(**kwargs):
    from src.core.database import db
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Connect synchronously for signal
    loop.run_until_complete(db.connect_to_storage())

if __name__ == "__main__":
    celery_app.start()
