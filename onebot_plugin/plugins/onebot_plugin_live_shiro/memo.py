from typing import Optional

from nonebot import on_command, get_driver, get_plugin_config, logger
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.rule import to_me

from nonebot_plugin_apscheduler import scheduler

from .common import get_db_connection
from .config import Config

import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import AsyncOpenAI

MEMO_DB_PATH = "./cache/memo.db"

BEIJING_TZ = ZoneInfo("Asia/Shanghai")  # 北京时间

memo_tools = [
    {
        "type": "function",
        "function": {
            "name": "create_memo",
            "description": "创建一个新的备忘录提醒，支持单次或循环提醒",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_id": {"type": ["integer", "null"], "description": "群组 ID，如果是群提醒，可不填则默认为私聊"},
                    "content": {"type": "string", "description": "备忘录的文本内容"},
                    "scheduled_time": {"type": ["string", "null"], "description": "单次提醒时间，ISO 8601"},
                    "loop_type": {"type": "integer", "description": "循环类型：0=不循环,1=每日,2=每周,3=每月,4=每年"},
                    "loop_hour": {"type": ["integer", "null"], "description": "循环提醒小时 0-23"},
                    "loop_minute": {"type": ["integer", "null"], "description": "循环提醒分钟 0-59"},
                    "loop_weekday": {"type": ["integer", "null"], "description": "每周循环时 0=周一, 6=周日"},
                    "loop_day": {"type": ["integer", "null"], "description": "每月/每年循环时表示几号"},
                    "loop_month": {"type": ["integer", "null"], "description": "每年循环时表示月份 1-12"}
                },
                "required": ["content", "loop_type"]
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_memo",
            "description": "更新已有的备忘录，可修改内容、提醒时间或循环参数",
            "parameters": {
                "type": "object",
                "properties": {
                    "memo_id": {"type": "integer", "description": "需要更新的备忘录 ID"},
                    "content": {"type": ["string", "null"], "description": "新的备忘录内容，可选"},
                    "scheduled_time": {"type": ["string", "null"], "description": "新的单次提醒时间，ISO 8601，可选"},
                    "loop_type": {"type": ["integer", "null"], "description": "新的循环类型，可选"},
                    "loop_hour": {"type": ["integer", "null"], "description": "循环提醒小时 0-23"},
                    "loop_minute": {"type": ["integer", "null"], "description": "循环提醒分钟 0-59"},
                    "loop_weekday": {"type": ["integer", "null"], "description": "每周循环时 0=周一, 6=周日"},
                    "loop_day": {"type": ["integer", "null"], "description": "每月/每年循环时表示几号"},
                    "loop_month": {"type": ["integer", "null"], "description": "每年循环时表示月份 1-12"},
                    "group_id": {"type": ["integer", "null"], "description": "新的群组 ID，可选"}
                },
                "required": ["memo_id"]
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_memo",
            "description": "删除指定的备忘录",
            "parameters": {
                "type": "object",
                "properties": {
                    "memo_id": {"type": "integer", "description": "备忘录 ID"}
                },
                "required": ["memo_id"]
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_memos",
            "description": "列出所有备忘录",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "strict": True
        }
    }
]

SYSTEM_PROMPT =(
    "你是备忘录助理。用户可能创建、更新、删除或查询备忘录。"
    "如果用户请求与备忘录相关，调用对应工具：  "
    "- 创建 → create_memo  "
    "- 更新 → update_memo  "
    "- 删除 → delete_memo  "
    "- 查询 → list_memos  "
    "如果请求无关备忘录，直接用自然语言回答即可。 "
)

plugin_config = get_plugin_config(Config)

memo_command = on_command("memo", rule=to_me(), force_whitespace=True)
@memo_command.handle()
async def handle_memo_command(bot: Bot, event: MessageEvent):
    content = event.get_plaintext()
    llm_client = AsyncOpenAI(api_key=plugin_config.live_shiro_deep_seek_key, base_url="https://api.deepseek.com/beta")

    llm_response = await llm_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        max_tokens=1024,
        tools=memo_tools
    )

    reply_text = "不想理你喵~"
    if getattr(llm_response, "choices", None):
        choice = llm_response.choices[0]
        message = getattr(choice, "message", None)
        if message:
            if function_call := getattr(message, "function_call", None):
                reply_text = f"想要调用工具{function_call.get('name')}"
            elif message_content := getattr(message, "content", None):
                reply_text = message_content

    await memo_command.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(reply_text)
    ]))

