import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Production Chat API"
    DEBUG: bool = False
    
    DEFAULT_MODEL: str = "gpt-4o-mini"
    CLASSIFIER_MODEL: str = "gpt-4o-mini"
    SMALLTALK_MODEL: str = "gpt-4o-mini"
    FAQ_MODEL: str = "gpt-4o"
    ORDER_STATUS_MODEL: str = "gpt-4o-mini"
    CREATE_ORDER_MODEL: str = "gpt-4o-mini"
    RAG_TYPE: str = "text"
    
    INVENTORY_CHECK_INTERVAL: int = 3600 # 1 hour
    
    # LangSmith Tracing
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_PROJECT: str = "wechat-assistant"
    LANGCHAIN_API_KEY: str = ""
    
    EMBEDDING_MODEL: str = "BAAI/bge-small-en"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_NORMALIZE: bool = True
    
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    PINECONE_API_KEY: str = ""
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    
    LOG_LEVEL: str = "INFO"
    LITELLM_PROXY_URL: str = ""
    USE_LITELLM_SERVER: bool = False
    LITELLM_MASTER_KEY: str = ""
    ENABLE_PROMPT_CACHING: bool = True
    
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "chat_app"
    USE_CELERY: bool = True  # Set to False to run without Celery

    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    SYSTEM_RULES: str = """
    You are a helpful and professional AI assistant.
    Personalize your responses based on the user's name and role provided in the context.
    Refer to their past conversation topics if relevant to maintain continuity.
    Be concise but informative.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
