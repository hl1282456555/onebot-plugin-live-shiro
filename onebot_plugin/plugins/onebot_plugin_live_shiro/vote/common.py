import aiosqlite

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_connection(path="vote.db"):
    db = await aiosqlite.connect(path)
    await db.execute("PRAGMA foreign_keys = ON;")
    try:
        yield db
    finally:
        await db.close()
