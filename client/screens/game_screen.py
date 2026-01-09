"""Main game screen for Wordle."""

import asyncio
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Korea Standard Time (UTC+9)
KST = timezone(timedelta(hours=9))
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.containers import Vertical, Horizontal, Container
from textual.binding import Binding
from rich.text import Text

from client.widgets.game_board import GameBoard
from client.widgets.keyboard import Keyboard
from client.widgets.tile import TileState
from client.screens.stats_screen import StatsScreen
from client.screens.leaderboard_screen import LeaderboardScreen
from client.screens.result_screen import ResultScreen
from client.screens.help_screen import HelpScreen
from client.screens.settings_screen import SettingsScreen


# Load valid words once
VALID_WORDS_FILE = Path(__file__).parent.parent.parent / "data" / "valid_words.txt"
VALID_WORDS: set[str] = set()

def load_valid_words() -> set[str]:
    """Load valid words from file."""
    global VALID_WORDS
    if not VALID_WORDS:
        if VALID_WORDS_FILE.exists():
            VALID_WORDS = set(
                word.strip().upper()
                for word in VALID_WORDS_FILE.read_text().splitlines()
                if word.strip()
            )
    return VALID_WORDS


def get_time_until_next_word() -> str:
    """Calculate time until next word (9 AM KST)."""
    now_kst = datetime.now(KST)

    # Next 9 AM KST
    next_9am = now_kst.replace(hour=9, minute=0, second=0, microsecond=0)
    if now_kst.hour >= 9:
        next_9am += timedelta(days=1)

    diff = next_9am - now_kst
    hours, remainder = divmod(int(diff.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class GameHeader(Static):
    """Game header with title and stats."""

    DEFAULT_CSS = """
    GameHeader {
        width: 100%;
        height: 4;
        content-align: center middle;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.streak = 0
        self.username = ""
        self.elapsed_seconds = 0
        self.timer_running = False

    def render(self) -> Text:
        # Line 1: Title and user info
        title = "[bold white]W O R D L E[/]"
        user_parts = []
        if self.username:
            user_parts.append(f"[#6aaa64]{self.username}[/]")
        if self.streak > 0:
            user_parts.append(f"[#ff6b35]🔥{self.streak}[/]")

        line1 = f"{title}  {'  '.join(user_parts)}" if user_parts else title

        # Line 2: Timers
        mins = self.elapsed_seconds // 60
        secs = self.elapsed_seconds % 60
        timer_str = f"⏱ {mins}:{secs:02d}"
        next_word_time = get_time_until_next_word()

        line2 = f"[#c9b458]{timer_str}[/]  [#818384]Next: {next_word_time}[/]"

        return Text.from_markup(f"{line1}\n{line2}")

    def set_info(self, username: str = "", streak: int = 0) -> None:
        self.username = username
        self.streak = streak
        self.refresh()

    def update_timer(self, seconds: int) -> None:
        self.elapsed_seconds = seconds
        self.refresh()


class GameMessage(Static):
    """Message display area."""

    DEFAULT_CSS = """
    GameMessage {
        width: 100%;
        height: 1;
        content-align: center middle;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = ""

    def render(self) -> Text:
        return Text.from_markup(self._message)

    def show(self, message: str, style: str = "#ffffff") -> None:
        self._message = f"[{style}]{message}[/]"
        self.refresh()

    def clear(self) -> None:
        self._message = ""
        self.refresh()


class GameScreen(Screen):
    """Main Wordle game screen."""

    BINDINGS = [
        Binding("escape", "quit", "Quit"),
        Binding("ctrl+q", "quit", "Quit", show=False),
        Binding("f1", "stats", "F1:Stats"),
        Binding("ctrl+s", "stats", "Stats", show=False),
        Binding("f2", "leaderboard", "F2:Leaderboard"),
        Binding("ctrl+l", "leaderboard", "Leaderboard", show=False),
        Binding("f3", "help", "F3:Help"),
        Binding("f4", "settings", "F4:Settings"),
    ]

    CSS = """
    GameScreen {
        background: #121213;
        layout: vertical;
        overflow: hidden;
    }

    #game-container {
        width: 100%;
        height: 100%;
        layout: vertical;
        align: center top;
        overflow: hidden;
    }

    #header {
        height: 4;
        overflow: hidden;
    }

    #board-area {
        width: 100%;
        height: 19;
        align: center middle;
        overflow: hidden;
    }

    #message {
        width: 100%;
        height: 2;
        content-align: center middle;
        overflow: hidden;
    }

    #keyboard-area {
        width: 100%;
        height: 7;
        align: center middle;
        content-align: center middle;
        overflow: hidden;
    }

    #footer-hint {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: #565758;
        overflow: hidden;
    }
    """

    def __init__(
        self,
        target_word: str = "CRANE",
        username: str = "",
        streak: int = 0,
        token: str = "",
        email: str = "",
        api_url: str = "",
        word_id: int = 0,
        saved_guesses: list[str] | None = None,
        saved_elapsed: int = 0,
    ) -> None:
        super().__init__()
        self.target_word = target_word.upper()
        self.username = username
        self.streak = streak
        self.token = token
        self.email = email
        self.api_url = api_url
        self.word_id = word_id
        self.saved_guesses = saved_guesses or []
        self.saved_elapsed = saved_elapsed
        self.game_over = False
        self.won = False
        self.start_time = time.time()
        self.elapsed_seconds = saved_elapsed
        self._timer_task = None
        self._api_client = None

    def compose(self) -> ComposeResult:
        with Vertical(id="game-container"):
            yield GameHeader(id="header")
            yield Container(id="board-area")
            yield GameMessage(id="message")
            yield Container(id="keyboard-area")
            yield Static("[#565758]ESC: Quit | F1: Stats | F2: Leaderboard | F3: Help | F4: Settings[/]", id="footer-hint")

    def on_mount(self) -> None:
        header = self.query_one("#header", GameHeader)
        header.set_info(self.username, self.streak)

        board_area = self.query_one("#board-area", Container)
        self.board = GameBoard()
        self.board.set_target(self.target_word)
        board_area.mount(self.board)

        keyboard_area = self.query_one("#keyboard-area", Container)
        self.keyboard = Keyboard()
        keyboard_area.mount(self.keyboard)

        # Initialize API client for auto-save
        if self.token and self.api_url:
            from client.api_client import WordleAPIClient, UserSession
            self._api_client = WordleAPIClient(self.api_url)
            self._api_client.session = UserSession(
                user_id=0,
                username=self.username,
                token=self.token,
            )

        # Restore saved guesses if any
        if self.saved_guesses:
            asyncio.create_task(self._restore_saved_guesses())

        # Start timer (account for saved elapsed time)
        self.start_time = time.time() - self.saved_elapsed
        self._timer_task = asyncio.create_task(self._run_timer())

    async def _restore_saved_guesses(self) -> None:
        """Restore previously saved guesses."""
        for guess in self.saved_guesses:
            for letter in guess:
                self.board.add_letter(letter)
            won, feedback = await self.board.submit_guess()
            self.keyboard.update_from_guess(guess, feedback)
            if won:
                self.game_over = True
                self.won = True
                return

    async def _run_timer(self) -> None:
        """Update timer every second."""
        header = self.query_one("#header", GameHeader)
        while not self.game_over:
            self.elapsed_seconds = int(time.time() - self.start_time)
            header.update_timer(self.elapsed_seconds)
            await asyncio.sleep(1)

    def on_key(self, event) -> None:
        if self.game_over:
            if event.key == "enter":
                self.app.exit()
            return

        key = event.key

        if key == "backspace":
            self.board.remove_letter()
        elif key == "enter":
            asyncio.create_task(self._submit_guess())
        elif len(key) == 1 and key.isalpha():
            self.board.add_letter(key)

    async def _submit_guess(self) -> None:
        if not self.board.is_row_complete():
            self._show_message("Not enough letters", "#c9b458")
            return

        guess = self.board.get_current_guess()

        # Validate word
        valid_words = load_valid_words()
        if valid_words and guess not in valid_words:
            self._show_message("Not in word list", "#c9b458")
            await self.board.shake_row()
            return

        won, feedback = await self.board.submit_guess()
        self.keyboard.update_from_guess(guess, feedback)

        if won:
            self.game_over = True
            self.won = True
            attempts = len(self.board.guesses)
            # Bounce animation for win
            await self.board.bounce_row(attempts - 1)
            # Submit result to server and show result screen
            await self._submit_and_show_result(won=True, attempts=attempts)
        elif self.board.current_row >= 6:
            self.game_over = True
            # Submit result to server and show result screen
            await self._submit_and_show_result(won=False, attempts=6)
        else:
            # Auto-save progress after each guess (only if not game over)
            asyncio.create_task(self._auto_save_progress())

    async def _auto_save_progress(self) -> None:
        """Save current game progress to server."""
        if not self._api_client or not self.word_id:
            return
        try:
            await self._api_client.save_progress(
                word_id=self.word_id,
                guesses=self.board.guesses,
                elapsed_seconds=self.elapsed_seconds,
            )
        except Exception:
            pass  # Silently fail - auto-save is best effort

    async def _submit_and_show_result(self, won: bool, attempts: int) -> None:
        """Submit game result to server and show result screen."""
        rank = 0
        server_streak = {"current": self.streak, "longest": self.streak}

        # Submit to server
        if self._api_client and self.word_id:
            try:
                result = await self._api_client.submit_game(
                    word_id=self.word_id,
                    attempts=attempts,
                    solved=won,
                    time_seconds=self.elapsed_seconds,
                    guess_history=self.board.guesses,
                )
                if result:
                    rank = result.get("rank", 0)
                    streak_data = result.get("streak", {})
                    server_streak = {
                        "current": streak_data.get("current", self.streak),
                        "longest": streak_data.get("longest", self.streak),
                    }
            except Exception:
                pass  # Show result anyway even if submit fails

        self._show_result_screen(won=won, attempts=attempts, rank=rank, streak=server_streak)

    def _show_message(self, message: str, color: str) -> None:
        msg = self.query_one("#message", GameMessage)
        msg.show(message, color)

    def _show_result_screen(
        self,
        won: bool,
        attempts: int,
        rank: int = 0,
        streak: dict | None = None,
    ) -> None:
        """Show result screen with stats."""
        streak = streak or {"current": self.streak, "longest": self.streak}

        result_data = {
            "won": won,
            "attempts": attempts,
            "target_word": self.target_word,
            "time_seconds": self.elapsed_seconds,
            "guesses": self.board.guesses,
            "username": self.username,
            "rank": rank,
            "personal_stats": {
                "total_games": 1,
                "total_wins": 1 if won else 0,
                "win_rate": 100.0 if won else 0.0,
                "current_streak": streak.get("current", 0),
                "longest_streak": streak.get("longest", 0),
                "avg_attempts": attempts if won else 0,
                "attempts_distribution": self._get_local_distribution(),
            },
            "global_stats": {},
        }
        self.app.push_screen(ResultScreen(
            result_data,
            api_url=self.api_url,
            token=self.token,
            email=self.email,
        ))

    def action_quit(self) -> None:
        self.app.exit()

    def action_stats(self) -> None:
        asyncio.create_task(self._show_stats())

    async def _show_stats(self) -> None:
        """Fetch and show stats from server."""
        stats = None
        if self._api_client:
            try:
                personal = await self._api_client.get_personal_stats()
                if personal:
                    # Also fetch game history for contribution graph
                    contribution = await self._api_client.get_contribution_data()
                    stats = {
                        "total_games": personal.get("total_games", 0),
                        "total_wins": personal.get("total_wins", 0),
                        "win_rate": personal.get("win_rate", 0.0),
                        "current_streak": personal.get("current_streak", 0),
                        "longest_streak": personal.get("longest_streak", 0),
                        "avg_attempts": personal.get("avg_attempts", 0.0),
                        "attempts_distribution": personal.get("attempts_distribution", {}),
                        "game_history": contribution or [],
                    }
            except Exception:
                pass

        if not stats:
            # Fallback to local stats
            stats = {
                "total_games": len(self.board.guesses) if self.game_over else 0,
                "total_wins": 1 if self.won else 0,
                "win_rate": 100.0 if self.won else 0.0,
                "current_streak": self.streak,
                "longest_streak": self.streak,
                "avg_attempts": len(self.board.guesses) if self.game_over else 0,
                "attempts_distribution": self._get_local_distribution(),
            }

        self.app.push_screen(StatsScreen(stats=stats))

    def action_leaderboard(self) -> None:
        asyncio.create_task(self._show_leaderboard())

    async def _show_leaderboard(self) -> None:
        """Fetch and show leaderboard from server."""
        entries = None
        if self._api_client:
            try:
                data = await self._api_client.get_leaderboard(limit=20)
                if data:
                    entries = [
                        {
                            "rank": i + 1,
                            "username": e.get("username", "???"),
                            "attempts": e.get("attempts", 0),
                            "time_seconds": e.get("time_seconds"),
                        }
                        for i, e in enumerate(data)
                    ]
            except Exception:
                pass

        self.app.push_screen(LeaderboardScreen(entries=entries))

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())

    def action_settings(self) -> None:
        """Open settings screen."""
        self.app.push_screen(
            SettingsScreen(
                username=self.username,
                email=self.email,
                token=self.token,
                api_url=self.api_url,
            ),
            self._on_settings_result,
        )

    def _on_settings_result(self, result: dict | None) -> None:
        """Handle settings screen result."""
        if result is None:
            return

        if result.get("action") == "logout":
            self.app.exit()
        elif result.get("action") == "updated":
            # Update username in header
            self.username = result.get("username", self.username)
            header = self.query_one("#header", GameHeader)
            header.set_info(self.username, self.streak)

    def _get_local_distribution(self) -> dict:
        """Get local game distribution."""
        dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}
        if self.game_over and self.won:
            attempts = len(self.board.guesses)
            if 1 <= attempts <= 6:
                dist[str(attempts)] = 1
        return dist
