from typing import Optional

from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message

from . import dynamic


async def bilibili_bot_connect_handler(bot: Bot) -> Optional[Message]:
    bilibili_message = Message()

    if dynamic_message := await dynamic.dynamic_bot_connect_handler(bot):
        bilibili_message += dynamic_message
    else:
        bilibili_message += Message("动态监控启动失败瞄~")

    return bilibili_message

__all__ = ["bilibili_bot_connect_handler"]
