from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from typing import Dict, Optional


class BrowserEngine(QObject):
    """Qt WebEngine 管理器"""

    # Signals
    signal_page_loaded = Signal(str, str)  # tab_id, url
    signal_page_error = Signal(str, str)  # tab_id, error

    def __init__(self):
        super().__init__()
        self._profile = QWebEngineProfile.defaultProfile()
        self._views: Dict[str, QWebEngineView] = {}
        self._current_tab_id: Optional[str] = None

    def create_view(self, tab_id: str) -> QWebEngineView:
        """建立新的 WebEngineView"""
        view = QWebEngineView()
        page = QWebEnginePage(self._profile, view)
        view.setPage(page)

        # 連接信號
        view.loadFinished.connect(lambda ok: self._on_load_finished(tab_id, ok))
        view.urlChanged.connect(lambda url: self._on_url_changed(tab_id, url))

        self._views[tab_id] = view
        return view

    def get_view(self, tab_id: str) -> Optional[QWebEngineView]:
        return self._views.get(tab_id)

    def close_view(self, tab_id: str):
        if tab_id in self._views:
            view = self._views.pop(tab_id)
            view.deleteLater()

    def navigate(self, tab_id: str, url: str):
        view = self.get_view(tab_id)
        if view:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            view.setUrl(QUrl(url))

    def go_back(self, tab_id: str):
        view = self.get_view(tab_id)
        if view:
            view.back()

    def go_forward(self, tab_id: str):
        view = self.get_view(tab_id)
        if view:
            view.forward()

    def refresh(self, tab_id: str):
        view = self.get_view(tab_id)
        if view:
            view.reload()

    def _on_load_finished(self, tab_id: str, ok: bool):
        view = self.get_view(tab_id)
        if view:
            url = view.url().toString()
            if ok:
                self.signal_page_loaded.emit(tab_id, url)
            else:
                self.signal_page_error.emit(tab_id, "Load failed")

    def _on_url_changed(self, tab_id: str, url: QUrl):
        pass  # 可用於更新 URL 欄

    @property
    def profile(self) -> QWebEngineProfile:
        return self._profile
