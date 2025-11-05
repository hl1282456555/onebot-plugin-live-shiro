from bilibili_api import user, select_client
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
from enum import Enum

select_client("httpx")

class DynamicType(Enum):
    NONE            = ("无效动态", "", -1, "")
    FORWARD         = ("动态转发", "动态本身id", 17, "")
    AV              = ("投稿视频", "视频AV号", 1, "视频AV号")
    PGC             = ("剧集（番剧、电影、纪录片）", "剧集分集AV号", 1, "剧集分集EP号")
    WORLD           = ("纯文字动态", "动态本身id", 17, "")
    DRAW            = ("带图动态", "相簿id", 11, "相簿id")
    ARTICLE         = ("投稿专栏", "专栏cv号", 12, "专栏cv号")
    MUSIC           = ("音乐", "音频au号", 14, "音频au号")
    COMMON_SQUARE   = ("装扮/剧集点评/普通分享", "", 17, "")
    LIVE            = ("直播间分享", "动态本身id", -1, "直播间id")
    MEDIALIST       = ("收藏夹", "收藏夹ml号", 19, "收藏夹ml号")
    COURSES_SEASON  = ("课程", "", -1, "")
    LIVE_RCMD       = ("直播开播", "动态本身id", 17, "live_id")
    UGC_SEASON      = ("合集更新", "视频AV号", 1, "视频AV号")

    def __init__(self, desc, comment_id_str_desc, comment_type, rid_str_desc):
        self.desc = desc
        self.comment_id_str_desc = comment_id_str_desc
        self.comment_type = comment_type
        self.rid_str_desc = rid_str_desc
        self.type_name = "DYNAMIC_TYPE_" + self.name

async def fetch_all_dynamics(uid: int) -> List[Dict]:
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

def get_last_dynamic(dynamics: List[Dict]) -> Optional[Dict]:
    """
    返回 dynamics 中最新的一条动态
    如果没有有效动态，返回 None
    """

    temp = []
    for item in dynamics:
        modules = item.get("modules", {})
        author = modules.get("module_author", {})
        pub_ts = author.get("pub_ts")
        type = item.get("type", "")

        if type == DynamicType.name:
            continue

        if not isinstance(pub_ts, int):
            continue

        temp.append((pub_ts, item))

    if not temp:
        return None

    temp.sort(key=lambda x: x[0], reverse=True)
    last_dynamic = temp[0][1]
    print(f'Lastest dynamic time - {pub_ts_to_str(temp[0][0])}')
    return last_dynamic

def pub_ts_to_str(pub_ts: int) -> str:
    """
    将动态 pub_ts 转换为可读时间字符串
    格式：YYYY-MM-DD HH:MM:SS
    """
    return datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%d %H:%M:%S")

def extract_dynamic_info(item: Dict) -> Dict:
    """
    从单条动态 item 提取统一结构
    支持：
        - 文字动态
        - 图文、多图动态
        - 视频动态
        - 作品 opus
    返回统一 dict:
    {
        "type": int,
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
    time_str = datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%d %H:%M:%S")
    author_name = author_info.get("name", "未知UP主")
    text = ""
    bvid = None
    cover = None
    url = None

    dyn_type = item.get("type")

    # 安全提取文本函数
    def get_text_from_desc(desc):
        if isinstance(desc, dict):
            return desc.get("text", "")
        elif isinstance(desc, str):
            return desc
        return ""

    # ===== 1. 优先取 module_dynamic.desc =====
    text = get_text_from_desc(dynamic_info.get("desc"))

    # ===== 2. 如果 text 为空，尝试 major 字段 =====
    major = dynamic_info.get("major", {})

    if not text:
        # 视频动态 / 投稿
        if "archive" in major:
            arc = major["archive"]
            text = get_text_from_desc(arc.get("desc"))
            bvid = arc.get("bvid")
            cover = arc.get("cover")
            url = f"https://www.bilibili.com/video/{bvid}" if bvid else None

        # 图文 / 多图动态
        elif "draw" in major:
            draw = major["draw"]
            text = get_text_from_desc(dynamic_info.get("desc")) or ""
            if draw.get("items"):
                cover = draw["items"][0].get("src")

        # 作品 opus
        elif "opus" in major:
            opus = major["opus"]
            summary = opus.get("summary", {})
            text = summary.get("text", "")
            url = f"https://www.bilibili.com/opus/{item.get('id_str')}"  # 跳转作品页面
            # 封面取第一张图片
            pics = opus.get("pics")
            if pics and isinstance(pics, list):
                cover = pics[0].get("url")

    # ===== 3. 去除首尾空格 =====
    text = text.strip() if isinstance(text, str) else ""

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