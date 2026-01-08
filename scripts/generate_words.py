#!/usr/bin/env python3
"""
Generate daily words for Wordle.

This script reads from a PRIVATE answer word list (not in repo)
and generates the daily word schedule.

Setup:
1. Create data/answer_words.txt with your curated 5-letter words (one per line)
2. This file should NOT be committed to the repo
3. Run this script to generate words_2026.json
4. Run seed_database.py to populate the database
"""

import json
import random
from pathlib import Path
from datetime import date, timedelta

SEED = 2026
TARGET_COUNT = 365
DATA_DIR = Path(__file__).parent.parent / "data"
ANSWER_WORDS_FILE = DATA_DIR / "answer_words.txt"
OUTPUT_FILE = DATA_DIR / "words_2026.json"


def load_answer_words() -> list[str]:
    """Load answer words from private file."""
    if not ANSWER_WORDS_FILE.exists():
        print(f"Error: {ANSWER_WORDS_FILE} not found!")
        print("")
        print("Please create this file with your curated answer words.")
        print("One 5-letter word per line. This file should NOT be in git.")
        print("")
        print("Example content:")
        print("  CRANE")
        print("  AUDIO")
        print("  STONE")
        print("  ...")
        exit(1)

    words = []
    for line in ANSWER_WORDS_FILE.read_text().splitlines():
        word = line.strip().upper()
        if len(word) == 5 and word.isalpha():
            words.append(word)

    return list(set(words))  # Remove duplicates


def generate_word_list() -> list[dict]:
    """Generate shuffled word schedule."""
    words = load_answer_words()

    if len(words) < TARGET_COUNT:
        print(f"Warning: Only {len(words)} words available, need {TARGET_COUNT}")
        print("Words will repeat if not enough unique words.")

    random.seed(SEED)
    random.shuffle(words)

    # Extend if needed
    while len(words) < TARGET_COUNT:
        words = words + words

    selected = words[:TARGET_COUNT]

    start_date = date(2026, 1, 1)
    word_schedule = []

    for i, word in enumerate(selected):
        game_date = start_date + timedelta(days=i)
        word_schedule.append({
            "date": game_date.isoformat(),
            "word": word.upper(),
            "day_number": i + 1,
        })

    return word_schedule


def main():
    DATA_DIR.mkdir(exist_ok=True)

    word_schedule = generate_word_list()

    OUTPUT_FILE.write_text(json.dumps(word_schedule, indent=2))

    print(f"Generated {len(word_schedule)} words")
    print(f"Saved to {OUTPUT_FILE}")
    print("")
    print("Next steps:")
    print("  1. Set DATABASE_URL environment variable")
    print("  2. Run: python scripts/seed_database.py")


if __name__ == "__main__":
    main()
