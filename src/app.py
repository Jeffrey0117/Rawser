"""
Rawser Application - 整合層
連接 GUI、Controller、Engine、Network、Downloader
"""
import asyncio
from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot

from .controller.tab_manager import TabManager, Tab
from .controller.state import TabState
from .engine.browser import BrowserEngine
from .network.interceptor import Interceptor, MediaURL
from .downloader.downloader import Downloader


class RawserApp(QObject):
    """Rawser 應用程式核心，整合所有模組"""

    # 發送給 GUI 的 Signal
    signal_tab_created = Signal(str, str)  # tab_id, url
    signal_tab_updated = Signal(str, str)  # tab_id, state
    signal_log = Signal(str)  # message
    signal_media_detected = Signal(str, str)  # url, media_type
    signal_download_progress = Signal(float)  # progress (0-1)
    signal_download_complete = Signal(str)  # file_path

    def __init__(self):
        super().__init__()
        self.tab_manager = TabManager()
        self.engine = BrowserEngine()
        self.interceptor = Interceptor()
        self.downloader = Downloader()

        # 設定 callback
        self.interceptor.set_callback(self._on_media_found)
        self.downloader.set_progress_callback(self._on_progress)
        self.downloader.set_complete_callback(self._on_complete)

        self._current_tab_id: Optional[str] = None

    async def start(self):
        """啟動應用程式"""
        self.signal_log.emit("[Rawser] Starting browser engine...")
        await self.engine.start(headless=False)
        self.signal_log.emit("[Rawser] Browser engine started")

    async def stop(self):
        """停止應用程式"""
        self.signal_log.emit("[Rawser] Stopping...")
        # 關閉所有 tab
        for tab in self.tab_manager.list_tabs():
            await self.tab_manager.close_tab(tab.id)
        await self.engine.stop()
        self.signal_log.emit("[Rawser] Stopped")

    @Slot(str)
    def on_create_tab(self, url: str):
        """建立新任務"""
        asyncio.create_task(self._create_tab_async(url))

    async def _create_tab_async(self, url: str):
        """非同步建立 Tab"""
        try:
            self.signal_log.emit(f"[Tab] Creating tab for: {url}")

            # 建立 context
            context = await self.engine.create_context()
            tab = self.tab_manager.create_tab(url, context)
            self._current_tab_id = tab.id

            self.signal_tab_created.emit(tab.id, url)
            self.signal_log.emit(f"[Tab] Created: {tab.id}")

            # 建立 page 並監聽關閉事件
            tab.page = await self.engine.create_page(tab.context)
            await self.interceptor.attach(tab.page)
            tab.page.on("close", lambda: self._on_page_closed(tab.id))

            # 導航到 URL
            if url:
                await self.engine.navigate(tab.page, url)

            self.tab_manager.update_state(tab.id, TabState.BROWSING)
            self.signal_tab_updated.emit(tab.id, TabState.BROWSING.value)

        except Exception as e:
            self.signal_log.emit(f"[Error] Failed to create tab: {e}")

    @Slot(str)
    def on_navigate(self, url: str):
        """導航到 URL（使用當前 tab）"""
        if self._current_tab_id:
            asyncio.create_task(self._navigate_async(self._current_tab_id, url))
        else:
            # 沒有 tab，建立新的
            self.on_create_tab(url)

    async def _navigate_async(self, tab_id: str, url: str):
        """非同步導航"""
        tab = self.tab_manager.get_tab(tab_id)
        if not tab:
            # 沒有 tab，建立新的
            self.on_create_tab(url)
            return

        try:
            self.signal_log.emit(f"[Nav] Navigating to: {url}")
            self.tab_manager.update_state(tab_id, TabState.ACTIVE)
            self.signal_tab_updated.emit(tab_id, TabState.ACTIVE.value)

            # 檢查 page 是否還活著，如果被關閉就重新建立
            if not tab.page or tab.page.is_closed():
                self.signal_log.emit(f"[Nav] Creating new page...")
                tab.page = await self.engine.create_page(tab.context)
                await self.interceptor.attach(tab.page)
                # 監聽 page 關閉事件
                tab.page.on("close", lambda: self._on_page_closed(tab_id))

            tab.url = url
            await self.engine.navigate(tab.page, url)

            self.tab_manager.update_state(tab_id, TabState.BROWSING)
            self.signal_tab_updated.emit(tab_id, TabState.BROWSING.value)
            self.signal_log.emit(f"[Nav] Loaded: {url}")

        except Exception as e:
            self.signal_log.emit(f"[Error] Navigation failed: {e}")
            # Page 可能已經關閉，清理狀態
            self.tab_manager.set_page(tab_id, None)
            self.tab_manager.update_state(tab_id, TabState.IDLE)
            self.signal_tab_updated.emit(tab_id, TabState.IDLE.value)

    @Slot(str)
    def on_toggle_browse(self, tab_id: str):
        """切換瀏覽模式"""
        asyncio.create_task(self._toggle_browse_async(tab_id))

    async def _toggle_browse_async(self, tab_id: str):
        """非同步切換瀏覽模式"""
        tab = self.tab_manager.get_tab(tab_id)
        if not tab:
            return

        if tab.state == TabState.BROWSING and tab.page:
            # 關閉瀏覽模式
            await self._detach_page(tab_id)
        else:
            # 開啟瀏覽模式
            await self._browse_tab(tab_id)

    def _on_page_closed(self, tab_id: str):
        """當 Page 被手動關閉時的處理"""
        self.signal_log.emit(f"[Page] Closed by user: {tab_id}")
        self.tab_manager.set_page(tab_id, None)
        self.tab_manager.update_state(tab_id, TabState.IDLE)
        self.signal_tab_updated.emit(tab_id, TabState.IDLE.value)

    async def _browse_tab(self, tab_id: str):
        """開啟瀏覽模式"""
        tab = self.tab_manager.get_tab(tab_id)
        if not tab:
            return

        try:
            self.signal_log.emit(f"[Browse] Opening page for tab: {tab_id}")

            # 檢查 page 是否還活著
            if not tab.page or tab.page.is_closed():
                tab.page = await self.engine.create_page(tab.context)
                await self.interceptor.attach(tab.page)
                # 監聽 page 關閉事件
                tab.page.on("close", lambda: self._on_page_closed(tab_id))

            if tab.url:
                await self.engine.navigate(tab.page, tab.url)

            self.tab_manager.update_state(tab_id, TabState.BROWSING)
            self.signal_tab_updated.emit(tab_id, TabState.BROWSING.value)

        except Exception as e:
            self.signal_log.emit(f"[Error] Browse failed: {e}")

    async def _detach_page(self, tab_id: str):
        """關閉 Page 但保留 session"""
        tab = self.tab_manager.get_tab(tab_id)
        if not tab or not tab.page:
            return

        try:
            self.signal_log.emit(f"[Detach] Closing page for tab: {tab_id}")
            await self.interceptor.detach(tab.page)
            await self.engine.close_page(tab.page)
            self.tab_manager.set_page(tab_id, None)
            self.tab_manager.update_state(tab_id, TabState.IDLE)
            self.signal_tab_updated.emit(tab_id, TabState.IDLE.value)

        except Exception as e:
            self.signal_log.emit(f"[Error] Detach failed: {e}")

    @Slot(str)
    def on_close_tab(self, tab_id: str):
        """關閉 Tab"""
        asyncio.create_task(self._close_tab_async(tab_id))

    async def _close_tab_async(self, tab_id: str):
        """非同步關閉 Tab"""
        try:
            self.signal_log.emit(f"[Tab] Closing: {tab_id}")
            await self.tab_manager.close_tab(tab_id)

            if self._current_tab_id == tab_id:
                tabs = self.tab_manager.list_tabs()
                self._current_tab_id = tabs[0].id if tabs else None

            self.signal_log.emit(f"[Tab] Closed: {tab_id}")

        except Exception as e:
            self.signal_log.emit(f"[Error] Close tab failed: {e}")

    @Slot(str)
    def on_start_download(self, media_url: str):
        """開始下載"""
        asyncio.create_task(self._download_async(media_url))

    async def _download_async(self, url: str):
        """非同步下載"""
        try:
            self.signal_log.emit(f"[Download] Starting: {url}")

            # 找到對應的 MediaURL
            media = None
            for m in self.interceptor.media_urls:
                if m.url == url:
                    media = m
                    break

            if not media:
                # 建立簡單的 MediaURL
                from .network.interceptor import MediaType
                media = MediaURL(
                    url=url,
                    media_type=MediaType.MP4,
                    headers={}
                )

            task = await self.downloader.download(media)

            if task.completed:
                self.signal_log.emit(f"[Download] Completed: {task.path}")
            elif task.error:
                self.signal_log.emit(f"[Download] Failed: {task.error}")

        except Exception as e:
            self.signal_log.emit(f"[Error] Download failed: {e}")

    def _on_media_found(self, media: MediaURL):
        """Media 偵測到時的 callback"""
        self.signal_log.emit(f"[Media] Found: {media.media_type.value} - {media.url[:80]}...")
        self.signal_media_detected.emit(media.url, media.media_type.value)

    def _on_progress(self, task_id: str, progress: float):
        """下載進度 callback"""
        self.signal_download_progress.emit(progress)

    def _on_complete(self, task_id: str, path: str):
        """下載完成 callback"""
        self.signal_download_complete.emit(path)
