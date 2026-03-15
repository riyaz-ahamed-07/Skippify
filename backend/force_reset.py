import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from database import DATABASE_URL, Base
from models import *

async def force_reset():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("Dropping tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Done")

if __name__ == "__main__":
    asyncio.run(force_reset())
