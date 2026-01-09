from enum import Enum

class TabState(Enum):
    IDLE = "idle"           # 閒置，無 page
    ACTIVE = "active"       # 執行中
    BROWSING = "browsing"   # 瀏覽模式，有 page
    DOWNLOADING = "downloading"  # 下載中
