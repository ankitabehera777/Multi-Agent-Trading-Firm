import os
import pymysql
from dotenv import load_dotenv, find_dotenv

print("Using .env file:", find_dotenv())
load_dotenv(override=True)

pw = os.getenv("DB_PASSWORD")
print("Password length:", len(pw), "| starts with:", pw[0], "| ends with:", pw[-1])

try:
    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=pw,
    )
    print("Login worked!")
    conn.close()
except Exception as e:
    print("Failed:", e)