import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from database import DATABASE_URL

async def drop_all():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("Dropping all tables in public schema...")
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
    print("Done dropping everything.")

if __name__ == "__main__":
    asyncio.run(drop_all())
