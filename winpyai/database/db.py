"""SQLite database connection and schema management."""

import sqlite3
import threading
from pathlib import Path

from winpyai.config import DB_PATH


SCHEMA_SQL = """
-- chats table
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL DEFAULT 'New Chat',
    model TEXT NOT NULL DEFAULT 'llama3.2:latest',
    system_prompt TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- messages table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL DEFAULT '',
    model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);

-- Index for fast message loading
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_chats_updated ON chats(updated_at DESC);
"""


class Database:
    """Thread-safe SQLite database manager with WAL mode."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        """Initialize database connection and schema.

        Args:
            db_path: Path to the SQLite database file.
        """
        self._db_path = db_path
        self._local = threading.local()
        self._init_schema()

    def _init_schema(self) -> None:
        """Create database tables and indexes if they do not exist."""
        conn = self.get_connection()
        conn.executescript(SCHEMA_SQL)
        conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Get a thread-local SQLite connection.

        Returns:
            sqlite3.Connection: A connection with Row factory and WAL mode enabled.
        """
        if not hasattr(self._local, "connection") or self._local.connection is None:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.connection = conn
        return self._local.connection

    def close(self) -> None:
        """Close the thread-local database connection if open."""
        if hasattr(self._local, "connection") and self._local.connection is not None:
            self._local.connection.close()
            self._local.connection = None

    def __enter__(self) -> "Database":
        """Enter context manager.

        Returns:
            Database: Self for use in 'with' statements.
        """
        return self

    def __exit__(self, *args) -> None:
        """Exit context manager, closing the connection."""
        self.close()
