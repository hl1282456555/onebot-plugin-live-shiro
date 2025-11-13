from typing import Optional

from nonebot import get_plugin_config, get_bot, logger
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from ..config import Config


import asyncio
import json
import aiohttp
from aiohttp_socks import ProxyConnector

plugin_config = get_plugin_config(Config)

# ==============================
# ⚙️ 配置区
# ==============================
CLIENT_ID = plugin_config.live_shiro_twitch_client_id
CLIENT_SECRET = plugin_config.live_shiro_twitch_client_secret
BROADCASTER_ID = "629147503"  # 主播ID
PROXY_URL = "http://127.0.0.1:10808"

# ==============================
# 🚀 核心逻辑
# ==============================
ACCESS_TOKEN = None  # 启动时自动生成

# ==============================
# 🔑 获取 App Access Token
# ==============================
async def get_app_token():
    global ACCESS_TOKEN
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    connector = ProxyConnector.from_url(PROXY_URL)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, params=params) as resp:
            data = await resp.json()
            ACCESS_TOKEN = data.get("access_token")
            if ACCESS_TOKEN:
                logger.info("✅ 成功获取 App Access Token")
            else:
                logger.error(f"❌ 获取 token 失败: {data}")

# ==============================
# 检查主播状态
# ==============================
async def check_stream_status():
    connector = ProxyConnector.from_url(PROXY_URL)
    url = f"https://api.twitch.tv/helix/streams?user_id={BROADCASTER_ID}"
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            bot = get_bot()
            if data.get("data"):
                for group_id in plugin_config.live_shiro_group_ids:
                    await bot.send_group_msg(
                        group_id=group_id,
                        message=Message([
                            MessageSegment.at('all'),
                            MessageSegment.text(f" 🎬 {data['data'][0]['user_name']} 当前正在直播！\n标题：{data['data'][0].get('title', '无标题')}")
                        ])
                    )
            else:
                for group_id in plugin_config.live_shiro_group_ids:
                    await bot.send_group_msg(
                        group_id=group_id,
                        message="小助手重启检测，当前 Shiro 当前未在Twitch开播， Safe喵~"
                    )

# ==============================
# EventSub 注册
# ==============================
async def subscribe_eventsub(session: aiohttp.ClientSession, session_id: str):
    connector = ProxyConnector.from_url(PROXY_URL)
    url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async def sub(event_type: str):
        payload = {
            "type": event_type,
            "version": "1",
            "condition": {"broadcaster_user_id": BROADCASTER_ID},
            "transport": {
                "method": "websocket",
                "session_id": session_id
            }
        }
        async with session.post(url, headers=headers, json=payload) as resp:
            r = await resp.json()
            logger.info(f"✅ 已注册 {event_type} 订阅: {r}")

    await sub("stream.online")
    await sub("stream.offline")

# ==============================
# EventSub WebSocket 监听
# ==============================
async def listen_eventsub():
    connector = ProxyConnector.from_url(PROXY_URL)
    url = "wss://eventsub.wss.twitch.tv/ws"
    async with aiohttp.ClientSession(connector=connector) as session, \
               session.ws_connect(url) as ws:
        logger.info("🔗 已连接 Twitch EventSub WebSocket")

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                metadata = data.get("metadata", {})
                message_type = metadata.get("message_type")

                if message_type == "session_welcome":
                    session_id = data["payload"]["session"]["id"]
                    logger.info(f"🪄 Session ID: {session_id}")
                    await subscribe_eventsub(session, session_id)

                elif message_type == "notification":
                    payload = data["payload"]
                    event_type = payload["subscription"]["type"]
                    event = payload["event"]

                    bot = get_bot()
                    if event_type == "stream.online":
                        for group_id in plugin_config.live_shiro_group_ids:
                            await bot.send_group_msg(
                                group_id=group_id,
                                message=Message([
                                    MessageSegment.at('all'),
                                    MessageSegment.text(f" 🎬 {event['broadcaster_user_name']} 开播啦！\n标题：{event.get('title', '无标题')}")
                                ])
                            )
                    elif event_type == "stream.offline":
                        for group_id in plugin_config.live_shiro_group_ids:
                            await bot.send_group_msg(
                                group_id=group_id,
                                message=Message([
                                    MessageSegment.at('all'),
                                    MessageSegment.text(f" 🏁 {event['broadcaster_user_name']} 下播了～")
                                ])
                            )

                elif message_type == "session_reconnect":
                    new_url = data["payload"]["session"]["reconnect_url"]
                    logger.warning(f"🔄 Twitch要求重连：{new_url}")
                    await listen_eventsub()  # 递归重连，不需要 return

            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f"WebSocket错误: {msg.data}")
                break

async def twitch_bot_connect_handler(bot: Bot) -> Optional[Message]:
    logger.info("🚀 获取 Twitch App Access Token...")
    await get_app_token()
    if not ACCESS_TOKEN:
        logger.error("❌ 无法获取 token，插件停止启动")
        return

    logger.info("📡 检查主播状态...")
    await check_stream_status()

    logger.info("🔗 启动 EventSub WebSocket 监听...")
    asyncio.create_task(listen_eventsub())
    return Message("twitch监听已启动喵~")
