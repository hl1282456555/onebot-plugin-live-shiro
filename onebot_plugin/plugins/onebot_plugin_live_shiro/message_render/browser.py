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
    """关闭浏览器"""
    global _playwright, _browser
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
