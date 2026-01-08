"""GitHub-style contribution graph widget."""

from datetime import date, timedelta
from textual.widget import Widget
from rich.text import Text
from rich.console import RenderableType


GRAPH_COLORS = {
    "level_0": "#161b22",
    "level_1": "#0e4429",
    "level_2": "#006d32",
    "level_3": "#26a641",
    "level_4": "#39d353",
    "failed": "#da3633",
}


class ContributionGraph(Widget):
    """GitHub-style contribution heatmap for Wordle streaks."""

    DEFAULT_CSS = """
    ContributionGraph {
        width: 100%;
        height: auto;
        padding: 1;
    }
    """

    def __init__(self, weeks: int = 16, **kwargs) -> None:
        super().__init__(**kwargs)
        self.weeks = weeks
        self.game_data: dict[date, dict] = {}

    def set_data(self, data: list[dict]) -> None:
        self.game_data = {}
        for item in data:
            d = item["date"]
            if isinstance(d, str):
                d = date.fromisoformat(d)
            self.game_data[d] = item
        self.refresh()

    def _get_intensity(self, game: dict | None) -> int:
        if game is None:
            return 0
        if not game.get("solved"):
            return -1

        attempts = game.get("attempts", 6)
        if attempts <= 2:
            return 4
        elif attempts == 3:
            return 3
        elif attempts == 4:
            return 2
        else:
            return 1

    def _get_color(self, intensity: int) -> str:
        if intensity == -1:
            return GRAPH_COLORS["failed"]
        return GRAPH_COLORS.get(f"level_{intensity}", GRAPH_COLORS["level_0"])

    def render(self) -> RenderableType:
        lines = []
        today = date.today()
        num_weeks = self.weeks

        start_date = today - timedelta(weeks=num_weeks - 1)
        days_since_sunday = start_date.weekday() + 1
        if days_since_sunday < 7:
            start_date = start_date - timedelta(days=days_since_sunday)

        month_labels = self._generate_month_labels(start_date, num_weeks)
        lines.append(f"[#818384]    {month_labels}[/]")

        day_names = ["S", "M", "T", "W", "T", "F", "S"]
        for day_of_week in range(7):
            row_chars = [f"[#818384]{day_names[day_of_week]}[/] "]

            for week in range(num_weeks):
                check_date = start_date + timedelta(days=day_of_week, weeks=week)

                if check_date > today:
                    row_chars.append(" ")
                else:
                    game = self.game_data.get(check_date)
                    intensity = self._get_intensity(game)
                    color = self._get_color(intensity)
                    row_chars.append(f"[{color}]■[/]")

            lines.append("".join(row_chars))

        lines.append("")
        lines.append(
            "[#818384]Less[/] "
            f"[{GRAPH_COLORS['level_0']}]■[/]"
            f"[{GRAPH_COLORS['level_1']}]■[/]"
            f"[{GRAPH_COLORS['level_2']}]■[/]"
            f"[{GRAPH_COLORS['level_3']}]■[/]"
            f"[{GRAPH_COLORS['level_4']}]■[/]"
            " [#818384]More[/]  "
            f"[{GRAPH_COLORS['failed']}]■[/] [#818384]Failed[/]"
        )

        return Text.from_markup("\n".join(lines))

    def _generate_month_labels(self, start_date: date, weeks: int) -> str:
        labels = []
        current_month = None

        for week in range(weeks):
            week_date = start_date + timedelta(weeks=week)
            if week_date.month != current_month:
                current_month = week_date.month
                labels.append(week_date.strftime("%b")[:3])
            else:
                labels.append(" ")

        return "".join(labels)
