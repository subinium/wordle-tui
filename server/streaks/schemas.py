from pydantic import BaseModel
from datetime import date
from typing import Optional


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    total_games: int
    total_wins: int
    last_played: Optional[date]

    class Config:
        from_attributes = True


class ContributionDataItem(BaseModel):
    date: date
    attempts: int
    solved: bool


class ContributionDataResponse(BaseModel):
    data: list[ContributionDataItem]
