import json
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".tui-wordle"
CONFIG_FILE = CONFIG_DIR / "config.json"


class ClientConfig:
    def __init__(self):
        CONFIG_DIR.mkdir(exist_ok=True)
        self._token: Optional[str] = None
        self._username: Optional[str] = None
        self._api_url: str = "http://localhost:8000"
        self._load()

    def _load(self) -> None:
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                self._token = data.get("token")
                self._username = data.get("username")
                self._api_url = data.get("api_url", self._api_url)
            except (json.JSONDecodeError, KeyError):
                pass

    def save(self, username: str, token: str) -> None:
        self._username = username
        self._token = token
        CONFIG_FILE.write_text(json.dumps({
            "username": username,
            "token": token,
            "api_url": self._api_url,
        }))

    def clear(self) -> None:
        self._token = None
        self._username = None
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    @property
    def token(self) -> Optional[str]:
        return self._token

    @property
    def username(self) -> Optional[str]:
        return self._username

    @property
    def api_url(self) -> str:
        return self._api_url
