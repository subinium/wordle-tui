from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from server.database import get_db
from server.auth.dependencies import get_current_user
from server.auth.models import User
from server.stats.schemas import (
    DailyStatsResponse,
    PersonalStatsResponse,
    MonthlyStatsResponse,
    MonthlyStatsItem,
)
from server.stats.service import get_daily_stats, get_personal_stats, get_monthly_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/today", response_model=DailyStatsResponse)
async def today_stats(db: AsyncSession = Depends(get_db)):
    stats = await get_daily_stats(db, date.today())
    if stats is None:
        raise HTTPException(status_code=404, detail="No stats for today")
    return DailyStatsResponse(**stats)


@router.get("/daily/{target_date}", response_model=DailyStatsResponse)
async def daily_stats(target_date: date, db: AsyncSession = Depends(get_db)):
    stats = await get_daily_stats(db, target_date)
    if stats is None:
        raise HTTPException(status_code=404, detail="No stats for this date")
    return DailyStatsResponse(**stats)


@router.get("/me", response_model=PersonalStatsResponse)
async def my_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_personal_stats(db, user.id)
    return PersonalStatsResponse(**stats)


@router.get("/me/monthly", response_model=MonthlyStatsResponse)
async def my_monthly_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await get_monthly_stats(db, user.id)
    return MonthlyStatsResponse(data=[MonthlyStatsItem(**item) for item in data])
