from pydantic import BaseModel
from datetime import date
from typing import Optional


class DailyStatsResponse(BaseModel):
    date: date
    total_players: int
    total_solved: int
    solve_rate: float
    avg_attempts: float
    winners_avg_attempts: float
    attempts_distribution: dict[str, int]


class PersonalStatsResponse(BaseModel):
    total_games: int
    total_wins: int
    win_rate: float
    current_streak: int
    longest_streak: int
    avg_attempts: float
    best_time_seconds: Optional[int]
    attempts_distribution: dict[str, int]


class MonthlyStatsItem(BaseModel):
    month: str
    played: int
    solved: int
    rate: float


class MonthlyStatsResponse(BaseModel):
    data: list[MonthlyStatsItem]
