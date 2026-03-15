import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from database import DATABASE_URL, Base
from models import *

async def create_all():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Done")

if __name__ == "__main__":
    asyncio.run(create_all())
