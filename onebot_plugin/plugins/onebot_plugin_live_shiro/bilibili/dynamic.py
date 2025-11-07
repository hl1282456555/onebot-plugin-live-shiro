import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from bilibili_api import user
from nonebot import get_bot, get_driver, get_plugin_config, logger
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot_plugin_apscheduler import scheduler

from ..config import Config
from .dynamic_type import DynamicType, MajorType

plugin_config = get_plugin_config(Config)

last_dynamic_timestamp: int = int(time.time())

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

def write_data_to_file_with_timestamp(subdir: str, base_name: str, data: str, ext = "txt") -> None:
    """
    使用 pathlib 将数据写入文件，文件名为 base_name + 当前时间戳 + ext。
    自动创建子目录（如果不存在）。

    :param subdir: 子目录名
    :param base_name: 文件名开头
    :param data: 要写入的数据
    :param ext: 文件扩展名，默认 txt
    :return: 写入文件的完整路径
    """
    # 当前目录
    cwd = Path.cwd()

    # 子目录路径
    dir_path = cwd / subdir
    dir_path.mkdir(parents=True, exist_ok=True)  # 创建子目录（可创建多级目录）

    # 当前时间戳
    timestamp = int(time.time())

    # 构造文件名
    filename = f"{base_name}_{timestamp}.{ext}"
    file_path = dir_path / filename

    # 写入文件
    file_path.write_text(data, encoding="utf-8")

    logger.info(f"数据已写入文件: {file_path}")

def process_jump_url(jump_url: str) -> str:
    return "https:" + jump_url if jump_url.startswith("//") else jump_url

