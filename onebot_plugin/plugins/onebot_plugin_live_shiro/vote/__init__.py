import os

from nonebot import get_driver, logger

from ..common import *
from .withdraw import *

driver = get_driver()

@driver.on_startup
async def handle_vote_driver_startup():
    db_path = "./cache/vote.db"

    # 创建 cache 目录（如果不存在）
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # 打开数据库（如果文件不存在，会自动创建）
    async with get_db_connection(db_path) as db:
        # ---------- vote_withdraw 表 ----------
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vote_withdraw';"
        ) as cursor:
            table_exists = await cursor.fetchone()

        if not table_exists:
            await db.execute("""
                CREATE TABLE vote_withdraw (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referenced_message_id INTEGER DEFAULT 0,     -- 被引用的消息ID
                    initiator_id INTEGER DEFAULT 0,              -- 投票发起人ID
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content TEXT NOT NULL,                       -- 消息内容
                    agree_count INTEGER DEFAULT 0,               -- 同意票数量
                    oppose_count INTEGER DEFAULT 0,              -- 反对票数量
                    abstain_count INTEGER DEFAULT 0              -- 弃权票数量
                )
            """)
            await db.commit()
            logger.info("表 vote_withdraw 已创建。")
        else:
            logger.info("表 vote_withdraw 已存在。")

        # ---------- vote_withdraw_user_record 表（关联表） ----------
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vote_withdraw_user_record';"
        ) as cursor:
            record_table_exists = await cursor.fetchone()

        if not record_table_exists:
            await db.execute("""
                CREATE TABLE vote_withdraw_user_record (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vote_id INTEGER NOT NULL,         -- 对应 vote_withdraw.id
                    user_id INTEGER NOT NULL,         -- 投票用户ID
                    choice TEXT NOT NULL,             -- "agree" / "oppose" / "abstain"
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vote_id, user_id),        -- 防止重复投票
                    FOREIGN KEY(vote_id) REFERENCES vote_withdraw(id) ON DELETE CASCADE
                )
            """)
            await db.commit()
            logger.info("表 vote_withdraw_user_record 已创建。")
        else:
            logger.info("表 vote_withdraw_user_record 已存在。")
