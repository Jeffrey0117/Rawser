# Facebooc 專案分析報告
## 與 Rawser 的對照學習

---

## 一、Facebooc 是什麼？

**Facebooc** 是 jserv（黃敬群）教授的教學專案，用純 C 語言實作一個完整的社群網站。

### 核心價值
```
不是要做一個能用的 Facebook
而是要展示：一個 Web 應用的底層到底長什麼樣子
```

### 技術棧
| 層級 | 技術 |
|------|------|
| 語言 | C (79.6%) |
| 資料庫 | SQLite3 |
| 事件驅動 | epoll (Linux) / kqueue (macOS) |
| 前端 | 純 HTML + CSS |

---

## 二、架構分析

### Facebooc 架構
```
┌─────────────────────────────────────────┐
│           瀏覽器 (Client)               │
└─────────────────┬───────────────────────┘
                  │ HTTP Request
┌─────────────────▼───────────────────────┐
│           server.c                      │
│  ┌─────────────────────────────────┐    │
│  │ Event Loop (epoll/kqueue)       │    │
│  │  - 監聽 socket                  │    │
│  │  - 非阻塞 I/O                   │    │
│  │  - 事件分派                     │    │
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           request.c                     │
│  - 解析 HTTP Method                     │
│  - 解析 URL Path                        │
│  - 解析 Headers                         │
│  - 解析 Query String                    │
│  - 解析 Cookies                         │
│  - 解析 POST Body                       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           main.c (Handler Chain)        │
│  - /login    → loginHandler()           │
│  - /post     → postHandler()            │
│  - /like     → likeHandler()            │
│  - /static/* → staticHandler()          │
│  - *         → notFoundHandler()        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           response.c                    │
│  - 設定 Status Code                     │
│  - 設定 Headers                         │
│  - 設定 Cookies                         │
│  - 組裝並發送 Response                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           SQLite3 (資料持久化)          │
│  - accounts (帳號)                      │
│  - sessions (會話)                      │
│  - posts    (貼文)                      │
│  - likes    (按讚)                      │
│  - connections (好友)                   │
└─────────────────────────────────────────┘
```

### Rawser 架構
```
┌─────────────────────────────────────────┐
│           Qt GUI (PySide6)              │
│  - URL 輸入                             │
│  - 任務列表                             │
│  - Media 列表                           │
│  - 歷史縮圖                             │
└─────────────────┬───────────────────────┘
                  │ Signal/Slot
┌─────────────────▼───────────────────────┐
│           QWebEngineView                │
│  - Chromium 渲染引擎                    │
│  - 內建 HTTP Client                     │
│  - JavaScript 執行                      │
│  - Cookie/Session 管理                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│     QWebEngineUrlRequestInterceptor     │
│  - 攔截所有 Request                     │
│  - 偵測 Media URL                       │
│  - 收集下載目標                         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Downloader                    │
│  - MP4 直接下載                         │
│  - M3U8 → FFmpeg                        │
└─────────────────────────────────────────┘
```

---

## 三、核心概念對照

### 1. HTTP 協議處理

| 概念 | Facebooc | Rawser |
|------|----------|--------|
| **角色** | HTTP Server（接收請求） | HTTP Client（發送請求） |
| **Request 解析** | 自己實作 `request.c` | Qt WebEngine 內建 |
| **Response 建構** | 自己實作 `response.c` | 收到後由 Chromium 處理 |
| **Cookie 管理** | 自己解析/設定 | Qt WebEngine 自動管理 |

**Facebooc 的 Request 解析（我們可以學習的）：**
```c
// request.c 核心邏輯
Request *RequestNew(const char *raw) {
    // 1. 解析 HTTP Method
    if (strncmp(raw, "GET", 3) == 0) req->method = GET;

    // 2. 解析 Path
    req->path = extractPath(raw);

    // 3. 解析 Headers
    parseHeaders(req, raw);

    // 4. 解析 Query String
    parseQS(req, queryPart);

    // 5. 解析 Cookies
    parseCookies(req, cookieHeader);

    return req;
}
```

**Rawser 可以應用的地方：**
- 理解攔截到的 Request 結構
- 自己建構 Request（下載時可能需要）
- 處理 Cookie 認證

---

### 2. 事件驅動模型

| 概念 | Facebooc | Rawser |
|------|----------|--------|
| **事件機制** | epoll/kqueue | Qt Event Loop |
| **非阻塞 I/O** | 自己實作 | Qt/asyncio 處理 |
| **多連線處理** | 單執行緒 + 事件驅動 | Qt 多執行緒 |

**Facebooc 的 Event Loop：**
```c
// server.c
void serverServe(Server *server) {
    while (1) {
        // 等待事件（新連線、資料到達）
        int n = epoll_wait(epfd, events, MAX_EVENTS, -1);

        for (int i = 0; i < n; i++) {
            if (events[i].data.fd == server->fd) {
                // 新連線
                acceptConnection();
            } else {
                // 處理請求
                handle(events[i].data.fd);
            }
        }
    }
}
```

**Rawser 對應的是：**
```python
# Qt 的 Event Loop
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

# Signal/Slot 就是事件驅動
webview.loadFinished.connect(self._on_load_finished)
```

---

### 3. 路由與 Handler 模式

**Facebooc 的 Handler Chain：**
```c
// main.c
serverAddHandler(server, session);       // 先檢查 session
serverAddHandler(server, login);         // /login
serverAddHandler(server, logout);        // /logout
serverAddHandler(server, home);          // /
serverAddHandler(server, staticHandler); // /static/*
serverAddHandler(server, notFound);      // 404
```

