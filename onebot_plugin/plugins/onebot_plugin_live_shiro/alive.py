from nonebot import get_bot, get_driver, get_plugin_config, on_keyword
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.rule import to_me
from nonebot_plugin_apscheduler import scheduler

from .config import Config

plugin_config = get_plugin_config(Config)

alive_command = on_keyword(keywords={"还活着吗", "死了没"}, rule=to_me())

@alive_command.handle()
async def _():
    await alive_command.finish("还活着喵")

async def shiro_sleep_clock():
    bot = get_bot()

    for group_id in plugin_config.live_shiro_group_ids:
        await bot.send_group_msg(group_id=group_id, message=Message([
            MessageSegment.at(plugin_config.live_shiro_shiro_qid),
            MessageSegment.text("老大，睡觉时间到了喵，早点休息喵~")
        ]))

bot_driver = get_driver()

@bot_driver.on_bot_connect
async def alive_handle_bot_connect(bot: Bot):
    if plugin_config.live_shiro_group_ids:
        for group_id in plugin_config.live_shiro_group_ids:
            await bot.send_group_msg(group_id=group_id, message=Message(f"小助手已经安全启动，今天又是美好的一天瞄~"))
        await bot.send_group_msg(group_id=plugin_config.live_shiro_group_ids[0], message=Message(f"老大的助眠闹钟 {plugin_config.live_shiro_sleep_clock_hour}:{plugin_config.live_shiro_sleep_clock_minute} 已安全启动瞄~"))

        scheduler.add_job(shiro_sleep_clock, trigger="cron",
                      hour=plugin_config.live_shiro_sleep_clock_hour,
                      minute=plugin_config.live_shiro_sleep_clock_minute,
                      id="job_shiro_sleep_clock")


__all__ = ["alive_command"]
