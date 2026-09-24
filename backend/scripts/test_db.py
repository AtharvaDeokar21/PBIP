import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


async def main():
    print("Connecting to Supabase...")

    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
    )

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT version();"))
            version = result.scalar()

            print("✅ Database connection successful!")
            print(f"PostgreSQL: {version}")

    except Exception as exc:
        print("❌ Database connection failed")
        print(type(exc).__name__)
        print(exc)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())