async def process_dynamic_ugc_season(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    major_ugc_season = major.get("ugc_season")
    if not major_ugc_season:
        await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了动态，但是解析失败喵~"))
        return

    combined_message = Message([
        MessageSegment.text(f"各位请注意！Shiro 在 {pub_time} 发布了一条 [剧集更新] 动态喵！\n"),
        MessageSegment.text(f'标题：{major_ugc_season.get("title", "无标题")}\n'),
        MessageSegment.text(f'简介：{major_ugc_season.get("desc", "无简介")}\n'),
        MessageSegment.text(f'链接：{process_jump_url(major_ugc_season.get("jump_url", "无链接"))}\n'),
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
        MessageSegment.text(f'链接：{process_jump_url(major_article.get("jump_url", "无链接"))}\n')
    ])

    for cover in major_article.get("covers", []):
        combined_message.append(MessageSegment.image(cover))

    await bot.send_group_msg(group_id=group_id, message=combined_message)

async def process_dynamic_draw(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    major_draw = major.get("draw")
    if not major_draw:
        await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了动态，但是解析失败喵~"))
        return
    
    combined_message = Message([
        MessageSegment.text(f"各位请注意！Shiro 在 {pub_time} 发布了一条 [图片] 动态喵！\n"),
        MessageSegment.text(f'相簿ID：{major_draw.get("id", "未知")}\n')
    ])

    for item in major_draw.get("items", []):
        if url := item.get("src"):
            combined_message.append(MessageSegment.image(url))
    
    await bot.send_group_msg(group_id=group_id, message=combined_message)

async def process_dynamic_archive(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    major_archive = major.get("archive")
    if not major_archive:
        await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了动态，但是解析失败喵~"))
        return
    
    combined_message = Message([
        MessageSegment.text(f"各位请注意！Shiro 在 {pub_time} 发布了一条 [视频] 动态喵！\n"),
        MessageSegment.text(f'标题：{major_archive.get("title", "无标题")}\n'),
        MessageSegment.text(f'简介：{major_archive.get("desc", "无简介")}\n'),
        MessageSegment.text(f'链接：{process_jump_url(major_archive.get("jump_url", "无链接"))}\n')
    ])

    if cover_url := major_archive.get("cover"):
        combined_message.append(MessageSegment.image(cover_url + "@300w_169h_.jpg"))
    
    await bot.send_group_msg(group_id=group_id, message=combined_message)

async def process_dynamic_live_rcmd(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    write_data_to_file_with_timestamp("dynamic_context", "live_rcmd", json.dumps(major, ensure_ascii=False), "json")
    await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了直播推荐动态喵，已保存详细信息到文件。"))

async def process_dynamic_common(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    major_common = major.get("common")
    if not major_common:
        await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了动态，但是解析失败喵~"))
        return
    
    combined_message = Message([
        MessageSegment.text(f"各位请注意！Shiro 在 {pub_time} 发布了一条 [普通] 动态喵！\n"),
        MessageSegment.text(f'标题：{major_common.get("title", "无标题")}\n'),
        MessageSegment.text(f'简介：{major_common.get("desc", "无简介")}\n'),
        MessageSegment.text(f'链接：{process_jump_url(major_common.get("jump_url", "无链接"))}\n')
    ])

    if cover_url := major_common.get("cover"):
        combined_message.append(MessageSegment.image(cover_url + "@300w_169h_.jpg"))
    
    await bot.send_group_msg(group_id=group_id, message=combined_message)

async def process_dynamic_pgc(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    major_pgc = major.get("pgc")
    if not major_pgc:
        await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了动态，但是解析失败喵~"))
        return
    
    sub_type = major_pgc.get("sub_type", 0)
    sub_type_map = {
        1: "番剧",
        2: "电影",
        3: "纪录片",
        4: "国创",
        5: "电视剧",
        6: "漫画",
        7: "综艺"
    }

    combined_message = Message([
        MessageSegment.text(f"各位请注意！Shiro 在 {pub_time} 发布了一条 [剧集-{sub_type_map.get(sub_type, '未知类型')}] 动态喵！\n"),
        MessageSegment.text(f'标题：{major_pgc.get("title", "无标题")}\n'),
        MessageSegment.text(f'链接：{process_jump_url(major_pgc.get("jump_url", "无链接"))}\n')
    ])

    if cover_url := major_pgc.get("cover"):
        combined_message.append(MessageSegment.image(cover_url + "@300w_169h_.jpg"))
    
    await bot.send_group_msg(group_id=group_id, message=combined_message)

async def process_dynamic_courses(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了 [课程] 动态瞄~"))

async def process_dynamic_music(bot:Bot, group_id: int, major: dict, pub_time: str) -> None:
    major_music = major.get("music")
    if not major_music:
        await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布了动态，但是解析失败喵~"))
        return
    
    combined_message = Message([
        MessageSegment.text(f"各位请注意！Shiro 在 {pub_time} 发布了一条 [音乐] 动态喵！\n"),
        MessageSegment.text(f'标题：{major_music.get("title", "无标题")}\n'),
        MessageSegment.text(f'分类：{major_music.get("label", "未知")}\n'),
        MessageSegment.text(f'链接：{process_jump_url(major_music.get("jump_url", "无链接"))}\n')
    ])

    if cover_url := major_music.get("cover"):
        combined_message.append(MessageSegment.image(cover_url + "@300w_169h_.jpg"))

    await bot.send_group_msg(group_id=group_id, message=combined_message)

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

    combined_message.append(MessageSegment.text(f'链接：{process_jump_url(major_opus.get("jump_url", "无链接"))}\n'))
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
            MessageSegment.text(f'链接：{process_jump_url(major_live.get("jump_url", "无链接"))}\n'),
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
    await bot.send_group_msg(group_id=group_id, message=Message(f"Shiro {pub_time} 发布的动态失效了喵~"))

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

async def get_latest_dynamic() -> None:
    bot = get_bot()

    logger.info("正在查找 Shiro 的最新动态...")

    all_dynamics = await fetch_all_dynamics(plugin_config.live_shiro_uid)
    logger.info(f"共找到 {len(all_dynamics)} 条动态。")

    last_dynamic = get_last_dynamic(all_dynamics)
    if not last_dynamic:
        logger.warning("未找到有效动态。")
        return

    pub_ts = last_dynamic.get("modules", {}).get("module_author", {}).get("pub_ts", 0)
    pub_ts_time = pub_ts_to_str(pub_ts)

    global last_dynamic_timestamp
    if last_dynamic_timestamp >= pub_ts:
        logger.info("没有发现新的动态喵~")
        return

    last_dynamic_timestamp = pub_ts

    pub_time = last_dynamic.get("modules", {}).get("module_author", {}).get("pub_time", "")

    logger.info(f"Shiro 的最新动态发布时间：{pub_ts_time}")

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

        for group_id in plugin_config.live_shiro_group_ids:
            await bot.send_group_msg(group_id=group_id, message=Message([
                    MessageSegment.text(f"Shiro 在 {pub_time} 转发了一条动态喵！\n"),
                    MessageSegment.text(text)
                ]))
    else:
        dynamic_content = module_dynamic.get("major")
        if not dynamic_content:
            logger.warning("解析major失败喵")
            return

        major_type = MajorType[dynamic_content.get("type")]
        if major_type in dynamic_content_processors:
            for group_id in plugin_config.live_shiro_group_ids:
                await dynamic_content_processors[major_type](bot, group_id, dynamic_content, pub_time)
        else:
            for group_id in plugin_config.live_shiro_group_ids:
                await bot.send_group_msg(group_id=group_id, message=Message("解析到不支持的动态了喵~"))

bot_driver = get_driver()

@bot_driver.on_bot_connect
async def dynamic_handle_bot_connect(bot: Bot):
    if plugin_config.live_shiro_group_ids:
        scheduler.add_job(get_latest_dynamic, "interval", minutes=1, id="job_get_latest_dynamic")
        for group_id in plugin_config.live_shiro_group_ids:
            await bot.send_group_msg(group_id=group_id, message=Message(f"小助手开始监控 Shiro 的动态喵~"))
    else:
        logger.info("没有配置 live_shiro_group_ids，跳过动态监控任务的启动。")
