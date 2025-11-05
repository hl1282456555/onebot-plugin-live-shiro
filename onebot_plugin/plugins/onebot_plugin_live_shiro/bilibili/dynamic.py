from datetime import datetime
from typing import Optional

from bilibili_api import user
from nonebot import on_command
from nonebot.rule import to_me

from .dynamic_type import DynamicType


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

dynamic_command = on_command("bilibili", rule=to_me())
@dynamic_command.handle()
async def handle_dynamic_command():
    await dynamic_command.send("正在查找 Shiro 的最新动态...")

    all_dynamics = await fetch_all_dynamics(342642068)
    await dynamic_command.send(f"共找到 {len(all_dynamics)} 条动态。")

    last_dynamic = get_last_dynamic(all_dynamics)
    if not last_dynamic:
        await dynamic_command.finish("未找到有效动态。")

    push_time = pub_ts_to_str(last_dynamic["modules"]["module_author"]["pub_ts"])
    await dynamic_command.finish(f"Shiro 的最新动态发布时间：{push_time}")
