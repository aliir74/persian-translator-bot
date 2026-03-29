from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

_WINDOW_QUERY = (
    "SELECT COUNT(*) FROM usage"
    " WHERE user_id = ? AND translated_at > datetime('now', '-60 seconds')"
)


class RateLimiter:
    def __init__(self, conn: sqlite3.Connection, max_per_minute: int) -> None:
        self._conn = conn
        self._max_per_minute = max_per_minute

    def is_allowed(self, user_id: int) -> bool:
        cursor = self._conn.execute(_WINDOW_QUERY, (user_id,))
        count = cursor.fetchone()[0]
        return count < self._max_per_minute

    def record(self, user_id: int, username: str | None) -> None:
        self._conn.execute(
            "INSERT INTO usage (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        self._conn.commit()
