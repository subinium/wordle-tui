"""Statistics panel with guess distribution chart."""

from textual.widget import Widget
from rich.text import Text
from rich.console import RenderableType


class StatsPanel(Widget):
    """Personal statistics panel."""

    DEFAULT_CSS = """
    StatsPanel {
        width: 100%;
        height: auto;
        padding: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats: dict = {
            "total_games": 0,
            "total_wins": 0,
            "win_rate": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "avg_attempts": 0,
            "attempts_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0},
        }

    def set_stats(self, stats: dict) -> None:
        self.stats = stats
        self.refresh()

    def render(self) -> RenderableType:
        lines = []

        games = self.stats.get("total_games", 0)
        wins = self.stats.get("total_wins", 0)
        win_rate = self.stats.get("win_rate", 0)
        current = self.stats.get("current_streak", 0)
        longest = self.stats.get("longest_streak", 0)
        avg = self.stats.get("avg_attempts", 0)

        lines.append("[bold white]Your Statistics[/]")
        lines.append("")

        stat_line = (
            f"[#818384]Played[/] [bold white]{games:>4}[/]   "
            f"[#818384]Win %[/] [bold white]{win_rate:>5.1f}[/]   "
            f"[#818384]Current[/] [bold #ff6b35]{current:>3}[/]   "
            f"[#818384]Max[/] [bold white]{longest:>3}[/]"
        )
        lines.append(stat_line)
        lines.append("")

        lines.append("[bold white]Guess Distribution[/]")
        lines.append("")

        dist = self.stats.get("attempts_distribution", {})
        max_count = max(dist.values()) if dist.values() else 1

        for i in range(1, 7):
            count = dist.get(str(i), 0)
            bar_width = int((count / max_count) * 20) if max_count > 0 else 0
            bar = "▓" * bar_width

            if bar_width == 0 and count > 0:
                bar = "▓"

            lines.append(
                f"[#818384]{i}[/] [{self._get_bar_color(i)}]{bar}[/] "
                f"[#818384]({count})[/]"
            )

        return Text.from_markup("\n".join(lines))

    def _get_bar_color(self, attempts: int) -> str:
        if attempts <= 2:
            return "#39d353"
        elif attempts <= 3:
            return "#26a641"
        elif attempts <= 4:
            return "#006d32"
        else:
            return "#0e4429"


class GlobalStatsPanel(Widget):
    """Today's global statistics panel."""

    DEFAULT_CSS = """
    GlobalStatsPanel {
        width: 100%;
        height: auto;
        padding: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats: dict = {}

    def set_stats(self, stats: dict) -> None:
        self.stats = stats
        self.refresh()

    def render(self) -> RenderableType:
        if not self.stats:
            return Text.from_markup("[#818384]Loading global stats...[/]")

        lines = []
        lines.append("[bold white]Today's Global Stats[/]")
        lines.append("")

        total = self.stats.get("total_players", 0)
        solved = self.stats.get("total_solved", 0)
        rate = self.stats.get("solve_rate", 0)
        avg = self.stats.get("winners_avg_attempts", 0)

        lines.append(
            f"[#818384]Players[/] [bold white]{total:>5}[/]   "
            f"[#818384]Solved[/] [bold #6aaa64]{solved:>5}[/]   "
            f"[#818384]Rate[/] [bold white]{rate:>5.1f}%[/]   "
            f"[#818384]Avg[/] [bold white]{avg:.1f}[/]"
        )

        return Text.from_markup("\n".join(lines))
