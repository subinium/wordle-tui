"""Individual letter tile with smooth animations."""

from enum import Enum
from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style
from rich.console import RenderableType


class TileState(str, Enum):
    EMPTY = "empty"
    FILLED = "filled"
    CORRECT = "correct"
    PRESENT = "present"
    ABSENT = "absent"


TILE_COLORS = {
    TileState.EMPTY: {"bg": "#121213", "border": "#3a3a3c"},
    TileState.FILLED: {"bg": "#121213", "border": "#565758"},
    TileState.CORRECT: {"bg": "#6aaa64", "border": "#6aaa64"},
    TileState.PRESENT: {"bg": "#c9b458", "border": "#c9b458"},
    TileState.ABSENT: {"bg": "#3a3a3c", "border": "#3a3a3c"},
}


class Tile(Widget):
    """A single letter tile for the Wordle board."""

    DEFAULT_CSS = """
    Tile {
        width: 7;
        height: 3;
        content-align: center middle;
        text-style: bold;
        overflow: hidden;
    }

    Tile.shake-left {
        offset: -1 0;
    }

    Tile.shake-right {
        offset: 1 0;
    }

    Tile.error {
        border: solid #c9b458;
    }
    """

    letter = reactive("")
    state = reactive(TileState.EMPTY)
    _animating = reactive(False)
    _error = reactive(False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._reveal_pending = False

    def render(self) -> RenderableType:
        colors = TILE_COLORS[self.state]
        bg = colors["bg"]
        border = colors["border"]

        # Show yellow border on error
        if self._error:
            border = "#c9b458"

        top = f"[{border}]╭─────╮[/]"
        mid_content = self.letter.upper() if self.letter else " "
        mid = f"[{border}]│[/][bold white on {bg}]  {mid_content}  [/][{border}]│[/]"
        bot = f"[{border}]╰─────╯[/]"

        return Text.from_markup(f"{top}\n{mid}\n{bot}")

    def set_error(self, error: bool) -> None:
        """Set error state for shake feedback."""
        self._error = error
        self.refresh()

    def set_letter(self, letter: str) -> None:
        self.letter = letter
        if letter:
            self.state = TileState.FILLED
        else:
            self.state = TileState.EMPTY

    def clear(self) -> None:
        self.letter = ""
        self.state = TileState.EMPTY

    async def reveal(self, new_state: TileState, delay: float = 0.0) -> None:
        """Reveal the tile with the given state after a delay."""
        import asyncio
        if delay > 0:
            await asyncio.sleep(delay)

        self._animating = True
        self.state = new_state
        self._animating = False
        self.refresh()
