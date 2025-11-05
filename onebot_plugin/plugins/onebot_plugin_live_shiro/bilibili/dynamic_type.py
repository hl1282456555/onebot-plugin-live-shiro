from enum import Enum


class DynamicType(Enum):
    NONE = ("无效动态", "", -1, "")
    FORWARD = ("动态转发", "动态本身id", 17, "")
    AV = ("投稿视频", "视频AV号", 1, "视频AV号")
    PGC = ("剧集（番剧、电影、纪录片）", "剧集分集AV号", 1, "剧集分集EP号")
    WORLD = ("纯文字动态", "动态本身id", 17, "")
    DRAW = ("带图动态", "相簿id", 11, "相簿id")
    ARTICLE = ("投稿专栏", "专栏cv号", 12, "专栏cv号")
    MUSIC = ("音乐", "音频au号", 14, "音频au号")
    COMMON_SQUARE = ("装扮/剧集点评/普通分享", "", 17, "")
    LIVE = ("直播间分享", "动态本身id", -1, "直播间id")
    MEDIALIST = ("收藏夹", "收藏夹ml号", 19, "收藏夹ml号")
    COURSES_SEASON = ("课程", "", -1, "")
    LIVE_RCMD = ("直播开播", "动态本身id", 17, "live_id")
    UGC_SEASON = ("合集更新", "视频AV号", 1, "视频AV号")

    def __init__(self, desc: str, comment_id_str_desc: str, comment_type: int, rid_str_desc: str) -> None:
        self.desc = desc
        self.comment_id_str_desc = comment_id_str_desc
        self.comment_type = comment_type
        self.rid_str_desc = rid_str_desc
        self.type_name = "DYNAMIC_TYPE_" + self.name

    @staticmethod
    def type_name_prefix() -> str:
        return "DYNAMIC_TYPE_"

    @classmethod
    def from_dynamic_type(cls, dynamic_type: str) -> "DynamicType":
        if dynamic_type and dynamic_type.startswith("DYNAMIC_TYPE_"):
            type_name = dynamic_type[len(cls.type_name_prefix()):]
            try:
                return cls[type_name]
            except KeyError:
                return cls.NONE
        return cls.NONE

class MajorType(Enum):
    MAJOR_TYPE_NONE             = (0)
    MAJOR_TYPE_FORWARD          = (1)
    MAJOR_TYPE_OPUS             = (2)
    MAJOR_TYPE_ARCHIVE          = (3)
    MAJOR_TYPE_PGC              = (4)
    MAJOR_TYPE_COURSES          = (5)
    MAJOR_TYPE_DRAW             = (6)
    MAJOR_TYPE_ARTICLE          = (7)
    MAJOR_TYPE_MUSIC            = (8)
    MAJOR_TYPE_COMMON           = (9)
    MAJOR_TYPE_LIVE             = (10)
    MAJOR_TYPE_MEDIALIST        = (11)
    MAJOR_TYPE_APPLET           = (12)
    MAJOR_TYPE_SUBSCRIPTION     = (13)
    MAJOR_TYPE_LIVE_RCMD        = (14)
    MAJOR_TYPE_UGC_SEASON       = (15)
    MAJOR_TYPE_SUBSCRIPTION_NEW = (16)
    MAJOR_TYPE_UPOWER_COMMON    = (17)

__all__ = ["DynamicType"]

