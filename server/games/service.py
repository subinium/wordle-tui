from datetime import date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from server.games.models import GameResult, GameProgress
from server.words.models import DailyWord
from server.streaks.service import update_streak


async def submit_game(
    db: AsyncSession,
    user_id: int,
    word_id: int,
    attempts: int,
    solved: bool,
    time_seconds: Optional[int],
    guess_history: list[str],
) -> tuple[GameResult, int]:
    game = GameResult(
        user_id=user_id,
        word_id=word_id,
        attempts=attempts,
        solved=solved,
        time_seconds=time_seconds,
        guess_history=guess_history,
    )
    db.add(game)

    # Clear any saved progress for this game
    await db.execute(
        delete(GameProgress).where(
            GameProgress.user_id == user_id,
            GameProgress.word_id == word_id,
        )
    )

    await db.commit()
    await db.refresh(game)

    rank = await get_rank_for_game(db, game)
    await update_streak(db, user_id, solved)

    return game, rank


async def get_rank_for_game(db: AsyncSession, game: GameResult) -> int:
    result = await db.execute(
        select(func.count(GameResult.id))
        .where(GameResult.word_id == game.word_id)
        .where(GameResult.solved == True)
        .where(GameResult.completed_at < game.completed_at)
    )
    count = result.scalar_one()
    return count + 1 if game.solved else 0


async def get_today_game(db: AsyncSession, user_id: int) -> Optional[GameResult]:
    today = date.today()
    result = await db.execute(
        select(GameResult)
        .join(DailyWord)
        .where(GameResult.user_id == user_id)
        .where(DailyWord.date == today)
    )
    return result.scalar_one_or_none()


async def get_game_history(
    db: AsyncSession, user_id: int, limit: int = 30, offset: int = 0
) -> list[GameResult]:
    result = await db.execute(
        select(GameResult)
        .where(GameResult.user_id == user_id)
        .order_by(GameResult.completed_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
