from .renderer import *
from nonebot import get_driver
from .browser import browser_manager  # 使用单例管理器

driver = get_driver()


@driver.on_startup
async def _startup():
    """插件启动时初始化浏览器"""
    await browser_manager.init_browser()


@driver.on_shutdown
async def _shutdown():
    """插件关闭时安全关闭浏览器"""
    await browser_manager.close_browser()
