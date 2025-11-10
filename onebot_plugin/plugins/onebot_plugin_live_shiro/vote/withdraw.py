import aiosqlite

from typing import Any
from datetime import datetime, timedelta

from nonebot import on_command, get_bot, logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.matcher import Matcher

from nonebot_plugin_apscheduler import scheduler

DB_PATH = "./cache/vote.db"

async def vote_exists(message_id: int) -> bool:
    """
    根据 referenced_message_id 检查 vote_withdraw 表中是否存在记录。

    :param db_path: 数据库文件路径
    :param message_id: 被引用的消息 ID
    :return: 如果存在返回 True，否则返回 False
    """
    query_str = f"SELECT 1 FROM vote_withdraw WHERE referenced_message_id = ? LIMIT 1"
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query_str, (message_id,))
        row = await cursor.fetchone()
        await cursor.close()

    return row is not None

async def create_record(
        referenced_message_id: int,
        initiator_id: int,
        content: str,
        agree_count: int = 0,
        oppose_count: int = 0,
        abstain_count: int = 0
) -> dict[str, Any]:
    sql = """
        INSERT INTO vote_withdraw (
            referenced_message_id,
            initiator_id,
            content,
            agree_count,
            oppose_count,
            abstain_count
        ) VALUES (?, ?, ?, ?, ?, ?)
    """

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                sql,
                (
                    referenced_message_id,
                    initiator_id,
                    content,
                    agree_count,
                    oppose_count,
                    abstain_count,
                ),
            )
            await db.commit()
            new_id = cursor.lastrowid
            await cursor.close()
        return {"success": True, "data": new_id, "error": None}

    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

async def update_record(
    record_id: int,
    **fields
) -> dict[str, Any]:

    if not fields:
        return {"success": False, "data": None, "error": "No fields to update"}

    set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
    values = list(fields.values())
    values.append(record_id)

    sql = f"UPDATE vote_withdraw SET {set_clause} WHERE id = ?"

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(sql, values)
            await db.commit()
            count = cursor.rowcount
            await cursor.close()

        if count == 0:
            return {"success": False, "data": 0, "error": "Record not found"}

        return {"success": True, "data": count, "error": None}

    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

async def delete_record(
    record_id: int
) -> dict[str, Any]:

    sql = "DELETE FROM vote_withdraw WHERE id = ?"

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(sql, (record_id,))
            await db.commit()
            count = cursor.rowcount
            await cursor.close()

        if count == 0:
            return {"success": False, "data": 0, "error": "Record not found"}

        return {"success": True, "data": count, "error": None}

    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

async def get_record_by_id(record_id: int) -> dict[str, Any]:
    sql = """
        SELECT
            id,
            referenced_message_id,
            initiator_id,
            timestamp,
            content,
            agree_count,
            oppose_count,
            abstain_count
        FROM vote_withdraw
        WHERE id = ?
    """

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, (record_id,))
            row = await cursor.fetchone()
            await cursor.close()

        if row is None:
            return {"success": False, "data": None, "error": f"Record {record_id} not found"}

        return {"success": True, "data": dict(row), "error": None}

    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

async def process_vote_withdraw_result(record_id: int, group_id: int):
    bot = get_bot()

    query_result = await get_record_by_id(record_id)
    if not query_result["success"]:
        await bot.send_group_msg(group_id=group_id, message=Message(MessageSegment.text(f"获取投票记录 [{record_id}] 失败瞄~")))
    else:
        data = query_result["data"]
        vote_result_text = "撤回" if data["agree_count"] > data["oppose_count"] else "不撤回"
        await bot.send_group_msg(group_id=group_id, message=Message([
            MessageSegment.text(f'检测时间到了, 撤回 {record_id} 投票结果如下：\n'),
            MessageSegment.text(f'同意：{data["agree_count"]}\n'),
            MessageSegment.text(f'反对：{data["oppose_count"]}\n'),
            MessageSegment.text(f'弃权：{data["abstain_count"]}\n'),
            MessageSegment.text(f"最终结果为 {vote_result_text} (测试版本，暂时不做任何操作)")
        ]))

