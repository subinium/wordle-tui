"""Leaderboard screen showing today's rankings."""

from datetime import date
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.containers import Vertical, Container
from textual.binding import Binding
from rich.text import Text


class LeaderboardScreen(ModalScreen):
    """Modal screen for viewing leaderboard."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("f2", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    CSS = """
    LeaderboardScreen {
        align: center middle;
        overflow: hidden;
    }

    #leaderboard-container {
        width: 55;
        height: auto;
        max-height: 30;
        background: #1a1a1b;
        border: solid #3a3a3c;
        padding: 1 2;
        overflow: hidden;
    }

    #leaderboard-title {
        width: 100%;
        height: 1;
        content-align: center middle;
        text-style: bold;
        color: #ffffff;
        overflow: hidden;
    }

    #leaderboard-date {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: #818384;
        padding-bottom: 1;
        overflow: hidden;
    }

    #leaderboard-header {
        width: 100%;
        height: 1;
        color: #818384;
        border-bottom: solid #3a3a3c;
        overflow: hidden;
    }

    #leaderboard-content {
        width: 100%;
        height: auto;
        max-height: 18;
        overflow: hidden;
        padding: 1 0;
    }

    #close-hint {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: #565758;
        padding-top: 1;
        overflow: hidden;
    }
    """

    def __init__(self, entries: list | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.entries = entries or []

    def compose(self) -> ComposeResult:
        with Container(id="leaderboard-container"):
            yield Static("[bold white]🏆 Leaderboard[/]", id="leaderboard-title")
            yield Static(f"[#818384]{date.today().strftime('%Y-%m-%d')}[/]", id="leaderboard-date")
            yield Static(
                "[#818384]Rank   Player              Tries   Time[/]",
                id="leaderboard-header"
            )
            yield Static(id="leaderboard-content")
            yield Static("[#565758]Press ESC or Q to close[/]", id="close-hint")

    def on_mount(self) -> None:
        self._render_leaderboard()

    def _render_leaderboard(self) -> None:
        content = self.query_one("#leaderboard-content", Static)

        if not self.entries:
            content.update(Text.from_markup("[#818384]No entries yet. Be the first![/]"))
            return

        lines = []
        for entry in self.entries[:15]:  # Show top 15
            rank = entry.get("rank", 0)
            username = entry.get("username", "???")[:15]
            attempts = entry.get("attempts", 0)
            time_sec = entry.get("time_seconds")

            # Rank styling
            if rank == 1:
                rank_str = "[bold #ffd700]🥇  1[/]"
            elif rank == 2:
                rank_str = "[bold #c0c0c0]🥈  2[/]"
            elif rank == 3:
                rank_str = "[bold #cd7f32]🥉  3[/]"
            else:
                rank_str = f"[#818384]   {rank:>2}[/]"

            # Time formatting
            if time_sec:
                mins = time_sec // 60
                secs = time_sec % 60
                time_str = f"{mins}:{secs:02d}"
            else:
                time_str = "-:--"

            # Attempts color
            if attempts <= 2:
                attempts_color = "#39d353"
            elif attempts <= 3:
                attempts_color = "#26a641"
            elif attempts <= 4:
                attempts_color = "#6aaa64"
            else:
                attempts_color = "#c9b458"

            line = (
                f"{rank_str}   "
                f"[white]{username:<15}[/]   "
                f"[{attempts_color}]{attempts}[/]       "
                f"[#818384]{time_str}[/]"
            )
            lines.append(line)

        content.update(Text.from_markup("\n".join(lines)))

    def action_dismiss(self) -> None:
        self.app.pop_screen()
