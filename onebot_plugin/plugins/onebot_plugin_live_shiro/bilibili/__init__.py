from typing import Optional

from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message

from . import dynamic, live_room


async def bilibili_bot_connect_handler(bot: Bot) -> Optional[Message]:
    bilibili_message = Message()

    if dynamic_message := await dynamic.dynamic_bot_connect_handler(bot):
        bilibili_message += dynamic_message
    else:
        bilibili_message += Message("动态监控启动失败喵~")

    if live_room_message := await live_room.start_monitor_bilibili_live_status(bot):
        bilibili_message += live_room_message
    else:
        bilibili_message += Message("B站直播状态监控启动失败喵~")

    return bilibili_message

__all__ = ["bilibili_bot_connect_handler"]
