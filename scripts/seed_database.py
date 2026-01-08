#!/usr/bin/env python3
"""Seed the daily_words table from generated word list."""

import asyncio
import json
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
WORDS_FILE = DATA_DIR / "words_2026.json"


async def seed_words():
    from sqlalchemy import select
    from server.database import async_session_factory
    from server.words.models import DailyWord

    if not WORDS_FILE.exists():
        print(f"Error: {WORDS_FILE} not found. Run generate_words.py first.")
        return

    word_data = json.loads(WORDS_FILE.read_text())

    async with async_session_factory() as session:
        existing = await session.execute(select(DailyWord))
        existing_dates = {row.date for row in existing.scalars().all()}

        added = 0
        for entry in word_data:
            word_date = date.fromisoformat(entry["date"])
            if word_date not in existing_dates:
                word = DailyWord(
                    date=word_date,
                    word=entry["word"],
                    difficulty_rank=5,
                )
                session.add(word)
                added += 1

        await session.commit()
        print(f"Added {added} new daily words (skipped {len(word_data) - added} existing)")


if __name__ == "__main__":
    asyncio.run(seed_words())
