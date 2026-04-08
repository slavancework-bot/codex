"""Database helpers for the reminder server."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from shared.config import DB_PATH


def ensure_db_parent() -> None:
    """Ensure the database folder exists."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_conn() -> sqlite3.Connection:
    """Yield a SQLite connection with row access by column name."""
    ensure_db_parent()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create required tables and a few sample users."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                computer_name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                created_by TEXT NOT NULL,
                repeat_type TEXT NOT NULL CHECK (repeat_type IN ('one_time', 'weekly')),
                day_of_week INTEGER
            );

            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'snoozed', 'completed')),
                snooze_until TEXT,
                completed_time TEXT,
                FOREIGN KEY (reminder_id) REFERENCES reminders (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            """
        )

        # Seed users for local demo if empty.
        count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        if count == 0:
            conn.executemany(
                "INSERT INTO users(name, computer_name) VALUES(?, ?)",
                [
                    ("Alice", "ALICE-PC"),
                    ("Bob", "BOB-LAPTOP"),
                    ("Charlie", "CHARLIE-DESKTOP"),
                ],
            )
