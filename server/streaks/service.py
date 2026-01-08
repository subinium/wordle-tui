from datetime import date, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from server.streaks.models import UserStreak
from server.games.models import GameResult
from server.words.models import DailyWord


async def get_user_streak(db: AsyncSession, user_id: int) -> Optional[UserStreak]:
    result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_streak(db: AsyncSession, user_id: int, solved: bool) -> UserStreak:
    streak = await get_user_streak(db, user_id)
    today = date.today()

    if streak is None:
        streak = UserStreak(
            user_id=user_id,
            current_streak=1 if solved else 0,
            longest_streak=1 if solved else 0,
            last_played=today,
            total_games=1,
            total_wins=1 if solved else 0,
        )
        db.add(streak)
    else:
        streak.total_games += 1
        if solved:
            streak.total_wins += 1

            if streak.last_played:
                yesterday = today - timedelta(days=1)
                if streak.last_played == yesterday:
                    streak.current_streak += 1
                elif streak.last_played < yesterday:
                    streak.current_streak = 1
            else:
                streak.current_streak = 1

            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
        else:
            streak.current_streak = 0

        streak.last_played = today

    await db.commit()
    await db.refresh(streak)
    return streak


async def get_contribution_data(
    db: AsyncSession, user_id: int, weeks: int = 52
) -> list[dict]:
    today = date.today()
    start_date = today - timedelta(weeks=weeks)

    result = await db.execute(
        select(GameResult, DailyWord)
        .join(DailyWord)
        .where(GameResult.user_id == user_id)
        .where(DailyWord.date >= start_date)
        .order_by(DailyWord.date)
    )

    data = []
    for game, word in result.all():
        data.append({
            "date": word.date,
            "attempts": game.attempts,
            "solved": game.solved,
        })

    return data
