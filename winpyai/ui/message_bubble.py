"""Message bubble widget for WinPyAI chat interface.

Provides a rounded, styled message bubble that aligns differently based on
message role (user right-aligned, assistant left-aligned, system centered).
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
    QWidget,
)
from PyQt6.QtCore import Qt

from winpyai.config import (
    TEXT_PRIMARY,
    FONT_SIZE_NORMAL,
    FONT_FAMILY,
    USER_COLOR,
    ASSISTANT_COLOR,
    USER_BUBBLE_BORDER,
    ASSISTANT_BUBBLE_BORDER,
    BORDER_COLOR,
    BG_TERTIARY,
    MESSAGE_BUBBLE_RADIUS,
)


class MessageBubble(QFrame):
    """A styled message bubble widget for chat messages.

    Parameters
    ----------
    role : str
        One of "user", "assistant", or "system" — controls alignment and color.
    content : str
        The message text to display.
    parent : QWidget | None
        Parent widget for Qt memory management.
    message_id : int
        Unique identifier used for streaming updates. Defaults to 0.

    Attributes
    ----------
    message_id : int
        The unique message identifier.
    role : str
        The message role ("user", "assistant", "system").
    """

    def __init__(
        self,
        role: str,
        content: str,
        parent: QWidget | None = None,
        message_id: int = 0,
    ) -> None:
        super().__init__(parent)
        self.role = role
        self.message_id = message_id

        self._setup_appearance()
        self._setup_layout(content)

    def _setup_appearance(self) -> None:
        """Configure the frame's visual appearance based on role."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)

        if self.role == "user":
            self.setObjectName("userBubble")
            bg_color = USER_COLOR
            border_color = USER_BUBBLE_BORDER
            radius_top_left = 12
            radius_top_right = 12
            radius_bottom_right = 4
            radius_bottom_left = 12
        elif self.role == "assistant":
            self.setObjectName("assistantBubble")
            bg_color = ASSISTANT_COLOR
            border_color = ASSISTANT_BUBBLE_BORDER
            radius_top_left = 12
            radius_top_right = 12
            radius_bottom_right = 12
            radius_bottom_left = 4
        else:  # system
            self.setObjectName("systemBubble")
            bg_color = BG_TERTIARY
            border_color = BORDER_COLOR
            radius_top_left = 12
            radius_top_right = 12
            radius_bottom_right = 12
            radius_bottom_left = 12

        self.setStyleSheet(f"""
            QFrame#{self.objectName()} {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {MESSAGE_BUBBLE_RADIUS}px;
            }}
        """)

        # Apply individual corner radii for asymmetric bubble shape
        self.setStyleSheet(f"""
            QFrame#{self.objectName()} {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-top-left-radius: {radius_top_left}px;
                border-top-right-radius: {radius_top_right}px;
                border-bottom-right-radius: {radius_bottom_right}px;
                border-bottom-left-radius: {radius_bottom_left}px;
                padding: 12px 16px;
            }}
        """)

        self.setMaximumWidth(720)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

    def _setup_layout(self, content: str) -> None:
        """Create internal layout and content label.

        Uses a QHBoxLayout (wrapped internally) so the bubble can be placed
        inside outer layouts for alignment.
        """
        self._content_label = QLabel(content, self)
        self._content_label.setWordWrap(True)
        self._content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard,
        )
        self._content_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_NORMAL}px;
                line-height: 1.5;
                background: transparent;
                border: none;
                padding: 0px;
            }}
        """)
        self._content_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._content_label.setMinimumWidth(100)
        self._content_label.setMaximumWidth(700)

        # Internal layout to hold the label with padding inside the frame
        inner_layout = QHBoxLayout(self)
        inner_layout.setContentsMargins(16, 12, 16, 12)
        inner_layout.setSpacing(0)
        inner_layout.addWidget(self._content_label, stretch=0)

    def update_content(self, new_content: str) -> None:
        """Update the displayed text content.

        Used during streaming responses to incrementally update the bubble.

        Parameters
        ----------
        new_content : str
            The new text to display.
        """
        self._content_label.setText(new_content)

    def set_max_width(self, width: int) -> None:
        """Set the maximum width of the bubble content.

        Parameters
        ----------
        width : int
            Maximum width in pixels.
        """
        effective_width = max(width - 32, 100)  # account for padding
        self.setMaximumWidth(width + 32)
        self._content_label.setMaximumWidth(effective_width)
