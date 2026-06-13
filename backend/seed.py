import asyncio
import sys
import os
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_factory, engine, Base
from app.models.user import User
from app.models.department import Department
from app.core.security import hash_password


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        existing = await db.execute(
            __import__('sqlalchemy').select(User).where(User.email == "admin@aegis.com")
        )
        if existing.scalar_one_or_none():
            print("Database already seeded.")
            return

        admin = User(
            email="admin@aegis.com",
            password_hash=hash_password("admin123"),
            full_name="System Admin",
            role="admin",
        )
        db.add(admin)

        hr_manager = User(
            email="hr@aegis.com",
            password_hash=hash_password("hr123"),
            full_name="HR Manager",
            role="hr_manager",
        )
        db.add(hr_manager)

        await db.flush()

        departments = [
            Department(name="Engineering"),
            Department(name="Product"),
            Department(name="Design"),
            Department(name="Marketing"),
            Department(name="HR"),
        ]
        for dept in departments:
            db.add(dept)

        await db.commit()
        print("Database seeded successfully!")
        print("Admin: admin@aegis.com / admin123")
        print("HR: hr@aegis.com / hr123")
        print("No fake data created. Upload real Excel files to populate employees and attendance.")


if __name__ == "__main__":
    asyncio.run(seed())
