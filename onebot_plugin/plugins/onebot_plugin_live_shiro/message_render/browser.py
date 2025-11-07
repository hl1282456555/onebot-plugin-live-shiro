from playwright.async_api import async_playwright, Browser

_playwright = None
_browser: Browser | None = None


async def init_browser() -> Browser:
    """初始化浏览器(Only once)"""
    global _playwright, _browser
    if _browser:
        return _browser

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(
        headless=True,
        args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
    )
    return _browser


async def get_browser() -> Browser:
    if _browser is None:
        return await init_browser()
    return _browser


async def close_browser():
    """安全关闭浏览器"""
    global _playwright, _browser
    # 尝试关闭浏览器实例
    if _browser:
        try:
            await _browser.close()
        except Exception as e:
            # 浏览器已关闭或通信管道断开，打印警告即可
            print(f"Warning: browser close failed: {e}")
        finally:
            _browser = None

    # 尝试停止 playwright
    if _playwright:
        try:
            await _playwright.stop()
        except Exception as e:
            print(f"Warning: playwright stop failed: {e}")
        finally:
            _playwright = None
