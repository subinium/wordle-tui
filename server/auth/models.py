from sqlalchemy import Column, Integer, String, DateTime, BigInteger, func
from sqlalchemy.orm import relationship
from server.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    github_id = Column(BigInteger, unique=True, nullable=True, index=True)
    avatar_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), onupdate=func.now())

    game_results = relationship("GameResult", back_populates="user")
    streak = relationship("UserStreak", back_populates="user", uselist=False)
