#!/usr/bin/env python3
"""
Generate daily words for OFFLINE mode.

This creates a PUBLIC word list that ships with the client.
Different from the server's word list for security.
"""

import json
import random
from pathlib import Path
from datetime import date, timedelta

SEED = 9999  # Different seed from online version
TARGET_COUNT = 365
DATA_DIR = Path(__file__).parent.parent / "data"
ANSWER_WORDS_FILE = DATA_DIR / "answer_words_offline.txt"
OUTPUT_FILE = DATA_DIR / "words_offline.json"


def load_answer_words() -> list[str]:
    """Load offline answer words."""
    if not ANSWER_WORDS_FILE.exists():
        print(f"Error: {ANSWER_WORDS_FILE} not found!")
        exit(1)

    words = []
    for line in ANSWER_WORDS_FILE.read_text().splitlines():
        word = line.strip().upper()
        if len(word) == 5 and word.isalpha():
            words.append(word)

    return list(set(words))


def generate_word_list() -> list[dict]:
    """Generate shuffled word schedule for offline mode."""
    words = load_answer_words()

    if len(words) < TARGET_COUNT:
        print(f"Warning: Only {len(words)} words available")
        while len(words) < TARGET_COUNT:
            words = words + words

    random.seed(SEED)
    random.shuffle(words)

    selected = words[:TARGET_COUNT]

    start_date = date(2026, 1, 1)
    word_schedule = []

    for i, word in enumerate(selected):
        game_date = start_date + timedelta(days=i)
        word_schedule.append({
            "date": game_date.isoformat(),
            "word": word.upper(),
        })

    return word_schedule


def main():
    DATA_DIR.mkdir(exist_ok=True)
    word_schedule = generate_word_list()
    OUTPUT_FILE.write_text(json.dumps(word_schedule, indent=2))

    print(f"Generated {len(word_schedule)} offline words")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
