# Rawser 開發 TODO

## 技術棧
- **GUI**: Python + PySide6 (Qt)
- **Engine**: Playwright (Python) + Chromium
- **Download**: aiohttp + FFmpeg

---

## Agent 分工

### Agent 1: GUI Layer
- PySide6 主視窗
- 控制面板 UI
- Signal/Slot 連接

### Agent 2: Controller + Engine Layer
- TabManager（任務管理）
- BrowserEngine（Playwright 控制）
- 狀態機

### Agent 3: Network + Downloader Layer
- Interceptor（Media 攔截）
- Downloader（aiohttp + FFmpeg）

---

## 檔案清單

```
rawser/
├── requirements.txt        [Agent 1]
├── main.py                 [Agent 1]
├── src/
│   ├── __init__.py
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py  [Agent 1]
│   │   └── widgets.py      [Agent 1]
│   ├── controller/
│   │   ├── __init__.py
│   │   ├── tab_manager.py  [Agent 2]
│   │   └── state.py        [Agent 2]
│   ├── engine/
│   │   ├── __init__.py
│   │   └── browser.py      [Agent 2]
│   ├── network/
│   │   ├── __init__.py
│   │   └── interceptor.py  [Agent 3]
│   └── downloader/
│       ├── __init__.py
│       └── downloader.py   [Agent 3]
├── logs/
└── downloads/
```

---

## Agent 1 任務：GUI Layer

### 檔案：requirements.txt
```
PySide6>=6.6.0
playwright>=1.40.0
aiohttp>=3.9.0
qasync>=0.27.0
```

### 檔案：main.py
- 初始化 Qt App
- 整合 asyncio (qasync)
- 啟動主視窗

### 檔案：src/gui/main_window.py
- QMainWindow 主視窗
- 佈局：
  - 頂部：URL 輸入 + Go 按鈕
  - 左側：任務列表 (QListWidget)
  - 右上：Log 區 (QTextEdit)
  - 右下：Media 列表 + Download 按鈕
  - 底部：狀態列 + 進度條

### 檔案：src/gui/widgets.py
- TaskItem（任務列表項目）
- MediaItem（Media URL 項目）

---

## Agent 2 任務：Controller + Engine

### 檔案：src/controller/tab_manager.py
- class TabManager
  - tabs: Dict[str, Tab]
  - create_tab(url) -> Tab
  - close_tab(tab_id)
  - get_tab(tab_id) -> Tab

- class Tab
  - id: str
  - url: str
  - state: TabState
  - context: BrowserContext
  - page: Optional[Page]

### 檔案：src/controller/state.py
- enum TabState: IDLE, ACTIVE, BROWSING, DOWNLOADING
- 狀態轉換邏輯

### 檔案：src/engine/browser.py
- class BrowserEngine
  - browser: Browser (Playwright Chromium)
  - async start()
  - async stop()
  - async create_context() -> BrowserContext
  - async create_page(context) -> Page
  - async close_page(page)
  - async navigate(page, url)

---

## Agent 3 任務：Network + Downloader

### 檔案：src/network/interceptor.py
- class Interceptor
  - media_urls: List[MediaURL]
  - async attach(page)
  - async detach(page)
  - _on_response(response) - 偵測 mp4/m3u8/mpd

- class MediaURL
  - url: str
  - type: MediaType (MP4, M3U8, MPD)
  - headers: dict

### 檔案：src/downloader/downloader.py
- class Downloader
  - download_dir: Path
  - async download(media: MediaURL) -> DownloadTask
  - async download_mp4(url, headers) - aiohttp stream
  - async download_m3u8(url, headers) - ffmpeg subprocess
  - 進度回報 (Signal)

---

## IPC / Signal 定義

```python
# GUI -> Controller
signal_navigate(url: str)
signal_create_tab(url: str)
signal_close_tab(tab_id: str)
signal_toggle_browse(tab_id: str)
signal_download(media_url: str)

# Controller -> GUI
signal_tab_created(tab: Tab)
signal_tab_updated(tab: Tab)
signal_log(message: str)
signal_media_detected(media: MediaURL)
signal_download_progress(task_id: str, progress: float)
signal_download_complete(task_id: str, path: str)
```
