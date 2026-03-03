from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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

class IntentScore(BaseModel):
    name: str # smalltalk, faq, not-able-classify, out-of-domain
    score: float = Field(ge=0, le=1)

class QueryClassification(BaseModel):
    intents: List[IntentScore]
    intent: str  # Top intent for backward compatibility or direct routing
    domain: str  # general, technical, support, etc.
    safety: str  # safe, unsafe
    required_tools: List[str]
    complexity_level: str  # low, medium, high

class FAQResponse(BaseModel):
    message: str
    score: float = Field(ge=0, le=1)

class SmallTalkResponse(BaseModel):
    message: str
    score: float = Field(ge=0, le=1)

class ScoredQuery(BaseModel):
    query: str
    score: float = Field(ge=0, le=1)

class QueryExpansion(BaseModel):
    expanded_queries: List[ScoredQuery]

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

# Document Schemas
class DocumentInfo(BaseModel):
    id: str
    filename: str
    status: str
    updated_at: datetime

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]

class DocumentUpdateResponse(BaseModel):
    success: bool
    message: str
    status: Optional[str] = None
