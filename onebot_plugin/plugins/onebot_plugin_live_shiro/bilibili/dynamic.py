from datetime import datetime
from typing import Optional

from bilibili_api import user
from nonebot import get_bot, logger, on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
from nonebot_plugin_apscheduler import scheduler

from .dynamic_type import DynamicType, MajorType

import json

async def fetch_all_dynamics(uid: int) -> list[dict]:
    """
    查询指定uid用户的所有动态
    """

    bili_user = user.User(uid)

    next_offset = ""
    dynamics = []

    while True:
        page = await bili_user.get_dynamics_new(next_offset)
        dynamics.extend(page["items"])

        if page["has_more"] != 1:
            break
        next_offset = page["offset"]

    return dynamics

def get_last_dynamic(dynamics: list[dict]) -> Optional[dict]:
    """
    返回 dynamics 中最新的一条动态
    如果没有有效动态，返回 None
    """

    temp = []
    for item in dynamics:
        modules = item.get("modules", {})
        author = modules.get("module_author", {})
        pub_ts = author.get("pub_ts")
        dynamic_type = item.get("type", "")

        if dynamic_type == DynamicType.NONE.type_name:
            continue

        if not isinstance(pub_ts, int):
            continue

        temp.append((pub_ts, item))

    if not temp:
        return None

    temp.sort(key=lambda x: x[0], reverse=True)
    return temp[0][1]

def pub_ts_to_str(pub_ts: int) -> str:
    """
    将动态 pub_ts 转换为可读时间字符串
    格式：YYYY-MM-DD HH:MM:SS
    """
    return datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%d %H:%M:%S")  # noqa: DTZ006

async def get_latest_dynamic(bot: Bot):
    # bot = get_bot()
    # if not bot:
    #     logger.warning("Bot 未启动，无法获取动态信息")
    #     return

    logger.info("正在查找 Shiro 的最新动态...")

    all_dynamics = await fetch_all_dynamics(342642068)
    logger.info(f"共找到 {len(all_dynamics)} 条动态。")

    last_dynamic = get_last_dynamic(all_dynamics)
    if not last_dynamic:
        logger.warning("未找到有效动态。")
        return

    push_time = pub_ts_to_str(last_dynamic.get("modules", {})
                              .get("module_author", {})
                              .get("pub_ts", 0))
    logger.info(f"Shiro 的最新动态发布时间：{push_time}")

    # dynamic_message = DynamicParser(last_dynamic).parse()
    # if not dynamic_message:
    #     logger.warning("动态解析失败。")
    #     return

    dynamic_type = DynamicType.from_dynamic_type(last_dynamic.get("type", ""))

    modules = {}
    if dynamic_type == DynamicType.FORWARD:
        modules = last_dynamic.get("orig")
    else:
        modules = last_dynamic.get("modules")

    if not modules:
        await bot.send_group_msg(group_id=1013384847, message=Message("解析modules失败喵"))
        return

    module_dynamic = modules.get("module_dynamic")
    if not module_dynamic:
        await bot.send_group_msg(group_id=1013384847, message=Message("解析module_dynamic失败喵"))
        return

    if dynamic_type == DynamicType.FORWARD:
        dynamic_content = module_dynamic.get("desc")
        if not dynamic_content:
            await bot.send_group_msg(group_id=1013384847, message=Message("解析desc失败喵"))
            return

        text = dynamic_content.get("text", "")
        await bot.send_group_msg(group_id=1013384847, message=Message([
                MessageSegment.text("Shiro 在 {push_time} 发布了一条动态喵！\n"),
                MessageSegment.text(text)
            ]))
    else:
        dynamic_content = module_dynamic.get("major")
        if not dynamic_content:
            await bot.send_group_msg(group_id=1013384847, message=Message("解析major失败喵"))
            return
        
        major_type = MajorType[dynamic_content.get("type")]
        if major_type == MajorType.MAJOR_TYPE_NONE:
            await bot.send_group_msg(group_id=1013384847, message=Message("最新的动态失效了喵~"))
        elif major_type == MajorType.MAJOR_TYPE_UGC_SEASON:
            await bot.send_group_msg(group_id=1013384847, message=Message("解析到剧集动态了喵~"))
        else:
            await bot.send_group_msg(group_id=1013384847, message=Message("解析到无效数据了喵~"))



test_common = on_command("test")
@test_common.handle()
async def _(bot):
    await get_latest_dynamic(bot)

# scheduler.add_job(get_latest_dynamic, "interval", minutes=1, id="job_get_latest_dynamic")
