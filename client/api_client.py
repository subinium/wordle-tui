"""API client for Wordle server."""

import httpx
from datetime import date
from typing import Optional
from dataclasses import dataclass


@dataclass
class UserSession:
    """User session data."""
    user_id: int
    username: str
    token: str


class WordleAPIClient:
    """Client for communicating with Wordle API server."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[UserSession] = None
        self._client = httpx.AsyncClient(timeout=30.0)

    @property
    def headers(self) -> dict:
        """Get headers with auth token if available."""
        headers = {"Content-Type": "application/json"}
        if self.session:
            headers["Authorization"] = f"Bearer {self.session.token}"
        return headers

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    # Auth endpoints
    async def login(self, username: str) -> Optional[UserSession]:
        """Login or create user and get session token."""
        try:
            response = await self._client.post(
                f"{self.base_url}/auth/login",
                json={"username": username},
            )
            if response.status_code == 200:
                data = response.json()
                self.session = UserSession(
                    user_id=data["user_id"],
                    username=data["username"],
                    token=data["token"],
                )
                return self.session
        except Exception:
            pass
        return None

    # Words endpoints
    async def get_today_word_hash(self) -> Optional[str]:
        """Get hash of today's word (for validation without revealing)."""
        try:
            response = await self._client.get(
                f"{self.base_url}/words/today",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json().get("hash")
        except Exception:
            pass
        return None

    async def validate_word(self, word: str) -> bool:
        """Check if a word is valid."""
        try:
            response = await self._client.post(
                f"{self.base_url}/words/validate",
                json={"word": word},
            )
            if response.status_code == 200:
                return response.json().get("valid", False)
        except Exception:
            pass
        return False

    # Games endpoints
    async def check_played_today(self) -> Optional[dict]:
        """Check if user has already played today."""
        try:
            response = await self._client.get(
                f"{self.base_url}/games/today",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    async def submit_game(
        self,
        word_id: int,
        attempts: int,
        solved: bool,
        time_seconds: int,
        guess_history: list[str],
    ) -> Optional[dict]:
        """Submit game result."""
        try:
            response = await self._client.post(
                f"{self.base_url}/games/submit",
                headers=self.headers,
                json={
                    "word_id": word_id,
                    "attempts": attempts,
                    "solved": solved,
                    "time_seconds": time_seconds,
                    "guess_history": guess_history,
                },
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    # Progress (auto-save) endpoints
    async def save_progress(
        self,
        word_id: int,
        guesses: list[str],
        elapsed_seconds: int,
    ) -> bool:
        """Save game progress (auto-save)."""
        try:
            response = await self._client.post(
                f"{self.base_url}/games/progress",
                headers=self.headers,
                json={
                    "word_id": word_id,
                    "guesses": guesses,
                    "elapsed_seconds": elapsed_seconds,
                },
            )
            if response.status_code == 200:
                return response.json().get("saved", False)
        except Exception:
            pass
        return False

    async def get_today_progress(self) -> Optional[dict]:
        """Get today's saved progress if exists."""
        try:
            response = await self._client.get(
                f"{self.base_url}/games/progress/today",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    # Leaderboard endpoints
    async def get_leaderboard(self, limit: int = 100) -> list[dict]:
        """Get today's leaderboard."""
        try:
            response = await self._client.get(
                f"{self.base_url}/leaderboard/today",
                params={"limit": limit},
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []

    # Stats endpoints
    async def get_today_stats(self) -> Optional[dict]:
        """Get today's global statistics."""
        try:
            response = await self._client.get(
                f"{self.base_url}/stats/today",
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    async def get_personal_stats(self) -> Optional[dict]:
        """Get personal statistics."""
        try:
            response = await self._client.get(
                f"{self.base_url}/stats/me",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    async def get_monthly_stats(self) -> list[dict]:
        """Get monthly completion stats."""
        try:
            response = await self._client.get(
                f"{self.base_url}/stats/me/monthly",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json().get("data", [])
        except Exception:
            pass
        return []

    # Streaks endpoints
    async def get_streak(self) -> Optional[dict]:
        """Get current streak information."""
        try:
            response = await self._client.get(
                f"{self.base_url}/streaks/me",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    async def get_contribution_data(self) -> list[dict]:
        """Get 52-week contribution graph data."""
        try:
            response = await self._client.get(
                f"{self.base_url}/streaks/contribution-data",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []

    # Health check
    async def health_check(self) -> bool:
        """Check if server is available."""
        try:
            response = await self._client.get(
                f"{self.base_url}/health",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False


# Global client instance
api_client: Optional[WordleAPIClient] = None


def get_api_client(base_url: str = "http://localhost:8000") -> WordleAPIClient:
    """Get or create API client instance."""
    global api_client
    if api_client is None:
        api_client = WordleAPIClient(base_url)
    return api_client
