from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from server.database import get_db
from server.auth.service import verify_token
from server.words.schemas import (
    TodayWordResponse,
    ValidateWordRequest,
    ValidateWordResponse,
    RevealWordResponse,
)
from server.words.service import get_todays_word, get_word_by_date, hash_word, is_valid_word

router = APIRouter(prefix="/words", tags=["words"])


@router.get("/today", response_model=TodayWordResponse)
async def get_today(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    word = await get_todays_word(db)
    if word is None:
        raise HTTPException(status_code=404, detail="No word set for today")

    # Check if user is authenticated
    actual_word = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        user_id = verify_token(token)
        if user_id:
            # Authenticated user gets the actual word
            actual_word = word.word

    return TodayWordResponse(
        date=word.date,
        word_id=word.id,
        word_hash=hash_word(word.word),
        word=actual_word,
    )


@router.post("/validate", response_model=ValidateWordResponse)
async def validate_word(request: ValidateWordRequest):
    return ValidateWordResponse(valid=is_valid_word(request.word))


@router.get("/reveal/{target_date}", response_model=RevealWordResponse)
async def reveal_word(target_date: date, db: AsyncSession = Depends(get_db)):
    today = date.today()
    if target_date >= today:
        raise HTTPException(status_code=403, detail="Cannot reveal today's or future words")

    word = await get_word_by_date(db, target_date)
    if word is None:
        raise HTTPException(status_code=404, detail="No word found for this date")

    return RevealWordResponse(date=word.date, word=word.word)
