from sqlalchemy import Column, Integer, String, Date, SmallInteger
from server.database import Base


class DailyWord(Base):
    __tablename__ = "daily_words"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    word = Column(String(5), nullable=False)
    difficulty_rank = Column(SmallInteger, default=5)
