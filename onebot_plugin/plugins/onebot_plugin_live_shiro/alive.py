from nonebot import on_keyword
from nonebot.rule import to_me

alive_command = on_keyword(keywords={"还活着吗", "死了没"}, rule=to_me())

@alive_command.handle()
async def _():
    await alive_command.finish("还活着喵")

__all__ = ["alive_command"]
