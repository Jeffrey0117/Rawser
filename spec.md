好，我幫你把**「Rawser」這個東西的規格**完整、乾淨地重講一次，
**不討論對錯、不補哲學，只講你到底要做的是什麼。**

---

# Rawser — 規格定義（重整版）

## 一句話定位

**Rawser = 任務導向、可視化的 User-Agent 瀏覽器**

* 能逛網頁 ✅
* 能跑 JS / token / cookie / session ✅
* 能攔 request、抓 media、下載 ✅
* 但 **不是長時間沉浸式瀏覽器**

---

## 一、Rawser 解決什麼問題（Problem Scope）

Rawser 要解的是這組衝突：

* 純前端 👉 被瀏覽器 sandbox、下載受限
* 純後端 👉 被 anti-bot、token / session 擋
* 傳統瀏覽器 👉 太肥、太不透明、不可控

👉 **Rawser 的目標是：
把「前端必要性」與「後端控制權」合在一起。**

---

## 二、使用者心智模型（很重要）

### ❌ Rawser 不是

* Chrome 替代品
* 日常上網瀏覽器
* 一直開著 50 個 tab 的東西

### ✅ Rawser 是

* 任務執行器
* 資源取得工具
* 網頁行為觀測台

---

## 三、核心設計原則（Design Principles）

1. **TAB ≠ 網頁**
2. **TAB = 任務 / Session**
3. **畫面是可選的，不是常駐的**
4. **下載不在 JS 做**
5. **一顆引擎，多個 context**
6. **Page 用完就釋放**

---

## 四、架構總覽

```
┌────────────────────┐
│ Minimal GUI        │  ← 觀察、控制
└─────────┬──────────┘
          │
┌─────────▼──────────┐
│ Controller Layer   │  ← 任務、狀態機
└─────────┬──────────┘
          │
┌─────────▼──────────┐
│ Chromium Engine    │  ← 單一實例
│ (Playwright)       │
└─────────┬──────────┘
          │
┌─────────▼──────────┐
│ Network / Media Tap│  ← 攔 request
└─────────┬──────────┘
          │
┌─────────▼──────────┐
│ Downloader / FFmpeg│  ← 真正存檔
└────────────────────┘
```

---

## 五、引擎與技術選型（定錨）

### 瀏覽器核心

* **Chromium**
* **Playwright**
* 使用 **BrowserContext**，不開多 process

### 為什麼

* JS 真實執行
* cookie / session 自然生成
* network interception 可控
* 比 Selenium 穩定

---

## 六、TAB / 任務模型（重點）

### 傳統瀏覽器

```
TAB = Renderer Process = RAM 地獄
```

### Rawser

```
TAB = Job / Session
Page = 臨時資源
```

#### 一個 TAB 包含：

* URL
* Cookie / Storage
* 狀態（idle / active / downloading）
* 可選 Page（存在 or 不存在）

---

## 七、兩種模式（這是關鍵）

### Mode A：任務模式（預設）

* ❌ 不顯示畫面
* ❌ 不跑多餘 JS
* ✅ 保留 session
* ✅ 極低 RAM

用途：

* 跑流程
* 拿 token
* 等待
* 下載中

---

### Mode B：瀏覽模式（臨時）

* ✅ 顯示完整網頁
* ✅ 可滑、可點、可登入
* ❌ 不常駐
* 用完就 **detach / close page**

用途：

* Inspect
* 登入
* 解 captcha
* 人工介入一次

---

## 八、多 TAB 不爆 RAM 的關鍵

### 做法

* **一個 Chromium instance**
* 多個 BrowserContext
* Page 用完即釋放

### 記憶體概念（粗估）

* Chromium：100–200MB（固定）
* Context：5–20MB / 個
* Page（活躍）：20–100MB
* Page（關閉）：0

👉 所以 Rawser 能「同時很多 TAB」，
但不是「同時很多畫面」。

---

## 九、下載行為（絕對不在前端）

### 攔截目標

* `.mp4`
* `.m3u8`
* `.mpd`

### 行為

* mp4 → 直接存
* m3u8 / dash → ffmpeg
* 檔名、路徑完全由 Rawser 決定

---

## 十、GUI 規格（極簡）

Rawser GUI **不是瀏覽器 UI**，而是控制台。

### 必要元件

1. URL 輸入框
2. 任務列表（TAB）
3. 狀態顯示
4. Inspect / Detach 按鈕
5. Log 區
6. 下載進度

### 不做

* 書籤
* 分頁拖拉
* 外掛
* 設定迷宮

---

## 十一、Repo 結構（建議）

```
rawser/
├─ app/
│  ├─ gui/
│  ├─ controller/
│  ├─ jobs/
│  ├─ network/
│  └─ downloader/
├─ engine/
├─ logs/
└─ README.md
```

---

## 十二、Rawser 的完成定義（Done）

Rawser **不是做到像 Chrome** 才算成功。

### MVP Done =

* 能載入頁面
* 能登入
* 能抓到真實 media
* 能下載
* 能關 page 但保留 session

做到這裡，Rawser 就是「成立的」。

