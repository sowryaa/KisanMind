from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    language: str = "te"
    user_id: Optional[str] = None   # Google ID or session ID for rate limiting
    district: Optional[str] = None  # User's preferred district fallback
