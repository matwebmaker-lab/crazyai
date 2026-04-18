"""ChatService — Business logic orchestration layer for WinPyAI."""

import logging
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from winpyai.config import DEFAULT_MODEL
from winpyai.database.repository import ChatRepository, MessageRepository
from winpyai.services.ollama_service import (
    OllamaConnectionError,
    OllamaModelError,
    OllamaResponseError,
    OllamaService,
)
from winpyai.workers.stream_worker import StreamWorker

logger = logging.getLogger(__name__)


class ChatService(QObject):
    """Business logic service that orchestrates chat operations.

    Bridges the UI layer with the Ollama API and database repositories.
    All methods are designed to be called from the UI thread; long-running
    operations (streaming) are delegated to StreamWorker threads.

    Signals:
        response_chunk(str, int): Cumulative assistant text so far with message ID.
        response_complete(int): Streaming completed for a message.
        response_error(str): Error message if streaming failed.
        chat_created(int): New chat was created with the given ID.
        chat_updated(int): Chat metadata was updated.
        chat_deleted(int): Chat was deleted.
        messages_loaded(list): Messages loaded for a chat.
        models_loaded(list): Available Ollama model names.
        ollama_status(bool, str): Ollama connection status and message.
    """

    response_chunk = pyqtSignal(str, int)       # (chunk_text, message_id)
    response_complete = pyqtSignal(int)          # (message_id)
    response_error = pyqtSignal(str)             # (error_message)
    chat_created = pyqtSignal(int)               # (chat_id)
    chat_updated = pyqtSignal(int)               # (chat_id)
    chat_deleted = pyqtSignal(int)               # (chat_id)
    messages_loaded = pyqtSignal(list)           # (list of message dicts)
    models_loaded = pyqtSignal(list)             # (list of model name strings)
    ollama_status = pyqtSignal(bool, str)        # (is_running, status_message)

    def __init__(self, db, ollama_service: OllamaService) -> None:
        """Initialize the ChatService.

        Args:
            db: The Database instance for persistence.
            ollama_service: The OllamaService instance for API calls.
        """
        super().__init__()
        self._db = db
        self.ollama = ollama_service
        self._chat_repo = ChatRepository(db)
        self._message_repo = MessageRepository(db)
        self._current_worker: StreamWorker | None = None
        self._current_assistant_message_id: int = 0
        self._current_chat_id: int = 0
        logger.debug("ChatService initialized")

    def check_ollama(self) -> None:
        """Check if Ollama is running and emit status signal.

        Calls ollama.is_running() and emits the ollama_status signal
        with the result and a human-readable message.
        """
        try:
            is_running = self.ollama.is_running()
            if is_running:
                self.ollama_status.emit(True, "Ollama is running")
                logger.debug("Ollama health check: running")
            else:
                self.ollama_status.emit(False, "Ollama is not running")
                logger.debug("Ollama health check: not running")
        except Exception as exc:
            logger.error("Ollama health check failed: %s", exc)
            self.ollama_status.emit(False, f"Ollama check failed: {exc}")

    def refresh_models(self) -> None:
        """Fetch and emit the list of available Ollama models.

        Calls ollama.list_models() and emits the models_loaded signal
        with the result. If Ollama is not running, emits an empty list.
        """
        try:
            models = self.ollama.list_models()
            self.models_loaded.emit(models)
            logger.debug("Refreshed models: %d found", len(models))
        except Exception as exc:
            logger.error("Failed to refresh models: %s", exc)
            self.models_loaded.emit([])

    def create_chat(self, title: str = "New Chat", model: str = DEFAULT_MODEL) -> int:
        """Create a new chat session.

        Args:
            title: Display title for the new chat.
            model: Ollama model to use for the chat.

        Returns:
            int: The ID of the newly created chat.
        """
        chat_id = self._chat_repo.create(title=title, model=model)
        self.chat_created.emit(chat_id)
        logger.info("Created chat id=%d title=%r model=%s", chat_id, title, model)
        return chat_id

    def load_chat(self, chat_id: int) -> None:
        """Load all messages for a chat and emit them.

        Args:
            chat_id: The chat ID to load messages for.
        """
        try:
            messages = self._message_repo.get_by_chat(chat_id)
            self.messages_loaded.emit(messages)
            logger.debug("Loaded %d messages for chat %d", len(messages), chat_id)
        except Exception as exc:
            logger.error("Failed to load chat %d: %s", chat_id, exc)
            self.messages_loaded.emit([])

    def delete_chat(self, chat_id: int) -> None:
        """Delete a chat and all its messages.

        Args:
            chat_id: The chat ID to delete.
        """
        try:
            self._chat_repo.delete(chat_id)
            self.chat_deleted.emit(chat_id)
            logger.info("Deleted chat %d", chat_id)
        except Exception as exc:
            logger.error("Failed to delete chat %d: %s", chat_id, exc)

    def rename_chat(self, chat_id: int, title: str) -> None:
        """Rename a chat.

        Args:
            chat_id: The chat ID to rename.
            title: The new title for the chat.
        """
        try:
            self._chat_repo.update_title(chat_id, title)
            self.chat_updated.emit(chat_id)
            logger.info("Renamed chat %d to %r", chat_id, title)
        except Exception as exc:
            logger.error("Failed to rename chat %d: %s", chat_id, exc)

    def set_chat_model(self, chat_id: int, model: str) -> None:
        """Change the model for a chat.

        Args:
            chat_id: The chat ID to update.
            model: The new model name.
        """
        try:
            self._chat_repo.update_model(chat_id, model)
            self.chat_updated.emit(chat_id)
            logger.info("Set chat %d model to %s", chat_id, model)
        except Exception as exc:
            logger.error("Failed to set model for chat %d: %s", chat_id, exc)

    def set_system_prompt(self, chat_id: int, prompt: str) -> None:
        """Set the system prompt for a chat.

        Args:
            chat_id: The chat ID to update.
            prompt: The system prompt text.
        """
        try:
            self._chat_repo.update_system_prompt(chat_id, prompt)
            self.chat_updated.emit(chat_id)
            logger.info("Set system prompt for chat %d", chat_id)
        except Exception as exc:
            logger.error("Failed to set system prompt for chat %d: %s", chat_id, exc)

    def get_all_chats(self) -> list[dict]:
        """Get all chats ordered by most recently updated.

        Returns:
            list[dict]: List of chat dicts with keys matching the chats table.
        """
        try:
            return self._chat_repo.get_all()
        except Exception as exc:
            logger.error("Failed to get all chats: %s", exc)
            return []

    def send_message(self, chat_id: int, content: str) -> None:
        """Send a user message and stream the assistant response.

        This method:
        1. Saves the user message to the database.
        2. Fetches the chat configuration (model, system_prompt).
        3. Gets recent context messages for the conversation.
        4. Creates and configures a StreamWorker.
        5. Starts the worker thread to stream the response.
        6. Updates the chat timestamp.

        Args:
            chat_id: The chat ID to send the message in.
            content: The user message text.
        """
        logger.info("Sending message to chat %d", chat_id)

        # Step 1: Save user message
        try:
            user_message_id = self._message_repo.create(
                chat_id=chat_id,
                role="user",
                content=content,
            )
            logger.debug("Saved user message id=%d", user_message_id)
        except Exception as exc:
            logger.error("Failed to save user message: %s", exc)
            self.response_error.emit(f"Failed to save message: {exc}")
            return

        # Step 2: Get chat config
        chat = self._chat_repo.get_by_id(chat_id)
        if chat is None:
            logger.error("Chat %d not found", chat_id)
            self.response_error.emit(f"Chat {chat_id} not found")
            return

        model = chat.get("model", DEFAULT_MODEL)
        system_prompt = chat.get("system_prompt", "") or ""

        # Step 3: Get recent context messages
        try:
            context_messages = self._message_repo.get_recent_context(chat_id, limit=20)
        except Exception as exc:
            logger.error("Failed to get context: %s", exc)
            self.response_error.emit(f"Failed to load context: {exc}")
            return

        # Build messages for the API: convert context to Ollama format
        api_messages: list[dict[str, str]] = []
        for msg in context_messages:
            api_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        # If the user message is not the last one in context, add it
        if not context_messages or context_messages[-1].get("role") != "user":
            api_messages.append({"role": "user", "content": content})

        logger.debug(
            "Streaming with model=%s context=%d messages",
            model,
            len(api_messages),
        )

        # Step 4: Create StreamWorker
        self._current_chat_id = chat_id
        worker = StreamWorker(
            ollama_service=self.ollama,
            model=model,
            messages=api_messages,
            system=system_prompt,
            parent=self,
        )

        # Pre-create the assistant message in DB (content will be updated later)
        try:
            self._current_assistant_message_id = self._message_repo.create(
                chat_id=chat_id,
                role="assistant",
                content="",
                model=model,
            )
            logger.debug(
                "Pre-created assistant message id=%d",
                self._current_assistant_message_id,
            )
        except Exception as exc:
            logger.error("Failed to create assistant message: %s", exc)
            self.response_error.emit(f"Failed to create assistant message: {exc}")
            return

        # Step 5: Connect worker signals
        # Ollama yields incremental token strings; UI expects full text so far.
        assistant_stream_text = ""

        def _on_chunk(delta: str) -> None:
            """Accumulate streaming deltas and emit cumulative text for the UI."""
            nonlocal assistant_stream_text
            assistant_stream_text += delta
            self.response_chunk.emit(
                assistant_stream_text,
                self._current_assistant_message_id,
            )

        def _on_finished(full_text: str) -> None:
            """Save full response and emit completion signal."""
            try:
                # Update the assistant message with the full response
                conn = self._db.get_connection()
                conn.execute(
                    "UPDATE messages SET content = ? WHERE id = ?",
                    (full_text, self._current_assistant_message_id),
                )
                conn.commit()
                logger.debug(
                    "Saved assistant response id=%d length=%d",
                    self._current_assistant_message_id,
                    len(full_text),
                )
            except Exception as exc:
                logger.error("Failed to save assistant response: %s", exc)

            # Update chat timestamp
            try:
                self._chat_repo.update_timestamp(chat_id)
            except Exception as exc:
                logger.warning("Failed to update chat timestamp: %s", exc)

            self.response_complete.emit(self._current_assistant_message_id)
            self._current_worker = None
            logger.info("Stream complete for chat %d", chat_id)

        def _on_error(error_msg: str) -> None:
            """Relay error from worker to UI."""
            self.response_error.emit(error_msg)
            self._current_worker = None
            logger.error("Stream error for chat %d: %s", chat_id, error_msg)

        worker.chunk_received.connect(_on_chunk)
        worker.finished_signal.connect(_on_finished)
        worker.error_occurred.connect(_on_error)

        self._current_worker = worker
        worker.start()
        logger.debug("StreamWorker started for chat %d", chat_id)

    def stop_generation(self) -> None:
        """Stop the current streaming generation.

        If a StreamWorker is currently running, sets its stop flag and
        waits for it to finish. Cleans up the worker reference.
        """
        if self._current_worker is not None:
            logger.debug("Stopping generation")
            self._current_worker.stop()
            # Wait up to 2 seconds for the thread to finish
            if not self._current_worker.wait(2000):
                logger.warning("StreamWorker did not finish in time, terminating")
                self._current_worker.terminate()
                self._current_worker.wait()
            self._current_worker = None
        else:
            logger.debug("No active generation to stop")
