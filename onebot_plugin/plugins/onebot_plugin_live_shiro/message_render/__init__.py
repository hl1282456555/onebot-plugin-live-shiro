from .renderer import *
from nonebot import get_driver
from .browser import init_browser, close_browser

driver = get_driver()


@driver.on_startup
async def _startup():
    await init_browser()


@driver.on_shutdown
async def _shutdown():
    await close_browser()
