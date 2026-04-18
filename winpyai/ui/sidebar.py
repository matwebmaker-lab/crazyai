"""Sidebar widget for WinPyAI.

Provides a fixed-width panel containing a "New Chat" button and a list
of existing chats. Supports selection, right-click context menu for
deletion, and chat title updates.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QAction

from winpyai.config import (
    ACCENT_COLOR,
    BG_SECONDARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BORDER_COLOR,
    FONT_SIZE_TITLE,
    FONT_SIZE_SMALL,
    FONT_SIZE_NORMAL,
)


class Sidebar(QWidget):
    """Sidebar panel with new-chat button and chat list.

    Signals
    -------
    chat_selected : pyqtSignal(int)
        Emitted when a chat item is clicked, carrying the chat_id.
    new_chat_clicked : pyqtSignal()
        Emitted when the "New Chat" button is pressed.
    delete_chat_requested : pyqtSignal(int)
        Emitted from the context menu, carrying the chat_id to delete.

    Parameters
    ----------
    parent : QWidget | None
        Parent widget for Qt memory management.
    """

    chat_selected = pyqtSignal(int)
    new_chat_clicked = pyqtSignal()
    delete_chat_requested = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Map chat_id -> QListWidgetItem for fast lookups
        self._chat_items: dict[int, QListWidgetItem] = {}
        self._chat_data: dict[int, dict] = {}

        self.setFixedWidth(260)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Build the sidebar layout and widgets."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_SECONDARY};
                border: none;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 16, 12, 16)
        main_layout.setSpacing(12)

        # Header: App name label
        header_widget = QWidget(self)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(0)

        app_label = QLabel("WinPyAI", self)
        app_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: {FONT_SIZE_TITLE}px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)
        header_layout.addWidget(app_label)
        header_layout.addStretch(1)
        main_layout.addWidget(header_widget)

        # New Chat button
        self._new_chat_button = QPushButton("+  New Chat", self)
        self._new_chat_button.setObjectName("newChatButton")
        self._new_chat_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_chat_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: {FONT_SIZE_NORMAL}px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #0D8C6D;
            }}
            QPushButton:pressed {{
                background-color: #0A6B52;
            }}
        """)
        self._new_chat_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        main_layout.addWidget(self._new_chat_button)

        # Separator label
        history_label = QLabel("Chat History", self)
        history_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: {FONT_SIZE_SMALL}px;
                font-weight: 600;
                padding: 8px 4px 4px 4px;
                background: transparent;
                border: none;
            }}
        """)
        main_layout.addWidget(history_label)

        # Chat list
        self._chat_list = QListWidget(self)
        self._chat_list.setObjectName("chatList")
        self._chat_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BG_SECONDARY};
                border: none;
                outline: none;
                padding: 0px;
            }}
            QListWidget::item {{
                background-color: transparent;
                color: {TEXT_PRIMARY};
                padding: 12px 12px;
                border-bottom: 1px solid {BORDER_COLOR};
                border-left: 3px solid transparent;
                border-radius: 0px;
            }}
            QListWidget::item:selected {{
                background-color: rgba(16, 163, 127, 0.30);
                color: {TEXT_PRIMARY};
                border-left: 3px solid {ACCENT_COLOR};
            }}
            QListWidget::item:hover:!selected {{
                background-color: #3D3D3D;
            }}
            QListWidget::item:selected:!active {{
                background-color: rgba(16, 163, 127, 0.25);
            }}
            QListWidget:focus {{
                border: none;
                outline: none;
            }}
        """)
        self._chat_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self._chat_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        self._chat_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu,
        )
        main_layout.addWidget(self._chat_list, stretch=1)

        # Status label at bottom
        self._status_label = QLabel("Ready", self)
        self._status_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: {FONT_SIZE_SMALL - 1}px;
                padding: 4px;
                background: transparent;
                border: none;
            }}
        """)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._status_label)

    def _connect_signals(self) -> None:
        """Connect internal widget signals to handlers."""
        self._new_chat_button.clicked.connect(self.new_chat_clicked.emit)
        self._chat_list.itemClicked.connect(self._on_item_clicked)
        self._chat_list.customContextMenuRequested.connect(
            self._on_context_menu,
        )

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle chat item click.

        Parameters
        ----------
        item : QListWidgetItem
            The clicked list item.
        """
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        if chat_id is not None:
            self.chat_selected.emit(int(chat_id))

    def _on_context_menu(self, position: QPoint) -> None:
        """Show right-click context menu for chat deletion.

        Parameters
        ----------
        position : QPoint
            Local coordinates where the click occurred.
        """
        item = self._chat_list.itemAt(position)
        if item is None:
            return

        chat_id = item.data(Qt.ItemDataRole.UserRole)
        if chat_id is None:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #2D2D2D;
                color: #ECECEC;
                border: 1px solid #4A4A4A;
                border-radius: 6px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: #3D3D3D;
            }}
        """)

        delete_action = QAction("Delete Chat", self)
        delete_action.triggered.connect(
            lambda: self.delete_chat_requested.emit(int(chat_id)),
        )
        menu.addAction(delete_action)

        # Show menu at global position
        global_pos = self._chat_list.mapToGlobal(position)
        menu.exec(global_pos)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_chats(self, chats: list[dict]) -> None:
        """Clear and populate the chat list.

        Each chat dict must contain: id, title, created_at, updated_at, model.

        Parameters
        ----------
        chats : list[dict]
            List of chat dictionaries to display.
        """
        self._chat_list.clear()
        self._chat_items.clear()
        self._chat_data.clear()

        for chat in chats:
            self.add_chat(chat)

    def add_chat(self, chat: dict) -> None:
        """Add a single chat to the top of the list.

        Parameters
        ----------
        chat : dict
            Chat dictionary with id, title, created_at, updated_at, model keys.
        """
        chat_id = chat["id"]
        title = chat.get("title", "New Chat")
        updated_at = chat.get("updated_at", "")
        model = chat.get("model", "")

        # Format display text: title on first line, timestamp on second
        display_text = title

        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, chat_id)
        item.setToolTip(f"{title}\nModel: {model}\n{updated_at}")

        self._chat_items[chat_id] = item
        self._chat_data[chat_id] = chat

        # Insert at top (index 0)
        self._chat_list.insertItem(0, item)

    def remove_chat(self, chat_id: int) -> None:
        """Remove a chat from the list by id.

        Parameters
        ----------
        chat_id : int
            The identifier of the chat to remove.
        """
        item = self._chat_items.pop(chat_id, None)
        if item is not None:
            row = self._chat_list.row(item)
            self._chat_list.takeItem(row)
        self._chat_data.pop(chat_id, None)

    def select_chat(self, chat_id: int) -> None:
        """Select a chat item by id.

        Parameters
        ----------
        chat_id : int
            The identifier of the chat to select.
        """
        item = self._chat_items.get(chat_id)
        if item is not None:
            self._chat_list.setCurrentItem(item)

    def update_chat_title(self, chat_id: int, title: str) -> None:
        """Update the display title of a chat item.

        Parameters
        ----------
        chat_id : int
            The identifier of the chat to update.
        title : str
            The new title text.
        """
        item = self._chat_items.get(chat_id)
        if item is not None:
            item.setText(title)
            chat = self._chat_data.get(chat_id)
            if chat is not None:
                chat["title"] = title
                model = chat.get("model", "")
                updated_at = chat.get("updated_at", "")
                item.setToolTip(f"{title}\nModel: {model}\n{updated_at}")

    def get_current_chat_id(self) -> int | None:
        """Return the currently selected chat id.

        Returns
        -------
        int | None
            The selected chat's identifier, or None if nothing is selected.
        """
        item = self._chat_list.currentItem()
        if item is None:
            return None
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        return int(chat_id) if chat_id is not None else None

    def set_status_text(self, text: str) -> None:
        """Update the status label at the bottom of the sidebar.

        Parameters
        ----------
        text : str
            Status text to display.
        """
        self._status_label.setText(text)
