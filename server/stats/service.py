from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, Integer
from server.games.models import GameResult
from server.words.models import DailyWord
from server.streaks.models import UserStreak


async def get_daily_stats(db: AsyncSession, target_date: date) -> dict:
    word_result = await db.execute(
        select(DailyWord).where(DailyWord.date == target_date)
    )
    word = word_result.scalar_one_or_none()
    if word is None:
        return None

    total_result = await db.execute(
        select(func.count(GameResult.id))
        .where(GameResult.word_id == word.id)
    )
    total_players = total_result.scalar_one() or 0

    solved_result = await db.execute(
        select(func.count(GameResult.id))
        .where(GameResult.word_id == word.id)
        .where(GameResult.solved == True)
    )
    total_solved = solved_result.scalar_one() or 0

    avg_result = await db.execute(
        select(func.avg(GameResult.attempts))
        .where(GameResult.word_id == word.id)
    )
    avg_attempts = float(avg_result.scalar_one() or 0)

    winners_avg_result = await db.execute(
        select(func.avg(GameResult.attempts))
        .where(GameResult.word_id == word.id)
        .where(GameResult.solved == True)
    )
    winners_avg = float(winners_avg_result.scalar_one() or 0)

    distribution = {}
    for i in range(1, 7):
        count_result = await db.execute(
            select(func.count(GameResult.id))
            .where(GameResult.word_id == word.id)
            .where(GameResult.attempts == i)
            .where(GameResult.solved == True)
        )
        distribution[str(i)] = count_result.scalar_one() or 0

    return {
        "date": target_date,
        "total_players": total_players,
        "total_solved": total_solved,
        "solve_rate": round((total_solved / total_players * 100) if total_players > 0 else 0, 1),
        "avg_attempts": round(avg_attempts, 2),
        "winners_avg_attempts": round(winners_avg, 2),
        "attempts_distribution": distribution,
    }


async def get_personal_stats(db: AsyncSession, user_id: int) -> dict:
    streak_result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == user_id)
    )
    streak = streak_result.scalar_one_or_none()

    total_games = streak.total_games if streak else 0
    total_wins = streak.total_wins if streak else 0

    avg_result = await db.execute(
        select(func.avg(GameResult.attempts))
        .where(GameResult.user_id == user_id)
        .where(GameResult.solved == True)
    )
    avg_attempts = float(avg_result.scalar_one() or 0)

    best_time_result = await db.execute(
        select(func.min(GameResult.time_seconds))
        .where(GameResult.user_id == user_id)
        .where(GameResult.solved == True)
        .where(GameResult.time_seconds.isnot(None))
    )
    best_time = best_time_result.scalar_one()

    distribution = {}
    for i in range(1, 7):
        count_result = await db.execute(
            select(func.count(GameResult.id))
            .where(GameResult.user_id == user_id)
            .where(GameResult.attempts == i)
            .where(GameResult.solved == True)
        )
        distribution[str(i)] = count_result.scalar_one() or 0

    return {
        "total_games": total_games,
        "total_wins": total_wins,
        "win_rate": round((total_wins / total_games * 100) if total_games > 0 else 0, 1),
        "current_streak": streak.current_streak if streak else 0,
        "longest_streak": streak.longest_streak if streak else 0,
        "avg_attempts": round(avg_attempts, 2),
        "best_time_seconds": best_time,
        "attempts_distribution": distribution,
    }


async def get_monthly_stats(db: AsyncSession, user_id: int) -> list[dict]:
    result = await db.execute(
        select(
            extract("year", DailyWord.date).label("year"),
            extract("month", DailyWord.date).label("month"),
            func.count(GameResult.id).label("played"),
            func.sum(func.cast(GameResult.solved, Integer)).label("solved"),
        )
        .select_from(GameResult)
        .join(DailyWord)
        .where(GameResult.user_id == user_id)
        .group_by("year", "month")
        .order_by("year", "month")
    )

    data = []
    for row in result.all():
        played = row.played or 0
        solved = row.solved or 0
        data.append({
            "month": f"{int(row.year)}-{int(row.month):02d}",
            "played": played,
            "solved": solved,
            "rate": round((solved / played * 100) if played > 0 else 0, 1),
        })

    return data
