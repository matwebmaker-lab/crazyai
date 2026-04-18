"""Input bar widget for WinPyAI.

Provides a multi-line text input area with a send/stop button and a model
name label. Supports Enter-to-send and Shift+Enter-for-newline.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QEvent
from PyQt6.QtGui import QKeyEvent

from winpyai.config import (
    ACCENT_COLOR,
    TEXT_SECONDARY,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    BG_SECONDARY,
    BORDER_COLOR,
)


class InputBar(QWidget):
    """Input bar with multi-line text edit, send/stop button, and model label.

    Signals
    -------
    send_clicked : pyqtSignal(str)
        Emitted when the user sends a message, carrying the text content.
    stop_clicked : pyqtSignal()
        Emitted when the user clicks the stop button during generation.

    Parameters
    ----------
    parent : QWidget | None
        Parent widget for Qt memory management.
    """

    send_clicked = pyqtSignal(str)
    stop_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._is_stop_mode: bool = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Build the input bar layout and widgets."""
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 12, 20, 12)
        main_layout.setSpacing(12)

        # Left side: vertical layout for text edit + model label
        left_widget = QWidget(self)
        left_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # Text edit for multi-line input
        self._text_edit = QTextEdit(self)
        self._text_edit.setPlaceholderText("Message WinPyAI...")
        self._text_edit.setFixedHeight(80)
        self._text_edit.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self._text_edit.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self._text_edit.setLineWrapMode(
            QTextEdit.LineWrapMode.WidgetWidth,
        )
        self._text_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self._text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_SECONDARY};
                color: #ECECEC;
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 10px 14px;
                font-family: "Segoe UI";
                font-size: {FONT_SIZE_NORMAL}px;
                line-height: 1.4;
            }}
            QTextEdit:focus {{
                border: 2px solid {ACCENT_COLOR};
                padding: 9px 13px;
            }}
        """)

        left_layout.addWidget(self._text_edit, stretch=1)

        # Model label (shown below text edit, right-aligned)
        self._model_label = QLabel("llama3.2:latest", self)
        self._model_label.setObjectName("modelLabel")
        self._model_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: {FONT_SIZE_SMALL}px;
                padding: 2px 6px;
                background: transparent;
                border: none;
            }}
        """)
        self._model_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        left_layout.addWidget(self._model_label, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(left_widget, stretch=1)

        # Right side: send/stop button (vertically centered)
        self._action_button = QPushButton("Send", self)
        self._action_button.setObjectName("sendButton")
        self._action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action_button.setFixedHeight(80)
        self._action_button.setFixedWidth(80)
        self._action_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: {FONT_SIZE_NORMAL}px;
            }}
            QPushButton:hover {{
                background-color: #0D8C6D;
            }}
            QPushButton:pressed {{
                background-color: #0A6B52;
            }}
            QPushButton:disabled {{
                background-color: #4A4A4A;
                color: #6B6B6B;
            }}
        """)

        main_layout.addWidget(self._action_button, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.setFixedHeight(120)

    def _connect_signals(self) -> None:
        """Connect widget signals to internal handlers."""
        self._action_button.clicked.connect(self._on_button_clicked)
        # Return/Enter goes to QTextEdit first, not this widget — filter keys there
        self._text_edit.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Enter sends; Shift+Enter inserts newline (QTextEdit has focus)."""
        if watched is self._text_edit and event.type() == QEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent) and event.key() in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
            ):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False
                self._try_send()
                return True
        return super().eventFilter(watched, event)

    def _on_button_clicked(self) -> None:
        """Handle send/stop button click."""
        if self._is_stop_mode:
            self.stop_clicked.emit()
        else:
            self._try_send()

    def _try_send(self) -> None:
        """Attempt to send the current text if non-empty."""
        text = self.get_text()
        if text:
            self.send_clicked.emit(text)
            self.clear_input()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_text(self) -> str:
        """Return the current input text, stripped of whitespace.

        Returns
        -------
        str
            The trimmed text content of the input field.
        """
        return self._text_edit.toPlainText().strip()

    def clear_input(self) -> None:
        """Clear all text from the input field."""
        self._text_edit.clear()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the input field and action button.

        Parameters
        ----------
        enabled : bool
            Whether the widgets should be interactive.
        """
        self._text_edit.setEnabled(enabled)
        self._action_button.setEnabled(enabled)

    def set_placeholder(self, text: str) -> None:
        """Set the placeholder text of the input field.

        Parameters
        ----------
        text : str
            The placeholder text to display.
        """
        self._text_edit.setPlaceholderText(text)

    def show_stop_button(self) -> None:
        """Switch the action button to "Stop" mode with red styling."""
        self._is_stop_mode = True
        self._action_button.setText("Stop")
        self._action_button.setObjectName("stopButton")
        self._action_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #A93226;
            }
        """)

    def show_send_button(self) -> None:
        """Switch the action button back to "Send" mode with accent styling."""
        self._is_stop_mode = False
        self._action_button.setText("Send")
        self._action_button.setObjectName("sendButton")
        self._action_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: {FONT_SIZE_NORMAL}px;
            }}
            QPushButton:hover {{
                background-color: #0D8C6D;
            }}
            QPushButton:pressed {{
                background-color: #0A6B52;
            }}
            QPushButton:disabled {{
                background-color: #4A4A4A;
                color: #6B6B6B;
            }}
        """)

    def set_model_label(self, text: str) -> None:
        """Update the model display label.

        Parameters
        ----------
        text : str
            The model name to display.
        """
        self._model_label.setText(text)
