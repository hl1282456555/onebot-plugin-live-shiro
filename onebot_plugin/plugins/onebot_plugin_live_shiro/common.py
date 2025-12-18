from nonebot import on_command, get_plugin_config
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent

from .config import Config

import aiosqlite

from contextlib import asynccontextmanager
from prettytable import PrettyTable

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

def format_table(data, headers):
    """
    将二维数组格式化为PrettyTable字符串，适合发送到QQ等宽显示。
    
    data: List[List[str]]，每个子列表为一行
    headers: List[str]，表头列表
    返回: str，带代码块的表格
    """
    if not data or not headers:
        return "```\n空表格\n```"
    
    table = PrettyTable()
    table.field_names = headers
    
    # 添加每一行
    for row in data:
        table.add_row(row)
    
    # 全部左对齐，中文对齐良好
    for h in headers:
        table.align[h] = "l"
    
    # 返回带代码块的表格
    return f"```\n{table}\n```"

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

help_command = on_command("help", aliases={"h", "help"}, rule=to_me())
@help_command.handle()
async def _(event: MessageEvent):
    await help_command.finish(message=Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text("感谢垂询小助手功能列表，以下是使用方式：\n"),
        MessageSegment.text(format_table(help_list, ["前缀", "命令", "说明"]))
    ]))
