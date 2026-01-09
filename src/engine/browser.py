from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional

class BrowserEngine:
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None

    async def start(self, headless: bool = True):
        """啟動 Chromium 引擎"""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )

    async def stop(self):
        """停止引擎"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def create_context(self) -> BrowserContext:
        """建立新的 BrowserContext（獨立 session）"""
        if not self._browser:
            raise RuntimeError("Browser not started")
        return await self._browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

    async def create_page(self, context: BrowserContext) -> Page:
        """在 context 中建立 Page"""
        return await context.new_page()

    async def close_page(self, page: Page):
        """關閉 Page（但保留 context）"""
        await page.close()

    async def navigate(self, page: Page, url: str):
        """導航到 URL"""
        await page.goto(url, wait_until='domcontentloaded')

    @property
    def is_running(self) -> bool:
        return self._browser is not None
