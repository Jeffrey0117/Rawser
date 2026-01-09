"""
Main Window for Rawser application.
Contains the primary GUI layout and signal/slot definitions.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLineEdit,
    QPushButton,
    QListWidget,
    QTextEdit,
    QProgressBar,
    QStatusBar,
    QLabel,
    QFrame,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from src.gui.widgets import TaskItemWidget, MediaItemWidget


class MainWindow(QMainWindow):
    """
    Main application window for Rawser.

    Layout:
    - Top: URL input + Go button
    - Left: Task list
    - Right Top: Log area
    - Right Bottom: Media URL list + Download button
    - Bottom: Status bar + Progress bar
    """

    # Signals emitted by this window
    signal_navigate = Signal(str)       # url - Navigate to URL
    signal_create_tab = Signal(str)     # url - Create new browser tab
    signal_close_tab = Signal(str)      # tab_id - Close browser tab
    signal_toggle_browse = Signal(str)  # tab_id - Toggle browse mode
    signal_start_download = Signal(str) # media_url - Start download

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("Rawser - Media Downloader")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Top bar: URL input + Go button
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        # Main content area with splitter
        content_splitter = self._create_content_area()
        main_layout.addWidget(content_splitter, 1)

        # Bottom: Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        main_layout.addWidget(self.progress_bar)

        # Status bar
        self._setup_status_bar()

    def _create_top_bar(self) -> QWidget:
        """Create the top URL input bar."""
        top_bar = QWidget()
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL to analyze...")
        self.url_input.setClearButtonEnabled(True)
        layout.addWidget(self.url_input, 1)

        # Go button
        self.go_button = QPushButton("Go")
        self.go_button.setFixedWidth(80)
        layout.addWidget(self.go_button)

        # New Tab button
        self.new_tab_button = QPushButton("+")
        self.new_tab_button.setFixedWidth(40)
        self.new_tab_button.setToolTip("Create new tab")
        layout.addWidget(self.new_tab_button)

        return top_bar

    def _create_content_area(self) -> QSplitter:
        """Create the main content area with splitters."""
        # Horizontal splitter: Left (tasks) | Right (logs + media)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Task list
        left_panel = self._create_task_panel()
        main_splitter.addWidget(left_panel)

        # Right panel: Logs + Media
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set initial sizes (30% left, 70% right)
        main_splitter.setSizes([300, 700])

        return main_splitter

    def _create_task_panel(self) -> QWidget:
        """Create the left task list panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Section title
        title = QLabel("TASKS")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Task list
        self.task_list = QListWidget()
        self.task_list.setAlternatingRowColors(False)
        self.task_list.setSpacing(2)
        layout.addWidget(self.task_list)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with logs and media list."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Vertical splitter: Top (logs) | Bottom (media)
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Log area
        log_panel = self._create_log_panel()
        splitter.addWidget(log_panel)

        # Media panel
        media_panel = self._create_media_panel()
        splitter.addWidget(media_panel)

        # Set initial sizes (60% logs, 40% media)
        splitter.setSizes([400, 300])

        layout.addWidget(splitter)
        return panel

    def _create_log_panel(self) -> QWidget:
        """Create the log display panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Section title
        title = QLabel("LOG")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Log text area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 10))
        self.log_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_area)

        # Clear log button
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.log_area.clear)
        layout.addWidget(clear_button)

        return panel

    def _create_media_panel(self) -> QWidget:
        """Create the media URL list panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Section title with count
        title_row = QHBoxLayout()
        title = QLabel("MEDIA")
        title.setObjectName("sectionTitle")
        title_row.addWidget(title)

        self.media_count_label = QLabel("(0)")
        self.media_count_label.setObjectName("sectionTitle")
        title_row.addWidget(self.media_count_label)
        title_row.addStretch()

        layout.addLayout(title_row)

        # Media list
        self.media_list = QListWidget()
        self.media_list.setAlternatingRowColors(False)
        self.media_list.setSpacing(2)
        self.media_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.media_list)

        # Button row
        button_row = QHBoxLayout()

        self.download_selected_button = QPushButton("Download Selected")
        self.download_selected_button.clicked.connect(self._on_download_selected)
        button_row.addWidget(self.download_selected_button)

        self.download_all_button = QPushButton("Download All")
        self.download_all_button.clicked.connect(self._on_download_all)
        button_row.addWidget(self.download_all_button)

        layout.addLayout(button_row)

        return panel

    def _setup_status_bar(self) -> None:
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self) -> None:
        """Connect internal signals to handlers."""
        # URL input enter key
        self.url_input.returnPressed.connect(self._on_go_clicked)

        # Go button
        self.go_button.clicked.connect(self._on_go_clicked)

        # New tab button
        self.new_tab_button.clicked.connect(self._on_new_tab_clicked)

    def _on_go_clicked(self) -> None:
        """Handle Go button click."""
        url = self.url_input.text().strip()
        if url:
            # Add protocol if missing
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            self.signal_navigate.emit(url)
            self.on_log(f"[NAV] Navigating to: {url}")

    def _on_new_tab_clicked(self) -> None:
        """Handle New Tab button click."""
        url = self.url_input.text().strip()
        if url:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
        else:
            url = "about:blank"
        self.signal_create_tab.emit(url)
        self.on_log(f"[TAB] Creating new tab: {url}")

    def _on_download_selected(self) -> None:
        """Download selected media items."""
        for item in self.media_list.selectedItems():
            widget = self.media_list.itemWidget(item)
            if isinstance(widget, MediaItemWidget):
                self.signal_start_download.emit(widget.url)
                self.on_log(f"[DL] Starting download: {widget.url}")

    def _on_download_all(self) -> None:
        """Download all media items."""
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            widget = self.media_list.itemWidget(item)
            if isinstance(widget, MediaItemWidget):
                self.signal_start_download.emit(widget.url)
        self.on_log(f"[DL] Starting download of {self.media_list.count()} items")

    def _update_media_count(self) -> None:
        """Update the media count label."""
        count = self.media_list.count()
        self.media_count_label.setText(f"({count})")

    # =========================================================================
    # Public Slots - Called by other components
    # =========================================================================

    @Slot(str, str)
    def on_tab_created(self, tab_id: str, url: str) -> None:
        """
        Handle new tab creation.

        Args:
            tab_id: Unique identifier for the tab
            url: URL loaded in the tab
        """
        # Create task item widget
        task_widget = TaskItemWidget(tab_id, url)
        task_widget.signal_inspect.connect(
            lambda tid=tab_id: self.signal_toggle_browse.emit(tid)
        )
        task_widget.signal_close.connect(
            lambda tid=tab_id: self._on_task_close(tid)
        )

        # Add to list
        item = QListWidgetItem(self.task_list)
        item.setSizeHint(task_widget.sizeHint())
        item.setData(Qt.ItemDataRole.UserRole, tab_id)
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, task_widget)

        self.on_log(f"[TAB] Tab created: {tab_id}")
        self.status_bar.showMessage(f"Tab created: {url}")

    @Slot(str, str)
    def on_tab_updated(self, tab_id: str, state: str) -> None:
        """
        Handle tab state update.

        Args:
            tab_id: Unique identifier for the tab
            state: New state of the tab
        """
        # Find and update the task widget
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == tab_id:
                widget = self.task_list.itemWidget(item)
                if isinstance(widget, TaskItemWidget):
                    widget.set_state(state)
                break

        self.on_log(f"[TAB] Tab {tab_id} state: {state}")

    @Slot(str)
    def on_log(self, message: str) -> None:
        """
        Append message to log area.

        Args:
            message: Log message to display
        """
        self.log_area.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @Slot(str, str)
    def on_media_detected(self, url: str, media_type: str) -> None:
        """
        Handle detected media URL.

        Args:
            url: Media URL
            media_type: Type of media (video, audio, etc.)
        """
        # Check for duplicates
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            widget = self.media_list.itemWidget(item)
            if isinstance(widget, MediaItemWidget) and widget.url == url:
                return  # Skip duplicate

        # Create media item widget
        media_widget = MediaItemWidget(url, media_type)
        media_widget.signal_download.connect(
            lambda u=url: self.signal_start_download.emit(u)
        )

        # Add to list
        item = QListWidgetItem(self.media_list)
        item.setSizeHint(media_widget.sizeHint())
        self.media_list.addItem(item)
        self.media_list.setItemWidget(item, media_widget)

        self._update_media_count()
        self.on_log(f"[MEDIA] Detected {media_type}: {url[:60]}...")
        self.status_bar.showMessage(f"Media detected: {media_type}")

    @Slot(float)
    def on_download_progress(self, progress: float) -> None:
        """
        Update download progress.

        Args:
            progress: Progress value (0.0 to 1.0)
        """
        percent = int(progress * 100)
        self.progress_bar.setValue(percent)
        self.status_bar.showMessage(f"Downloading... {percent}%")

    @Slot(str)
    def on_download_complete(self, path: str) -> None:
        """
        Handle download completion.

        Args:
            path: Path where the file was saved
        """
        self.progress_bar.setValue(100)
        self.on_log(f"[DL] Download complete: {path}")
        self.status_bar.showMessage(f"Downloaded: {path}")

        # Reset progress after a short delay
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.progress_bar.setValue(0))

    def _on_task_close(self, tab_id: str) -> None:
        """Handle task close request."""
        # Remove from list
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == tab_id:
                self.task_list.takeItem(i)
                break

        # Emit close signal
        self.signal_close_tab.emit(tab_id)
        self.on_log(f"[TAB] Tab closed: {tab_id}")

    # =========================================================================
    # Public Methods
    # =========================================================================

    def clear_media_list(self) -> None:
        """Clear all items from the media list."""
        self.media_list.clear()
        self._update_media_count()

    def set_url(self, url: str) -> None:
        """Set the URL in the input field."""
        self.url_input.setText(url)

    def get_url(self) -> str:
        """Get the current URL from the input field."""
        return self.url_input.text().strip()
