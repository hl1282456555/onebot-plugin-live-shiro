import aiosqlite

from nonebot import on_message, on_command, logger
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment

DB_PATH = "./cache/vote.db"


async def create_vote(referenced_message_id: str, initiator_id: str, content: str):
    """创建一个新的投票记录"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO vote_withdraw (
                referenced_message_id, initiator_id, content
            ) VALUES (?, ?, ?)
            """,
            (referenced_message_id, initiator_id, content)
        )
        await db.commit()
        logger.info(f"创建投票记录: {referenced_message_id} 发起人: {initiator_id}")


async def update_vote(referenced_message_id: str, vote_type: str):
    """
    更新投票票数
    vote_type: "agree", "oppose", "abstain"
    """
    column_map = {
        "agree": "agree_count",
        "oppose": "oppose_count",
        "abstain": "abstain_count"
    }

    if vote_type not in column_map:
        raise ValueError("vote_type 必须是 'agree', 'oppose' 或 'abstain'")

    column = column_map[vote_type]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"""
            UPDATE vote_withdraw
            SET {column} = {column} + 1
            WHERE referenced_message_id = ?
            """,
            (referenced_message_id,)
        )
        await db.commit()
        logger.info(f"投票更新: {referenced_message_id} -> {vote_type}")

async def vote_exists(db_path: str, message_id: str) -> bool:
    """
    根据 referenced_message_id 检查 vote_withdraw 表中是否存在记录。

    :param db_path: 数据库文件路径
    :param message_id: 被引用的消息 ID
    :return: 如果存在返回 True，否则返回 False
    """
    async with aiosqlite.connect(db_path) as db, db.execute(
        "SELECT 1 FROM vote_withdraw WHERE referenced_message_id = ? LIMIT 1",
        (message_id,)
    ) as cursor:
        result = await cursor.fetchone()
        return result is not None

vote_command = on_command("vote", rule=to_me(), block=False)
@vote_command.handle()
async def handle_vote(bot: Bot, event: GroupMessageEvent):
    # 检查是否引用消息
    if not event.reply:
        await vote_command.finish("请回复你想发起投票的消息！")  # 如果没有引用消息，直接结束
    else:
        # 获取被引用消息的ID
        referenced_message_id = event.reply.message_id
        # 发起投票者ID
        initiator_id = str(event.user_id)
        # 消息内容
        content = event.reply.message or "（无文本内容）"
        message_sender = event.reply.sender.user_id

        await vote_command.finish(f'{event.sender.nickname} 发起了撤销 {event.reply.sender.nickname} 的消息 "{content}" 的投票！')