async def process_vote_withdraw_command(event: GroupMessageEvent):
    # 检查是否引用消息
    if not event.reply:
        await vote_command.finish("请引用你想发起撤销投票的消息！")  # 如果没有引用消息，直接结束
    else:
        # 获取被引用消息的ID
        referenced_message_id = event.reply.message_id
        if await vote_exists(referenced_message_id):
            await vote_command.finish("该消息已经存在撤回投票，请等待结果瞄~")

        create_result = await create_record(referenced_message_id,
                                    event.user_id,
                                    event.reply.message.extract_plain_text())
        if not create_result["success"]:
            logger.warning(f"创建投票任务失败：{create_result['error']}")
            await vote_command.finish(f"创建投票任务失败：{create_result['error']}")

        scheduler.add_job(process_vote_withdraw_result,
                          "date",
                          run_date=datetime.now() + timedelta(minutes=1),
                          kwargs={
                                "record_id": create_result["data"],
                                "group_id": event.group_id
                              })

        await vote_command.finish(Message([
            MessageSegment.reply(event.reply.message_id),
            MessageSegment.text(f"{event.sender.nickname} 发起了撤回对这条消息的投票。\n"),
            MessageSegment.text(f'投票ID为 {create_result["data"]}。\n'),
            MessageSegment.text("请使用以下命令进行投票：\n"),
            MessageSegment.text(f'/agree {create_result["data"]} - 同意撤回\n'),
            MessageSegment.text(f'/oppose {create_result["data"]} - 反对撤回\n'),
            MessageSegment.text(f'/abstain {create_result["data"]} - 弃权\n'),
            MessageSegment.text("将在一分钟后统计投票结果瞄~")
        ]))

vote_command = on_command("vote", block=False)
@vote_command.handle()
async def handle_vote(event: GroupMessageEvent, args: Message = CommandArg()):
    args_text = args.extract_plain_text().strip()
    if not args_text:
        await vote_command.finish("请提供投票内容！例如：/vote 撤回")

    if args_text == "撤回":
        await process_vote_withdraw_command(event)

async def process_memeber_vote_withdraw(
        command: type[Matcher],
        event: GroupMessageEvent,
        record_id: int,
        vote_type: str
):
    query_result = await get_record_by_id(record_id)
    if not query_result["success"]:
        logger.warning(f'查询投票信息失败 - [{record_id}] : {query_result["error"]}')
        await command.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(f'查询投票记录 [{record_id}] 失败，请检查命令瞄~')
        ]))

    start_time = datetime.strptime(query_result["data"]["timestamp"], "%Y-%m-%d %H:%M:%S")
    passed_time = datetime.now() - start_time
    if passed_time >= timedelta(minutes=1):
        await command.finish(f"投票 [{record_id}] 已经过期了瞄~")

    new_count = query_result["data"]["oppose_count"] + 1
    update_result = await update_record(int(record_id), oppose_count=new_count)
    if not update_result["success"]:
        logger.warning(f'更新投票信息失败 - [{record_id}] : {update_result["error"]}')
        await command.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(f"更新投票 [{record_id}] 信息失败，请联系管理员瞄~")
        ]))

    await command.finish(Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(f"已为 {record_id} 成功投下一票{vote_type}瞄~")
    ]))

agree_withdraw_command = on_command("agree")
@agree_withdraw_command.handle()
async def handle_agree_withdraw(event: GroupMessageEvent, args: Message = CommandArg()): 
    await process_memeber_vote_withdraw(
        agree_withdraw_command,
        event,
        int(args.extract_plain_text().strip()),
        "同意"
    )

oppose_withdraw_command = on_command("oppose")
@oppose_withdraw_command.handle()
async def handle_oppose_withdraw(event: GroupMessageEvent, args: Message = CommandArg()):
    await process_memeber_vote_withdraw(
        oppose_withdraw_command,
        event,
        int(args.extract_plain_text().strip()),
        "反对"
    )

abstain_withdraw_command = on_command("abstain")
@abstain_withdraw_command.handle()
async def handle_abstain_withdraw(event: GroupMessageEvent, args: Message = CommandArg()):
    await process_memeber_vote_withdraw(
        abstain_withdraw_command,
        event,
        int(args.extract_plain_text().strip()),
        "弃权"
    )
