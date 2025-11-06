from datetime import datetime
from typing import Optional

from bilibili_api import user
from nonebot import get_bot, get_plugin_config, logger, on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
from nonebot_plugin_apscheduler import scheduler

from ..config import Config
from .dynamic_type import DynamicType, MajorType

plugin_config = get_plugin_config(Config)

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

async def process_dynamic_ugc_season(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    major_ugc_season = major.get("ugc_season")
    if not major_ugc_season:
        await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了动态，但是解析失败喵~"))
        return

    combined_message = Message([
        MessageSegment.text(f"各位请注意！Shiro 在 {pub_time} 发布了一条 [剧集更新] 动态喵！\n"),
        MessageSegment.text(f'标题：{major_ugc_season.get("title", "无标题")}\n'),
        MessageSegment.text(f'简介：{major_ugc_season.get("desc", "无简介")}\n'),
        MessageSegment.text(f'链接：{major_ugc_season.get("jump_url", "无链接")}\n'),
    ])

    if cover_url := major_ugc_season.get("cover"):
        combined_message.append(MessageSegment.image(cover_url + "@300w_169h_.jpg"))

    await bot.send_group_msg(group_id=group_id, message=combined_message)

async def process_dynamic_article(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    major_article = major.get("article")
    if not major_article:
        await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了动态，但是解析失败喵~"))
        return

    combined_message = Message([
        MessageSegment.text(f"各位请注意！Shiro 在 {pub_time} 发布了一条 [专栏] 动态喵！\n"),
        MessageSegment.text(f'标题：{major_article.get("title", "无标题")}\n'),
        MessageSegment.text(f'简介：{major_article.get("desc", "无简介")}\n'),
        MessageSegment.text(f'链接：{major_article.get("jump_url", "无链接")}\n')
    ])

    for cover in major_article.get("covers", []):
        combined_message.append(MessageSegment.image(cover))

    await bot.send_group_msg(group_id=group_id, message=combined_message)

async def process_dynamic_draw(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    pass

async def process_dynamic_archive(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    pass

async def process_dynamic_live_rcmd(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    pass

async def process_dynamic_common(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    pass

async def process_dynamic_pgc(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    pass

async def process_dynamic_courses(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    pass

async def process_dynamic_music(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    pass

async def process_dynamic_opus(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    major_opus = major.get("opus")
    if not major_opus:
        await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了动态，但是解析失败喵~"))
        return

    combined_message = Message([
        MessageSegment.text(f"各位请注意！Shiro 在 {pub_time} 发布了一条 [图文] 动态喵！\n"),
        MessageSegment.text(f'标题：{major_opus.get("title", "无标题")}\n')
    ])

    summary = major_opus.get("summary")
    if not summary:
        combined_message.append(MessageSegment.text("简介：无简介\n"))
    else:
        combined_message.append(MessageSegment.text(f'简介：{summary.get("text", "无简介")}\n'))

    combined_message.append(MessageSegment.text(f'链接：{major_opus.get("jump_url", "无链接")}\n'))
    for image in major_opus.get("pics", []):
        if url := image.get("url"):
            combined_message.append(MessageSegment.image(url))

    await bot.send_group_msg(group_id=group_id, message=combined_message)

async def process_dynamic_live(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    major_live = major.get("live")
    if not major_live:
        await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了动态，但是解析失败喵~"))
        return

    live_state = major_live.get("live_state")
    if not live_state:
        await bot.send_group_msg(group_id=group_id, message=Message("获取到了直播状态，但是解析失败了瞄~"))

    if live_state == 1:
        start_message = Message([
            MessageSegment.text(f"各位请注意！Shiro {pub_time} 开始了直播喵！\n"),
            MessageSegment.text(f'标题：{major_live.get("title", "无标题")}\n'),
            MessageSegment.text(f'链接：{major_live.get("jump_url", "无链接")}\n'),
        ])

        if cover := major_live.get("cover"):
            start_message.append(MessageSegment.image(cover + "@300w_169h_.jpg"))
        await bot.send_group_msg(group_id=group_id, message=start_message)
    elif live_state == 0:
        end_message = Message([
            MessageSegment.text(f"各位请注意！Shiro {pub_time} 结束了直播喵！\n"),
            MessageSegment.text("期待下次再见喵~\n"),
        ])

        await bot.send_group_msg(group_id=group_id, message=end_message)

async def process_dynamic_none(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    pass

async def process_dynamic_upower_common(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    pass

dynamic_content_processors = {
    MajorType.MAJOR_TYPE_NONE: process_dynamic_none,
    MajorType.MAJOR_TYPE_OPUS: process_dynamic_opus,
    MajorType.MAJOR_TYPE_ARCHIVE: process_dynamic_archive,
    MajorType.MAJOR_TYPE_PGC: process_dynamic_pgc,
    MajorType.MAJOR_TYPE_COURSES: process_dynamic_courses,
    MajorType.MAJOR_TYPE_DRAW: process_dynamic_draw,
    MajorType.MAJOR_TYPE_ARTICLE: process_dynamic_article,
    MajorType.MAJOR_TYPE_MUSIC: process_dynamic_music,
    MajorType.MAJOR_TYPE_COMMON: process_dynamic_common,
    MajorType.MAJOR_TYPE_LIVE: process_dynamic_live,
    MajorType.MAJOR_TYPE_LIVE_RCMD: process_dynamic_live_rcmd,
    MajorType.MAJOR_TYPE_UGC_SEASON: process_dynamic_ugc_season,
    MajorType.MAJOR_TYPE_UPOWER_COMMON: process_dynamic_upower_common
}

async def get_latest_dynamic(bot: Bot, group_ids: list[int]) -> None:
    # bot = get_bot()
    # if not bot:
    #     logger.warning("Bot 未启动，无法获取动态信息")
    #     return

    logger.info("正在查找 Shiro 的最新动态...")

    all_dynamics = await fetch_all_dynamics(plugin_config.live_shiro_uid)
    logger.info(f"共找到 {len(all_dynamics)} 条动态。")

    last_dynamic = get_last_dynamic(all_dynamics)
    if not last_dynamic:
        logger.warning("未找到有效动态。")
        return

    push_ts_time = pub_ts_to_str(last_dynamic.get("modules", {})
                              .get("module_author", {})
                              .get("pub_ts", 0))

    pub_time = last_dynamic.get("modules", {}).get("module_author", {}).get("pub_time", "")

    logger.info(f"Shiro 的最新动态发布时间：{push_ts_time}")

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
        logger.warning("解析modules失败喵~")
        return

    module_dynamic = modules.get("module_dynamic")
    if not module_dynamic:
        logger.warning("解析module_dynamic失败喵~")
        return

    if dynamic_type == DynamicType.FORWARD:
        dynamic_content = module_dynamic.get("desc")
        if not dynamic_content:
            logger.warning("解析desc失败喵~")
            return

        text = dynamic_content.get("text")
        if not text:
            logger.warning("解析text失败喵~")
            return

        for group_id in group_ids:
            await bot.send_group_msg(group_id=group_id, message=Message([
                    MessageSegment.text(f"Shiro 在 {pub_time} 发布了一条动态喵！\n"),
                    MessageSegment.text(text)
                ]))
    else:
        dynamic_content = module_dynamic.get("major")
        if not dynamic_content:
            logger.warning("解析major失败喵")
            return

        major_type = MajorType[dynamic_content.get("type")]
        if major_type in dynamic_content_processors:
            for group_id in group_ids:
                await dynamic_content_processors[major_type](bot, group_id, dynamic_content, pub_time)
        else:
            for group_id in group_ids:
                await bot.send_group_msg(group_id=group_id, message=Message("解析到不支持的动态了喵~"))


test_common = on_command("test")
@test_common.handle()
async def _(bot):
    if not plugin_config.live_shiro_group_ids:
        logger.info("没有配置监听群列表，不查询Shiro的B站动态。")
        await test_common.finish("没有配置监听群列表，不查询Shiro的B站动态。")
    else:
        await get_latest_dynamic(bot, plugin_config.live_shiro_group_ids)

# scheduler.add_job(get_latest_dynamic, "interval", minutes=1, id="job_get_latest_dynamic")
