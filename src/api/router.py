from fastapi import APIRouter

from src.api.auth import router as auth_router
from src.api.sessions import router as sessions_router
from src.api.chat import router as chat_router
from src.api.history import router as history_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])

router.include_router(history_router, prefix="/chat/history", tags=["history"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
