"""Dark theme QSS stylesheet and palette for WinPyAI.

Provides the complete visual theme including:
- DARK_THEME_QSS: Full QSS string for all application widgets
- get_palette(): Factory for dark QPalette
"""

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

from winpyai.config import (
    ACCENT_COLOR,
    ACCENT_HOVER,
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_DISABLED,
    BORDER_COLOR,
    FONT_FAMILY,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    SCROLLBAR_WIDTH,
    USER_COLOR,
    ASSISTANT_COLOR,
    USER_BUBBLE_BORDER,
    ASSISTANT_BUBBLE_BORDER,
    MESSAGE_BUBBLE_RADIUS,
)

# ---------------------------------------------------------------------------
# Dark Theme QSS
# ---------------------------------------------------------------------------
DARK_THEME_QSS = f"""
/* ================================================================
   WinPyAI Dark Theme
   ================================================================ */

/* --- Global font ------------------------------------------------ */
QWidget {{
    font-family: "{FONT_FAMILY}";
    font-size: {FONT_SIZE_NORMAL}px;
    color: {TEXT_PRIMARY};
    background-color: {BG_PRIMARY};
}}

/* --- Main Window ------------------------------------------------ */
QMainWindow {{
    background-color: {BG_PRIMARY};
    border: none;
}}

/* --- Generic Widgets -------------------------------------------- */
QWidget {{
    background-color: {BG_PRIMARY};
    border: none;
    outline: none;
}}

/* --- Scroll Area ------------------------------------------------ */
QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background-color: transparent;
    border: none;
}}

/* --- Scroll Bars ------------------------------------------------ */
QScrollBar:vertical {{
    background-color: {BG_SECONDARY};
    width: {SCROLLBAR_WIDTH}px;
    border: none;
    border-radius: 4px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {BORDER_COLOR};
    min-height: 40px;
    border-radius: 4px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {TEXT_SECONDARY};
}}

QScrollBar::handle:vertical:pressed {{
    background-color: {TEXT_PRIMARY};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
    border: none;
    background: none;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {BG_SECONDARY};
    height: {SCROLLBAR_WIDTH}px;
    border: none;
    border-radius: 4px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: {BORDER_COLOR};
    min-width: 40px;
    border-radius: 4px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {TEXT_SECONDARY};
}}

QScrollBar::handle:horizontal:pressed {{
    background-color: {TEXT_PRIMARY};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
    border: none;
    background: none;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* --- Push Buttons ----------------------------------------------- */
QPushButton {{
    background-color: {ACCENT_COLOR};
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: {FONT_SIZE_NORMAL}px;
}}

QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton:pressed {{
    background-color: #0A6B52;
}}

QPushButton:disabled {{
    background-color: #4A4A4A;
    color: {TEXT_DISABLED};
}}

/* --- Secondary button variant (styled via class) ---------------- */
QPushButton#newChatButton {{
    background-color: {ACCENT_COLOR};
    color: #FFFFFF;
    border-radius: 6px;
    padding: 10px 16px;
    font-weight: 600;
    font-size: {FONT_SIZE_NORMAL}px;
}}

QPushButton#newChatButton:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton#sendButton {{
    background-color: {ACCENT_COLOR};
    color: #FFFFFF;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: {FONT_SIZE_NORMAL}px;
}}

QPushButton#sendButton:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton#stopButton {{
    background-color: #E74C3C;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: {FONT_SIZE_NORMAL}px;
}}

QPushButton#stopButton:hover {{
    background-color: #C0392B;
}}

/* --- Line Edit -------------------------------------------------- */
QLineEdit {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: {FONT_SIZE_NORMAL}px;
    selection-background-color: {ACCENT_COLOR};
    selection-color: #FFFFFF;
}}

QLineEdit:focus {{
    border: 2px solid {ACCENT_COLOR};
    padding: 7px 11px;
}}

QLineEdit:disabled {{
    background-color: {BG_PRIMARY};
    color: {TEXT_DISABLED};
    border: 1px solid {BG_SECONDARY};
}}

/* --- Text Edit -------------------------------------------------- */
QTextEdit {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: {FONT_SIZE_NORMAL}px;
    selection-background-color: {ACCENT_COLOR};
    selection-color: #FFFFFF;
}}

QTextEdit:focus {{
    border: 2px solid {ACCENT_COLOR};
    padding: 7px 11px;
}}

QTextEdit:disabled {{
    background-color: {BG_PRIMARY};
    color: {TEXT_DISABLED};
    border: 1px solid {BG_SECONDARY};
}}

/* --- List Widget (Sidebar chat list) ---------------------------- */
QListWidget {{
    background-color: {BG_SECONDARY};
    border: none;
    outline: none;
    padding: 0px;
    alternate-background-color: transparent;
}}

QListWidget::item {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    padding: 12px 16px;
    border-bottom: 1px solid {BORDER_COLOR};
    border-radius: 0px;
}}

QListWidget::item:selected {{
    background-color: rgba(16, 163, 127, 0.30);
    color: {TEXT_PRIMARY};
    border-left: 3px solid {ACCENT_COLOR};
    padding-left: 13px;
}}

QListWidget::item:hover:!selected {{
    background-color: {BG_TERTIARY};
}}

QListWidget::item:selected:!active {{
    background-color: rgba(16, 163, 127, 0.25);
    color: {TEXT_PRIMARY};
}}

/* --- List Widget focus ------------------------------------------ */
QListWidget:focus {{
    border: none;
    outline: none;
}}

QListWidget::item:focus {{
    border: none;
    outline: none;
}}

/* --- Labels ----------------------------------------------------- */
QLabel {{
    color: {TEXT_PRIMARY};
    background-color: transparent;
    border: none;
}}

QLabel#modelLabel {{
    color: {TEXT_SECONDARY};
    font-size: {FONT_SIZE_SMALL}px;
    padding: 4px 8px;
    background-color: {BG_SECONDARY};
    border-radius: 4px;
}}

QLabel#placeholderLabel {{
    color: {TEXT_SECONDARY};
    font-size: {FONT_SIZE_NORMAL + 2}px;
}}

/* --- Frames (Message Bubbles) ----------------------------------- */
QFrame#userBubble {{
    background-color: {USER_COLOR};
    border: 1px solid {USER_BUBBLE_BORDER};
    border-radius: {MESSAGE_BUBBLE_RADIUS}px {MESSAGE_BUBBLE_RADIUS}px 4px {MESSAGE_BUBBLE_RADIUS}px;
    padding: 12px 16px;
}}

QFrame#assistantBubble {{
    background-color: {ASSISTANT_COLOR};
    border: 1px solid {ASSISTANT_BUBBLE_BORDER};
    border-radius: {MESSAGE_BUBBLE_RADIUS}px {MESSAGE_BUBBLE_RADIUS}px {MESSAGE_BUBBLE_RADIUS}px 4px;
    padding: 12px 16px;
}}

QFrame#systemBubble {{
    background-color: {BG_TERTIARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: {MESSAGE_BUBBLE_RADIUS}px;
    padding: 12px 16px;
}}

/* --- Menu (Context menus) --------------------------------------- */
QMenu {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
}}

QMenu::item:disabled {{
    color: {TEXT_DISABLED};
}}

QMenu::separator {{
    height: 1px;
    background-color: {BORDER_COLOR};
    margin: 4px 8px;
}}

/* --- Status Bar ------------------------------------------------- */
QStatusBar {{
    background-color: {BG_SECONDARY};
    color: {TEXT_SECONDARY};
    border-top: 1px solid {BORDER_COLOR};
}}

QStatusBar::item {{
    border: none;
}}

/* --- Splitter --------------------------------------------------- */
QSplitter::handle {{
    background-color: {BORDER_COLOR};
    width: 1px;
    height: 1px;
}}

QSplitter::handle:hover {{
    background-color: {ACCENT_COLOR};
}}

/* --- Tooltip ---------------------------------------------------- */
QToolTip {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: {FONT_SIZE_SMALL}px;
}}
"""


