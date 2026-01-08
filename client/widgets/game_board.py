"""6x5 Wordle game board widget."""

import asyncio
from textual.widget import Widget
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from client.widgets.tile import Tile, TileState


class GameBoard(Widget):
    """The main 6x5 Wordle game board."""

    DEFAULT_CSS = """
    GameBoard {
        width: 100%;
        height: auto;
        align: center middle;
        overflow: hidden;
    }

    .tile-row {
        width: auto;
        height: auto;
        align: center middle;
        overflow: hidden;
    }
    """

    current_row = reactive(0)
    current_col = reactive(0)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.tiles: list[list[Tile]] = []
        self.guesses: list[str] = []
        self._target_word: str = ""

    def compose(self):
        with Vertical(id="board"):
            for row in range(6):
                row_tiles = []
                with Horizontal(classes="tile-row"):
                    for col in range(5):
                        tile = Tile(id=f"tile-{row}-{col}")
                        row_tiles.append(tile)
                        yield tile
                self.tiles.append(row_tiles)

    def set_target(self, word: str) -> None:
        self._target_word = word.upper()

    def add_letter(self, letter: str) -> bool:
        if self.current_row >= 6 or self.current_col >= 5:
            return False

        tile = self.tiles[self.current_row][self.current_col]
        tile.set_letter(letter.upper())
        self.current_col += 1
        return True

    def remove_letter(self) -> bool:
        if self.current_col <= 0:
            return False

        self.current_col -= 1
        tile = self.tiles[self.current_row][self.current_col]
        tile.clear()
        return True

    def get_current_guess(self) -> str:
        return "".join(
            self.tiles[self.current_row][col].letter
            for col in range(5)
        ).upper()

    def is_row_complete(self) -> bool:
        return self.current_col == 5

    def evaluate_guess(self, guess: str, target: str) -> list[TileState]:
        """Evaluate a guess against the target word."""
        guess = guess.upper()
        target = target.upper()

        result = [TileState.ABSENT] * 5
        target_chars = list(target)
        used = [False] * 5

        for i in range(5):
            if guess[i] == target[i]:
                result[i] = TileState.CORRECT
                used[i] = True

        for i in range(5):
            if result[i] == TileState.CORRECT:
                continue
            for j in range(5):
                if not used[j] and guess[i] == target_chars[j]:
                    result[i] = TileState.PRESENT
                    used[j] = True
                    break

        return result

    async def submit_guess(self) -> tuple[bool, list[TileState]]:
        """Submit the current guess and animate the reveal."""
        if not self.is_row_complete() or not self._target_word:
            return False, []

        guess = self.get_current_guess()
        feedback = self.evaluate_guess(guess, self._target_word)

        tasks = []
        for col, state in enumerate(feedback):
            tile = self.tiles[self.current_row][col]
            delay = col * 0.2
            tasks.append(tile.reveal(state, delay))

        await asyncio.gather(*tasks)

        self.guesses.append(guess)
        won = guess == self._target_word
        self.current_row += 1
        self.current_col = 0

        return won, feedback

    def reset(self) -> None:
        for row in self.tiles:
            for tile in row:
                tile.clear()
        self.current_row = 0
        self.current_col = 0
        self.guesses = []
        self._target_word = ""

    async def shake_row(self) -> None:
        """Shake animation for invalid word."""
        if self.current_row >= 6:
            return

        row_tiles = self.tiles[self.current_row]

        # Shake animation with offset classes and error border
        for tile in row_tiles:
            tile.set_error(True)

        for _ in range(3):
            for tile in row_tiles:
                tile.add_class("shake-left")
            await asyncio.sleep(0.04)
            for tile in row_tiles:
                tile.remove_class("shake-left")
                tile.add_class("shake-right")
            await asyncio.sleep(0.04)
            for tile in row_tiles:
                tile.remove_class("shake-right")

        # Reset error state after shake
        await asyncio.sleep(0.1)
        for tile in row_tiles:
            tile.set_error(False)

    async def bounce_row(self, row_idx: int) -> None:
        """Vibration animation for winning row."""
        if row_idx < 0 or row_idx >= 6:
            return

        row_tiles = self.tiles[row_idx]

        # Sequential vibration for each tile
        for i, tile in enumerate(row_tiles):
            await asyncio.sleep(0.05)
            # Quick left-right shake
            for _ in range(2):
                tile.add_class("shake-left")
                await asyncio.sleep(0.03)
                tile.remove_class("shake-left")
                tile.add_class("shake-right")
                await asyncio.sleep(0.03)
                tile.remove_class("shake-right")
