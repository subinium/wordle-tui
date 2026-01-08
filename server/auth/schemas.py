from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)


class UserResponse(BaseModel):
    id: int
    username: str
    github_id: Optional[int] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    id: int
    username: str
    token: str


# GitHub OAuth Device Flow
class GitHubDeviceCodeResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


class GitHubTokenRequest(BaseModel):
    device_code: str


class GitHubTokenResponse(BaseModel):
    status: str  # "pending", "authorized", "expired", "error"
    user_id: Optional[int] = None
    username: Optional[str] = None
    token: Optional[str] = None
    error: Optional[str] = None
