import hashlib
from datetime import date
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from server.words.models import DailyWord

VALID_WORDS_FILE = Path(__file__).parent.parent.parent / "data" / "valid_words.txt"
_valid_words_cache: set[str] = set()


def load_valid_words() -> set[str]:
    global _valid_words_cache
    if not _valid_words_cache and VALID_WORDS_FILE.exists():
        _valid_words_cache = {
            word.strip().upper()
            for word in VALID_WORDS_FILE.read_text().splitlines()
            if len(word.strip()) == 5
        }
    return _valid_words_cache


async def get_todays_word(db: AsyncSession) -> Optional[DailyWord]:
    today = date.today()
    result = await db.execute(select(DailyWord).where(DailyWord.date == today))
    return result.scalar_one_or_none()


async def get_word_by_date(db: AsyncSession, target_date: date) -> Optional[DailyWord]:
    result = await db.execute(select(DailyWord).where(DailyWord.date == target_date))
    return result.scalar_one_or_none()


def hash_word(word: str) -> str:
    return hashlib.sha256(word.upper().encode()).hexdigest()[:16]


def is_valid_word(word: str) -> bool:
    valid_words = load_valid_words()
    return word.upper() in valid_words
