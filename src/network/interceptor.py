"""
Media URL Interceptor - Handler Chain 模式
參考 facebooc 的 Handler Chain 設計
"""
from abc import ABC, abstractmethod
from PySide6.QtWebEngineCore import (
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
    QWebEngineProfile,
)
from PySide6.QtNetwork import QNetworkCookie
from PySide6.QtCore import QUrl
from typing import List, Callable, Optional, Dict
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse


class MediaType(Enum):
    MP4 = "mp4"
    M3U8 = "m3u8"
    MPD = "mpd"
    WEBM = "webm"
    AUDIO = "audio"
    UNKNOWN = "unknown"


@dataclass
class MediaURL:
    """Media URL 資訊 - 包含完整的 Request 資訊"""
    url: str
    media_type: MediaType
    headers: Dict[str, str] = field(default_factory=dict)
    referrer: str = ""
    method: str = "GET"
    content_type: str = ""
    content_length: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)

    # 額外的請求資訊
    first_party_url: str = ""  # 發起請求的頁面
    resource_type: str = ""    # 資源類型


# =============================================================================
# Handler Chain 模式 - 參考 facebooc 設計
# =============================================================================

class MediaHandler(ABC):
    """Media Handler 基類 - Chain of Responsibility 模式"""

    def __init__(self):
        self._next: Optional['MediaHandler'] = None

    def set_next(self, handler: 'MediaHandler') -> 'MediaHandler':
        """設定下一個 handler，返回下一個以便鏈式呼叫"""
        self._next = handler
        return handler

    def handle(self, url: str, info: QWebEngineUrlRequestInfo) -> Optional[MediaURL]:
        """
        處理請求，如果是自己負責的類型就處理，否則傳給下一個
        """
        result = self._try_handle(url, info)
        if result:
            return result

        # 傳給下一個 handler
        if self._next:
            return self._next.handle(url, info)

        return None

    @abstractmethod
    def _try_handle(self, url: str, info: QWebEngineUrlRequestInfo) -> Optional[MediaURL]:
        """子類實作：嘗試處理這個 URL"""
        pass

    def _extract_headers(self, info: QWebEngineUrlRequestInfo) -> Dict[str, str]:
        """從 QWebEngineUrlRequestInfo 提取 Headers"""
        headers = {}

        # Qt WebEngine 可用的 header 資訊有限
        # 但我們可以取得一些重要的
        referrer = info.firstPartyUrl().toString()
        if referrer:
            headers['Referer'] = referrer

        # 設定常見的瀏覽器 headers
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        headers['Accept'] = '*/*'
        headers['Accept-Language'] = 'en-US,en;q=0.9'
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        headers['Connection'] = 'keep-alive'

        return headers

    def _create_media_url(
        self,
        url: str,
        media_type: MediaType,
        info: QWebEngineUrlRequestInfo
    ) -> MediaURL:
        """建立 MediaURL 物件，包含完整資訊"""
        headers = self._extract_headers(info)

        return MediaURL(
            url=url,
            media_type=media_type,
            headers=headers,
            referrer=info.firstPartyUrl().toString(),
            method=info.requestMethod().data().decode('utf-8', errors='ignore'),
            first_party_url=info.firstPartyUrl().toString(),
            resource_type=str(info.resourceType())
        )


class MP4Handler(MediaHandler):
    """處理 MP4 / MOV 影片"""

    # 支援的副檔名
    VIDEO_EXTENSIONS = ['.mp4', '.mov', '.m4v']

    def _try_handle(self, url: str, info: QWebEngineUrlRequestInfo) -> Optional[MediaURL]:
        url_lower = url.lower()

        # 檢查副檔名
        for ext in self.VIDEO_EXTENSIONS:
            if ext in url_lower:
                # 過濾掉廣告和追蹤
                if self._is_valid_media_url(url_lower):
                    return self._create_media_url(url, MediaType.MP4, info)

        # 檢查 content-type 暗示
        if 'video/mp4' in url_lower or 'video/quicktime' in url_lower:
            return self._create_media_url(url, MediaType.MP4, info)

        return None

    def _is_valid_media_url(self, url: str) -> bool:
        """檢查是否為有效的 media URL（非廣告/追蹤）"""
        invalid_patterns = [
            'googleads', 'doubleclick', 'facebook.com/tr',
            'analytics', 'tracking', 'beacon', 'pixel'
        ]
        return not any(p in url for p in invalid_patterns)


