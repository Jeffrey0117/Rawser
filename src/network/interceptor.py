"""
Media URL Interceptor - 使用 Qt WebEngine 攔截機制
"""
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from typing import List, Callable, Optional
from enum import Enum
from dataclasses import dataclass


class MediaType(Enum):
    MP4 = "mp4"
    M3U8 = "m3u8"
    MPD = "mpd"
    WEBM = "webm"
    AUDIO = "audio"
    UNKNOWN = "unknown"


@dataclass
class MediaURL:
    url: str
    media_type: MediaType
    headers: dict
    content_length: Optional[int] = None


class MediaInterceptor(QWebEngineUrlRequestInterceptor):
    """攔截並偵測 media URL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.media_urls: List[MediaURL] = []
        self._callback: Optional[Callable[[MediaURL], None]] = None

        # Media 檔案副檔名
        self._media_extensions = {
            '.mp4': MediaType.MP4,
            '.m3u8': MediaType.M3U8,
            '.mpd': MediaType.MPD,
            '.webm': MediaType.WEBM,
            '.mp3': MediaType.AUDIO,
            '.m4a': MediaType.AUDIO,
            '.aac': MediaType.AUDIO,
            '.ts': MediaType.M3U8,
        }

    def set_callback(self, callback: Callable[[MediaURL], None]):
        """設定發現 media 時的 callback"""
        self._callback = callback

    def interceptRequest(self, info):
        """Qt WebEngine 會呼叫這個方法攔截每個請求"""
        url = info.requestUrl().toString()

        # 檢查是否為 media URL
        media_type = self._detect_media_type(url)
        if media_type != MediaType.UNKNOWN:
            media = MediaURL(
                url=url,
                media_type=media_type,
                headers={}
            )

            # 避免重複
            if not any(m.url == url for m in self.media_urls):
                self.media_urls.append(media)
                if self._callback:
                    self._callback(media)

    def _detect_media_type(self, url: str) -> MediaType:
        """偵測 URL 的 media 類型"""
        url_lower = url.lower()

        # 過濾掉常見的非 media URL
        skip_patterns = [
            'google', 'facebook', 'analytics', 'tracking',
            'advertisement', 'beacon', '.js', '.css', '.png',
            '.jpg', '.gif', '.svg', '.ico', '.woff', '.ttf'
        ]
        if any(skip in url_lower for skip in skip_patterns):
            return MediaType.UNKNOWN

        # 檢查副檔名
        for ext, media_type in self._media_extensions.items():
            if ext in url_lower:
                return media_type

        # 檢查 URL 中的關鍵字
        if 'm3u8' in url_lower or 'manifest' in url_lower:
            return MediaType.M3U8
        if '.mpd' in url_lower or 'dash' in url_lower:
            return MediaType.MPD

        return MediaType.UNKNOWN

    def clear(self):
        """清除已收集的 media URLs"""
        self.media_urls.clear()

    def get_all(self) -> List[MediaURL]:
        """取得所有已偵測到的 media URLs"""
        return self.media_urls.copy()


# 為了相容性保留舊的類名
Interceptor = MediaInterceptor
