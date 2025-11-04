import importlib

from bilibili_api import select_client
from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

for _m in ("common", "alive", "bible", "bilibili"):
    importlib.import_module(f".{_m}", __name__)

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="onebot-plugin-live-shiro",
    description="A onebot plugin for vtuber Shiro.",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

select_client("httpx")


