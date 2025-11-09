import os

import aiosqlite
from nonebot import get_driver, logger

from .withdraw import *

driver = get_driver()

@driver.on_startup
async def _startup():
    db_path = "./cache/vote.db"

    # 创建 cache 目录（如果不存在）
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # 打开数据库（如果文件不存在，会自动创建）
    async with aiosqlite.connect(db_path) as db:
        # 检查表是否存在
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vote_withdraw';"
        ) as cursor:
            table_exists = await cursor.fetchone()

        # 如果表不存在，则创建
        if not table_exists:
            await db.execute("""
                CREATE TABLE vote_withdraw (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referenced_message_id TEXT NOT NULL,  -- 被引用的消息ID
                    initiator_id TEXT NOT NULL,           -- 投票发起人ID
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content TEXT NOT NULL,                -- 消息内容
                    agree_count INTEGER DEFAULT 0,        -- 同意票数量
                    oppose_count INTEGER DEFAULT 0,       -- 反对票数量
                    abstain_count INTEGER DEFAULT 0       -- 弃权票数量
                )
            """)
            await db.commit()
            logger.info("表 vote_withdraw 已创建。")
        else:
            logger.info("表 vote_withdraw 已存在。")
