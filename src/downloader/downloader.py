"""
Downloader - 使用完整 Request Headers 模擬瀏覽器下載
"""
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Callable, Dict
from dataclasses import dataclass
from ..network.interceptor import MediaURL, MediaType


@dataclass
class DownloadTask:
    """下載任務"""
    id: str
    url: str
    path: Path
    progress: float = 0.0
    completed: bool = False
    error: Optional[str] = None
    headers_used: Dict[str, str] = None  # 記錄使用的 headers

    def __post_init__(self):
        if self.headers_used is None:
            self.headers_used = {}


class Downloader:
    """
    下載器 - 使用攔截到的 Headers 模擬瀏覽器請求

    參考 facebooc 的 HTTP 請求建構方式
    """

    # 預設的瀏覽器 Headers
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'video',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
    }

    def __init__(self, download_dir: str = "./downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._progress_callback: Optional[Callable] = None
        self._complete_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """設定進度回報 callback(task_id, progress)"""
        self._progress_callback = callback

    def set_complete_callback(self, callback: Callable[[str, str], None]):
        """設定完成回報 callback(task_id, path)"""
        self._complete_callback = callback

    def _build_headers(self, media: MediaURL) -> Dict[str, str]:
        """
        建構下載用的 Headers

        優先使用攔截到的 headers，缺少的用預設值補充
        這樣可以更好地模擬瀏覽器行為，避免被伺服器拒絕
        """
        from urllib.parse import urlparse

        headers = self.DEFAULT_HEADERS.copy()

        # 使用攔截到的 headers 覆蓋預設值
        if media.headers:
            headers.update(media.headers)

        # 確保 Referer 存在（很多影片伺服器會檢查）
        if media.referrer and 'Referer' not in headers:
            headers['Referer'] = media.referrer
        elif 'Referer' not in headers:
            # 如果沒有 referrer，用 media URL 的 origin 作為 Referer
            parsed = urlparse(media.url)
            headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"

        # 如果有 first_party_url，用作 Origin
        if media.first_party_url:
            parsed = urlparse(media.first_party_url)
            headers['Origin'] = f"{parsed.scheme}://{parsed.netloc}"
        elif 'Origin' not in headers:
            # 沒有 first_party_url，用 media URL 的 origin
            parsed = urlparse(media.url)
            headers['Origin'] = f"{parsed.scheme}://{parsed.netloc}"

        return headers

    async def download(self, media: MediaURL, filename: Optional[str] = None) -> DownloadTask:
        """開始下載"""
        import uuid
        task_id = str(uuid.uuid4())[:8]

        if not filename:
            filename = self._generate_filename(media.url, media.media_type)

        path = self.download_dir / filename

        # 建構 headers
        headers = self._build_headers(media)

        task = DownloadTask(
            id=task_id,
            url=media.url,
            path=path,
            headers_used=headers
        )

        try:
            if media.media_type == MediaType.MP4:
                await self._download_direct(task, headers)
            elif media.media_type == MediaType.WEBM:
                await self._download_direct(task, headers)
            elif media.media_type in (MediaType.M3U8, MediaType.MPD):
                await self._download_ffmpeg(task, headers)
            elif media.media_type == MediaType.AUDIO:
                await self._download_direct(task, headers)
            else:
                await self._download_direct(task, headers)

            task.completed = True
            if self._complete_callback:
                self._complete_callback(task_id, str(task.path))

        except Exception as e:
            task.error = str(e)

        return task

    async def _download_direct(self, task: DownloadTask, headers: Dict[str, str]):
        """
        直接下載 (MP4/WebM/Audio)

        使用完整的 headers 模擬瀏覽器請求
        """
        timeout = aiohttp.ClientTimeout(total=3600)  # 1 小時超時

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(task.url, headers=headers) as response:
                # 檢查回應狀態
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}: {response.reason}")

                total = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(task.path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(65536):  # 64KB chunks
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total > 0:
                            task.progress = downloaded / total
                            if self._progress_callback:
                                self._progress_callback(task.id, task.progress)

    async def _download_ffmpeg(self, task: DownloadTask, headers: Dict[str, str]):
        """
        使用 FFmpeg 下載 (M3U8/MPD)

        FFmpeg 支援 -headers 參數傳入 HTTP headers
        """
        # 建構 header 字串（FFmpeg 格式）
        header_lines = []
        for key, value in headers.items():
            # FFmpeg headers 用 \r\n 分隔
            header_lines.append(f"{key}: {value}")
        header_str = '\r\n'.join(header_lines) + '\r\n'

        # 輸出路徑
        output_path = task.path.with_suffix('.mp4')

        cmd = [
            'ffmpeg', '-y',
            '-headers', header_str,
            '-i', task.url,
            '-c', 'copy',  # 不重新編碼，直接複製
            '-bsf:a', 'aac_adtstoasc',  # 修復某些 HLS 的音訊問題
            str(output_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # 讀取 stderr 來獲取進度（FFmpeg 輸出進度到 stderr）
        stderr_output = []
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            stderr_output.append(line.decode('utf-8', errors='ignore'))

            # 可以解析 FFmpeg 的進度輸出，但這比較複雜
            # 簡單起見，先不實作進度回報

        await process.wait()

        if process.returncode != 0:
            error_msg = ''.join(stderr_output[-10:])  # 取最後 10 行錯誤
            raise RuntimeError(f"FFmpeg failed (code {process.returncode}): {error_msg}")

        task.progress = 1.0
        task.path = output_path

    def _generate_filename(self, url: str, media_type: MediaType) -> str:
        """從 URL 生成檔名"""
        from urllib.parse import urlparse, unquote
        import time

        parsed = urlparse(url)
        path = unquote(parsed.path)  # URL decode

        # 嘗試從 URL 取得檔名
        if '/' in path:
            name = path.split('/')[-1].split('?')[0]
            if name and '.' in name:
                # 清理檔名中的非法字元
                name = self._sanitize_filename(name)
                if name:
                    return name

        # 生成預設檔名
        timestamp = int(time.time())
        ext_map = {
            MediaType.MP4: '.mp4',
            MediaType.WEBM: '.webm',
            MediaType.M3U8: '.mp4',  # HLS 轉成 mp4
            MediaType.MPD: '.mp4',   # DASH 轉成 mp4
            MediaType.AUDIO: '.mp3',
        }
        ext = ext_map.get(media_type, '.mp4')
        return f"video_{timestamp}{ext}"

    def _sanitize_filename(self, filename: str) -> str:
        """清理檔名中的非法字元"""
        # Windows 不允許的字元
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # 移除控制字元
        filename = ''.join(c for c in filename if ord(c) >= 32)

        # 限制長度
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:200 - len(ext) - 1] + '.' + ext if ext else name[:200]

        return filename.strip()

    async def download_with_retry(
        self,
        media: MediaURL,
        filename: Optional[str] = None,
        max_retries: int = 3
    ) -> DownloadTask:
        """帶重試的下載"""
        last_error = None

        for attempt in range(max_retries):
            task = await self.download(media, filename)

            if task.completed:
                return task

            last_error = task.error

            # 等待後重試
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指數退避

        # 所有重試都失敗
        import uuid
        return DownloadTask(
            id=str(uuid.uuid4())[:8],
            url=media.url,
            path=self.download_dir / "failed",
            error=f"Failed after {max_retries} attempts: {last_error}"
        )
