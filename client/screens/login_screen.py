"""Login screen with GitHub OAuth support."""

import asyncio
import webbrowser
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, Button
from textual.containers import Vertical, Container, Horizontal
from textual.binding import Binding
from rich.text import Text

from client.api_client import get_api_client


class LoginScreen(Screen):
    """Login screen with GitHub OAuth and offline mode."""

    BINDINGS = [
        Binding("escape", "quit", "Quit"),
        Binding("enter", "submit", "Login", show=False),
    ]

    CSS = """
    LoginScreen {
        background: #121213;
        align: center middle;
        overflow: hidden;
    }

    #login-container {
        width: 50;
        height: auto;
        background: #1a1a1b;
        border: solid #3a3a3c;
        padding: 2;
        overflow: hidden;
    }

    #login-title {
        width: 100%;
        height: 5;
        content-align: center middle;
        overflow: hidden;
    }

    #login-subtitle {
        width: 100%;
        height: 2;
        content-align: center middle;
        color: #818384;
        overflow: hidden;
    }

    #github-section {
        width: 100%;
        height: auto;
        padding: 1 0;
        overflow: hidden;
    }

    #github-button {
        width: 100%;
        margin-top: 1;
    }

    #github-status {
        width: 100%;
        height: auto;
        content-align: center middle;
        padding: 1 0;
        overflow: hidden;
    }

    #divider {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: #3a3a3c;
        margin: 1 0;
        overflow: hidden;
    }

    #offline-section {
        width: 100%;
        height: auto;
        overflow: hidden;
    }

    #offline-hint {
        width: 100%;
        height: 1;
        color: #565758;
        overflow: hidden;
    }

    #offline-button {
        width: 100%;
        margin-top: 1;
    }

    #server-status {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: #565758;
        margin-top: 2;
        overflow: hidden;
    }
    """

    def __init__(self, api_url: str = "http://localhost:8000", **kwargs) -> None:
        super().__init__(**kwargs)
        self.api_url = api_url
        self.server_online = False
        self.github_available = False
        self._polling = False
        self._device_code = None

    def compose(self) -> ComposeResult:
        with Container(id="login-container"):
            yield Static(id="login-title")
            yield Static("[#818384]Play Wordle every day![/]", id="login-subtitle")

            with Container(id="github-section"):
                yield Button("🔗 Login with GitHub", id="github-button", variant="primary")
                yield Static(id="github-status")

            yield Static("[#3a3a3c]─────────── or ───────────[/]", id="divider")

            with Container(id="offline-section"):
                yield Static("[#565758]Play without an account[/]", id="offline-hint")
                yield Button("Play Offline", id="offline-button", variant="default")

            yield Static(id="server-status")

    def on_mount(self) -> None:
        self._render_title()
        asyncio.create_task(self._check_server())

    def _render_title(self) -> None:
        title = self.query_one("#login-title", Static)
        logo = """[bold white]╦ ╦╔═╗╦═╗╔╦╗╦  ╔═╗
║║║║ ║╠╦╝ ║║║  ║╣
╚╩╝╚═╝╩╚══╩╝╩═╝╚═╝[/]"""
        title.update(Text.from_markup(logo))

    async def _check_server(self) -> None:
        """Check if server is available and GitHub OAuth is configured."""
        status = self.query_one("#server-status", Static)
        status.update(Text.from_markup("[#c9b458]Checking server...[/]"))

        client = get_api_client(self.api_url)
        self.server_online = await client.health_check()

        if self.server_online:
            status.update(Text.from_markup("[#6aaa64]● Server online[/]"))
            # Check if GitHub OAuth is available by trying to get device code
            try:
                response = await client._client.post(
                    f"{self.api_url}/auth/github/device-code",
                    timeout=5.0,
                )
                self.github_available = response.status_code == 200
            except Exception:
                self.github_available = False

            if not self.github_available:
                github_btn = self.query_one("#github-button", Button)
                github_btn.disabled = True
                github_btn.label = "GitHub Login (Not configured)"
        else:
            status.update(Text.from_markup("[#787c7e]○ Server offline[/]"))
            github_btn = self.query_one("#github-button", Button)
            github_btn.disabled = True
            github_btn.label = "GitHub Login (Server offline)"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "github-button":
            await self._start_github_login()
        elif event.button.id == "offline-button":
            self._play_offline()

    async def _start_github_login(self) -> None:
        """Start GitHub device flow."""
        if not self.server_online:
            return

        github_status = self.query_one("#github-status", Static)
        github_status.update(Text.from_markup("[#c9b458]Getting code...[/]"))

        client = get_api_client(self.api_url)

        try:
            response = await client._client.post(
                f"{self.api_url}/auth/github/device-code",
            )

            if response.status_code != 200:
                github_status.update(Text.from_markup("[#787c7e]Failed to start GitHub login[/]"))
                return

            data = response.json()
            self._device_code = data["device_code"]
            user_code = data["user_code"]
            verification_uri = data["verification_uri"]
            interval = data.get("interval", 5)

            # Show code to user
            github_status.update(Text.from_markup(
                f"[bold white]Code: {user_code}[/]\n"
                f"[#818384]Go to: [link={verification_uri}]{verification_uri}[/link][/]\n"
                f"[#565758]Waiting for authorization...[/]"
            ))

            # Open browser
            webbrowser.open(verification_uri)

            # Start polling
            self._polling = True
            await self._poll_for_token(interval)

        except Exception as e:
            github_status.update(Text.from_markup(f"[#787c7e]Error: {str(e)}[/]"))

    async def _poll_for_token(self, interval: int) -> None:
        """Poll for GitHub token."""
        github_status = self.query_one("#github-status", Static)
        client = get_api_client(self.api_url)

        for _ in range(60):  # Max 5 minutes
            if not self._polling:
                return

            await asyncio.sleep(interval)

            try:
                response = await client._client.post(
                    f"{self.api_url}/auth/github/poll-token",
                    json={"device_code": self._device_code},
                )

                if response.status_code != 200:
                    continue

                data = response.json()
                status = data.get("status")

                if status == "authorized":
                    github_status.update(Text.from_markup(
                        f"[bold #6aaa64]✓ Welcome, {data['username']}![/]"
                    ))
                    await asyncio.sleep(1)
                    self.dismiss({
                        "username": data["username"],
                        "token": data["token"],
                        "streak": 0,  # Will be fetched after
                    })
                    return
                elif status == "expired":
                    github_status.update(Text.from_markup("[#787c7e]Code expired. Try again.[/]"))
                    return
                elif status == "error":
                    github_status.update(Text.from_markup(f"[#787c7e]{data.get('error', 'Error')}[/]"))
                    return
                # status == "pending" - continue polling

            except Exception:
                pass

        github_status.update(Text.from_markup("[#787c7e]Timeout. Try again.[/]"))

    def _play_offline(self) -> None:
        """Start offline game."""
        self.dismiss({"username": "Player", "token": None, "streak": 0})

    def action_submit(self) -> None:
        # Default to offline if enter is pressed
        self._play_offline()

    def action_quit(self) -> None:
        self.app.exit()
