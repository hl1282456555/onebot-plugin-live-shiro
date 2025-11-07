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

from nonebot import get_driver, get_plugin_config, logger
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from . import alive, bible, bilibili, common

plugin_config = get_plugin_config(Config)

driver = get_driver()
@driver.on_bot_connect
async def union_bot_connect_handler(bot: Bot) -> None:
    if not plugin_config.live_shiro_group_ids:
        logger.info("没有配置群组列表，跳过启动。")
        return

    message = Message([
        MessageSegment.text("小助手已经安全启动，今天又是美好的一天瞄~\n"),
        MessageSegment.text("服务启动状态：\n")
    ])

    if alive_message := await alive.alive_bot_connect_handler(bot):
        message += Message("\n") + alive_message

    if bilibili_message := await bilibili.bilibili_bot_connect_handler(bot):
        message += Message("\n") + bilibili_message

    # for group_id in plugin_config.live_shiro_group_ids:
    #     await bot.send_group_msg(group_id=group_id, message=message)
