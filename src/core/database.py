from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_to_storage(cls):
        logger.info("Connecting to MongoDB...")
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        cls.db = cls.client[settings.DATABASE_NAME]
        logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")

    @classmethod
    async def close_storage(cls):
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection.")

db = Database()
