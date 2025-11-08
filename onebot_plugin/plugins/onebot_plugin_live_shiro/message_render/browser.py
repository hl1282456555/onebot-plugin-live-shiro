import asyncio
from playwright.async_api import async_playwright, Browser, Playwright

class BrowserManager:
    """异步安全的单例浏览器管理器"""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._playwright: Playwright | None = None
            cls._instance._browser: Browser | None = None
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def init_browser(self) -> Browser:
        """初始化浏览器(只执行一次)"""
        async with self._lock:
            if self._browser:
                return self._browser
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
            )
            return self._browser

    async def get_browser(self) -> Browser:
        """获取浏览器实例"""
        if self._browser is None:
            return await self.init_browser()
        return self._browser

    async def close_browser(self):
        """安全关闭浏览器"""
        async with self._lock:
            if self._browser:
                try:
                    await self._browser.close()
                except Exception as e:
                    print(f"Warning: browser close failed: {e}")
                finally:
                    self._browser = None

            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception as e:
                    print(f"Warning: playwright stop failed: {e}")
                finally:
                    self._playwright = None


# 全局单例
browser_manager = BrowserManager()

# 使用示例
# await browser_manager.get_browser()
# await browser_manager.close_browser()
