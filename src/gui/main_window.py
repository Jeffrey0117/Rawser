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
from PySide6.QtGui import QFont, QColor, QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView

from src.gui.widgets import TaskItemWidget, MediaItemWidget
from src.gui.history_popup import HistoryPopup, HistoryItem, LongPressButton


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
        self._history_thumbnails: Dict[str, Dict[str, QPixmap]] = {}  # tab_id -> {url: thumbnail}
        self._setup_ui()
        self._setup_history_popup()
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

        # Back button (支援長按)
        self.back_button = LongPressButton("←")
        self.back_button.setFixedWidth(36)
        self.back_button.setToolTip("Back (long press for history)")
        self.back_button.clicked.connect(self._on_back)
        self.back_button.long_pressed.connect(self._on_back_long_press)
        layout.addWidget(self.back_button)

        # Forward button (支援長按)
        self.forward_button = LongPressButton("→")
        self.forward_button.setFixedWidth(36)
        self.forward_button.setToolTip("Forward (long press for history)")
        self.forward_button.clicked.connect(self._on_forward)
        self.forward_button.long_pressed.connect(self._on_forward_long_press)
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

    def _setup_history_popup(self) -> None:
        """Setup history popup for back/forward buttons."""
        self.history_popup = HistoryPopup(self)
        self.history_popup.history_selected.connect(self._on_history_selected)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.url_input.returnPressed.connect(self._on_go_clicked)
        self.go_button.clicked.connect(self._on_go_clicked)
        self.new_tab_button.clicked.connect(self._on_new_tab_clicked)

    # =========================================================================
    # Navigation handlers
    # =========================================================================

    def _on_go_clicked(self) -> None:
        """Handle Go button click - navigate in current tab."""
        url = self.url_input.text().strip()
        if not url:
            return

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # 如果有當前 Tab，直接在當前 Tab 導航
        if self._current_tab_id and self._current_tab_id in self._webviews:
            self._webviews[self._current_tab_id].setUrl(QUrl(url))
        else:
            # 沒有 Tab，建立新的
            self.signal_create_tab.emit(url)

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

    def _on_back_long_press(self) -> None:
        """Handle long press on back button - show history."""
        self._show_history_popup(back=True)

    def _on_forward_long_press(self) -> None:
        """Handle long press on forward button - show forward history."""
        self._show_history_popup(back=False)

    def _show_history_popup(self, back: bool = True) -> None:
        """Show history popup with thumbnails."""
        if not self._current_tab_id or self._current_tab_id not in self._webviews:
            return

        view = self._webviews[self._current_tab_id]
        history = view.history()

        items = []
        current_index = history.currentItemIndex()

        if back:
            # 顯示返回歷史 (當前頁面之前的)
            for i in range(current_index - 1, max(current_index - 10, -1), -1):
                hist_item = history.itemAt(i)
                if hist_item.isValid():
                    url = hist_item.url().toString()
                    title = hist_item.title() or url
                    # 取得縮圖（如果有）
                    thumbnail = self._get_thumbnail(self._current_tab_id, url)
                    items.append(HistoryItem(
                        url=url,
                        title=title,
                        thumbnail=thumbnail,
                        index=i - current_index  # 負數表示要回退幾步
                    ))
            anchor = self.back_button
        else:
            # 顯示前進歷史 (當前頁面之後的)
            for i in range(current_index + 1, min(current_index + 10, history.count())):
                hist_item = history.itemAt(i)
                if hist_item.isValid():
                    url = hist_item.url().toString()
                    title = hist_item.title() or url
                    thumbnail = self._get_thumbnail(self._current_tab_id, url)
                    items.append(HistoryItem(
                        url=url,
                        title=title,
                        thumbnail=thumbnail,
                        index=i - current_index  # 正數表示要前進幾步
                    ))
            anchor = self.forward_button

        if items:
            self.history_popup.show_history(items, anchor)
        else:
            self.status_bar.showMessage("No history available")

    def _on_history_selected(self, steps: int) -> None:
        """Handle history item selection."""
        if not self._current_tab_id or self._current_tab_id not in self._webviews:
            return

        view = self._webviews[self._current_tab_id]
        history = view.history()

        # 計算目標 index
        target_index = history.currentItemIndex() + steps
        if 0 <= target_index < history.count():
            history.goToItem(history.itemAt(target_index))

    def _get_thumbnail(self, tab_id: str, url: str) -> Optional[QPixmap]:
        """Get cached thumbnail for URL."""
        if tab_id in self._history_thumbnails:
            return self._history_thumbnails[tab_id].get(url)
        return None

    def _capture_thumbnail(self, tab_id: str) -> None:
        """Capture thumbnail of current page."""
        if tab_id not in self._webviews:
            return

        view = self._webviews[tab_id]
        url = view.url().toString()

        if not url or url == "about:blank":
            return

        # 初始化 tab 的縮圖快取
        if tab_id not in self._history_thumbnails:
            self._history_thumbnails[tab_id] = {}

        # 截圖
        pixmap = view.grab()
        if not pixmap.isNull():
            # 縮小尺寸節省記憶體
            scaled = pixmap.scaled(
                320, 180,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._history_thumbnails[tab_id][url] = scaled

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

        # 設定深色背景避免載入時閃白
        webview.setStyleSheet("background-color: #1e1e1e;")
        webview.page().setBackgroundColor(QColor("#1e1e1e"))

        # 連接信號
        webview.urlChanged.connect(lambda qurl: self._on_url_changed(tab_id, qurl))
        webview.loadStarted.connect(lambda: self._on_load_started(tab_id))
        webview.loadProgress.connect(lambda p: self._on_load_progress(tab_id, p))
        webview.loadFinished.connect(lambda ok: self._on_load_finished(tab_id, ok))

        self._webviews[tab_id] = webview
        self.browser_stack.addWidget(webview)
        self.browser_stack.setCurrentWidget(webview)
        self._current_tab_id = tab_id

        # 開始載入
        webview.setUrl(QUrl(url))

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

    def _on_load_started(self, tab_id: str) -> None:
        """Handle page load started."""
        if tab_id == self._current_tab_id:
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.status_bar.showMessage("Loading...")

    def _on_load_progress(self, tab_id: str, progress: int) -> None:
        """Handle page load progress."""
        if tab_id == self._current_tab_id:
            self.progress_bar.setValue(progress)

    def _on_load_finished(self, tab_id: str, ok: bool) -> None:
        """Handle page load finished."""
        if tab_id == self._current_tab_id:
            self.progress_bar.setValue(100)
            # 載入完成後隱藏進度條
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self.progress_bar.setValue(0))

        status = "loaded" if ok else "failed"
        self.status_bar.showMessage(f"Page {status}")
        self.on_log(f"[NAV] Page {status}: {tab_id}")

        # 載入成功後截圖（延遲一點確保頁面渲染完成）
        if ok:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(800, lambda: self._capture_thumbnail(tab_id))

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
