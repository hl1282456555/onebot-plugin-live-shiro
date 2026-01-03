from typing import Optional
import asyncio
import json
import aiohttp
from aiohttp_socks import ProxyConnector
from aiohttp import web

from nonebot import get_plugin_config, get_bot, get_driver, logger
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from ..config import Config

plugin_config = get_plugin_config(Config)
dirver_config = get_driver().config

# ==============================
# ⚙️ 配置区
# ==============================
CLIENT_ID = plugin_config.live_shiro_twitch_client_id
CLIENT_SECRET = plugin_config.live_shiro_twitch_client_secret
BROADCASTER_ID = "629147503"  # 主播ID
PROXY_URL = "http://127.0.0.1:10808"  # HTTP/HTTPS 代理端口

# OAuth / cloudflared 配置
REDIRECT_URI = plugin_config.live_shiro_twitch_redirect_uri
LOCAL_OAUTH_HOST = plugin_config.live_shiro_twitch_oauth_host
LOCAL_OAUTH_PORT = plugin_config.live_shiro_twitch_oauth_port
OAUTH_SCOPE = plugin_config.live_shiro_twitch_oauth_scope

# ==============================
# 🔑 全局变量
# ==============================
ACCESS_TOKEN: Optional[str] = None
OAUTH_CODE: Optional[str] = None

# ==============================
# 🔗 OAuth URL 生成
# ==============================
def get_auth_url() -> str:
    return (
        "https://id.twitch.tv/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        f"&scope={OAUTH_SCOPE}"
    )

# ==============================
# 🔑 本地 OAuth 回调服务
# ==============================
async def oauth_callback(request: web.Request):
    global OAUTH_CODE
    OAUTH_CODE = request.query.get("code")
    if not OAUTH_CODE:
        return web.Response(text="授权失败，没有 code", status=400)
    return web.Response(text="Twitch 授权成功，可以关闭页面了~")

async def start_oauth_server():
    app = web.Application()
    app.router.add_get("/twitch/callback", oauth_callback)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, LOCAL_OAUTH_HOST, LOCAL_OAUTH_PORT)
    await site.start()
    logger.info(f"✅ OAuth server 已启动 http://{LOCAL_OAUTH_HOST}:{LOCAL_OAUTH_PORT}/twitch/callback")

# ==============================
# 🔑 使用 code 获取 User Access Token
# ==============================
async def get_user_token(code: str):
    global ACCESS_TOKEN
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }

    connector = ProxyConnector.from_url(PROXY_URL)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, params=params) as resp:
            data = await resp.json()
            ACCESS_TOKEN = data.get("access_token")
            if ACCESS_TOKEN:
                logger.info("✅ 成功获取 User Access Token")
            else:
                logger.error(f"❌ 获取 User token 失败: {data}")

# ==============================
# 🔍 检查主播状态
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
                            MessageSegment.text(
                                f"🎬 {data['data'][0]['user_name']} 当前正在直播！\n标题：{data['data'][0].get('title', '无标题')}"
                            )
                        ])
                    )

# ==============================
# 🚀 EventSub 注册
# ==============================
async def subscribe_eventsub(session: aiohttp.ClientSession, session_id: str):
    url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
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
            logger.info(f"📡 EventSub {event_type}: {r}")

    await sub("stream.online")
    await sub("stream.offline")

# ==============================
# 🌐 EventSub WebSocket 监听
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
                meta = data.get("metadata", {})
                msg_type = meta.get("message_type")

                if msg_type == "session_welcome":
                    session_id = data["payload"]["session"]["id"]
                    logger.info(f"🪄 EventSub Session ID: {session_id}")
                    await subscribe_eventsub(session, session_id)

                elif msg_type == "notification":
                    payload = data["payload"]
                    event_type = payload["subscription"]["type"]
                    event = payload["event"]

                    bot = get_bot()
                    if event_type == "stream.online":
                        for gid in plugin_config.live_shiro_group_ids:
                            await bot.send_group_msg(
                                group_id=gid,
                                message=Message([
                                    MessageSegment.at("all"),
                                    MessageSegment.text(
                                        f"🎬 {event['broadcaster_user_name']} 开播啦！\n标题：{event.get('title', '无标题')}"
                                    )
                                ])
                            )

                    elif event_type == "stream.offline":
                        for gid in plugin_config.live_shiro_group_ids:
                            await bot.send_group_msg(
                                group_id=gid,
                                message=Message([
                                    MessageSegment.at("all"),
                                    MessageSegment.text(
                                        f"🏁 {event['broadcaster_user_name']} 下播了～"
                                    )
                                ])
                            )

async def wait_for_oauth_code(timeout: int = 120):  # 5 分钟超时
    global OAUTH_CODE
    start = asyncio.get_event_loop().time()
    while OAUTH_CODE is None:
        await asyncio.sleep(1)
        if asyncio.get_event_loop().time() - start > timeout:
            logger.error("⏱ OAuth 授权超时，停止启动 bot")
            return False
    return True

# ==============================
# 🏁 Nonebot 启动入口
# ==============================
async def twitch_bot_connect_handler(bot: Bot) -> Optional[Message]:
    logger.info("🚀 启动 Twitch OAuth 回调服务...")
    await start_oauth_server()

    auth_url = get_auth_url()
    logger.warning(f"👉 请在浏览器打开完成授权：\n{auth_url}")
    for user_id in dirver_config.superusers:
        await bot.send_private_msg(user_id=user_id, message=Message(f"👉 请在浏览器打开完成Twitch授权：\n{auth_url}"))

    # 等待授权，但加超时
    success = await wait_for_oauth_code()
    if not success:
        logger.error("❌ OAuth 授权失败")
        return Message("Twitch OAuth 授权失败")

    if not OAUTH_CODE:
        logger.error("❌ OAuth 授权失败")
        return Message("Twitch OAuth 授权失败")

    await get_user_token(OAUTH_CODE)
    if not ACCESS_TOKEN:
        logger.error("❌ 获取 User Token 失败")
        return Message("Twitch User Token 获取失败")

    logger.info("🔗 启动 EventSub WebSocket 监听...")
    asyncio.create_task(listen_eventsub())

    logger.info("✅ Twitch WebSocket 监听已启动")
    return Message("Twitch 监听已启动喵~")
