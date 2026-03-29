from persian_translator_bot.database import get_connection, init_db


class TestDatabase:
    def test_init_creates_usage_table(self) -> None:
        conn = get_connection(":memory:")
        init_db(conn)

        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage'")
        assert cursor.fetchone() is not None

    def test_init_creates_index(self) -> None:
        conn = get_connection(":memory:")
        init_db(conn)

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_usage_user_time'"
        )
        assert cursor.fetchone() is not None

    def test_init_is_idempotent(self) -> None:
        conn = get_connection(":memory:")
        init_db(conn)
        init_db(conn)  # Should not raise

        cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='usage'")
        assert cursor.fetchone()[0] == 1

    def test_usage_table_schema(self) -> None:
        conn = get_connection(":memory:")
        init_db(conn)

        conn.execute(
            "INSERT INTO usage (user_id, username) VALUES (?, ?)",
            (12345, "testuser"),
        )
        cursor = conn.execute("SELECT id, user_id, username, translated_at FROM usage")
        row = cursor.fetchone()

        assert row[0] == 1  # autoincrement id
        assert row[1] == 12345
        assert row[2] == "testuser"
        assert row[3] is not None  # default timestamp
