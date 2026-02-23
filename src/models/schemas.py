from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    assistant_id: str

class StreamChunk(BaseModel):
    chunk: str

class StreamError(BaseModel):
    error: str

# Authentication Schemas
class LoginRequest(BaseModel):
    mobile_number: str

class UserResponse(BaseModel):
    id: str
    mobile_number: str

# Session Schemas
class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"

class SessionInfo(BaseModel):
    id: str
    title: str
    updated_at: datetime

class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]
