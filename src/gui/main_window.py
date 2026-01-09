"""
Main Window for Rawser application.
使用 Qt WebEngineView 嵌入瀏覽器。
"""
from typing import Optional, Dict

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
    QListWidgetItem,
    QStackedWidget,
)
from PySide6.QtCore import Qt, Signal, Slot, QUrl
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView

from src.gui.widgets import TaskItemWidget, MediaItemWidget


class MainWindow(QMainWindow):
    """
    Main application window for Rawser.

    Layout:
    ┌─────────────────────────────────────────────────┐
    │ [URL] [Go] [←] [→] [↻] [+]                      │
    ├────────────┬────────────────────────────────────┤
    │            │                                    │
    │   TASKS    │   QWebEngineView (瀏覽器)          │
    │            │                                    │
    ├────────────┼────────────────────────────────────┤
    │   MEDIA    │   LOG                              │
    │            │                                    │
    ├────────────┴────────────────────────────────────┤
    │ [狀態列] [進度條]                                │
    └─────────────────────────────────────────────────┘
    """

    # Signals
    signal_navigate = Signal(str)
    signal_create_tab = Signal(str)
    signal_close_tab = Signal(str)
    signal_start_download = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._webviews: Dict[str, QWebEngineView] = {}
        self._current_tab_id: Optional[str] = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("Rawser - Media Downloader")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Top bar
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        # Main content
        content_splitter = self._create_content_area()
        main_layout.addWidget(content_splitter, 1)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        main_layout.addWidget(self.progress_bar)

        # Status bar
        self._setup_status_bar()

    def _create_top_bar(self) -> QWidget:
        """Create the top navigation bar."""
        top_bar = QWidget()
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Back button
        self.back_button = QPushButton("←")
        self.back_button.setFixedWidth(36)
        self.back_button.setToolTip("Back")
        self.back_button.clicked.connect(self._on_back)
        layout.addWidget(self.back_button)

        # Forward button
        self.forward_button = QPushButton("→")
        self.forward_button.setFixedWidth(36)
        self.forward_button.setToolTip("Forward")
        self.forward_button.clicked.connect(self._on_forward)
        layout.addWidget(self.forward_button)

        # Refresh button
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setFixedWidth(36)
        self.refresh_button.setToolTip("Refresh")
        self.refresh_button.clicked.connect(self._on_refresh)
        layout.addWidget(self.refresh_button)

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL...")
        self.url_input.setClearButtonEnabled(True)
        layout.addWidget(self.url_input, 1)

        # Go button
        self.go_button = QPushButton("Go")
        self.go_button.setFixedWidth(60)
        layout.addWidget(self.go_button)

        # New Tab button
        self.new_tab_button = QPushButton("+")
        self.new_tab_button.setFixedWidth(36)
        self.new_tab_button.setToolTip("New Tab")
        layout.addWidget(self.new_tab_button)

        return top_bar

    def _create_content_area(self) -> QSplitter:
        """Create the main content area."""
        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel (Tasks + Media)
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)

        # Right panel (Browser + Log)
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        main_splitter.setSizes([280, 1000])
        return main_splitter

    def _create_left_panel(self) -> QWidget:
        """Create left panel with tasks and media."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Tasks section
        tasks_label = QLabel("TASKS")
        tasks_label.setObjectName("sectionTitle")
        layout.addWidget(tasks_label)

        self.task_list = QListWidget()
        self.task_list.setSpacing(2)
        self.task_list.itemClicked.connect(self._on_task_clicked)
        layout.addWidget(self.task_list)

        # Media section
        media_label = QLabel("MEDIA")
        media_label.setObjectName("sectionTitle")
        layout.addWidget(media_label)

        self.media_count_label = QLabel("(0)")
        self.media_count_label.setObjectName("sectionTitle")

        self.media_list = QListWidget()
        self.media_list.setSpacing(2)
        layout.addWidget(self.media_list)

        # Download buttons
        btn_layout = QHBoxLayout()
        self.download_selected_button = QPushButton("Download")
        self.download_selected_button.clicked.connect(self._on_download_selected)
        btn_layout.addWidget(self.download_selected_button)

        self.download_all_button = QPushButton("All")
        self.download_all_button.clicked.connect(self._on_download_all)
        btn_layout.addWidget(self.download_all_button)
        layout.addLayout(btn_layout)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create right panel with browser and log."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Vertical splitter: Browser | Log
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Browser stack (多個 WebView 堆疊)
        self.browser_stack = QStackedWidget()
        self.browser_stack.setMinimumHeight(400)
        splitter.addWidget(self.browser_stack)

        # Log area
        log_panel = QWidget()
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(4)

        log_label = QLabel("LOG")
        log_label.setObjectName("sectionTitle")
        log_layout.addWidget(log_label)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 10))
        self.log_area.setMaximumHeight(150)
        log_layout.addWidget(self.log_area)

        splitter.addWidget(log_panel)
        splitter.setSizes([600, 150])

        layout.addWidget(splitter)
        return panel

    def _setup_status_bar(self) -> None:
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.url_input.returnPressed.connect(self._on_go_clicked)
        self.go_button.clicked.connect(self._on_go_clicked)
        self.new_tab_button.clicked.connect(self._on_new_tab_clicked)

    # =========================================================================
    # Navigation handlers
    # =========================================================================

    def _on_go_clicked(self) -> None:
        """Handle Go button click."""
        url = self.url_input.text().strip()
        if url:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            self.signal_navigate.emit(url)

    def _on_new_tab_clicked(self) -> None:
        """Handle New Tab button click."""
        url = self.url_input.text().strip()
        if url:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
        else:
            url = "https://www.google.com"
        self.signal_create_tab.emit(url)

    def _on_back(self) -> None:
        """Go back in history."""
        if self._current_tab_id and self._current_tab_id in self._webviews:
            self._webviews[self._current_tab_id].back()

    def _on_forward(self) -> None:
        """Go forward in history."""
        if self._current_tab_id and self._current_tab_id in self._webviews:
            self._webviews[self._current_tab_id].forward()

    def _on_refresh(self) -> None:
        """Refresh current page."""
        if self._current_tab_id and self._current_tab_id in self._webviews:
            self._webviews[self._current_tab_id].reload()

    def _on_task_clicked(self, item: QListWidgetItem) -> None:
        """Switch to clicked tab."""
        tab_id = item.data(Qt.ItemDataRole.UserRole)
        if tab_id and tab_id in self._webviews:
            self._current_tab_id = tab_id
            view = self._webviews[tab_id]
            self.browser_stack.setCurrentWidget(view)
            self.url_input.setText(view.url().toString())

    def _on_download_selected(self) -> None:
        """Download selected media items."""
        for item in self.media_list.selectedItems():
            widget = self.media_list.itemWidget(item)
            if isinstance(widget, MediaItemWidget):
                self.signal_start_download.emit(widget.url)

    def _on_download_all(self) -> None:
        """Download all media items."""
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            widget = self.media_list.itemWidget(item)
            if isinstance(widget, MediaItemWidget):
                self.signal_start_download.emit(widget.url)

    # =========================================================================
    # Public Slots
    # =========================================================================

    @Slot(str, str)
    def on_tab_created(self, tab_id: str, url: str) -> None:
        """Handle new tab creation with WebEngineView."""
        # 建立 WebEngineView
        webview = QWebEngineView()
        webview.setUrl(QUrl(url))

        # URL 變更時更新輸入框
        webview.urlChanged.connect(lambda qurl: self._on_url_changed(tab_id, qurl))
        webview.loadFinished.connect(lambda ok: self._on_load_finished(tab_id, ok))

        self._webviews[tab_id] = webview
        self.browser_stack.addWidget(webview)
        self.browser_stack.setCurrentWidget(webview)
        self._current_tab_id = tab_id

        # 建立 Task item
        task_widget = TaskItemWidget(tab_id, url)
        task_widget.signal_close.connect(lambda tid=tab_id: self._on_task_close(tid))

        item = QListWidgetItem(self.task_list)
        item.setSizeHint(task_widget.sizeHint())
        item.setData(Qt.ItemDataRole.UserRole, tab_id)
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, task_widget)

        self.url_input.setText(url)
        self.on_log(f"[TAB] Created: {tab_id}")

    def _on_url_changed(self, tab_id: str, qurl: QUrl) -> None:
        """Handle URL change in webview."""
        if tab_id == self._current_tab_id:
            self.url_input.setText(qurl.toString())

    def _on_load_finished(self, tab_id: str, ok: bool) -> None:
        """Handle page load finished."""
        status = "loaded" if ok else "failed"
        self.on_log(f"[NAV] Page {status}: {tab_id}")

    @Slot(str, str)
    def on_tab_updated(self, tab_id: str, state: str) -> None:
        """Handle tab state update."""
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == tab_id:
                widget = self.task_list.itemWidget(item)
                if isinstance(widget, TaskItemWidget):
                    widget.set_state(state)
                break

    @Slot(str)
    def on_log(self, message: str) -> None:
        """Append message to log area."""
        self.log_area.append(message)
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @Slot(str, str)
    def on_media_detected(self, url: str, media_type: str) -> None:
        """Handle detected media URL."""
        # 檢查重複
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            widget = self.media_list.itemWidget(item)
            if isinstance(widget, MediaItemWidget) and widget.url == url:
                return

        media_widget = MediaItemWidget(url, media_type)
        media_widget.signal_download.connect(lambda u=url: self.signal_start_download.emit(u))

        item = QListWidgetItem(self.media_list)
        item.setSizeHint(media_widget.sizeHint())
        self.media_list.addItem(item)
        self.media_list.setItemWidget(item, media_widget)

        self.on_log(f"[MEDIA] {media_type}: {url[:60]}...")

    @Slot(float)
    def on_download_progress(self, progress: float) -> None:
        """Update download progress."""
        self.progress_bar.setValue(int(progress * 100))

    @Slot(str)
    def on_download_complete(self, path: str) -> None:
        """Handle download completion."""
        self.progress_bar.setValue(100)
        self.on_log(f"[DL] Complete: {path}")
        self.status_bar.showMessage(f"Downloaded: {path}")

    def _on_task_close(self, tab_id: str) -> None:
        """Handle task close."""
        # 移除 WebView
        if tab_id in self._webviews:
            view = self._webviews.pop(tab_id)
            self.browser_stack.removeWidget(view)
            view.deleteLater()

        # 移除 Task item
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == tab_id:
                self.task_list.takeItem(i)
                break

        # 切換到其他 tab
        if self._current_tab_id == tab_id:
            if self._webviews:
                self._current_tab_id = list(self._webviews.keys())[0]
                self.browser_stack.setCurrentWidget(self._webviews[self._current_tab_id])
            else:
                self._current_tab_id = None

        self.signal_close_tab.emit(tab_id)
        self.on_log(f"[TAB] Closed: {tab_id}")

    # =========================================================================
    # Public Methods
    # =========================================================================

    def get_webview(self, tab_id: str) -> Optional[QWebEngineView]:
        """Get WebEngineView by tab_id."""
        return self._webviews.get(tab_id)

    def get_current_webview(self) -> Optional[QWebEngineView]:
        """Get current active WebEngineView."""
        if self._current_tab_id:
            return self._webviews.get(self._current_tab_id)
        return None

    def navigate_current(self, url: str) -> None:
        """Navigate current tab to URL."""
        view = self.get_current_webview()
        if view:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            view.setUrl(QUrl(url))
            self.url_input.setText(url)
