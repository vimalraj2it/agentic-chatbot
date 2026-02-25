from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class ChatRequest(BaseModel):
    session_id: str
    user_id: str # Required for context injection
    message: str
    images: Optional[List[str]] = None
    model: Optional[str] = None
    app_state: Optional[Dict] = None
    referenced_data: Optional[List[Dict]] = None
    files: Optional[List[Dict]] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    assistant_id: str

class StreamChunk(BaseModel):
    chunk: str

class StreamError(BaseModel):
    error: str

class QueryClassification(BaseModel):
    intent: str  # smalltalk, faq, not-able-classify, out-of-domain
    domain: str  # general, technical, support, etc.
    safety: str  # safe, unsafe
    required_tools: List[str]
    complexity_level: str  # low, medium, high

# Authentication Schemas
class LoginRequest(BaseModel):
    mobile_number: str

class UserResponse(BaseModel):
    id: str
    mobile_number: str
    name: str
    role: str

# Session Schemas
class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"

class SessionInfo(BaseModel):
    id: str
    title: str
    updated_at: datetime

class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]
