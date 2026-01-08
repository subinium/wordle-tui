"""Wordle TUI - Main Application."""

import asyncio
import json
import os
from datetime import date
from pathlib import Path
from textual.app import App
from textual.binding import Binding

from client.screens.game_screen import GameScreen
from client.screens.login_screen import LoginScreen
from client.api_client import get_api_client
from client.config import ClientConfig


DATA_DIR = Path(__file__).parent.parent / "data"
OFFLINE_WORDS_FILE = DATA_DIR / "words_offline.json"

# API URL from environment or default (production)
API_URL = os.environ.get("WORDLE_API_URL", "https://wordle-tui-production.up.railway.app")


def get_local_word() -> str:
    """Get today's word from the LOCAL word list (offline mode)."""
    if not OFFLINE_WORDS_FILE.exists():
        return "CRANE"

    words = json.loads(OFFLINE_WORDS_FILE.read_text())
    today = date.today().isoformat()

    for entry in words:
        if entry["date"] == today:
            return entry["word"]

    # Fallback: use day of year as index
    day_of_year = date.today().timetuple().tm_yday
    return words[day_of_year % len(words)]["word"] if words else "CRANE"


async def get_server_word(token: str) -> str | None:
    """Get today's word from SERVER (logged-in mode)."""
    try:
        client = get_api_client(API_URL)
        client.session = type('Session', (), {'token': token})()

        response = await client._client.get(
            f"{API_URL}/words/today",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("word")
    except Exception:
        pass
    return None


class WordleApp(App):
    """Wordle TUI Application."""

    TITLE = "Wordle TUI"

    CSS = """
    Screen {
        background: #121213;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self, skip_login: bool = False) -> None:
        super().__init__()
        self.skip_login = skip_login
        self.username = "Player"
        self.user_token = None
        self.streak = 0
        self.target_word = None  # Will be set based on login status
        self._config = ClientConfig()

    def on_mount(self) -> None:
        if self.skip_login:
            # Skip login, use local word
            self.target_word = get_local_word()
            self._start_game()
        elif self._config.is_authenticated:
            # Auto-login with saved token
            self.username = self._config.username or "Player"
            self.user_token = self._config.token
            asyncio.create_task(self._fetch_server_word_and_start())
        else:
            # Show login screen first
            self.push_screen(LoginScreen(api_url=API_URL), self._on_login)

    def _on_login(self, result: dict) -> None:
        """Handle login result."""
        self.username = result.get("username", "Player")
        self.user_token = result.get("token")
        self.streak = result.get("streak", 0)

        if self.user_token:
            # Logged in - fetch word from server
            asyncio.create_task(self._fetch_server_word_and_start())
        else:
            # Offline - use local word
            self.target_word = get_local_word()
            self._start_game()

    async def _fetch_server_word_and_start(self) -> None:
        """Fetch word from server and start game."""
        server_word = await get_server_word(self.user_token)

        if server_word:
            self.target_word = server_word.upper()
        else:
            # Fallback to local if server fails
            self.target_word = get_local_word()

        self._start_game()

    def _start_game(self) -> None:
        """Start the game screen."""
        if not self.target_word:
            self.target_word = get_local_word()

        self.push_screen(GameScreen(
            target_word=self.target_word,
            username=self.username,
            streak=self.streak,
        ))


def main():
    app = WordleApp()
    app.run()


if __name__ == "__main__":
    main()
