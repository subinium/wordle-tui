from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from server.database import get_db
from server.leaderboard.schemas import LeaderboardEntry
from server.leaderboard.service import get_leaderboard_for_date

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/today", response_model=list[LeaderboardEntry])
async def get_today_leaderboard(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    data = await get_leaderboard_for_date(db, date.today(), limit)
    return [LeaderboardEntry(**entry) for entry in data]


@router.get("/date/{target_date}", response_model=list[LeaderboardEntry])
async def get_date_leaderboard(
    target_date: date,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    data = await get_leaderboard_for_date(db, target_date, limit)
    return [LeaderboardEntry(**entry) for entry in data]
