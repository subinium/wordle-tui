from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class TodayWordResponse(BaseModel):
    date: date
    word_id: int
    word_hash: str
    word: Optional[str] = None  # Only returned for authenticated users


class ValidateWordRequest(BaseModel):
    word: str = Field(..., min_length=5, max_length=5)


class ValidateWordResponse(BaseModel):
    valid: bool


class RevealWordResponse(BaseModel):
    date: date
    word: str
