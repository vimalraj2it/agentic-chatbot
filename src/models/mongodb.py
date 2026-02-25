from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any
from uuid import uuid4

class MessageDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str
    content: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SessionDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    title: str = "New Chat"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[MessageDoc] = []

class UserDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    mobile_number: str
    name: Optional[str] = "Anonymous"
    role: str = "User"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    status: str = "unloaded" # unloaded, loaded, loading, error
    file_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
