"""Shared configuration values for server/admin/client apps."""

from pathlib import Path

# Base URL for the FastAPI reminder server.
SERVER_BASE_URL = "http://127.0.0.1:8000"

# Polling interval for the client app (seconds).
POLL_INTERVAL_SECONDS = 5

# SQLite database file path used by the server.
DB_PATH = Path(__file__).resolve().parent.parent / "server" / "reminders.db"