async def memo_bot_connect_handler(bot: Bot) -> Optional[Message]:
    await load_all_memo_jobs()
    return Message("定时备忘录已启动喵~")

async def send_memo_reminder(bot: Bot, content: str, user_id: int, group_id: int):
    await bot.send_group_msg(group_id=group_id, message=Message([
        MessageSegment.at(user_id=user_id),
        MessageSegment.text(" 老大，你预定的备忘录提醒到了喵~\n"),
        MessageSegment.text(f"内容：{content}")
    ]))

def schedule_memo_job(memo: dict):
    memo_id = memo["id"]
    content = memo["content"]
    user_id = memo["initiator_id"]
    loop_type = memo["loop_type"]
    loop_param = memo.get("loop_param") or {}
    group_id = memo.get("group_id", 0)

    job_id = f"memo_{memo_id}"

    # 移除已有任务
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # 单次任务
    if loop_type == 0:
        if not memo.get("scheduled_time"):
            return
        run_dt = datetime.fromisoformat(memo["scheduled_time"]).astimezone(BEIJING_TZ)
        scheduler.add_job(
            send_memo_reminder,
            "date",
            run_date=run_dt,
            args=[memo_id, content, user_id, group_id],
            id=job_id,
            replace_existing=True,
            timezone=BEIJING_TZ
        )
    else:
        cron_args = {}
        if loop_type == 1:  # 每日
            cron_args = {"hour": loop_param.get("hour", 9),
                         "minute": loop_param.get("minute", 0)}
        elif loop_type == 2:  # 每周
            cron_args = {"day_of_week": loop_param.get("weekday", 0),
                         "hour": loop_param.get("hour", 9),
                         "minute": loop_param.get("minute", 0)}
        elif loop_type == 3:  # 每月
            cron_args = {"day": loop_param.get("day", 1),
                         "hour": loop_param.get("hour", 9),
                         "minute": loop_param.get("minute", 0)}
        elif loop_type == 4:  # 每年
            cron_args = {"month": loop_param.get("month", 1),
                         "day": loop_param.get("day", 1),
                         "hour": loop_param.get("hour", 9),
                         "minute": loop_param.get("minute", 0)}
        else:
            logger.warning(f"未知循环类型 {loop_type}，备忘录 {memo_id} 不注册任务")
            return

        scheduler.add_job(
            send_memo_reminder,
            "cron",
            args=[memo_id, content, user_id, group_id],
            id=job_id,
            replace_existing=True,
            timezone=BEIJING_TZ,
            **cron_args
        )

    logger.info(f"已注册备忘录 {memo_id} 的提醒任务")

