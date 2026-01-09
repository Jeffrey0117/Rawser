"""
Custom widgets for Rawser application.
Contains TaskItemWidget and MediaItemWidget for list displays.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont


class TaskItemWidget(QWidget):
    """
    Widget for displaying a task/tab item in the task list.

    Displays:
    - URL (truncated)
    - State indicator
    - Inspect button (toggle browse mode)
    - Close button
    """

    # Signals
    signal_inspect = Signal()  # Emitted when inspect button clicked
    signal_close = Signal()    # Emitted when close button clicked

    # State colors
    STATE_COLORS = {
        "idle": "#6d6d6d",
        "loading": "#dcdcaa",
        "ready": "#4ec9b0",
        "browsing": "#569cd6",
        "error": "#f14c4c",
        "downloading": "#ce9178",
    }

    def __init__(
        self,
        tab_id: str,
        url: str,
        state: str = "idle",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.tab_id = tab_id
        self.url = url
        self._state = state

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Initialize the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # State indicator dot
        self.state_dot = QLabel()
        self.state_dot.setFixedSize(8, 8)
        self.state_dot.setStyleSheet(self._get_dot_style())
        layout.addWidget(self.state_dot)

        # URL and state info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        # URL label (truncated)
        self.url_label = QLabel(self._truncate_url(self.url))
        self.url_label.setToolTip(self.url)
        self.url_label.setFont(QFont("Segoe UI", 10))
        self.url_label.setStyleSheet("color: #d4d4d4;")
        info_layout.addWidget(self.url_label)

        # State label
        self.state_label = QLabel(self._state.upper())
        self.state_label.setFont(QFont("Consolas", 8))
        self.state_label.setStyleSheet(
            f"color: {self.STATE_COLORS.get(self._state, '#6d6d6d')};"
        )
        info_layout.addWidget(self.state_label)

        layout.addLayout(info_layout, 1)

        # Inspect button
        self.inspect_button = QPushButton("Inspect")
        self.inspect_button.setFixedWidth(60)
        self.inspect_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                padding: 4px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
        """)
        self.inspect_button.clicked.connect(self.signal_inspect.emit)
        layout.addWidget(self.inspect_button)

        # Close button
        self.close_button = QPushButton("X")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setObjectName("dangerButton")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                border-radius: 12px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #c42b1c;
            }
        """)
        self.close_button.clicked.connect(self.signal_close.emit)
        layout.addWidget(self.close_button)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _apply_styles(self) -> None:
        """Apply widget styles."""
        self.setStyleSheet("""
            TaskItemWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
            TaskItemWidget:hover {
                background-color: #37373d;
            }
        """)

    def _get_dot_style(self) -> str:
        """Get style for state indicator dot."""
        color = self.STATE_COLORS.get(self._state, "#6d6d6d")
        return f"""
            background-color: {color};
            border-radius: 4px;
        """

    def _truncate_url(self, url: str, max_length: int = 40) -> str:
        """Truncate URL for display."""
        if len(url) <= max_length:
            return url
        return url[:max_length - 3] + "..."

    def set_state(self, state: str) -> None:
        """Update the task state."""
        self._state = state
        self.state_label.setText(state.upper())
        self.state_label.setStyleSheet(
            f"color: {self.STATE_COLORS.get(state, '#6d6d6d')};"
        )
        self.state_dot.setStyleSheet(self._get_dot_style())

    def set_url(self, url: str) -> None:
        """Update the displayed URL."""
        self.url = url
        self.url_label.setText(self._truncate_url(url))
        self.url_label.setToolTip(url)

    def sizeHint(self) -> QSize:
        """Return preferred size."""
        return QSize(280, 50)


class MediaItemWidget(QWidget):
    """
    Widget for displaying a detected media item.

    Displays:
    - Media type icon/indicator
    - URL (truncated)
    - Download button
    """

    # Signal
    signal_download = Signal()  # Emitted when download button clicked

    # Media type colors
    TYPE_COLORS = {
        "video": "#569cd6",
        "audio": "#4ec9b0",
        "image": "#dcdcaa",
        "stream": "#ce9178",
        "playlist": "#c586c0",
        "unknown": "#6d6d6d",
    }

    # Media type icons (text representation)
    TYPE_ICONS = {
        "video": "[VID]",
        "audio": "[AUD]",
        "image": "[IMG]",
        "stream": "[STR]",
        "playlist": "[PLS]",
        "unknown": "[???]",
    }

    def __init__(
        self,
        url: str,
        media_type: str = "unknown",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.url = url
        self.media_type = media_type.lower()

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Initialize the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Type indicator
        type_icon = self.TYPE_ICONS.get(self.media_type, "[???]")
        type_color = self.TYPE_COLORS.get(self.media_type, "#6d6d6d")

        self.type_label = QLabel(type_icon)
        self.type_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self.type_label.setStyleSheet(f"color: {type_color};")
        self.type_label.setFixedWidth(40)
        layout.addWidget(self.type_label)

        # URL info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        # URL label
        self.url_label = QLabel(self._truncate_url(self.url))
        self.url_label.setToolTip(self.url)
        self.url_label.setFont(QFont("Segoe UI", 9))
        self.url_label.setStyleSheet("color: #d4d4d4;")
        info_layout.addWidget(self.url_label)

        # File info (extracted from URL)
        file_info = self._extract_file_info(self.url)
        self.info_label = QLabel(file_info)
        self.info_label.setFont(QFont("Consolas", 8))
        self.info_label.setStyleSheet("color: #6d6d6d;")
        info_layout.addWidget(self.info_label)

        layout.addLayout(info_layout, 1)

        # Download button
        self.download_button = QPushButton("DL")
        self.download_button.setFixedSize(36, 28)
        self.download_button.setToolTip("Download this media")
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                padding: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        self.download_button.clicked.connect(self.signal_download.emit)
        layout.addWidget(self.download_button)

        # Copy URL button
        self.copy_button = QPushButton("CP")
        self.copy_button.setFixedSize(36, 28)
        self.copy_button.setToolTip("Copy URL to clipboard")
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                padding: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
        """)
        self.copy_button.clicked.connect(self._copy_to_clipboard)
        layout.addWidget(self.copy_button)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _apply_styles(self) -> None:
        """Apply widget styles."""
        self.setStyleSheet("""
            MediaItemWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
            MediaItemWidget:hover {
                background-color: #37373d;
            }
        """)

    def _truncate_url(self, url: str, max_length: int = 50) -> str:
        """Truncate URL for display."""
        if len(url) <= max_length:
            return url
        return url[:max_length - 3] + "..."

    def _extract_file_info(self, url: str) -> str:
        """Extract filename and extension from URL."""
        try:
            from urllib.parse import urlparse, unquote
            parsed = urlparse(url)
            path = unquote(parsed.path)

            # Get filename from path
            if "/" in path:
                filename = path.split("/")[-1]
            else:
                filename = path

            # Clean up query strings
            if "?" in filename:
                filename = filename.split("?")[0]

            if filename:
                return filename[:40] + ("..." if len(filename) > 40 else "")
            return parsed.netloc
        except Exception:
            return "Unknown"

    def _copy_to_clipboard(self) -> None:
        """Copy URL to clipboard."""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.url)

    def sizeHint(self) -> QSize:
        """Return preferred size."""
        return QSize(300, 50)

    def set_downloading(self, downloading: bool) -> None:
        """Update widget state during download."""
        self.download_button.setEnabled(not downloading)
        if downloading:
            self.download_button.setText("...")
            self.download_button.setStyleSheet("""
                QPushButton {
                    background-color: #ce9178;
                    padding: 4px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
        else:
            self.download_button.setText("DL")
            self.download_button.setStyleSheet("""
                QPushButton {
                    background-color: #0e639c;
                    padding: 4px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
            """)
