import sqlite3

import pytest

from persian_translator_bot.database import get_connection, init_db


@pytest.fixture
def db_conn() -> sqlite3.Connection:
    conn = get_connection(":memory:")
    init_db(conn)
    return conn
