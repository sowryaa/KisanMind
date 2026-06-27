from pydantic import BaseModel
from typing import Optional

class UserProfile(BaseModel):
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_language: str = "te"
    district: Optional[str] = None
