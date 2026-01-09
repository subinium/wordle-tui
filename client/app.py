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
from client.screens.result_screen import ResultScreen
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


async def get_server_word_and_progress(token: str) -> dict:
    """Get today's word and any saved progress from SERVER."""
    result = {"word": None, "word_id": 0, "guesses": [], "elapsed_seconds": 0, "auth_failed": False}
    try:
        client = get_api_client(API_URL)
        client.session = type('Session', (), {'token': token})()
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch today's word
        response = await client._client.get(
            f"{API_URL}/words/today",
            headers=headers,
        )

        # Check for auth failure (deleted user, invalid token)
        if response.status_code == 401:
            result["auth_failed"] = True
            return result

        if response.status_code == 200:
            data = response.json()
            result["word"] = data.get("word")
            result["word_id"] = data.get("word_id", 0)

        # Fetch any saved progress
        progress_response = await client._client.get(
            f"{API_URL}/games/progress/today",
            headers=headers,
        )
        if progress_response.status_code == 200:
            progress_data = progress_response.json()
            if progress_data.get("has_progress"):
                result["guesses"] = progress_data.get("guesses", [])
                result["elapsed_seconds"] = progress_data.get("elapsed_seconds", 0)
            elif progress_data.get("completed"):
                # Game already completed
                result["completed"] = True
                result["completed_result"] = progress_data.get("result", {})
    except Exception:
        pass
    return result


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
        self.user_email = ""
        self.user_token = None
        self.streak = 0
        self.target_word = None  # Will be set based on login status
        self.word_id = 0
        self.saved_guesses: list[str] = []
        self.saved_elapsed = 0
        self._config = ClientConfig()
        self.api_url = API_URL

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
        self.user_email = result.get("email", "")
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
        server_data = await get_server_word_and_progress(self.user_token)

        # Handle auth failure (deleted user, invalid token)
        if server_data.get("auth_failed"):
            self._config.clear()
            self.user_token = None
            self.username = "Player"
            # Show login screen
            self.push_screen(LoginScreen(api_url=API_URL), self._on_login)
            return

        if server_data.get("word"):
            self.target_word = server_data["word"].upper()
            self.word_id = server_data.get("word_id", 0)
            self.saved_guesses = server_data.get("guesses", [])
            self.saved_elapsed = server_data.get("elapsed_seconds", 0)
        else:
            # Fallback to local if server fails
            self.target_word = get_local_word()

        # If game is already completed, show result screen
        if server_data.get("completed"):
            completed_result = server_data.get("completed_result", {})
            self._show_completed_result(completed_result)
        else:
            self._start_game()

    def _show_completed_result(self, result: dict) -> None:
        """Show result screen for already completed game."""
        solved = result.get("solved", False)
        attempts = result.get("attempts", 0)
        time_seconds = result.get("time_seconds", 0)
        guesses = result.get("guess_history", [])

        result_data = {
            "won": solved,
            "attempts": attempts,
            "target_word": self.target_word,
            "time_seconds": time_seconds or 0,
            "guesses": guesses,
            "username": self.username,
            "already_played": True,
            "personal_stats": {
                "total_games": 0,
                "total_wins": 0,
                "win_rate": 0,
                "current_streak": self.streak,
                "longest_streak": self.streak,
                "avg_attempts": 0,
                "attempts_distribution": {},
            },
            "global_stats": {},
        }
        self.push_screen(ResultScreen(
            result_data,
            api_url=self.api_url,
            token=self.user_token or "",
            email=self.user_email,
        ))

    def _start_game(self) -> None:
        """Start the game screen."""
        if not self.target_word:
            self.target_word = get_local_word()

        self.push_screen(GameScreen(
            target_word=self.target_word,
            username=self.username,
            streak=self.streak,
            token=self.user_token or "",
            email=self.user_email,
            api_url=self.api_url,
            word_id=self.word_id,
            saved_guesses=self.saved_guesses,
            saved_elapsed=self.saved_elapsed,
        ))


def main():
    app = WordleApp()
    app.run()


if __name__ == "__main__":
    main()
