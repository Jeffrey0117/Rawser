# Rawser — 完整開發規格書

## 一、專案定位

**Rawser = 任務導向、可視化的 User-Agent 瀏覽器**

### 是什麼
- 任務執行器
- 資源取得工具
- 網頁行為觀測台

### 不是什麼
- Chrome 替代品
- 日常上網瀏覽器

---

## 二、技術選型

| 層級 | 技術 | 說明 |
|------|------|------|
| **GUI** | Python + PySide6 (Qt) | 純控制面板，不是瀏覽器 |
| **Engine** | Playwright + Chromium | 唯一的瀏覽器引擎 |
| **Downloader** | aiohttp + FFmpeg | 下載 mp4 / 處理 m3u8 |

### 為什麼不用 Electron
```
Electron 架構（錯誤）:
Electron
 └── Chromium（GUI）      ← 第一個瀏覽器
     └── Playwright
         └── Chromium    ← 第二個瀏覽器（重複！）

Python + Qt 架構（正確）:
Qt GUI（純殼）
 └── Playwright
     └── Chromium        ← 唯一的瀏覽器引擎
```

---

## 三、系統架構

```
┌─────────────────────────┐
│ Qt GUI (PySide6)        │  ← 純控制面板
│ - URL 輸入              │
│ - 任務列表              │
│ - Log 區                │
│ - Media 列表            │
│ - 下載進度              │
└───────────┬─────────────┘
            │ Signal/Slot
┌───────────▼─────────────┐
│ Controller              │  ← 任務管理、狀態機
│ - TabManager            │
│ - StateManager          │
└───────────┬─────────────┘
            │ async
┌───────────▼─────────────┐
│ Playwright Engine       │  ← 唯一瀏覽器引擎
│ - BrowserContext 管理   │
│ - Page 生命週期         │
│ - Network Interception  │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ Downloader              │  ← 下載處理
│ - MP4 直存 (aiohttp)    │
│ - M3U8 → FFmpeg         │
└─────────────────────────┘
```

---

## 四、TAB / 任務模型

### 一個 TAB 包含
- URL
- BrowserContext（cookie/storage）
- 狀態：`idle` | `active` | `browsing` | `downloading`
- Page（可選，用完釋放）

### 兩種模式
| 模式 | 說明 | Page |
|------|------|------|
| 任務模式 | 背景執行，保留 session | 無 |
| 瀏覽模式 | 顯示網頁，可互動 | 有 |

---

## 五、GUI 規格（極簡控制台）

### 必要元件
1. URL 輸入框 + Go 按鈕
2. 任務列表（TAB list）
3. 狀態顯示
4. Inspect 按鈕（開啟瀏覽模式）
5. Log 區（QTextEdit）
6. Media URL 列表
7. Download 按鈕 + 進度條

### 不做
- 書籤、歷史
- 分頁拖拉
- 外掛
- 複雜設定

---

## 六、目錄結構

```
rawser/
├── requirements.txt
├── main.py                 # 入口
├── src/
│   ├── gui/
│   │   ├── main_window.py  # 主視窗
│   │   └── widgets.py      # 自訂元件
│   ├── controller/
│   │   ├── tab_manager.py  # TAB 管理
│   │   └── state.py        # 狀態機
│   ├── engine/
│   │   └── browser.py      # Playwright 控制
│   ├── network/
│   │   └── interceptor.py  # Media 攔截
│   └── downloader/
│       └── downloader.py   # 下載 + FFmpeg
├── logs/
└── downloads/
```

---

## 七、MVP 完成定義

- [ ] 能載入頁面（JS 執行）
- [ ] 能登入、保留 session
- [ ] 能攔截 media URL（mp4/m3u8）
- [ ] 能下載存檔
- [ ] 能關 page 但保留 session