def get_palette() -> QPalette:
    """Return a dark QPalette configured for the WinPyAI theme.

    Returns
    -------
    QPalette
        A fully configured dark palette matching the application theme.
    """
    palette = QPalette()

    # Window / background
    palette.setColor(QPalette.ColorRole.Window, QColor(BG_PRIMARY))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(BG_SECONDARY))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(BG_TERTIARY))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(BG_SECONDARY))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT_PRIMARY))

    # Text
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(TEXT_SECONDARY))

    # Buttons
    palette.setColor(QPalette.ColorRole.Button, QColor(ACCENT_COLOR))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#FFFFFF"))

    # Highlight
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT_COLOR))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))

    # Disabled states
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor(TEXT_DISABLED),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor(TEXT_DISABLED),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(TEXT_DISABLED),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Button,
        QColor(BG_TERTIARY),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Base,
        QColor(BG_PRIMARY),
    )

    # BrightText (used for contrasting text on dark backgrounds)
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))

    # Light / mid / dark / shadow (used for 3D bevel effects)
    palette.setColor(QPalette.ColorRole.Light, QColor(BG_TERTIARY))
    palette.setColor(QPalette.ColorRole.Midlight, QColor(BG_SECONDARY))
    palette.setColor(QPalette.ColorRole.Mid, QColor(BORDER_COLOR))
    palette.setColor(QPalette.ColorRole.Dark, QColor("#151515"))
    palette.setColor(QPalette.ColorRole.Shadow, QColor("#0A0A0A"))

    # Link
    palette.setColor(QPalette.ColorRole.Link, QColor(ACCENT_COLOR))
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor(ACCENT_HOVER))

    return palette
