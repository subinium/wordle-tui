"""Help screen showing game rules."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.containers import Container
from textual.binding import Binding
from rich.text import Text


class HelpScreen(ModalScreen):
    """Modal screen for showing game rules."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("f3", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-container {
        width: 65;
        height: auto;
        background: #1a1a1b;
        border: solid #3a3a3c;
        padding: 1 2;
    }

    #help-title {
        width: 100%;
        height: 1;
        content-align: center middle;
        text-style: bold;
        color: #ffffff;
        padding-bottom: 1;
    }

    #help-content {
        width: 100%;
        height: auto;
        padding: 1 0;
    }

    #close-hint {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: #565758;
        padding-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            yield Static("[bold white]📖 How to Play[/]", id="help-title")
            yield Static(id="help-content")
            yield Static("[#565758]Press ESC or Q to close[/]", id="close-hint")

    def on_mount(self) -> None:
        self._render_help()

    def _render_help(self) -> None:
        content = self.query_one("#help-content", Static)

        help_text = """[bold white]🎯 Goal[/]
Guess the 5-letter word within 6 tries!

[bold white]🎮 How to Play[/]
• Type a 5-letter word and press Enter
• Tile colors will change after each guess

[bold #6aaa64]🟩 Green[/]  - Correct letter in the right spot
[bold #c9b458]🟨 Yellow[/] - Correct letter in the wrong spot
[#3a3a3c]⬛ Gray[/]   - Letter not in the word

[bold white]📌 Note[/]
• Each word has [bold]NO duplicate letters[/]
• All 5 letters are unique!

[bold white]⌨️ Shortcuts[/]
[#818384]ESC[/]     Quit game
[#818384]F1[/]      View my stats
[#818384]F2[/]      Leaderboard
[#818384]F3[/]      How to play

[bold white]🔥 Streak[/]
Play daily to build your streak!
Login to compete with players worldwide.

[bold white]⏰ New Word[/]
A new word is available every day at 9:00 AM (KST)."""

        content.update(Text.from_markup(help_text))

    def action_dismiss(self) -> None:
        self.app.pop_screen()
