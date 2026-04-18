"""Repository layer for Chat and Message CRUD operations."""

import logging
from typing import Any

from winpyai.config import DEFAULT_MODEL
from winpyai.database.db import Database

logger = logging.getLogger(__name__)


class ChatRepository:
    """Repository for chat CRUD operations."""

    def __init__(self, db: Database) -> None:
        """Initialize with a Database instance.

        Args:
            db: The Database instance to use for connections.
        """
        self._db = db

    def create(self, title: str = "New Chat", model: str = DEFAULT_MODEL, system_prompt: str = "") -> int:
        """Create a new chat session.

        Args:
            title: Display title for the chat.
            model: Ollama model name to use.
            system_prompt: Optional system prompt for the chat.

        Returns:
            int: The ID of the newly created chat.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "INSERT INTO chats (title, model, system_prompt) VALUES (?, ?, ?)",
            (title, model, system_prompt),
        )
        conn.commit()
        chat_id = cursor.lastrowid
        logger.debug("Created chat id=%s title=%r", chat_id, title)
        return chat_id  # type: ignore[return-value]

    def get_by_id(self, chat_id: int) -> dict | None:
        """Get a single chat by its ID.

        Args:
            chat_id: The chat ID to look up.

        Returns:
            dict or None: Chat row as a dict, or None if not found.
        """
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT * FROM chats WHERE id = ?", (chat_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Get all chats ordered by most recently updated first.

        Args:
            limit: Maximum number of chats to return.
            offset: Number of chats to skip for pagination.

        Returns:
            list[dict]: List of chat dicts.
        """
        conn = self._db.get_connection()
        rows = conn.execute(
            "SELECT * FROM chats ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(row) for row in rows]

    def update_title(self, chat_id: int, title: str) -> bool:
        """Update a chat\'s title.

        Args:
            chat_id: The chat ID to update.
            title: The new title.

        Returns:
            bool: True if a row was updated, False otherwise.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "UPDATE chats SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, chat_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def update_model(self, chat_id: int, model: str) -> bool:
        """Update a chat\'s model.

        Args:
            chat_id: The chat ID to update.
            model: The new model name.

        Returns:
            bool: True if a row was updated, False otherwise.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "UPDATE chats SET model = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (model, chat_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def update_system_prompt(self, chat_id: int, system_prompt: str) -> bool:
        """Update a chat\'s system prompt.

        Args:
            chat_id: The chat ID to update.
            system_prompt: The new system prompt text.

        Returns:
            bool: True if a row was updated, False otherwise.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "UPDATE chats SET system_prompt = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (system_prompt, chat_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def update_timestamp(self, chat_id: int) -> bool:
        """Update a chat\'s updated_at timestamp to the current time.

        Args:
            chat_id: The chat ID to update.

        Returns:
            bool: True if a row was updated, False otherwise.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (chat_id,),
        )
        conn.commit()
        return cursor.rowcount > 0

    def delete(self, chat_id: int) -> bool:
        """Delete a chat and all its messages (cascading delete).

        Args:
            chat_id: The chat ID to delete.

        Returns:
            bool: True if a row was deleted, False otherwise.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "DELETE FROM chats WHERE id = ?", (chat_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_message_count(self, chat_id: int) -> int:
        """Count messages in a chat.

        Args:
            chat_id: The chat ID to count messages for.

        Returns:
            int: Number of messages in the chat.
        """
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return row[0] if row else 0


class MessageRepository:
    """Repository for message CRUD operations."""

    def __init__(self, db: Database) -> None:
        """Initialize with a Database instance.

        Args:
            db: The Database instance to use for connections.
        """
        self._db = db

    def create(self, chat_id: int, role: str, content: str, model: str | None = None) -> int:
        """Create a new message in a chat.

        Args:
            chat_id: The chat ID this message belongs to.
            role: One of 'user', 'assistant', or 'system'.
            content: The message text content.
            model: Optional model name that generated this message.

        Returns:
            int: The ID of the newly created message.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "INSERT INTO messages (chat_id, role, content, model) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, model),
        )
        conn.commit()
        message_id = cursor.lastrowid
        logger.debug("Created message id=%s chat_id=%s role=%s", message_id, chat_id, role)
        return message_id  # type: ignore[return-value]

    def get_by_chat(self, chat_id: int, limit: int = 1000, offset: int = 0) -> list[dict]:
        """Get all messages for a chat, oldest first.

        Args:
            chat_id: The chat ID to load messages for.
            limit: Maximum number of messages to return.
            offset: Number of messages to skip.

        Returns:
            list[dict]: List of message dicts ordered by created_at ascending.
        """
        conn = self._db.get_connection()
        rows = conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (chat_id, limit, offset),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_recent_context(self, chat_id: int, limit: int = 20) -> list[dict]:
        """Get the most recent messages for context building.

        Args:
            chat_id: The chat ID to load context for.
            limit: Maximum number of recent messages to return.

        Returns:
            list[dict]: List of message dicts ordered by created_at ascending,
                suitable for passing to the Ollama API.
        """
        conn = self._db.get_connection()
        rows = conn.execute(
            """
            SELECT * FROM messages
            WHERE chat_id = ? AND role IN ('user', 'assistant')
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (chat_id, limit),
        ).fetchall()
        # Reverse so oldest is first, matching API expectation
        messages = [dict(row) for row in reversed(rows)]
        return messages

    def delete_by_chat(self, chat_id: int) -> bool:
        """Delete all messages belonging to a chat.

        Args:
            chat_id: The chat ID whose messages should be deleted.

        Returns:
            bool: True if any rows were deleted, False otherwise.
        """
        conn = self._db.get_connection()
        cursor = conn.execute(
            "DELETE FROM messages WHERE chat_id = ?", (chat_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
