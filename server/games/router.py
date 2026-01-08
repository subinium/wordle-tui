from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from server.database import get_db
from server.auth.dependencies import get_current_user
from server.auth.models import User
from server.games.schemas import (
    GameSubmitRequest,
    GameSubmitResponse,
    TodayGameResponse,
    GameHistoryItem,
    StreakInfo,
)
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