class M3U8Handler(MediaHandler):
    """處理 M3U8 串流 (HLS)"""

    def _try_handle(self, url: str, info: QWebEngineUrlRequestInfo) -> Optional[MediaURL]:
        url_lower = url.lower()

        # M3U8 播放列表
        if '.m3u8' in url_lower:
            return self._create_media_url(url, MediaType.M3U8, info)

        # HLS manifest
        if 'manifest' in url_lower and ('m3u8' in url_lower or 'hls' in url_lower):
            return self._create_media_url(url, MediaType.M3U8, info)

        # .ts 片段（通常伴隨 m3u8）
        if '.ts' in url_lower and ('seg' in url_lower or 'chunk' in url_lower or 'fragment' in url_lower):
            # 注意：.ts 片段通常不需要單獨下載，m3u8 會包含它們
            pass

        return None


class MPDHandler(MediaHandler):
    """處理 MPD 串流 (DASH)"""

    def _try_handle(self, url: str, info: QWebEngineUrlRequestInfo) -> Optional[MediaURL]:
        url_lower = url.lower()

        # DASH manifest
        if '.mpd' in url_lower:
            return self._create_media_url(url, MediaType.MPD, info)

        # DASH 關鍵字
        if 'dash' in url_lower and 'manifest' in url_lower:
            return self._create_media_url(url, MediaType.MPD, info)

        return None


class WebMHandler(MediaHandler):
    """處理 WebM 影片"""

    def _try_handle(self, url: str, info: QWebEngineUrlRequestInfo) -> Optional[MediaURL]:
        url_lower = url.lower()

        if '.webm' in url_lower:
            if self._is_valid_media_url(url_lower):
                return self._create_media_url(url, MediaType.WEBM, info)

        return None

    def _is_valid_media_url(self, url: str) -> bool:
        invalid_patterns = ['googleads', 'doubleclick', 'analytics']
        return not any(p in url for p in invalid_patterns)


class AudioHandler(MediaHandler):
    """處理音訊檔案"""

    AUDIO_EXTENSIONS = ['.mp3', '.m4a', '.aac', '.ogg', '.wav', '.flac']

    def _try_handle(self, url: str, info: QWebEngineUrlRequestInfo) -> Optional[MediaURL]:
        url_lower = url.lower()

        for ext in self.AUDIO_EXTENSIONS:
            if ext in url_lower:
                return self._create_media_url(url, MediaType.AUDIO, info)

        return None


class SkipHandler(MediaHandler):
    """
    過濾掉不需要的 URL（放在 chain 最前面）
    這樣可以快速跳過不相關的請求
    """

    SKIP_PATTERNS = [
        # 追蹤/分析
        'google-analytics', 'googletagmanager', 'facebook.com/tr',
        'doubleclick', 'googlesyndication', 'analytics',
        'tracking', 'beacon', 'pixel', 'telemetry',

        # 靜態資源
        '.js', '.css', '.woff', '.woff2', '.ttf', '.eot',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',

        # 其他
        'favicon', 'fonts.googleapis', 'fonts.gstatic'
    ]

    def _try_handle(self, url: str, info: QWebEngineUrlRequestInfo) -> Optional[MediaURL]:
        url_lower = url.lower()

        # 如果匹配到跳過模式，返回 None 且不傳給下一個 handler
        for pattern in self.SKIP_PATTERNS:
            if pattern in url_lower:
                # 返回特殊值表示「已處理但不是 media」
                return None

        # 不匹配跳過模式，傳給下一個 handler
        if self._next:
            return self._next.handle(url, info)

        return None


# =============================================================================
# Cookie 管理器 - 從 WebEngine 獲取真實 Cookies
# =============================================================================

