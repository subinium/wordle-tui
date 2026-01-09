"""Result screen shown after game ends with tabbed navigation."""

import asyncio
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, TabbedContent, TabPane
from textual.containers import Container, Vertical
from textual.binding import Binding
from rich.text import Text

from client.api_client import get_api_client


class ResultScreen(ModalScreen):
    """Modal screen for showing game results with tabs."""

    BINDINGS = [
        Binding("enter", "close", "Exit Game"),
        Binding("escape", "close", "Exit"),
        Binding("1", "tab_result", "Result", show=False),
        Binding("2", "tab_stats", "Stats", show=False),
        Binding("3", "tab_leaderboard", "Leaderboard", show=False),
        Binding("left", "prev_tab", "Previous Tab", show=False),
        Binding("right", "next_tab", "Next Tab", show=False),
    ]

    CSS = """
    ResultScreen {
        align: center middle;
        overflow: hidden;
    }

    #result-container {
        width: 60;
        height: 32;
        background: #1a1a1b;
        border: solid #3a3a3c;
        overflow: hidden;
    }

    #result-header {
        width: 100%;
        height: 4;
        content-align: center middle;
        background: #121213;
        border-bottom: solid #3a3a3c;
        overflow: hidden;
    }

    TabbedContent {
        height: auto;
        overflow: hidden;
    }

    TabPane {
        padding: 1 2;
        overflow: hidden;
    }

    ContentSwitcher {
        height: auto;
        overflow: hidden;
    }

    #tab-result, #tab-stats, #tab-leaderboard {
        height: auto;
        overflow: hidden;
    }

    .tab-section {
        width: 100%;
        height: auto;
        padding: 1 0;
        overflow: hidden;
    }

    #footer-nav {
        width: 100%;
        height: 2;
        content-align: center middle;
        background: #121213;
        border-top: solid #3a3a3c;
        overflow: hidden;
        dock: bottom;
    }
    """

    def __init__(self, result_data: dict, api_url: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.result_data = result_data
        self.api_url = api_url
        self.leaderboard_entries = []

    def compose(self) -> ComposeResult:
        with Container(id="result-container"):
            yield Static(id="result-header")
            with TabbedContent(id="tabs"):
                with TabPane("Result", id="tab-result"):
                    yield Static(id="result-content")
                with TabPane("My Stats", id="tab-stats"):
                    yield Static(id="stats-content")
                with TabPane("Leaderboard", id="tab-leaderboard"):
                    yield Static(id="leaderboard-content")
            yield Static(id="footer-nav")

    def on_mount(self) -> None:
        self._render_header()
        self._render_result()
        self._render_stats()
        self._render_leaderboard()
        self._render_footer()
        # Fetch real leaderboard data
        asyncio.create_task(self._fetch_leaderboard())

    def _render_header(self) -> None:
        header = self.query_one("#result-header", Static)
        won = self.result_data.get("won", False)
        attempts = self.result_data.get("attempts", 0)
        username = self.result_data.get("username", "Player")

        if won:
            messages = ["Genius!", "Magnificent!", "Impressive!", "Splendid!", "Great!", "Phew!"]
            msg = messages[min(attempts - 1, 5)]
            header.update(Text.from_markup(
                f"[bold #6aaa64]🎉 {msg} 🎉[/]\n"
                f"[#6aaa64]{username}[/]"
            ))
        else:
            header.update(Text.from_markup(
                f"[bold #787c7e]😔 Better luck next time![/]\n"
                f"[#818384]{username}[/]"
            ))

    def _render_result(self) -> None:
        content = self.query_one("#result-content", Static)

        won = self.result_data.get("won", False)
        attempts = self.result_data.get("attempts", 0)
        target = self.result_data.get("target_word", "?????")
        time_sec = self.result_data.get("time_seconds", 0)
        guesses = self.result_data.get("guesses", [])

        mins = time_sec // 60
        secs = time_sec % 60
        time_str = f"{mins}:{secs:02d}"

        personal = self.result_data.get("personal_stats", {})
        streak = personal.get("current_streak", 0)

        lines = []

        # Word result
        if won:
            lines.append(f"[bold #6aaa64]✓ {target}[/]")
        else:
            lines.append(f"[#818384]The word was: [bold white]{target}[/][/]")
        lines.append("")

        # Stats row
        if won:
            lines.append(f"[#818384]Solved in[/] [bold #6aaa64]{attempts}/6[/] [#818384]attempts[/]")
        else:
            lines.append(f"[#818384]Used all[/] [bold #787c7e]6/6[/] [#818384]attempts[/]")

        lines.append(f"[#818384]Time:[/] [bold white]{time_str}[/]")

        if streak > 0:
            lines.append(f"[#818384]Streak:[/] [bold #ff6b35]🔥 {streak} days[/]")

        # Show rank if available
        rank = self.result_data.get("rank", 0)
        if rank > 0 and won:
            lines.append(f"[#818384]Rank:[/] [bold #ffd700]#{rank}[/] [#818384]today[/]")
        lines.append("")

        # Guess history
        lines.append("[bold white]Your Guesses[/]")
        for i, guess in enumerate(guesses, 1):
            lines.append(f"[#818384]{i}.[/] [white]{guess}[/]")

        content.update(Text.from_markup("\n".join(lines)))

    def _render_stats(self) -> None:
        content = self.query_one("#stats-content", Static)
        personal = self.result_data.get("personal_stats", {})

        games = personal.get("total_games", 0)
        wins = personal.get("total_wins", 0)
        win_rate = personal.get("win_rate", 0)
        current = personal.get("current_streak", 0)
        longest = personal.get("longest_streak", 0)
        avg = personal.get("avg_attempts", 0)
        dist = personal.get("attempts_distribution", {})

        lines = [
            "[bold white]Your Statistics[/]",
            "",
            f"[#818384]Games[/]   [bold white]{games:>4}[/]     [#818384]Win Rate[/]  [bold white]{win_rate:>5.1f}%[/]",
            f"[#818384]Streak[/]  [bold #ff6b35]{current:>4}[/]     [#818384]Max[/]       [bold white]{longest:>5}[/]",
            f"[#818384]Avg[/]     [bold white]{avg:>4.1f}[/]",
            "",
            "[bold white]Guess Distribution[/]",
            "",
        ]

        max_count = max(dist.values()) if dist and max(dist.values()) > 0 else 1
        current_attempts = self.result_data.get("attempts", 0)
        won = self.result_data.get("won", False)

        for i in range(1, 7):
            count = dist.get(str(i), 0)
            bar_width = int((count / max_count) * 20) if max_count > 0 else 0
            if bar_width == 0 and count > 0:
                bar_width = 1
            bar = "█" * bar_width

            if won and i == current_attempts:
                lines.append(f"[#818384]{i}[/] [#6aaa64]{bar:<20}[/] [bold #6aaa64]{count}[/]")
            else:
                color = "#0e4429" if i > 4 else "#006d32" if i > 3 else "#26a641" if i > 2 else "#39d353"
                lines.append(f"[#818384]{i}[/] [{color}]{bar:<20}[/] [#818384]{count}[/]")

        content.update(Text.from_markup("\n".join(lines)))

    async def _fetch_leaderboard(self) -> None:
        """Fetch real leaderboard data from API."""
        if not self.api_url:
            return

        try:
            client = get_api_client(self.api_url)
            data = await client.get_leaderboard(limit=10)
            if data:
                self.leaderboard_entries = data
                self._render_leaderboard()
        except Exception:
            pass

    def _render_leaderboard(self) -> None:
        content = self.query_one("#leaderboard-content", Static)

        entries = self.leaderboard_entries

        lines = [
            "[bold white]Today's Leaderboard[/]",
            "",
        ]

        if not entries:
            lines.append("[#818384]No entries yet. Be the first![/]")
        else:
            lines.append("[#818384]Rank  Player          Tries  Time[/]")
            lines.append("[#3a3a3c]─────────────────────────────────[/]")

            for i, entry in enumerate(entries[:10], 1):
                rank = i
                if rank == 1:
                    rank_str = "[#ffd700]🥇 1[/]"
                elif rank == 2:
                    rank_str = "[#c0c0c0]🥈 2[/]"
                elif rank == 3:
                    rank_str = "[#cd7f32]🥉 3[/]"
                else:
                    rank_str = f"[#818384]   {rank}[/]"

                username = entry.get("username", "???")[:12]
                attempts = entry.get("attempts", 0)
                time_sec = entry.get("time_seconds")

                if time_sec:
                    mins = time_sec // 60
                    secs = time_sec % 60
                    time_str = f"{mins}:{secs:02d}"
                else:
                    time_str = "-:--"

                attempts_color = "#6aaa64" if attempts <= 3 else "#c9b458" if attempts <= 4 else "#787c7e"

                lines.append(
                    f"{rank_str}  [white]{username:<12}[/]  [{attempts_color}]{attempts}[/]     [#818384]{time_str}[/]"
                )

        content.update(Text.from_markup("\n".join(lines)))

    def _render_footer(self) -> None:
        footer = self.query_one("#footer-nav", Static)
        footer.update(Text.from_markup(
            "[#565758]← → or 1/2/3: Switch tabs  |  ENTER: Exit[/]"
        ))

    def action_close(self) -> None:
        self.app.exit()

    def action_tab_result(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab-result"

    def action_tab_stats(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab-stats"

    def action_tab_leaderboard(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab-leaderboard"

    def action_prev_tab(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tab_order = ["tab-result", "tab-stats", "tab-leaderboard"]
        current_idx = tab_order.index(tabs.active) if tabs.active in tab_order else 0
        new_idx = (current_idx - 1) % len(tab_order)
        tabs.active = tab_order[new_idx]

    def action_next_tab(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tab_order = ["tab-result", "tab-stats", "tab-leaderboard"]
        current_idx = tab_order.index(tabs.active) if tabs.active in tab_order else 0
        new_idx = (current_idx + 1) % len(tab_order)
        tabs.active = tab_order[new_idx]
