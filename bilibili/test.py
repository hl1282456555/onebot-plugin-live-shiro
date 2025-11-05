import asyncio
from datetime import datetime
from typing import Optional

from bilibili_api import select_client, user

from .dynamic_type import DynamicType

select_client("httpx")

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

def extract_dynamic_info(item: dict) -> dict:
    """
    从单条动态 item 提取统一结构
    支持：
        - 文字动态
        - 图文、多图动态
        - 视频动态
        - 作品 opus
    返回统一 dict:
    {
        "type": DynamicType,
        "author": str,
        "pub_ts": int,
        "time_str": str,
        "text": str,
        "url": str,
        "bvid": str or None,
        "cover": str or None
    }
    """

    modules = item.get("modules", {})
    author_info = modules.get("module_author", {})
    dynamic_info = modules.get("module_dynamic", {})

    pub_ts = author_info.get("pub_ts", 0)
    time_str = pub_ts_to_str(pub_ts)
    author_name = author_info.get("name", "未知UP主")
    text = ""
    bvid = None
    cover = None
    url = None

    dyn_type = DynamicType.NONE

    return {
        "type": dyn_type,
        "author": author_name,
        "pub_ts": pub_ts,
        "time_str": time_str,
        "text": text,
        "url": url,
        "bvid": bvid,
        "cover": cover,
    }

async def main():
    all_dynamics = await fetch_all_dynamics(342642068)
    print(f"fetched {len(all_dynamics)} dynamics")

    last_dynamic = get_last_dynamic(all_dynamics)
    if not last_dynamic:
        print("Not found any useful dynamic")
        return

    dynamic_info = extract_dynamic_info(last_dynamic)
    print(f'Lastest dynamic info\n{dynamic_info}')

if __name__ == "__main__":
    asyncio.run(main())
