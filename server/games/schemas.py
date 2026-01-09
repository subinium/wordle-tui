from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional


class GameSubmitRequest(BaseModel):
    word_id: int
    attempts: int = Field(..., ge=1, le=7)
    solved: bool
    time_seconds: Optional[int] = Field(None, ge=0)
    guess_history: list[str] = Field(..., min_length=1, max_length=6)


class StreakInfo(BaseModel):
    current: int
    longest: int


class GameSubmitResponse(BaseModel):
    id: int
    rank: int
    streak: StreakInfo


class GameHistoryItem(BaseModel):
    date: date
    attempts: int
    solved: bool
    time_seconds: Optional[int]
    word: Optional[str] = None

    class Config:
        from_attributes = True


class TodayGameResponse(BaseModel):
    played: bool
    result: Optional[GameHistoryItem] = None


# Game Progress (auto-save)
class SaveProgressRequest(BaseModel):
    word_id: int
    guesses: list[str] = Field(default_factory=list, max_length=6)
    elapsed_seconds: int = Field(0, ge=0)


class ProgressResponse(BaseModel):
    word_id: int
    guesses: list[str]
    elapsed_seconds: int
    has_progress: bool = True
