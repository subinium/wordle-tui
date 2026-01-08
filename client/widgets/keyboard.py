"""Virtual keyboard widget showing letter states."""

from textual.widget import Widget
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from rich.text import Text
from rich.console import RenderableType
from client.widgets.tile import TileState


KEYBOARD_LAYOUT = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
    ["ENTER", "Z", "X", "C", "V", "B", "N", "M", "DEL"],
]

KEY_COLORS = {
    "unused": {"bg": "#818384", "fg": "#ffffff"},
    "correct": {"bg": "#6aaa64", "fg": "#ffffff"},
    "present": {"bg": "#c9b458", "fg": "#ffffff"},
    "absent": {"bg": "#3a3a3c", "fg": "#ffffff"},
}


class Keyboard(Widget):
    """Virtual keyboard showing letter states."""

    DEFAULT_CSS = """
    Keyboard {
        width: 100%;
        height: 7;
        min-height: 7;
        align: center middle;
        content-align: center middle;
        overflow: hidden;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.key_states: dict[str, str] = {}

    def render(self) -> RenderableType:
        lines = []

        for i, row in enumerate(KEYBOARD_LAYOUT):
            row_parts = []
            for key in row:
                state = self.key_states.get(key, "unused")
                colors = KEY_COLORS[state]
                bg = colors["bg"]
                fg = colors["fg"]

                if key == "ENTER":
                    display = " ENTER "
                elif key == "DEL":
                    display = "  DEL  "
                else:
                    display = f"  {key}  "

                row_parts.append(f"[{fg} on {bg}]{display}[/]")

            lines.append(" ".join(row_parts))
            # Add spacing between rows (except after last row)
            if i < len(KEYBOARD_LAYOUT) - 1:
                lines.append("")

        return Text.from_markup("\n".join(lines))

    def update_key(self, letter: str, state: TileState) -> None:
        """Update a key's state (only upgrade, never downgrade)."""
        letter = letter.upper()
        if letter not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            return

        state_str = state.value if state != TileState.FILLED else "unused"
        priority = {"unused": 0, "absent": 1, "present": 2, "correct": 3}

        current = self.key_states.get(letter, "unused")
        if priority.get(state_str, 0) > priority.get(current, 0):
            self.key_states[letter] = state_str
            self.refresh()

    def update_from_guess(self, guess: str, feedback: list[TileState]) -> None:
        """Update keyboard based on guess feedback."""
        for letter, state in zip(guess.upper(), feedback):
            self.update_key(letter, state)

    def reset(self) -> None:
        self.key_states = {}
        self.refresh()
