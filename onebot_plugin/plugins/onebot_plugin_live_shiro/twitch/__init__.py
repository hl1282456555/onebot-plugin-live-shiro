from typing import Optional

import twitchio
from twitchio import Client

from nonebot import get_plugin_config
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

from ..config import Config

plugin_config = get_plugin_config(Config)

CLIENT_ID = plugin_config.live_shiro_twitch_client_id
CLIENT_SECRET = plugin_config.live_shiro_twitch_client_secret

async def bilibili_bot_connect_handler(bot: Bot) -> Optional[Message]:
    pass
