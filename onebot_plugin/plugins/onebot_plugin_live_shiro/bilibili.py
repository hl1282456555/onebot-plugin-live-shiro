from bilibili_api import user
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.rule import to_me

bili_user = user.User(342642068)

def is_top_dynamic(dynamic: dict) -> bool:
    text = dynamic.get("modules", {}).get("module_tag", {}).get("text")
    return bool(text)

# def convert_dynamic_to_notice(dynamic: dict) -> Message:
#     return Message("还没好喵")

bili_command = on_command("bilibili", rule=to_me(), force_whitespace=True)
@bili_command.handle()
async def _(args: Message = CommandArg()):
    sub_command = args.extract_plain_text()
    if sub_command == "动态":
        next_offset = ""
        last_dynamic = {}
        while True:
            page = await bili_user.get_dynamics_new(next_offset)
            dynamics = page["items"]

            for dynamic in dynamics.get("items", []):
                visible = dynamic.get("visible")
                if visible and not is_top_dynamic(dynamic):
                    last_dynamic = dynamic
                    break

            if page["has_more"] != 1:
                break

        await bili_command.finish(str(last_dynamic))



__all__ = ["bili_command", "bili_user"]
