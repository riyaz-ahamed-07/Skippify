import os
from sqlalchemy import create_engine
from database import Base
from models import *
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL").replace("+asyncpg", "").replace("ssl=require", "sslmode=require")

def create_all_sync():
    engine = create_engine(db_url)
    print("Creating tables synchronously...")
    Base.metadata.create_all(engine)
    print("Done")

if __name__ == "__main__":
    create_all_sync()
