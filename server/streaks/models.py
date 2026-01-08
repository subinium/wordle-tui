from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from server.database import Base


class UserStreak(Base):
    __tablename__ = "user_streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_played = Column(Date, nullable=True)
    total_games = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)

    user = relationship("User", back_populates="streak")
