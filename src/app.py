"""
Rawser Application - 整合層
使用 Qt WebEngine，GUI 直接管理 WebView
"""
import uuid
from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWebEngineCore import QWebEngineProfile

from .network.interceptor import MediaInterceptor, MediaURL
from .downloader.downloader import Downloader


class RawserApp(QObject):
    """Rawser 應用程式核心"""

    # 發送給 GUI 的 Signal
    signal_tab_created = Signal(str, str)  # tab_id, url
    signal_tab_updated = Signal(str, str)  # tab_id, state
    signal_log = Signal(str)  # message
    signal_media_detected = Signal(str, str)  # url, media_type
    signal_download_progress = Signal(float)  # progress (0-1)
    signal_download_complete = Signal(str)  # file_path

    def __init__(self):
        super().__init__()
        self.downloader = Downloader()
        self.interceptor = MediaInterceptor()

        # 設定 Interceptor callback
        self.interceptor.set_callback(self._on_media_found)

        # 設定 Downloader callback
        self.downloader.set_progress_callback(self._on_progress)
        self.downloader.set_complete_callback(self._on_complete)

        self._current_tab_id: Optional[str] = None

    def start(self):
        """啟動應用程式 - 設定 URL Interceptor"""
        self.signal_log.emit("[Rawser] Starting...")

        # 設定全域 URL 攔截器
        profile = QWebEngineProfile.defaultProfile()
        profile.setUrlRequestInterceptor(self.interceptor)

        self.signal_log.emit("[Rawser] URL Interceptor installed")
        self.signal_log.emit("[Rawser] Ready")

    def stop(self):
        """停止應用程式"""
        self.signal_log.emit("[Rawser] Stopping...")
        # 移除攔截器
        profile = QWebEngineProfile.defaultProfile()
        profile.setUrlRequestInterceptor(None)
        self.signal_log.emit("[Rawser] Stopped")

    @Slot(str)
    def on_create_tab(self, url: str):
        """建立新 Tab"""
        tab_id = str(uuid.uuid4())[:8]
        self._current_tab_id = tab_id
        self.signal_log.emit(f"[Tab] Creating: {tab_id} -> {url}")
        self.signal_tab_created.emit(tab_id, url)

    @Slot(str)
    def on_navigate(self, url: str):
        """導航到 URL"""
        if not self._current_tab_id:
            # 沒有 tab，建立新的
            self.on_create_tab(url)
        else:
            self.signal_log.emit(f"[Nav] {url}")

    @Slot(str)
    def on_close_tab(self, tab_id: str):
        """關閉 Tab"""
        self.signal_log.emit(f"[Tab] Closed: {tab_id}")
        if self._current_tab_id == tab_id:
            self._current_tab_id = None

    @Slot(str)
    def on_start_download(self, media_url: str):
        """開始下載"""
        import asyncio
        asyncio.create_task(self._download_async(media_url))

    async def _download_async(self, url: str):
        """非同步下載"""
        try:
            self.signal_log.emit(f"[Download] Starting: {url[:60]}...")

            # 找到對應的 MediaURL
            media = None
            for m in self.interceptor.media_urls:
                if m.url == url:
                    media = m
                    break

            if not media:
                from .network.interceptor import MediaType
                media = MediaURL(
                    url=url,
                    media_type=MediaType.MP4,
                    headers={}
                )

            task = await self.downloader.download(media)

            if task.completed:
                self.signal_log.emit(f"[Download] Completed: {task.path}")
                self.signal_download_complete.emit(str(task.path))
            elif task.error:
                self.signal_log.emit(f"[Download] Failed: {task.error}")

        except Exception as e:
            self.signal_log.emit(f"[Error] Download failed: {e}")

    def _on_media_found(self, media: MediaURL):
        """Media 偵測到時的 callback"""
        self.signal_log.emit(f"[Media] {media.media_type.value}: {media.url[:60]}...")
        self.signal_media_detected.emit(media.url, media.media_type.value)

    def _on_progress(self, task_id: str, progress: float):
        """下載進度 callback"""
        self.signal_download_progress.emit(progress)

    def _on_complete(self, task_id: str, path: str):
        """下載完成 callback"""
        self.signal_download_complete.emit(path)
