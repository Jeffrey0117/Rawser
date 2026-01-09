import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
from ..network.interceptor import MediaURL, MediaType

@dataclass
class DownloadTask:
    id: str
    url: str
    path: Path
    progress: float = 0.0
    completed: bool = False
    error: Optional[str] = None

class Downloader:
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

    async def download(self, media: MediaURL, filename: Optional[str] = None) -> DownloadTask:
        """開始下載"""
        import uuid
        task_id = str(uuid.uuid4())[:8]

        if not filename:
            filename = self._generate_filename(media.url, media.media_type)

        path = self.download_dir / filename
        task = DownloadTask(id=task_id, url=media.url, path=path)

        try:
            if media.media_type == MediaType.MP4:
                await self._download_direct(task, media.headers)
            elif media.media_type in (MediaType.M3U8, MediaType.MPD):
                await self._download_ffmpeg(task, media.headers)
            else:
                await self._download_direct(task, media.headers)

            task.completed = True
            if self._complete_callback:
                self._complete_callback(task_id, str(path))
        except Exception as e:
            task.error = str(e)

        return task

    async def _download_direct(self, task: DownloadTask, headers: dict):
        """直接下載 (MP4)"""
        async with aiohttp.ClientSession() as session:
            async with session.get(task.url, headers=headers) as response:
                total = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(task.path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            task.progress = downloaded / total
                            if self._progress_callback:
                                self._progress_callback(task.id, task.progress)

    async def _download_ffmpeg(self, task: DownloadTask, headers: dict):
        """使用 FFmpeg 下載 (M3U8/MPD)"""
        # 建構 header 字串
        header_str = '\r\n'.join([f'{k}: {v}' for k, v in headers.items()])

        cmd = [
            'ffmpeg', '-y',
            '-headers', header_str,
            '-i', task.url,
            '-c', 'copy',
            str(task.path.with_suffix('.mp4'))
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed with code {process.returncode}")

        task.progress = 1.0
        task.path = task.path.with_suffix('.mp4')

    def _generate_filename(self, url: str, media_type: MediaType) -> str:
        """從 URL 生成檔名"""
        from urllib.parse import urlparse
        import time

        parsed = urlparse(url)
        path = parsed.path

        # 嘗試從 URL 取得檔名
        if '/' in path:
            name = path.split('/')[-1].split('?')[0]
            if name and '.' in name:
                return name

        # 生成預設檔名
        timestamp = int(time.time())
        ext = '.mp4' if media_type == MediaType.MP4 else '.mp4'
        return f"video_{timestamp}{ext}"
