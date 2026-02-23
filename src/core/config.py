import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Production Chat API"
    DEBUG: bool = False
    
    DEFAULT_MODEL: str = "gpt-4o-mini"
    
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    
    LOG_LEVEL: str = "INFO"
    LITELLM_PROXY_URL: str = ""
    USE_LITELLM_SERVER: bool = False
    LITELLM_MASTER_KEY: str = ""
    
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "chat_app"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
