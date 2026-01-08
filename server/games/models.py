from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, JSON, UniqueConstraint, func
from sqlalchemy.orm import relationship
from server.database import Base


class GameResult(Base):
    __tablename__ = "game_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    word_id = Column(Integer, ForeignKey("daily_words.id"), nullable=False)
    attempts = Column(Integer, nullable=False)
    solved = Column(Boolean, nullable=False)
    time_seconds = Column(Integer, nullable=True)
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    guess_history = Column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "word_id", name="unique_user_daily_game"),
    )

    user = relationship("User", back_populates="game_results")
    word = relationship("DailyWord")
