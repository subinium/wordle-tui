"""Admin API endpoints - protected by secret key."""

from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from server.database import get_db
from server.config import get_settings
from server.auth.models import User
from server.games.models import GameResult
from server.streaks.models import UserStreak
from server.words.models import DailyWord

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin_key(x_admin_key: str = Header(None)):
    """Verify admin secret key."""
    settings = get_settings()
    if not x_admin_key or x_admin_key != settings.admin_secret_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return True


@router.get("/stats")
async def get_overall_stats(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    """Get overall server statistics."""
    # Total users
    total_users = await db.scalar(select(func.count(User.id)))

    # Total games played
    total_games = await db.scalar(select(func.count(GameResult.id)))

    # Total games solved
    total_solved = await db.scalar(
        select(func.count(GameResult.id)).where(GameResult.solved == True)
    )

    # Average attempts for solved games
    avg_attempts = await db.scalar(
        select(func.avg(GameResult.attempts)).where(GameResult.solved == True)
    )

    # Active users (played in last 7 days)
    week_ago = date.today() - timedelta(days=7)
    active_users = await db.scalar(
        select(func.count(func.distinct(GameResult.user_id))).where(
            GameResult.completed_at >= week_ago
        )
    )

    # Today's stats
    today = date.today()
    today_word = await db.scalar(select(DailyWord).where(DailyWord.date == today))
    today_games = 0
    today_solved = 0

    if today_word:
        today_games = await db.scalar(
            select(func.count(GameResult.id)).where(GameResult.word_id == today_word.id)
        )
        today_solved = await db.scalar(
            select(func.count(GameResult.id)).where(
                GameResult.word_id == today_word.id,
                GameResult.solved == True
            )
        )

    return {
        "total_users": total_users or 0,
        "total_games": total_games or 0,
        "total_solved": total_solved or 0,
        "solve_rate": round((total_solved / total_games * 100), 1) if total_games else 0,
        "avg_attempts": round(avg_attempts, 2) if avg_attempts else 0,
        "active_users_7d": active_users or 0,
        "today": {
            "date": today.isoformat(),
            "word": today_word.word if today_word else None,
            "games": today_games or 0,
            "solved": today_solved or 0,
        }
    }


@router.get("/users")
async def get_users(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    """Get list of users with their stats."""
    result = await db.execute(
        select(User, UserStreak)
        .outerjoin(UserStreak, User.id == UserStreak.user_id)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    users = []
    for user, streak in result.all():
        users.append({
            "id": user.id,
            "username": user.username,
            "github_id": user.github_id,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "total_games": streak.total_games if streak else 0,
            "total_wins": streak.total_wins if streak else 0,
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
        })

    return {"users": users, "limit": limit, "offset": offset}


@router.get("/leaderboard")
async def get_full_leaderboard(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    """Get full leaderboard by streak."""
    result = await db.execute(
        select(User, UserStreak)
        .join(UserStreak, User.id == UserStreak.user_id)
        .order_by(UserStreak.longest_streak.desc(), UserStreak.total_wins.desc())
        .limit(limit)
    )

    leaderboard = []
    for rank, (user, streak) in enumerate(result.all(), 1):
        leaderboard.append({
            "rank": rank,
            "username": user.username,
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "total_games": streak.total_games,
            "total_wins": streak.total_wins,
            "win_rate": round(streak.total_wins / streak.total_games * 100, 1) if streak.total_games else 0,
        })

    return {"leaderboard": leaderboard}


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    """Get detailed stats for a specific user."""
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    streak = await db.scalar(select(UserStreak).where(UserStreak.user_id == user_id))

    # Get all game results for this user
    games_result = await db.execute(
        select(GameResult, DailyWord)
        .join(DailyWord, GameResult.word_id == DailyWord.id)
        .where(GameResult.user_id == user_id)
        .order_by(GameResult.completed_at.desc())
        .limit(100)
    )

    games = []
    for game, word in games_result.all():
        games.append({
            "date": word.date.isoformat(),
            "word": word.word,
            "attempts": game.attempts,
            "solved": game.solved,
            "time_seconds": game.time_seconds,
            "guess_history": game.guess_history,
            "completed_at": game.completed_at.isoformat() if game.completed_at else None,
        })

    # Attempts distribution
    distribution = {}
    for i in range(1, 7):
        count = await db.scalar(
            select(func.count(GameResult.id)).where(
                GameResult.user_id == user_id,
                GameResult.solved == True,
                GameResult.attempts == i
            )
        )
        distribution[str(i)] = count or 0

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "github_id": user.github_id,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "stats": {
            "total_games": streak.total_games if streak else 0,
            "total_wins": streak.total_wins if streak else 0,
            "win_rate": round(streak.total_wins / streak.total_games * 100, 1) if streak and streak.total_games else 0,
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "last_played": streak.last_played.isoformat() if streak and streak.last_played else None,
            "distribution": distribution,
        },
        "games": games,
    }


@router.get("/daily/{target_date}")
async def get_daily_stats(
    target_date: date,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    """Get stats for a specific date."""
    word = await db.scalar(select(DailyWord).where(DailyWord.date == target_date))

    if not word:
        return {"date": target_date.isoformat(), "word": None, "games": 0}

    total_games = await db.scalar(
        select(func.count(GameResult.id)).where(GameResult.word_id == word.id)
    )
    total_solved = await db.scalar(
        select(func.count(GameResult.id)).where(
            GameResult.word_id == word.id,
            GameResult.solved == True
        )
    )
    avg_attempts = await db.scalar(
        select(func.avg(GameResult.attempts)).where(
            GameResult.word_id == word.id,
            GameResult.solved == True
        )
    )

    # Attempts distribution
    distribution = {}
    for i in range(1, 7):
        count = await db.scalar(
            select(func.count(GameResult.id)).where(
                GameResult.word_id == word.id,
                GameResult.solved == True,
                GameResult.attempts == i
            )
        )
        distribution[str(i)] = count or 0

    return {
        "date": target_date.isoformat(),
        "word": word.word,
        "total_games": total_games or 0,
        "total_solved": total_solved or 0,
        "solve_rate": round((total_solved / total_games * 100), 1) if total_games else 0,
        "avg_attempts": round(avg_attempts, 2) if avg_attempts else 0,
        "distribution": distribution,
    }
