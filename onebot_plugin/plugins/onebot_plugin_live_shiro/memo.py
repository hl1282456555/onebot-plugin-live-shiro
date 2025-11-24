from typing import Optional

from nonebot import CommandGroup
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.params import ArgPlainText
from nonebot.rule import to_me
from nonebot_plugin_apscheduler import scheduler

memo_command_group = CommandGroup("memo", rule=to_me(), prefix_aliases=True)

help_command = memo_command_group.command("help")
@help_command.handle()
async def _(bot, event: MessageEvent, ars: str = ArgPlainText()):
    await help_command.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text("还在开发中喵~")
    ]))

async def memo_bot_connect_handler(bot: Bot) -> Optional[Message]:
    return Message("定时备忘录已启动喵~")
