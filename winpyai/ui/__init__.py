"""WinPyAI UI layer.

Provides all user interface components for the WinPyAI desktop chat application.
"""

from winpyai.ui.styles import DARK_THEME_QSS, get_palette
from winpyai.ui.message_bubble import MessageBubble
from winpyai.ui.chat_area import ChatArea
from winpyai.ui.input_bar import InputBar
from winpyai.ui.sidebar import Sidebar
from winpyai.ui.main_window import MainWindow

__all__ = [
    "DARK_THEME_QSS",
    "get_palette",
    "MessageBubble",
    "ChatArea",
    "InputBar",
    "Sidebar",
    "MainWindow",
]