# -------------------- 数据库操作 --------------------
async def init_db():
    os.makedirs(os.path.dirname(MEMO_DB_PATH), exist_ok=True)
    async with get_db_connection(MEMO_DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memo_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                initiator_id INTEGER DEFAULT 0,
                create_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                scheduled_time DATETIME,
                loop_type INTEGER DEFAULT 0,
                loop_param TEXT,
                content TEXT NOT NULL,
                group_id INTEGER DEFAULT 0
            )
        """)
        await db.commit()
        logger.info("数据库初始化完成")

async def load_all_memo_jobs():
    async with get_db_connection(MEMO_DB_PATH) as db:
        async with db.execute(
            "SELECT id, initiator_id, content, scheduled_time, loop_type, loop_param, group_id FROM memo_list"
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                memo = {
                    "id": row[0],
                    "initiator_id": row[1],
                    "content": row[2],
                    "scheduled_time": row[3],
                    "loop_type": row[4],
                    "loop_param": json.loads(row[5]) if row[5] else None,
                    "group_id": row[6]
                }
                schedule_memo_job(memo)
    logger.info("已加载所有备忘录任务到 APScheduler")

# -------------------- CRUD --------------------
async def insert_memo(user_id: int, content: str, scheduled_time: Optional[str] = None,
                      loop_type: int = 0, loop_param: Optional[dict] = None, group_id: int = 0):
    async with get_db_connection(MEMO_DB_PATH) as db:
        loop_param_json = json.dumps(loop_param) if loop_param else None
        cursor = await db.execute("""
            INSERT INTO memo_list (initiator_id, content, scheduled_time, loop_type, loop_param, group_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, content, scheduled_time, loop_type, loop_param_json, group_id))
        await db.commit()
        memo_id = cursor.lastrowid
        memo = {
            "id": memo_id,
            "initiator_id": user_id,
            "content": content,
            "scheduled_time": scheduled_time,
            "loop_type": loop_type,
            "loop_param": loop_param,
            "group_id": group_id
        }
        schedule_memo_job(memo)
        return memo_id

async def update_memo(user_id: int, memo_id: int, content: Optional[str] = None,
                      scheduled_time: Optional[str] = None, loop_type: Optional[int] = None,
                      loop_param: Optional[dict] = None, group_id: Optional[int] = None):
    async with get_db_connection(MEMO_DB_PATH) as db:
        async with db.execute("SELECT initiator_id FROM memo_list WHERE id=?", (memo_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] != user_id:
                return False

        fields = []
        params = []
        if content is not None:
            fields.append("content=?")
            params.append(content)
        if scheduled_time is not None:
            fields.append("scheduled_time=?")
            params.append(scheduled_time)
        if loop_type is not None:
            fields.append("loop_type=?")
            params.append(loop_type)
        if loop_param is not None:
            fields.append("loop_param=?")
            params.append(json.dumps(loop_param))
        if group_id is not None:
            fields.append("group_id=?")
            params.append(group_id)

        if fields:
            fields.append("update_ts=?")
            params.append(datetime.now(BEIJING_TZ).isoformat())
            sql = f"UPDATE memo_list SET {', '.join(fields)} WHERE id=?"
            params.append(memo_id)
            await db.execute(sql, params)
            await db.commit()

            async with db.execute(
                "SELECT initiator_id, content, scheduled_time, loop_type, loop_param, group_id FROM memo_list WHERE id=?",
                (memo_id,)
            ) as cursor2:
                if row2 := await cursor2.fetchone():
                    memo = {
                        "id": memo_id,
                        "initiator_id": row2[0],
                        "content": row2[1],
                        "scheduled_time": row2[2],
                        "loop_type": row2[3],
                        "loop_param": json.loads(row2[4]) if row2[4] else None,
                        "group_id": row2[5]
                    }
                    schedule_memo_job(memo)
            return True
        return False

async def delete_memo(user_id: int, memo_id: int):
    async with get_db_connection(MEMO_DB_PATH) as db:
        async with db.execute("SELECT initiator_id FROM memo_list WHERE id=?", (memo_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] != user_id:
                return False

        await db.execute("DELETE FROM memo_list WHERE id=?", (memo_id,))
        await db.commit()

        job_id = f"memo_{memo_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        return True

async def get_user_memos(user_id: int):
    async with get_db_connection(MEMO_DB_PATH) as db:
        async with db.execute(
            "SELECT id, content, scheduled_time, loop_type, loop_param, group_id, create_ts, update_ts "
            "FROM memo_list WHERE initiator_id=? ORDER BY create_ts DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            memos = []
            for row in rows:
                memos.append({
                    "id": row[0],
                    "content": row[1],
                    "scheduled_time": row[2],
                    "loop_type": row[3],
                    "loop_param": json.loads(row[4]) if row[4] else None,
                    "group_id": row[5],
                    "create_ts": row[6],
                    "update_ts": row[7]
                })
            return memos

driver = get_driver()
@driver.on_startup
async def handle_memo_driver_startup():
    await init_db()
