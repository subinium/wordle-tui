"""Settings screen for profile management."""

import asyncio
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Input, Button
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from rich.text import Text

from client.config import ClientConfig


class SettingsScreen(ModalScreen):
    """Settings modal for profile and logout."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    CSS = """
    SettingsScreen {
        align: center middle;
    }

    #settings-container {
        width: 50;
        height: auto;
        background: #1a1a1b;
        border: solid #3a3a3c;
        padding: 1 2;
    }

    #settings-title {
        width: 100%;
        height: 2;
        content-align: center middle;
        text-style: bold;
        color: #6aaa64;
    }

    #settings-email {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: #818384;
        margin-bottom: 1;
    }

    .form-label {
        width: 100%;
        height: 1;
        color: #818384;
        margin-top: 1;
    }

    #username-input {
        width: 100%;
        margin-bottom: 1;
    }

    #status-message {
        width: 100%;
        height: 1;
        content-align: center middle;
        margin: 1 0;
    }

    #button-row {
        width: 100%;
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }

    #save-btn {
        background: #6aaa64;
    }

    #logout-btn {
        background: #787c7e;
    }

    #cancel-btn {
        background: #3a3a3c;
    }
    """

    def __init__(
        self,
        username: str = "",
        email: str = "",
        token: str = "",
        api_url: str = "",
    ) -> None:
        super().__init__()
        self.current_username = username
        self.email = email
        self.token = token
        self.api_url = api_url
        self._config = ClientConfig()

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-container"):
            yield Static("Settings", id="settings-title")
            yield Static(self.email or "Not logged in", id="settings-email")
            yield Static("Username", classes="form-label")
            yield Input(value=self.current_username, placeholder="Enter username", id="username-input")
            yield Static("", id="status-message")
            with Horizontal(id="button-row"):
                yield Button("Save", id="save-btn", variant="primary")
                yield Button("Logout", id="logout-btn", variant="warning")
                yield Button("Cancel", id="cancel-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            asyncio.create_task(self._save_username())
        elif event.button.id == "logout-btn":
            self._logout()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    async def _save_username(self) -> None:
        """Save username to server."""
        input_widget = self.query_one("#username-input", Input)
        new_username = input_widget.value.strip()

        if not new_username:
            self._show_status("Username cannot be empty", error=True)
            return

        if new_username == self.current_username:
            self._show_status("No changes to save", error=False)
            return

        # Validate locally first
        if len(new_username) < 2:
            self._show_status("Username must be at least 2 characters", error=True)
            return
        if len(new_username) > 30:
            self._show_status("Username must be 30 characters or less", error=True)
            return
        if not all(c.isalnum() or c == "_" for c in new_username):
            self._show_status("Letters, numbers, underscores only", error=True)
            return

        # Save to server
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_url}/auth/me",
                    json={"username": new_username},
                    headers={"Authorization": f"Bearer {self.token}"},
                )

                if response.status_code == 200:
                    # Update local config
                    self._config.save(new_username, self.token)
                    self._show_status("Username updated!", error=False)
                    # Return new username
                    await asyncio.sleep(0.5)
                    self.dismiss({"action": "updated", "username": new_username})
                else:
                    error = response.json().get("detail", "Failed to update")
                    self._show_status(error, error=True)
        except Exception as e:
            self._show_status(f"Error: {str(e)[:30]}", error=True)

    def _logout(self) -> None:
        """Clear credentials and logout."""
        self._config.clear()
        self.dismiss({"action": "logout"})

    def _show_status(self, message: str, error: bool = False) -> None:
        status = self.query_one("#status-message", Static)
        color = "#da3633" if error else "#6aaa64"
        status.update(Text.from_markup(f"[{color}]{message}[/]"))

    def action_close(self) -> None:
        self.dismiss(None)
