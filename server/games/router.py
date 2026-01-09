from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from server.database import get_db
from server.auth.dependencies import get_current_user
from server.auth.models import User
from server.words.models import DailyWord
from server.games.schemas import (
    GameSubmitRequest,
    GameSubmitResponse,
    TodayGameResponse,
    GameHistoryItem,
    StreakInfo,
    SaveProgressRequest,
    ProgressResponse,
)
from server.games.models import GameProgress
from server.games.service import submit_game, get_today_game, get_game_history
from server.streaks.service import get_user_streak

router = APIRouter(prefix="/games", tags=["games"])


@router.post("/submit", response_model=GameSubmitResponse)
async def submit(
    request: GameSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        game, rank = await submit_game(
            db=db,
            user_id=user.id,
            word_id=request.word_id,
            attempts=request.attempts,
            solved=request.solved,
            time_seconds=request.time_seconds,
            guess_history=request.guess_history,
        )
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Already played today")

    streak = await get_user_streak(db, user.id)

    return GameSubmitResponse(
        id=game.id,
        rank=rank,
        streak=StreakInfo(
            current=streak.current_streak if streak else 0,
            longest=streak.longest_streak if streak else 0,
        ),
    )


@router.get("/today", response_model=TodayGameResponse)
async def check_today(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    game = await get_today_game(db, user.id)
    if game is None:
        return TodayGameResponse(played=False)

    return TodayGameResponse(
        played=True,
        result=GameHistoryItem(
            date=game.word.date,
            attempts=game.attempts,
            solved=game.solved,
            time_seconds=game.time_seconds,
        ),
    )


@router.get("/history", response_model=list[GameHistoryItem])
async def history(
    limit: int = 30,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    games = await get_game_history(db, user.id, limit, offset)
    return [
        GameHistoryItem(
            date=game.word.date,
            attempts=game.attempts,
            solved=game.solved,
            time_seconds=game.time_seconds,
            word=game.word.word if game.word.date < game.word.date.today() else None,
        )
        for game in games
    ]


# ==================== Game Progress (Auto-save) ====================

@router.post("/progress")
async def save_progress(
    request: SaveProgressRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save game progress (auto-save while playing)."""
    # Check if game is already completed
    from server.games.models import GameResult
    existing_result = await db.scalar(
        select(GameResult).where(
            GameResult.user_id == user.id,
            GameResult.word_id == request.word_id,
        )
    )
    if existing_result:
        return {"saved": False, "message": "Game already completed"}

    # Find or create progress
    progress = await db.scalar(
        select(GameProgress).where(
            GameProgress.user_id == user.id,
            GameProgress.word_id == request.word_id,
        )
    )

    if progress:
        # Prevent cheating: guesses can only be appended, not removed
        existing_guesses = progress.guesses or []
        new_guesses = request.guesses or []

        # New guesses must start with all existing guesses (append-only)
        if len(new_guesses) < len(existing_guesses):
            return {"saved": False, "message": "Cannot remove guesses"}
        if new_guesses[:len(existing_guesses)] != existing_guesses:
            return {"saved": False, "message": "Cannot modify previous guesses"}

        progress.guesses = request.guesses
        # Time can only increase
        progress.elapsed_seconds = max(progress.elapsed_seconds, request.elapsed_seconds)
    else:
        progress = GameProgress(
            user_id=user.id,
            word_id=request.word_id,
            guesses=request.guesses,
            elapsed_seconds=request.elapsed_seconds,
        )
        db.add(progress)

    await db.commit()
    return {"saved": True}


@router.get("/progress/today")
async def get_today_progress(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get today's game progress if exists."""
    today = date.today()

    # Get today's word
    today_word = await db.scalar(select(DailyWord).where(DailyWord.date == today))
    if not today_word:
        return {"has_progress": False}

    # Check if game is already completed
    from server.games.models import GameResult
    existing_result = await db.scalar(
        select(GameResult).where(
            GameResult.user_id == user.id,
            GameResult.word_id == today_word.id,
        )
    )
    if existing_result:
        return {
            "has_progress": False,
            "completed": True,
            "result": {
                "attempts": existing_result.attempts,
                "solved": existing_result.solved,
                "time_seconds": existing_result.time_seconds,
                "guess_history": existing_result.guess_history or [],
            }
        }

    # Check for progress
    progress = await db.scalar(
        select(GameProgress).where(
            GameProgress.user_id == user.id,
            GameProgress.word_id == today_word.id,
        )
    )

    if progress and progress.guesses:
        return ProgressResponse(
            word_id=today_word.id,
            guesses=progress.guesses,
            elapsed_seconds=progress.elapsed_seconds,
            has_progress=True,
        )

    return {"has_progress": False, "word_id": today_word.id}


@router.delete("/progress/today")
async def clear_progress(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear today's progress (called after game completion)."""
    today = date.today()
    today_word = await db.scalar(select(DailyWord).where(DailyWord.date == today))

    if today_word:
        progress = await db.scalar(
            select(GameProgress).where(
                GameProgress.user_id == user.id,
                GameProgress.word_id == today_word.id,
            )
        )
        if progress:
            await db.delete(progress)
            await db.commit()

    return {"cleared": True}
