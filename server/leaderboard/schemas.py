from pydantic import BaseModel
from typing import Optional


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    attempts: int
    time_seconds: Optional[int]

    class Config:
        from_attributes = True
