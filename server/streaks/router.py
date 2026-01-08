from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from server.database import get_db
from server.auth.dependencies import get_current_user
from server.auth.models import User
from server.streaks.schemas import StreakResponse, ContributionDataResponse, ContributionDataItem
from server.streaks.service import get_user_streak, get_contribution_data

router = APIRouter(prefix="/streaks", tags=["streaks"])


@router.get("/me", response_model=StreakResponse)
async def get_my_streak(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    streak = await get_user_streak(db, user.id)
    if streak is None:
        return StreakResponse(
            current_streak=0,
            longest_streak=0,
            total_games=0,
            total_wins=0,
            last_played=None,
        )
    return streak


@router.get("/contribution-data", response_model=ContributionDataResponse)
async def get_contributions(
    weeks: int = 52,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await get_contribution_data(db, user.id, weeks)
    return ContributionDataResponse(
        data=[ContributionDataItem(**item) for item in data]
    )
