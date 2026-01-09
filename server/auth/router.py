import httpx
import secrets
import hmac
from urllib.parse import urlencode
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from server.database import get_db
from server.config import get_settings

# In-memory state storage (use Redis in production for horizontal scaling)
_oauth_states: dict[str, datetime] = {}
STATE_EXPIRY_MINUTES = 10
from server.auth.schemas import (
    UserCreate,
    TokenResponse,
    GoogleAuthUrlResponse,
    GoogleCallbackRequest,
    GoogleCallbackResponse,
)
from server.auth.service import create_or_get_user, create_or_get_google_user
from server.auth.dependencies import get_current_user
from server.auth.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


class UpdateProfileRequest(BaseModel):
    username: str

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Simple username-based login."""
    user, token = await create_or_get_user(db, user_data.username)
    return TokenResponse(id=user.id, username=user.username, token=token)


def _cleanup_expired_states():
    """Remove expired OAuth states."""
    now = datetime.utcnow()
    expired = [s for s, exp in _oauth_states.items() if exp < now]
    for s in expired:
        _oauth_states.pop(s, None)


@router.get("/google/auth-url", response_model=GoogleAuthUrlResponse)
async def google_auth_url(redirect_uri: str):
    """Get Google OAuth authorization URL."""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    # Generate and store state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.utcnow() + timedelta(minutes=STATE_EXPIRY_MINUTES)

    # Cleanup old states
    _cleanup_expired_states()

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return GoogleAuthUrlResponse(auth_url=auth_url, state=state)


@router.post("/google/callback", response_model=GoogleCallbackResponse)
async def google_callback(
    request: GoogleCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback - exchange code for token and get user info."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    # SECURITY: Validate OAuth state to prevent CSRF attacks
    if not request.state:
        return GoogleCallbackResponse(success=False, error="Missing state parameter")

    stored_expiry = _oauth_states.pop(request.state, None)
    if stored_expiry is None:
        return GoogleCallbackResponse(success=False, error="Invalid or expired state")
    if datetime.utcnow() > stored_expiry:
        return GoogleCallbackResponse(success=False, error="State expired")

    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": request.code,
                "grant_type": "authorization_code",
                "redirect_uri": request.redirect_uri,
            },
        )

        if token_response.status_code != 200:
            return GoogleCallbackResponse(
                success=False,
                error=f"Failed to exchange code: {token_response.text}"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return GoogleCallbackResponse(
                success=False,
                error="No access token received"
            )

        # Get user info
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            return GoogleCallbackResponse(
                success=False,
                error="Failed to get user info"
            )

        userinfo = userinfo_response.json()
        google_id = userinfo.get("id")
        email = userinfo.get("email")
        name = userinfo.get("name")
        avatar_url = userinfo.get("picture")

        if not google_id or not email:
            return GoogleCallbackResponse(
                success=False,
                error="Invalid user info from Google"
            )

        # Create or get user
        user, token = await create_or_get_google_user(
            db,
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )

        return GoogleCallbackResponse(
            success=True,
            user_id=user.id,
            username=user.username,
            token=token,
        )


@router.get("/google/status")
async def google_status():
    """Check if Google OAuth is configured."""
    return {
        "configured": bool(settings.google_client_id and settings.google_client_secret)
    }


# ==================== Profile Endpoints ====================

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
    }


@router.patch("/me")
async def update_profile(
    request: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile (username)."""
    new_username = request.username.strip()

    # Validate username
    if len(new_username) < 2:
        raise HTTPException(status_code=400, detail="Username must be at least 2 characters")
    if len(new_username) > 30:
        raise HTTPException(status_code=400, detail="Username must be 30 characters or less")
    if not all(c.isalnum() or c == "_" for c in new_username):
        raise HTTPException(status_code=400, detail="Username can only contain letters, numbers, and underscores")

    # Check if username is taken (by another user)
    if new_username != user.username:
        existing = await db.scalar(
            select(User).where(User.username == new_username)
        )
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")

    # Update username
    user.username = new_username
    await db.commit()

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
    }
