from typing import Optional

import httpx
from nonebot import get_plugin_config, logger
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot_plugin_apscheduler import scheduler

from ..config import Config

plugin_config = get_plugin_config(Config)

live_status = 0

async def check_live_status(bot: Bot):
    global live_status
    query_url = "https://api.live.bilibili.com/room/v1/Room/get_info"
    query_params = {
        "room_id" : plugin_config.live_shiro_bilibili_live_room_id
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(query_url, params=query_params)

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("code", 1) != 0:
                    logger.warning(f"Some errors occurred: {response_data['msg']}")
                    return

                room_info = response_data["data"]
                if room_info["live_status"] == live_status:
                    logger.info("Live status is not changed, skip broadcast.")
                    return

                live_status = room_info["live_status"]
                message = Message(MessageSegment.at('all'))
                if live_status == 0:
                    message += " Shiro 已经下播啦，辛苦各位观看喵~\n"
                elif live_status == 1:
                    message += " Shiro 已经开播啦，大家快来看喵~\n"
                elif live_status == 2:
                    message += " Shiro 正在播放轮播视频喵~\n"

                if cover_url := room_info.get("user_cover"):
                    message.append(MessageSegment.image(cover_url))
                    message.append(MessageSegment.text("\n"))

                if descritpion := room_info.get("description"):
                    message.append(MessageSegment.text(f"简介：{descritpion}\n"))

                message.append(MessageSegment.text(f"https://live.bilibili.com/{query_params['room_id']}"))
                for group_id in plugin_config.live_shiro_group_ids:
                    await bot.send_group_msg(group_id=group_id, message=message)

            else:
                logger.warning(f"Query bilibili live room info failed, code: {response.status_code}, return: {response.text}")

    except httpx.RequestError as err:
        logger.warning(f"Query bilibili live room info failed: {err}")

async def start_monitor_bilibili_live_status(bot: Bot) -> Optional[Message]:
    scheduler.add_job(check_live_status, trigger="interval")
    return Message("已开始监控 Shiro 的B站直播状态喵~")
