from nonebot import get_bot, on_keyword
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.rule import to_me
from nonebot_plugin_apscheduler import scheduler

alive_command = on_keyword(keywords={"还活着吗", "死了没"}, rule=to_me())

@alive_command.handle()
async def _():
    await alive_command.finish("还活着喵")

async def shiro_sleep_clock():
    bot = get_bot()
    if not bot:
        return
    await bot.send_group_msg(group_id=0, message=Message([
            MessageSegment.at(""),
            MessageSegment.text("嘀嘀嘀，睡觉提醒服务时间")
        ]))

scheduler.add_job(shiro_sleep_clock, trigger="cron", hour=2, minute=0, id="job_shiro_sleep_clock")

__all__ = ["alive_command"]
