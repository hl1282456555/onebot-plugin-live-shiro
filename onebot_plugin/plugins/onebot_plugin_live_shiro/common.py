from nonebot import on_command
from nonebot.rule import to_me

twitch_command = on_command("twitch", rule=to_me(), force_whitespace=True)

@twitch_command.handle()
async def _():
    await twitch_command.finish("Shiro的Twitch频道是：https://www.twitch.tv/shiroyukitv")

discord_command = on_command("discord", rule=to_me(), force_whitespace=True)

@discord_command.handle()
async def _():
    await discord_command.finish("Shiro的Discord服务器是：https://discord.gg/uAYcmfszP")

__all__ = ["discord_command", "twitch_command"]
