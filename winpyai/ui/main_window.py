"""Main window for WinPyAI.

Provides the primary application window containing the sidebar, chat area,
and input bar. Connects all UI signals to the ChatService backend.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QStatusBar,
    QLabel,
    QMessageBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer

from winpyai.ui.styles import DARK_THEME_QSS, get_palette
from winpyai.ui.sidebar import Sidebar
from winpyai.ui.chat_area import ChatArea
from winpyai.ui.input_bar import InputBar
from winpyai.config import (
    APP_NAME,
    BG_PRIMARY,
    TEXT_SECONDARY,
    MAX_CHAT_WIDTH,
    DEFAULT_MODEL,
)


class MainWindow(QMainWindow):
    """Main application window for WinPyAI.

    Parameters
    ----------
    chat_service : ChatService
        The business logic service that handles chat operations.
    """

    def __init__(self, chat_service: "ChatService") -> None:  # type: ignore[name-defined]
        super().__init__()

        self._chat_service = chat_service
        self._current_chat_id: int | None = None
        self._current_assistant_msg_id: int | None = None
        # First message with no chat selected: create chat, then send this text
        self._pending_send_text: str | None = None

        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._load_initial_data()

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 600)
        self.resize(1280, 800)

        # Apply dark palette
        self.setPalette(get_palette())

        # Apply QSS stylesheet
        self.setStyleSheet(DARK_THEME_QSS)

    def _setup_ui(self) -> None:
        """Build the main window layout."""
        # Central widget
        central_widget = QWidget(self)
        central_widget.setStyleSheet(f"background-color: {BG_PRIMARY};")
        self.setCentralWidget(central_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter for resizable sidebar / chat divider
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #4A4A4A;
                width: 1px;
            }
            QSplitter::handle:hover {
                background-color: #10A37F;
            }
        """)

        # --- Sidebar (left, 260px fixed) ---
        self._sidebar = Sidebar(self)
        splitter.addWidget(self._sidebar)

        # --- Right panel: Chat area + Input bar ---
        right_panel = QWidget(self)
        right_panel.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Chat area (stretch to fill)
        self._chat_area = ChatArea(self)
        self._chat_area.set_max_chat_width(MAX_CHAT_WIDTH)
        right_layout.addWidget(self._chat_area, stretch=1)

        # Separator line between chat and input
        separator = QWidget(self)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #4A4A4A;")
        right_layout.addWidget(separator)

        # Input bar (fixed height)
        self._input_bar = InputBar(self)
        right_layout.addWidget(self._input_bar, alignment=Qt.AlignmentFlag.AlignBottom)

        splitter.addWidget(right_panel)

        # Set sidebar to fixed proportion
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 1020])

        main_layout.addWidget(splitter, stretch=1)

        # Status bar
        self._status_bar = QStatusBar(self)
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: #2D2D2D;
                color: {TEXT_SECONDARY};
                border-top: 1px solid #4A4A4A;
            }}
        """)
        self._status_label = QLabel("Initializing...", self)
        self._status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; padding: 2px 8px;")
        self._status_bar.addWidget(self._status_label)
        self.setStatusBar(self._status_bar)

    def _connect_signals(self) -> None:
        """Connect all UI signals to their corresponding handlers."""
        # Sidebar signals
        self._sidebar.chat_selected.connect(self.on_chat_selected)
        self._sidebar.new_chat_clicked.connect(self.on_new_chat)
        self._sidebar.delete_chat_requested.connect(self._chat_service.delete_chat)

        # Input bar signals
        self._input_bar.send_clicked.connect(self.on_send_message)
        self._input_bar.stop_clicked.connect(self._chat_service.stop_generation)

        # ChatService signals
        self._chat_service.response_chunk.connect(self.on_stream_chunk)
        self._chat_service.response_complete.connect(self.on_stream_complete)
        self._chat_service.response_error.connect(self.on_stream_error)
        self._chat_service.messages_loaded.connect(self.on_messages_loaded)
        self._chat_service.chat_created.connect(self._on_chat_created)
        self._chat_service.chat_deleted.connect(self._on_chat_deleted)
        self._chat_service.ollama_status.connect(self.on_ollama_status)

    def _load_initial_data(self) -> None:
        """Load initial data: chat list and Ollama status."""
        # Populate sidebar with existing chats
        QTimer.singleShot(0, self._refresh_sidebar)
        QTimer.singleShot(0, self._chat_service.check_ollama)

    def _refresh_sidebar(self) -> None:
        """Refresh the sidebar chat list from the service."""
        chats = self._chat_service.get_all_chats()
        self._sidebar.set_chats(chats)

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def on_chat_selected(self, chat_id: int) -> None:
        """Handle chat selection from sidebar.

        Parameters
        ----------
        chat_id : int
            The identifier of the selected chat.
        """
        self._current_chat_id = chat_id
        self._chat_service.load_chat(chat_id)

    def on_send_message(self, text: str) -> None:
        """Handle send message from input bar.

        Adds the user message bubble, disables input, and calls the service.

        Parameters
        ----------
        text : str
            The message text to send.
        """
        if not text:
            return
        if self._current_chat_id is None:
            self._pending_send_text = text
            self._chat_service.create_chat()
            return

        self._deliver_user_message(text)

    def _deliver_user_message(self, text: str) -> None:
        """Append user bubble, lock input, and start generation for current chat."""
        if self._current_chat_id is None:
            return

        self._chat_area.add_message("user", text, message_id=self._generate_temp_id())

        self._input_bar.show_stop_button()
        self._input_bar.set_enabled(False)

        self._chat_area.show_thinking_indicator()
        self._chat_service.send_message(self._current_chat_id, text)

    def on_new_chat(self) -> None:
        """Handle new chat creation request."""
        self._chat_service.create_chat()

    def on_stream_chunk(self, chunk: str, message_id: int) -> None:
        """Handle streaming response chunk.

        Updates the assistant message bubble with new content.

        Parameters
        ----------
        chunk : str
            The accumulated response text so far.
        message_id : int
            The identifier of the message being streamed.
        """
        self._current_assistant_msg_id = message_id

        self._chat_area.hide_thinking_indicator()

        if message_id not in self._chat_area._bubbles:
            # First chunk: create the assistant bubble
            self._chat_area.add_message("assistant", chunk, message_id=message_id)
        else:
            # Update existing bubble
            self._chat_area.update_message(message_id, chunk)

    def on_stream_complete(self, message_id: int) -> None:
        """Handle completion of streaming response.

        Re-enables input and switches back to send button.

        Parameters
        ----------
        message_id : int
            The identifier of the completed message.
        """
        self._current_assistant_msg_id = None
        self._chat_area.hide_thinking_indicator()
        self._input_bar.show_send_button()
        self._input_bar.set_enabled(True)
        self._input_bar.setFocus()
        self._refresh_sidebar()

    def on_stream_error(self, error: str) -> None:
        """Handle streaming error.

        Shows an error message and re-enables input.

        Parameters
        ----------
        error : str
            The error message.
        """
        self._current_assistant_msg_id = None
        self._chat_area.hide_thinking_indicator()
        self._input_bar.show_send_button()
        self._input_bar.set_enabled(True)

        # Show error in chat area as a system message
        self._chat_area.add_message("system", f"Error: {error}")

        # Also update status bar
        self._status_label.setText(f"Error: {error}")

    def on_messages_loaded(self, messages: list[dict]) -> None:
        """Handle loaded messages for the current chat.

        Clears the chat area and populates it with all messages.

        Parameters
        ----------
        messages : list[dict]
            List of message dicts with role, content, id keys.
        """
        self._chat_area.clear_messages()

        for msg in messages:
            role = msg.get("role", "system")
            content = msg.get("content", "")
            msg_id = msg.get("id", 0)
            self._chat_area.add_message(role, content, message_id=msg_id)

    def on_ollama_status(self, is_running: bool, message: str) -> None:
        """Handle Ollama status update.

        Updates the status bar and input placeholder based on connection state.

        Parameters
        ----------
        is_running : bool
            Whether Ollama is running.
        message : str
            Status message text.
        """
        self._status_label.setText(message)
        self._sidebar.set_status_text(message)

        if not is_running:
            self._input_bar.set_placeholder("Ollama is not running...")
            self._input_bar.set_enabled(False)
        else:
            self._input_bar.set_placeholder("Message WinPyAI...")
            self._input_bar.set_enabled(True)

    # ------------------------------------------------------------------
    # Internal ChatService response handlers
    # ------------------------------------------------------------------

    def _on_chat_created(self, chat_id: int) -> None:
        """Handle new chat creation: refresh sidebar and select new chat.

        Parameters
        ----------
        chat_id : int
            The identifier of the newly created chat.
        """
        self._refresh_sidebar()
        self._sidebar.select_chat(chat_id)
        self._current_chat_id = chat_id
        self._chat_area.clear_messages()

        # Load the new chat (even if empty, to ensure state is clean)
        self._chat_service.load_chat(chat_id)

        pending = self._pending_send_text
        self._pending_send_text = None
        if pending:
            QTimer.singleShot(0, lambda p=pending: self._deliver_user_message(p))

    def _on_chat_deleted(self, chat_id: int) -> None:
        """Handle chat deletion: refresh sidebar and clear chat area if needed.

        Parameters
        ----------
        chat_id : int
            The identifier of the deleted chat.
        """
        if self._current_chat_id == chat_id:
            self._current_chat_id = None
            self._chat_area.clear_messages()

        self._refresh_sidebar()

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _generate_temp_id(self) -> int:
        """Generate a temporary negative message id for user messages.

        Returns
        -------
        int
            A negative integer safe for temporary use.
        """
        import time
        return -int(time.time() * 1000)

    # ------------------------------------------------------------------
    # Event overrides
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        """Handle window close: stop generation and clean up resources.

        Parameters
        ----------
        event : QCloseEvent
            The close event.
        """
        # Stop any active generation
        try:
            self._chat_service.stop_generation()
        except Exception:
            pass

        # Accept the close event
        event.accept()
