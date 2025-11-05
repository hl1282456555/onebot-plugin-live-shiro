from nonebot import require

require("nonebot_plugin_apscheduler")

from bilibili_api import select_client
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

select_client("httpx")

from . import alive
from . import bible
from . import common
from . import bilibili
