from typing import Optional

from twitchio import Client

from nonebot import get_plugin_config, logger
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from ..config import Config

plugin_config = get_plugin_config(Config)

CLIENT_ID = plugin_config.live_shiro_twitch_client_id
CLIENT_SECRET = plugin_config.live_shiro_twitch_client_secret

async def check_live(bot: Bot, username: str):
    client = Client(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    try:
        logger.info(f"正在请求 twitch 登录… client_id={CLIENT_ID}")

        await client.login()

        logger.info("Twitch 登录成功，fetch_users…")
        users = await client.fetch_users(logins=[username])
        logger.info(f"fetch_users result: {users}")

        if not users:
            logger.warning(f"用户 {username} 未找到")
            return

        user_id = users[0].id
        logger.info(f"获取到 user_id={user_id}，fetch_streams…")

        streams = await client.fetch_streams(user_ids=[user_id])
        logger.info(f"fetch_streams result: {streams}")

        if streams:
            logger.info(f"{username} 正在直播")
        else:
            logger.info(f"{username} 未处于直播状态")

    except Exception as e:
        logger.exception("❌ check_live 执行失败")  # 打印完整 traceback

async def twitch_bot_connect_handler(bot: Bot) -> Optional[Message]:
    # await check_live(bot, "yosumi_shiro")
    return Message("twitch监听已启动喵~")
