from nonebot.adapters import Bot

from . import dynamic


async def bilibili_bot_connect_handler(bot: Bot) -> None:
    await dynamic.dynamic_bot_connect_handler(bot)

__all__ = ["bilibili_bot_connect_handler"]
