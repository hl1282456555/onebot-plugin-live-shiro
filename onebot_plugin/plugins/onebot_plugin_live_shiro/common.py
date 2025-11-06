from nonebot import on_command, get_plugin_config
from nonebot.rule import to_me

from .config import Config

plugin_config = get_plugin_config(Config)

twitch_command = on_command("twitch", rule=to_me(), force_whitespace=True)

@twitch_command.handle()
async def _():
    await twitch_command.finish(f"Shiro的Twitch频道是：{plugin_config.live_shiro_twitch_url}")

discord_command = on_command("discord", rule=to_me(), force_whitespace=True)

@discord_command.handle()
async def _():
    await discord_command.finish(f"Shiro的Discord服务器是：{plugin_config.live_shiro_discord_url}")

steam_command = on_command("steam", rule=to_me(), force_whitespace=True)

@steam_command.handle()
async def _():
    await steam_command.finish(f"Shiro的Steam好友码是：{plugin_config.live_shiro_steam_friend_code}")

__all__ = ["discord_command", "twitch_command"]
