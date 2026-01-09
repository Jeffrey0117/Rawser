from dataclasses import dataclass
from enum import Enum
from typing import List, Callable, Optional
from playwright.async_api import Page, Response

class MediaType(Enum):
    MP4 = "mp4"
    M3U8 = "m3u8"
    MPD = "mpd"
    UNKNOWN = "unknown"

@dataclass
class MediaURL:
    url: str
    media_type: MediaType
    headers: dict
    content_length: Optional[int] = None

class Interceptor:
    def __init__(self):
        self.media_urls: List[MediaURL] = []
        self._on_media_callback: Optional[Callable] = None

    def set_callback(self, callback: Callable[[MediaURL], None]):
        """設定偵測到 media 時的 callback"""
        self._on_media_callback = callback

    async def attach(self, page: Page):
        """附加到 Page，開始攔截"""
        page.on("response", self._on_response)

    async def detach(self, page: Page):
        """從 Page 分離"""
        page.remove_listener("response", self._on_response)

    async def _on_response(self, response: Response):
        """處理每個 response"""
        url = response.url
        content_type = response.headers.get('content-type', '')

        media_type = self._detect_media_type(url, content_type)
        if media_type != MediaType.UNKNOWN:
            media = MediaURL(
                url=url,
                media_type=media_type,
                headers=dict(response.request.headers),
                content_length=int(response.headers.get('content-length', 0)) or None
            )
            self.media_urls.append(media)
            if self._on_media_callback:
                self._on_media_callback(media)

    def _detect_media_type(self, url: str, content_type: str) -> MediaType:
        """偵測 media 類型"""
        url_lower = url.lower()

        # 檢查 URL
        if '.mp4' in url_lower or 'video/mp4' in content_type:
            return MediaType.MP4
        if '.m3u8' in url_lower or 'application/vnd.apple.mpegurl' in content_type:
            return MediaType.M3U8
        if '.mpd' in url_lower or 'application/dash+xml' in content_type:
            return MediaType.MPD

        return MediaType.UNKNOWN

    def clear(self):
        """清除收集的 URL"""
        self.media_urls.clear()
