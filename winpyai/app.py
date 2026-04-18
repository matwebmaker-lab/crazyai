"""Application bootstrap for WinPyAI.

Creates and configures the QApplication, initializes all services,
and wires together the complete application stack from database to UI.
"""

import sys
import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QFont

from winpyai.config import APP_NAME, FONT_FAMILY, FONT_SIZE_NORMAL
from winpyai.database.db import Database
from winpyai.services.ollama_service import OllamaService
from winpyai.services.chat_service import ChatService
from winpyai.ui.main_window import MainWindow
from winpyai.ui.styles import get_palette, DARK_THEME_QSS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> QApplication:
    """Create and configure the QApplication.

    Sets up the application with:
    - Fusion style for consistent cross-platform rendering
    - Dark palette from styles module
    - Global font from config constants
    - QSS stylesheet for fine-grained widget styling
    - High DPI scaling with pass-through rounding policy

    Returns:
        QApplication: Fully configured application instance.
    """
    # Must run before QApplication exists (Qt 6 / PyQt6 requirement)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Set dark palette
    app.setPalette(get_palette())

    # Set global font
    font = QFont(FONT_FAMILY, FONT_SIZE_NORMAL)
    app.setFont(font)

    # Apply QSS stylesheet
    app.setStyleSheet(DARK_THEME_QSS)

    return app


def run_app() -> None:
    """Main application entry point.

    Initializes the full application stack in dependency order:
    1. QApplication (event loop, styling, fonts)
    2. Database (SQLite connection + schema)
    3. OllamaService (HTTP client for local AI)
    4. ChatService (business logic / signal hub)
    5. MainWindow (UI presentation)

    After showing the window, performs initial data loading:
    - Checks Ollama availability
    - Loads installed model list
    - Populates sidebar with existing chats

    Finally enters the Qt event loop until the user closes the application.
    """
    app = create_app()

    # Initialize database
    db = Database()
    logger.info("Database initialized")

    # Initialize Ollama service
    ollama = OllamaService()

    # Initialize chat service (QObject, needs app)
    chat_service = ChatService(db, ollama)

    # Create main window
    window = MainWindow(chat_service)
    window.show()

    # Check Ollama status
    chat_service.check_ollama()

    # Load available models
    chat_service.refresh_models()

    # Initial chat list: MainWindow._load_initial_data schedules _refresh_sidebar

    logger.info("Application started successfully")

    # Run event loop
    sys.exit(app.exec())
