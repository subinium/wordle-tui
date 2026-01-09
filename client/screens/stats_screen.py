"""Statistics screen showing personal and global stats."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.containers import Vertical, Container
from textual.binding import Binding
from rich.text import Text

from client.widgets.contribution_graph import ContributionGraph


class StatsScreen(ModalScreen):
    """Modal screen for viewing statistics."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("f1", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    CSS = """
    StatsScreen {
        align: center middle;
    }

    #stats-container {
        width: 70;
        height: auto;
        background: #1a1a1b;
        border: solid #3a3a3c;
        padding: 1 2;
    }

    #stats-title {
        width: 100%;
        height: 1;
        content-align: center middle;
        text-style: bold;
        color: #ffffff;
        padding-bottom: 1;
    }

    .stats-section {
        width: 100%;
        height: auto;
        padding: 1 0;
    }

    .stats-row {
        width: 100%;
        height: 1;
    }

    #contribution-section {
        width: 100%;
        height: auto;
        padding: 1 0;
        border-top: solid #3a3a3c;
    }

    #contribution-title {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: #ffffff;
        padding-bottom: 1;
    }

    #close-hint {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: #565758;
        padding-top: 1;
    }
    """

    def __init__(self, stats: dict | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = stats or self._get_default_stats()

    def _get_default_stats(self) -> dict:
        """Return default/demo stats when not connected to server."""
        return {
            "total_games": 0,
            "total_wins": 0,
            "win_rate": 0.0,
            "current_streak": 0,
            "longest_streak": 0,
            "avg_attempts": 0.0,
            "attempts_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0},
            "game_history": [],  # List of {date, solved, attempts}
        }

    def compose(self) -> ComposeResult:
        with Container(id="stats-container"):
            yield Static("[bold white]📊 Statistics[/]", id="stats-title")
            yield Static(id="stats-content", classes="stats-section")
            yield Static(id="distribution-content", classes="stats-section")
            with Container(id="contribution-section"):
                yield Static("[bold white]🌱 Activity[/]", id="contribution-title")
                yield ContributionGraph(id="contribution-graph")
            yield Static("[#565758]Press ESC or Q to close[/]", id="close-hint")

    def on_mount(self) -> None:
        self._render_stats()
        self._render_distribution()
        self._render_contribution_graph()

    def _render_stats(self) -> None:
        content = self.query_one("#stats-content", Static)

        games = self.stats.get("total_games", 0)
        wins = self.stats.get("total_wins", 0)
        win_rate = self.stats.get("win_rate", 0)
        current = self.stats.get("current_streak", 0)
        longest = self.stats.get("longest_streak", 0)
        avg = self.stats.get("avg_attempts", 0)

        lines = [
            f"[#818384]Games Played[/]    [bold white]{games:>5}[/]      [#818384]Win Rate[/]   [bold white]{win_rate:>6.1f}%[/]",
            f"[#818384]Current Streak[/]  [bold #ff6b35]{current:>5}[/]      [#818384]Max Streak[/] [bold white]{longest:>6}[/]",
            f"[#818384]Avg Attempts[/]    [bold white]{avg:>5.1f}[/]",
        ]

        content.update(Text.from_markup("\n".join(lines)))

    def _render_distribution(self) -> None:
        content = self.query_one("#distribution-content", Static)

        dist = self.stats.get("attempts_distribution", {})
        max_count = max(dist.values()) if dist and max(dist.values()) > 0 else 1

        lines = ["[bold white]Guess Distribution[/]", ""]

        for i in range(1, 7):
            count = dist.get(str(i), 0)
            bar_width = int((count / max_count) * 25) if max_count > 0 else 0
            if bar_width == 0 and count > 0:
                bar_width = 1

            bar = "█" * bar_width
            color = self._get_bar_color(i)

            lines.append(f"[#818384]{i}[/] [{color}]{bar:<25}[/] [#818384]{count:>3}[/]")

        content.update(Text.from_markup("\n".join(lines)))

    def _get_bar_color(self, attempts: int) -> str:
        if attempts <= 2:
            return "#39d353"
        elif attempts <= 3:
            return "#26a641"
        elif attempts <= 4:
            return "#006d32"
        else:
            return "#0e4429"

    def _render_contribution_graph(self) -> None:
        """Set up the contribution graph with game history."""
        graph = self.query_one("#contribution-graph", ContributionGraph)
        game_history = self.stats.get("game_history", [])
        graph.set_data(game_history)

    def action_dismiss(self) -> None:
        self.app.pop_screen()
