import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv('MYSQL_HOST', 'localhost')
user = os.getenv('MYSQL_USER', 'root')
password = os.getenv('MYSQL_PASSWORD')
db_name = os.getenv('MYSQL_DB', 'Memory_Retention_Predictor')

if not password:
    print("Please set MYSQL_PASSWORD in the .env file first!")
    exit(1)

try:
    conn = pymysql.connect(host=host, user=user, password=password)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    print(f"Database '{db_name}' ensured (created or already exists).")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
