from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from server.games.models import GameResult
from server.words.models import DailyWord
from server.auth.models import User


async def get_leaderboard_for_date(
    db: AsyncSession, target_date: date, limit: int = 100
) -> list[dict]:
    """Get leaderboard sorted by: attempts (fewer = better), then time (faster = better)."""
    result = await db.execute(
        select(GameResult, User)
        .join(DailyWord)
        .join(User)
        .where(DailyWord.date == target_date)
        .where(GameResult.solved == True)
        .order_by(
            GameResult.attempts.asc(),  # Fewer attempts = better
            GameResult.time_seconds.asc().nullslast(),  # Faster time = better
        )
        .limit(limit)
    )

    leaderboard = []
    for rank, (game, user) in enumerate(result.all(), start=1):
        leaderboard.append({
            "rank": rank,
            "username": user.username,
            "attempts": game.attempts,
            "time_seconds": game.time_seconds,
        })

    return leaderboard