class CookieManager:
    """
    管理從 Qt WebEngine 獲取的 Cookies

    Qt WebEngine 的 cookie store 是非同步的，
    我們需要收集 cookies 然後在下載時使用
    """

    def __init__(self):
        self._cookies: Dict[str, Dict[str, str]] = {}  # domain -> {name: value}
        self._cookie_store = None

    def setup(self, profile: QWebEngineProfile):
        """設定 cookie store 監聽"""
        self._cookie_store = profile.cookieStore()
        self._cookie_store.cookieAdded.connect(self._on_cookie_added)
        self._cookie_store.cookieRemoved.connect(self._on_cookie_removed)

    def _on_cookie_added(self, cookie: QNetworkCookie):
        """當 cookie 被添加時"""
        domain = cookie.domain()
        name = cookie.name().data().decode('utf-8', errors='ignore')
        value = cookie.value().data().decode('utf-8', errors='ignore')

        # 移除開頭的 . (如 .example.com -> example.com)
        if domain.startswith('.'):
            domain = domain[1:]

        if domain not in self._cookies:
            self._cookies[domain] = {}

        self._cookies[domain][name] = value

    def _on_cookie_removed(self, cookie: QNetworkCookie):
        """當 cookie 被移除時"""
        domain = cookie.domain()
        name = cookie.name().data().decode('utf-8', errors='ignore')

        if domain.startswith('.'):
            domain = domain[1:]

        if domain in self._cookies and name in self._cookies[domain]:
            del self._cookies[domain][name]

    def get_cookies_for_url(self, url: str) -> str:
        """
        取得特定 URL 的 cookies（格式化為 Cookie header）

        會匹配 domain 和其子域名
        例如：cookies for .youtube.com 會匹配 www.youtube.com
        """
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()

            matching_cookies = {}

            for domain, cookies in self._cookies.items():
                # 完全匹配或子域名匹配
                if host == domain or host.endswith('.' + domain):
                    matching_cookies.update(cookies)

            if matching_cookies:
                return '; '.join(f'{k}={v}' for k, v in matching_cookies.items())

        except Exception:
            pass

        return ''

    def get_all_cookies(self) -> Dict[str, Dict[str, str]]:
        """取得所有 cookies（用於 debug）"""
        return self._cookies.copy()


# =============================================================================
# 主要的 Interceptor 類
# =============================================================================

class MediaInterceptor(QWebEngineUrlRequestInterceptor):
    """
    Media URL 攔截器 - 使用 Handler Chain 模式

    Handler Chain:
    SkipHandler → MP4Handler → M3U8Handler → MPDHandler → WebMHandler → AudioHandler

    新增功能：
    - 自動收集瀏覽器的 Cookies
    - 下載時附帶真實的 Cookie header
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.media_urls: List[MediaURL] = []
        self._callback: Optional[Callable[[MediaURL], None]] = None
        self._seen_urls: set = set()  # 用於快速去重

        # Cookie 管理器
        self.cookie_manager = CookieManager()

        # 建立 Handler Chain
        self._handler_chain = self._build_handler_chain()

    def setup_cookie_tracking(self, profile: QWebEngineProfile):
        """設定 cookie 追蹤（需要在安裝 interceptor 後呼叫）"""
        self.cookie_manager.setup(profile)

    def _build_handler_chain(self) -> MediaHandler:
        """
        建立 Handler Chain
        順序：Skip → MP4 → M3U8 → MPD → WebM → Audio
        """
        skip = SkipHandler()
        mp4 = MP4Handler()
        m3u8 = M3U8Handler()
        mpd = MPDHandler()
        webm = WebMHandler()
        audio = AudioHandler()

        # 鏈接起來
        skip.set_next(mp4).set_next(m3u8).set_next(mpd).set_next(webm).set_next(audio)

        return skip

    def set_callback(self, callback: Callable[[MediaURL], None]):
        """設定發現 media 時的 callback"""
        self._callback = callback

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        """Qt WebEngine 會呼叫這個方法攔截每個請求"""
        url = info.requestUrl().toString()

        # 快速去重
        if url in self._seen_urls:
            return

        # 用 Handler Chain 處理
        media = self._handler_chain.handle(url, info)

        if media:
            # 附加 cookies 到 media headers
            cookies = self.cookie_manager.get_cookies_for_url(url)
            if cookies:
                media.headers['Cookie'] = cookies

            self._seen_urls.add(url)
            self.media_urls.append(media)

            if self._callback:
                self._callback(media)

    def clear(self):
        """清除已收集的 media URLs"""
        self.media_urls.clear()
        self._seen_urls.clear()

    def get_all(self) -> List[MediaURL]:
        """取得所有已偵測到的 media URLs"""
        return self.media_urls.copy()

    def get_by_type(self, media_type: MediaType) -> List[MediaURL]:
        """取得特定類型的 media URLs"""
        return [m for m in self.media_urls if m.media_type == media_type]

    def get_cookies_for_download(self, url: str) -> str:
        """取得下載用的 cookies"""
        return self.cookie_manager.get_cookies_for_url(url)


# 為了相容性保留舊的類名
Interceptor = MediaInterceptor
