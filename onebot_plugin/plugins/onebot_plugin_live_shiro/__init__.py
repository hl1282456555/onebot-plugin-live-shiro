from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="onebot-plugin-live-shiro",
    description="A onebot plugin for vtuber Shiro.",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

from nonebot import on_command, on_keyword
from nonebot.adapters import Message
from nonebot.params import ArgPlainText, CommandArg
from nonebot.rule import to_me

alive_command = on_keyword(keywords={"还活着吗", "死了没"}, rule=to_me())

@alive_command.handle()
async def _():
    await alive_command.finish("还活着喵")

bible_book = {
    "shiro" : {
        "title": "伟大的Shiro曾经说过：",
        "content": [
            "《今天不耐久，玩一会就下播》",
            "《做完这个任务就睡》",
            "《整理完仓库就睡》",
            "《我光顾着玩了根本没时间切片》"
        ]
    },
    "member" : {
        "title": "堕入黑暗的群友曾经说过：",
        "content": [
            "《都怪柠檬》",
            "《单纯好色》"
        ]
    }
}

bible_command = on_command("bible", rule=to_me(), force_whitespace=True)

async def process_bible_command(bible_type: str) -> bool:
    if bible_type in bible_book:
        title = bible_book[bible_type]["title"]
        content = bible_book[bible_type]["content"]
        await bible_command.finish(title + "\n" + "\n".join(content))
    return False

@bible_command.handle()
async def _(args: Message = CommandArg()):
    bible_type = args.extract_plain_text()
    await process_bible_command(bible_type)


@bible_command.got("bible_type", prompt="你想看什么shiro圣经还是member圣经？")
async def _(bible_type: str = ArgPlainText()):
    result = await process_bible_command(bible_type)
    if not result:
        title = "暂时没有你想找的圣经喵，请在以下圣经中进行选中:"
        bible_type_list = "\n".join(bible_book.keys())
        await bible_command.reject(title + "\n" + bible_type_list)
