from typing import Optional

from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message

from . import common, dynamic, live_room


async def bilibili_bot_connect_handler(bot: Bot) -> Optional[Message]:
    bilibili_message = Message()

    if login_message := await common.bilibili_login_bot_connect_handler(bot):
        bilibili_message += Message("\n") + login_message
    else:
        bilibili_message += Message("\n") +Message("B站登陆状态检测启动失败喵~")

    if dynamic_message := await dynamic.dynamic_bot_connect_handler(bot):
        bilibili_message += Message("\n") +dynamic_message
    else:
        bilibili_message += Message("\n") +Message("动态监控启动失败喵~")

    if live_room_message := await live_room.start_monitor_bilibili_live_status(bot):
        bilibili_message += Message("\n") +live_room_message
    else:
        bilibili_message += Message("\n") +Message("B站直播状态监控启动失败喵~")

    return bilibili_message

__all__ = ["bilibili_bot_connect_handler"]