**Rawser 可以借鏡的設計：**
```python
# 類似的 Handler 模式用於 URL 攔截
class MediaInterceptor:
    def interceptRequest(self, info):
        url = info.requestUrl().toString()

        # Handler Chain 概念
        if self._is_mp4(url):
            self._handle_mp4(url)
        elif self._is_m3u8(url):
            self._handle_m3u8(url)
        elif self._is_mpd(url):
            self._handle_mpd(url)
```

---

## 四、我們可以從 Facebooc 學到什麼？

### 1. 自己實作 HTTP Client（進階功能）

目前 Rawser 依賴 `aiohttp` 下載，但理解 HTTP 協議後可以：

```python
# 參考 facebooc 的方式，自己建構 HTTP Request
class RawHttpClient:
    def build_request(self, method, url, headers, cookies):
        """
        像 facebooc/response.c 那樣組裝 HTTP
        """
        request = f"{method} {path} HTTP/1.1\r\n"
        request += f"Host: {host}\r\n"

        for key, value in headers.items():
            request += f"{key}: {value}\r\n"

        if cookies:
            cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
            request += f"Cookie: {cookie_str}\r\n"

        request += "\r\n"
        return request
```

### 2. 更精細的 Request 攔截

```python
# 參考 facebooc/request.c 的解析邏輯
class AdvancedInterceptor:
    def parse_request(self, raw_request):
        """
        解析攔截到的原始 Request
        """
        lines = raw_request.split('\r\n')

        # Method + Path
        method, path, version = lines[0].split(' ')

        # Headers
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key] = value

        return {
            'method': method,
            'path': path,
            'headers': headers
        }
```

### 3. Session 管理概念

Facebooc 的 Session 機制：
```c
// 1. 登入時建立 session
char *sessionId = generateSessionId();
setCookie("session_id", sessionId);
saveToDatabase(sessionId, accountId);

// 2. 每次請求檢查 session
char *sessionId = getCookie("session_id");
Account *account = getAccountBySession(sessionId);
```

Rawser 可以應用於：
- 保存登入狀態後下載需要認證的資源
- 管理多個網站的 Session

---

## 五、實際應用建議

### 短期（可立即實作）

1. **增強 Media 偵測**
   - 參考 facebooc 的 Handler Chain，建立 Media 類型處理鏈
   - 更精確判斷 media URL

2. **Request Header 複製**
   - 攔截到 media URL 時，保存完整的 Request Headers
   - 下載時使用相同的 Headers（模擬瀏覽器）

```python
class EnhancedInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        url = info.requestUrl().toString()

        if self._is_media(url):
            # 保存完整的 request 資訊
            self.media_requests[url] = {
                'url': url,
                'method': info.requestMethod(),
                'headers': self._extract_headers(info),
                'referrer': info.firstPartyUrl().toString()
            }
```

### 中期（深入學習後）

1. **自製簡易 HTTP Server**
   - 用於接收某些特殊的回調
   - 本地 Proxy 功能

2. **Cookie 持久化**
   - 像 facebooc 用 SQLite 存 session
   - Rawser 也可以存 Cookie 實現「記住登入」

### 長期（完整理解後）

1. **完整的 Proxy Server**
   - 參考 facebooc 的 server.c
   - 所有流量經過本地 Proxy
   - 更強大的攔截與修改能力

---

## 六、關鍵原始碼對照

### HTTP 狀態碼（facebooc/response.c）
```c
static const char *statusMessage(Status status) {
    switch (status) {
        case OK: return "OK";
        case MOVED_PERMANENTLY: return "Moved Permanently";
        case FOUND: return "Found";
        case NOT_FOUND: return "Not Found";
        // ...
    }
}
```

### URL 解碼（facebooc/request.c）
```c
// 這個我們下載時可能需要
static void urldecode(char *dst, const char *src) {
    while (*src) {
        if (*src == '%') {
            // %XX → 字元
            sscanf(src + 1, "%2x", &code);
            *dst++ = code;
            src += 3;
        } else if (*src == '+') {
            *dst++ = ' ';
            src++;
        } else {
            *dst++ = *src++;
        }
    }
}
```

---

## 七、結論

| 面向 | Facebooc | Rawser |
|------|----------|--------|
| **目的** | 教學：展示 Web 底層 | 實用：下載 Media |
| **角色** | Server（被動接收） | Client（主動請求） |
| **價值** | 理解 HTTP 協議本質 | 理解後可增強功能 |

**最大的學習價值：**

Facebooc 告訴我們：
> HTTP 不是魔法，就是文字協議
> Server 不是黑盒，就是 Socket + 事件循環
> Cookie/Session 不神秘，就是字串傳來傳去

理解這些後，Rawser 可以：
- 更精準地攔截和分析 Request
- 更好地模擬瀏覽器行為
- 處理更複雜的認證場景
- 甚至建立本地 Proxy 實現更強大的功能

---

## 八、延伸閱讀

1. **facebooc 原始碼**：https://github.com/jserv/facebooc
2. **HTTP/1.1 規範**：RFC 2616
3. **epoll 教學**：Linux man pages
4. **Qt WebEngine 文檔**：Qt 官方文檔

---

*報告完成日期：2026-01-09*
*對照專案：Rawser v0.2.0*
