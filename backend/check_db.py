import sys
sys.path.insert(0, '.')
import asyncio
from app.database import async_session_factory
from sqlalchemy import text

async def test():
    async with async_session_factory() as db:
        result = await db.execute(text("SELECT id, file_name, status, file_hash FROM upload_log"))
        rows = result.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, File: {row[1]}, Status: {row[2]}, Hash: {row[3][:20]}...")

asyncio.run(test())
