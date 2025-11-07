from nonebot import require

require("nonebot_plugin_apscheduler")

from bilibili_api import select_client
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="onebot-plugin-live-shiro",
    description="A onebot plugin for vtuber Shiro.",
    usage="",
    config=Config,
)

select_client("httpx")

from nonebot import get_driver
from nonebot.adapters import Bot

from . import alive, bible, bilibili, common

driver = get_driver()
@driver.on_bot_connect
async def union_bot_connect_handler(bot: Bot) -> None:
    await alive.alive_bot_connect_handler(bot)
    await bilibili.bilibili_bot_connect_handler(bot)
