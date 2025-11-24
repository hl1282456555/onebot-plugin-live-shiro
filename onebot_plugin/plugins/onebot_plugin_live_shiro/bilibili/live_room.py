from typing import Optional

from nonebot import get_plugin_config, logger
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot_plugin_apscheduler import scheduler

from bilibili_api import live

from ..config import Config

from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_PATH = ROOT_DIR / "cache" / "live_status.txt"

plugin_config = get_plugin_config(Config)

live_status = 0

def load_live_status_from_cache() -> int:
    if not CACHE_PATH.exists():
        return 0
    try:
        content = CACHE_PATH.read_text(encoding="utf-8").strip()
        return int(content or 0)
    except Exception:
        return 0

def save_live_status_to_cache(status: int):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(str(status), encoding="utf-8")


async def check_live_status(bot: Bot):
    global live_status

    live_room = live.LiveRoom(plugin_config.live_shiro_bilibili_live_room_id)
    live_room_info = await live_room.get_room_info()
    room_info = live_room_info["room_info"]
    logger.info(f"room_info: {json.dumps(room_info, ensure_ascii=False)}")
    if room_info["live_status"] == live_status:
        logger.info("Live status is not changed, skip broadcast.")
        return

    live_status = room_info["live_status"]
    save_live_status_to_cache(live_status)

    message = Message(MessageSegment.at('all'))
    if live_status == 0:
        message += " Shiro 已经下播啦，辛苦各位观看喵~\n"
    elif live_status == 1:
        message += " Shiro 已经开播啦，大家快来看喵~\n"
    elif live_status == 2:
        message += " Shiro 正在播放轮播视频喵~\n"

    if cover_url := room_info.get("cover"):
        message.append(MessageSegment.image(cover_url))
        message.append(MessageSegment.text("\n"))

    if title := room_info.get("title"):
        message.append(MessageSegment.text(f"标题：{title}\n"))

    if descritpion := room_info.get("description"):
        message.append(MessageSegment.text(f"简介：{descritpion}\n"))

    message.append(MessageSegment.text(f"直播间地址：https://live.bilibili.com/{plugin_config.live_shiro_bilibili_live_room_id}"))
    for group_id in plugin_config.live_shiro_group_ids:
        await bot.send_group_msg(group_id=group_id, message=message)

async def start_monitor_bilibili_live_status(bot: Bot) -> Optional[Message]:
    global live_status

    live_status = load_live_status_from_cache()
    logger.info(f"Initialized live_status from cache: {live_status}")

    scheduler.add_job(check_live_status, "interval", minutes=1, kwargs={'bot': bot})
    return Message("已开始监控 Shiro 的B站直播状态喵~")
