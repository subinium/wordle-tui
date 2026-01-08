import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from server.database import get_db
from server.config import get_settings
from server.auth.schemas import (
    UserCreate,
    TokenResponse,
    GitHubDeviceCodeResponse,
    GitHubTokenRequest,
    GitHubTokenResponse,
)
from server.auth.service import create_or_get_user, create_or_get_github_user

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Simple username-based login."""
    user, token = await create_or_get_user(db, user_data.username)
    return TokenResponse(id=user.id, username=user.username, token=token)


@router.post("/github/device-code", response_model=GitHubDeviceCodeResponse)
async def github_device_code():
    """Start GitHub device flow - get a user code to show."""
    if not settings.github_client_id:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/device/code",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "scope": "read:user",
            },
        )

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to get device code from GitHub")

        data = response.json()
        return GitHubDeviceCodeResponse(
            device_code=data["device_code"],
            user_code=data["user_code"],
            verification_uri=data["verification_uri"],
            expires_in=data["expires_in"],
            interval=data["interval"],
        )


@router.post("/github/poll-token", response_model=GitHubTokenResponse)
async def github_poll_token(request: GitHubTokenRequest, db: AsyncSession = Depends(get_db)):
    """Poll GitHub for access token after user authorizes."""
    if not settings.github_client_id:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    async with httpx.AsyncClient() as client:
        # Exchange device code for access token
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "device_code": request.device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )

        if response.status_code != 200:
            return GitHubTokenResponse(status="error", error="GitHub request failed")

        data = response.json()

        # Check for errors
        if "error" in data:
            error = data["error"]
            if error == "authorization_pending":
                return GitHubTokenResponse(status="pending")
            elif error == "slow_down":
                return GitHubTokenResponse(status="pending")
            elif error == "expired_token":
                return GitHubTokenResponse(status="expired", error="Code expired")
            elif error == "access_denied":
                return GitHubTokenResponse(status="error", error="Access denied")
            else:
                return GitHubTokenResponse(status="error", error=data.get("error_description", error))

        # Got access token - get user info
        access_token = data.get("access_token")
        if not access_token:
            return GitHubTokenResponse(status="error", error="No access token received")

        # Fetch GitHub user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )

        if user_response.status_code != 200:
            return GitHubTokenResponse(status="error", error="Failed to get user info")

        github_user = user_response.json()
        github_id = github_user["id"]
        github_username = github_user["login"]
        avatar_url = github_user.get("avatar_url")

        # Create or get our user
        user, token = await create_or_get_github_user(
            db,
            github_id=github_id,
            username=github_username,
            avatar_url=avatar_url,
        )

        return GitHubTokenResponse(
            status="authorized",
            user_id=user.id,
            username=user.username,
            token=token,
        )
