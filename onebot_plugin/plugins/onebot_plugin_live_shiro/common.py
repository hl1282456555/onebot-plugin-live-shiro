from nonebot import on_command, get_plugin_config
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent

from .config import Config
from . import message_render

import aiosqlite

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_connection(path: str):
    db = await aiosqlite.connect(path)
    await db.execute("PRAGMA foreign_keys = ON;")
    try:
        yield db
    finally:
        await db.close()

plugin_config = get_plugin_config(Config)

twitch_command = on_command("twitch", rule=to_me(), force_whitespace=True)

@twitch_command.handle()
async def _():
    await twitch_command.finish(f"Shiro的Twitch频道是：{plugin_config.live_shiro_twitch_url}")

discord_command = on_command("discord", rule=to_me(), force_whitespace=True)

@discord_command.handle()
async def _():
    await discord_command.finish(f"Shiro的Discord服务器是：{plugin_config.live_shiro_discord_url}")

steam_command = on_command("steam", rule=to_me(), force_whitespace=True)

@steam_command.handle()
async def _():
    await steam_command.finish(f"Shiro的Steam好友码是：{plugin_config.live_shiro_steam_friend_code}")


help_list = [
    ["/", "@小助手 /bible", "查看圣经"],
    ["引用消息", "@小助手 /vote 撤回", "撤回引用的消息"],
    ["引用消息", "@小助手 /cut_meme", "按照指定行列数，裁剪图片"],
    ["/", "@小助手 /clear_cut_meme_cache", "清理裁剪缓存"],
    ["/", "@小助手 /rd [1]d[100]", "掷骰子"],
    ["/", "/prefix_dog", "自动撤回本条消息"],
    ["/", "@小助手 /twitch", "查看Shiro的twitch频道"],
    ["/", "@小助手 /discord", "查看Shiro的discord频道"],
    ["/", "@小助手 /steam", "查看Shiro的stream好友码"]
]

help_command = on_command("help", aliases={"h", "帮助", "菜单"}, rule=to_me())
@help_command.handle()
async def _(event: MessageEvent):
    table_data = {
        "title": "小助手指令列表",
        "headers": ["前置条件", "指令格式", "功能说明"],
        "rows": help_list
    }
    image_data = await message_render.render_png_from_template(message_render.RenderPageType.TABLE, table_data, width=800)
    await help_command.finish(message=Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.image(image_data)
    ]))
