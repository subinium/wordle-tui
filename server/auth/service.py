import jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from server.config import get_settings
from server.auth.models import User

settings = get_settings()
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 365


async def create_or_get_user(db: AsyncSession, username: str) -> tuple[User, str]:
    """Create or get user by username (simple auth)."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(username=username)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(user.id)
    return user, token


async def create_or_get_github_user(
    db: AsyncSession,
    github_id: int,
    username: str,
    avatar_url: str | None = None,
) -> tuple[User, str]:
    """Create or get user by GitHub ID."""
    # First try to find by GitHub ID
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if user is None:
        # Check if username exists, add suffix if needed
        base_username = username
        suffix = 0
        while True:
            check_username = base_username if suffix == 0 else f"{base_username}_{suffix}"
            result = await db.execute(select(User).where(User.username == check_username))
            if result.scalar_one_or_none() is None:
                username = check_username
                break
            suffix += 1

        user = User(
            username=username,
            github_id=github_id,
            avatar_url=avatar_url,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update avatar if changed
        if user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            await db.commit()

    token = create_access_token(user.id)
    return user, token


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return user_id
    except jwt.PyJWTError:
        return None


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
