"""Chat area widget for WinPyAI.

Provides a scrollable area that displays message bubbles stacked vertically.
Messages are pushed to the top by a bottom spacer. Auto-scrolls to the
bottom when new messages are added.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QLabel,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    pyqtSignal,
)

from winpyai.config import TEXT_SECONDARY, FONT_SIZE_SMALL
from winpyai.ui.message_bubble import MessageBubble


class ChatArea(QWidget):
    """Scrollable chat area that displays message bubbles.

    Signals
    -------
    message_added : pyqtSignal(int)
        Emitted when a new message bubble is added, carrying the message_id.

    Parameters
    ----------
    parent : QWidget | None
        Parent widget for Qt memory management.
    """

    message_added = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Internal storage: message_id -> MessageBubble
        self._bubbles: dict[int, MessageBubble] = {}
        self._max_chat_width: int = 800
        self._typing_row: QWidget | None = None
        self._typing_label: QLabel | None = None
        self._typing_timer: QTimer | None = None
        self._typing_dots: int = 0

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the scroll area, viewport, and message layout."""
        # Main layout for this widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self._scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        self._scroll_area.setFrameShape(
            self._scroll_area.frameShape().NoFrame,
        )
        self._scroll_area.viewport().setStyleSheet("background: transparent;")

        # Viewport widget that holds the message layout
        self._viewport = QWidget(self._scroll_area)
        self._viewport.setStyleSheet("background: transparent;")
        self._viewport.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        # Message layout — vertical stack with stretch at bottom
        self._message_layout = QVBoxLayout(self._viewport)
        self._message_layout.setContentsMargins(20, 20, 20, 20)
        self._message_layout.setSpacing(8)
        self._message_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
        )

        # Add stretch at bottom so messages stick to top
        self._message_layout.addStretch(1)

        self._scroll_area.setWidget(self._viewport)
        main_layout.addWidget(self._scroll_area)

    def clear_messages(self) -> None:
        """Remove all message bubbles from the layout.

        Clears internal storage and removes all widgets from the
        message layout (except the bottom stretch).
        """
        self.hide_thinking_indicator()

        # Remove all tracked bubbles from layout
        for bubble in self._bubbles.values():
            bubble.hide()
            self._message_layout.removeWidget(bubble)
            bubble.deleteLater()

        self._bubbles.clear()

    def add_message(
        self,
        role: str,
        content: str,
        message_id: int = 0,
    ) -> MessageBubble:
        """Add a new message bubble to the chat area.

        The bubble is inserted before the bottom stretch so messages
        appear top-to-bottom. Auto-scrolls to the bottom.

        Parameters
        ----------
        role : str
            One of "user", "assistant", or "system".
        content : str
            Initial message text.
        message_id : int
            Unique identifier for streaming updates. Defaults to 0.

        Returns
        -------
        MessageBubble
            The created bubble widget (useful for streaming updates).
        """
        bubble = MessageBubble(role, content, parent=self._viewport, message_id=message_id)
        bubble.set_max_width(self._max_chat_width)

        # Store in lookup dict
        self._bubbles[message_id] = bubble

        # Insert before the last stretch item
        stretch_index = self._message_layout.count() - 1
        if stretch_index < 0:
            stretch_index = self._message_layout.count()

        # Wrap in a row layout for alignment
        row_widget = QWidget(self._viewport)
        row_widget.setStyleSheet("background: transparent;")
        row_layout = QVBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        # Create horizontal layout for left/right alignment
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        if role == "user":
            # Right-aligned: stretch on left, bubble on right
            h_layout.addStretch(1)
            h_layout.addWidget(bubble, 0, Qt.AlignmentFlag.AlignRight)
        elif role == "assistant":
            # Left-aligned: bubble on left, stretch on right
            h_layout.addWidget(bubble, 0, Qt.AlignmentFlag.AlignLeft)
            h_layout.addStretch(1)
        else:
            # System: centered
            h_layout.addStretch(1)
            h_layout.addWidget(bubble, 0, Qt.AlignmentFlag.AlignCenter)
            h_layout.addStretch(1)

        row_layout.addLayout(h_layout)

        self._message_layout.insertWidget(stretch_index, row_widget)

        self.message_added.emit(message_id)

        # Scroll to bottom after layout settles
        QTimer.singleShot(50, self.scroll_to_bottom)

        return bubble

    def show_thinking_indicator(self) -> None:
        """Show a left-aligned 'thinking' row until the first assistant token."""
        self.hide_thinking_indicator()

        stretch_index = self._message_layout.count() - 1
        if stretch_index < 0:
            stretch_index = self._message_layout.count()

        row = QWidget(self._viewport)
        row.setStyleSheet("background: transparent;")
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        self._typing_label = QLabel("Thinking", row)
        self._typing_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: {FONT_SIZE_SMALL}px;
                padding: 10px 14px;
                background-color: rgba(45, 45, 45, 0.95);
                border: 1px solid #4A4A4A;
                border-radius: 12px;
            }}
        """)
        h_layout.addWidget(self._typing_label, 0, Qt.AlignmentFlag.AlignLeft)
        h_layout.addStretch(1)
        row_layout.addLayout(h_layout)

        self._message_layout.insertWidget(stretch_index, row)
        self._typing_row = row
        self._typing_dots = 0

        self._typing_timer = QTimer(self)
        self._typing_timer.timeout.connect(self._tick_thinking_label)
        self._typing_timer.start(450)

        QTimer.singleShot(0, self.scroll_to_bottom)

    def hide_thinking_indicator(self) -> None:
        """Remove the thinking row and stop its animation."""
        if self._typing_timer is not None:
            self._typing_timer.stop()
            self._typing_timer.deleteLater()
            self._typing_timer = None

        if self._typing_row is not None:
            self._message_layout.removeWidget(self._typing_row)
            self._typing_row.deleteLater()
            self._typing_row = None
        self._typing_label = None

    def _tick_thinking_label(self) -> None:
        if self._typing_label is None:
            return
        self._typing_dots = (self._typing_dots + 1) % 4
        self._typing_label.setText("Thinking" + "." * self._typing_dots)

    def update_message(self, message_id: int, content: str) -> None:
        """Update the content of an existing message bubble.

        Parameters
        ----------
        message_id : int
            The identifier of the message to update.
        content : str
            New text content.
        """
        bubble = self._bubbles.get(message_id)
        if bubble is not None:
            bubble.update_content(content)
            self.scroll_to_bottom()

    def scroll_to_bottom(self) -> None:
        """Scroll to the latest content (instant; safe during rapid stream updates).

        Avoids QPropertyAnimation with DeleteWhenStopped — that pattern left a
        dangling Python reference after Qt deleted the C++ object, crashing
        on the next scroll when ``stop()`` was called.
        """
        scrollbar = self._scroll_area.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())

    def set_max_chat_width(self, width: int) -> None:
        """Set the maximum width constraint for message bubbles.

        Parameters
        ----------
        width : int
            Maximum width in pixels.
        """
        self._max_chat_width = width
        for bubble in self._bubbles.values():
            bubble.set_max_width(width)
