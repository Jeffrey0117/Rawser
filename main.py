"""
Rawser - Media Download Tool
Main entry point with Qt and asyncio integration via qasync.
"""

import sys
import asyncio

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qasync import QEventLoop, asyncClose

from src.gui.main_window import MainWindow


def setup_dark_theme(app: QApplication) -> None:
    """Apply dark theme stylesheet to the application."""
    dark_stylesheet = """
    QWidget {
        background-color: #1e1e1e;
        color: #d4d4d4;
        font-family: 'Segoe UI', 'Consolas', monospace;
        font-size: 12px;
    }

    QMainWindow {
        background-color: #1e1e1e;
    }

    QLineEdit {
        background-color: #2d2d2d;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        padding: 8px 12px;
        color: #d4d4d4;
        selection-background-color: #264f78;
    }

    QLineEdit:focus {
        border: 1px solid #007acc;
    }

    QPushButton {
        background-color: #0e639c;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: #ffffff;
        font-weight: bold;
    }

    QPushButton:hover {
        background-color: #1177bb;
    }

    QPushButton:pressed {
        background-color: #0d5a8c;
    }

    QPushButton:disabled {
        background-color: #3c3c3c;
        color: #6d6d6d;
    }

    QPushButton#dangerButton {
        background-color: #c42b1c;
    }

    QPushButton#dangerButton:hover {
        background-color: #d63a2c;
    }

    QListWidget {
        background-color: #252526;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        padding: 4px;
        outline: none;
    }

    QListWidget::item {
        background-color: #2d2d2d;
        border: none;
        border-radius: 3px;
        margin: 2px 0;
        padding: 4px;
    }

    QListWidget::item:selected {
        background-color: #094771;
    }

    QListWidget::item:hover {
        background-color: #37373d;
    }

    QTextEdit {
        background-color: #1e1e1e;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        padding: 8px;
        color: #d4d4d4;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 11px;
    }

    QProgressBar {
        background-color: #3c3c3c;
        border: none;
        border-radius: 2px;
        height: 4px;
        text-align: center;
    }

    QProgressBar::chunk {
        background-color: #0e639c;
        border-radius: 2px;
    }

    QStatusBar {
        background-color: #007acc;
        color: #ffffff;
        font-size: 11px;
    }

    QLabel {
        color: #d4d4d4;
    }

    QLabel#sectionTitle {
        color: #569cd6;
        font-weight: bold;
        font-size: 11px;
        padding: 4px 0;
    }

    QSplitter::handle {
        background-color: #3c3c3c;
    }

    QSplitter::handle:horizontal {
        width: 2px;
    }

    QSplitter::handle:vertical {
        height: 2px;
    }

    QScrollBar:vertical {
        background-color: #1e1e1e;
        width: 12px;
        margin: 0;
    }

    QScrollBar::handle:vertical {
        background-color: #5a5a5a;
        border-radius: 6px;
        min-height: 20px;
        margin: 2px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #6d6d6d;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0;
    }

    QScrollBar:horizontal {
        background-color: #1e1e1e;
        height: 12px;
        margin: 0;
    }

    QScrollBar::handle:horizontal {
        background-color: #5a5a5a;
        border-radius: 6px;
        min-width: 20px;
        margin: 2px;
    }

    QScrollBar::handle:horizontal:hover {
        background-color: #6d6d6d;
    }

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0;
    }
    """
    app.setStyleSheet(dark_stylesheet)


async def main_async() -> int:
    """Async main function."""
    from src.app import RawserApp

    # Create app and window
    app_core = RawserApp()
    window = MainWindow()

    # Connect signals: GUI -> App
    window.signal_navigate.connect(app_core.on_navigate)
    window.signal_create_tab.connect(app_core.on_create_tab)
    window.signal_close_tab.connect(app_core.on_close_tab)
    window.signal_toggle_browse.connect(app_core.on_toggle_browse)
    window.signal_start_download.connect(app_core.on_start_download)

    # Connect signals: App -> GUI
    app_core.signal_tab_created.connect(window.on_tab_created)
    app_core.signal_tab_updated.connect(window.on_tab_updated)
    app_core.signal_log.connect(window.on_log)
    app_core.signal_media_detected.connect(window.on_media_detected)
    app_core.signal_download_progress.connect(window.on_download_progress)
    app_core.signal_download_complete.connect(window.on_download_complete)

    # Start browser engine
    await app_core.start()

    window.show()

    # Wait until window is closed
    while window.isVisible():
        await asyncio.sleep(0.1)

    # Cleanup
    await app_core.stop()

    return 0


def main() -> int:
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Rawser")
    app.setApplicationVersion("0.1.0")

    # Apply dark theme
    setup_dark_theme(app)

    # Create event loop with qasync
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Run async main
    with loop:
        return loop.run_until_complete(main_async())


if __name__ == "__main__":
    sys.exit(main())
