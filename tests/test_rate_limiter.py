import datetime as dt
import sqlite3
from datetime import timedelta

from persian_translator_bot.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_allows_first_request(self, db_conn: sqlite3.Connection) -> None:
        limiter = RateLimiter(db_conn, max_per_minute=10)
        assert limiter.is_allowed(user_id=123) is True

    def test_records_usage(self, db_conn: sqlite3.Connection) -> None:
        limiter = RateLimiter(db_conn, max_per_minute=10)
        limiter.record(user_id=123, username="alice")

        cursor = db_conn.execute("SELECT COUNT(*) FROM usage WHERE user_id = 123")
        assert cursor.fetchone()[0] == 1

    def test_blocks_after_limit(self, db_conn: sqlite3.Connection) -> None:
        limiter = RateLimiter(db_conn, max_per_minute=3)

        for _ in range(3):
            limiter.record(user_id=123, username="alice")

        assert limiter.is_allowed(user_id=123) is False

    def test_allows_after_window_expires(self, db_conn: sqlite3.Connection) -> None:
        limiter = RateLimiter(db_conn, max_per_minute=1)

        # Insert a record 2 minutes ago (outside the window)
        two_min_ago = dt.datetime.now(dt.UTC) - timedelta(minutes=2)
        db_conn.execute(
            "INSERT INTO usage (user_id, username, translated_at) VALUES (?, ?, ?)",
            (123, "alice", two_min_ago.strftime("%Y-%m-%d %H:%M:%S")),
        )
        db_conn.commit()

        assert limiter.is_allowed(user_id=123) is True

    def test_independent_per_user(self, db_conn: sqlite3.Connection) -> None:
        limiter = RateLimiter(db_conn, max_per_minute=1)
        limiter.record(user_id=111, username="alice")

        # User 111 is at the limit, but user 222 should still be allowed
        assert limiter.is_allowed(user_id=111) is False
        assert limiter.is_allowed(user_id=222) is True

    def test_records_username(self, db_conn: sqlite3.Connection) -> None:
        limiter = RateLimiter(db_conn, max_per_minute=10)
        limiter.record(user_id=123, username="bob")

        cursor = db_conn.execute("SELECT username FROM usage WHERE user_id = 123")
        assert cursor.fetchone()[0] == "bob"

    def test_records_none_username(self, db_conn: sqlite3.Connection) -> None:
        limiter = RateLimiter(db_conn, max_per_minute=10)
        limiter.record(user_id=123, username=None)

        cursor = db_conn.execute("SELECT username FROM usage WHERE user_id = 123")
        assert cursor.fetchone()[0] is None
