from typing import Optional

from nonebot import CommandGroup
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.rule import to_me

memo_command_group = CommandGroup("memo", rule=to_me())

help_command = memo_command_group.command("help")
@help_command.handle()
async def handle_memo_help_command(bot, event: MessageEvent):
    await help_command.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text("定时备忘录帮助文档：\n"),
        MessageSegment.text("1. 添加备忘录：@我 /memo.add <时间> <内容>\n"),
        MessageSegment.text("2. 查看备忘录：@我 /memo.list\n"),
        MessageSegment.text("3. 删除备忘录：@我 /memo.delete <备忘录ID>\n"),
        MessageSegment.text("4. 修改备忘录：@我 /memo.edit <备忘录ID> <时间> <内容>\n"),
        MessageSegment.text("5. 帮助文档：@我 /memo.help\n"),
        MessageSegment.text("以上功能均未完成喵~")
    ]))

add_command = memo_command_group.command("add")
@add_command.handle()
async def handle_memo_add_command(bot, event: MessageEvent):
    pass

list_command = memo_command_group.command("list")
@list_command.handle()
async def handle_memo_list_command(bot, event: MessageEvent):
    pass

delete_command = memo_command_group.command("delete")
@delete_command.handle()
async def handle_memo_delete_command(bot, event: MessageEvent):
    pass

edit_command = memo_command_group.command("edit")
@edit_command.handle()
async def handle_memo_edit_command(bot, event: MessageEvent):
    pass

async def memo_bot_connect_handler(bot: Bot) -> Optional[Message]:
    return Message("定时备忘录已启动喵~")
