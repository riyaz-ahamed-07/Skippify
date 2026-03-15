import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL").replace("+asyncpg", "").replace("ssl=require", "sslmode=require")

conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

try:
    print("Dropping schema...")
    cur.execute("DROP SCHEMA IF EXISTS public CASCADE;")
    cur.execute("CREATE SCHEMA public;")
    cur.execute("GRANT ALL ON SCHEMA public TO public;")
    print("Done dropping everything.")
except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()
