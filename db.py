# db.py
import psycopg2
import os
import urllib.parse as up
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Parse the database URL (Render provides a full URL)
DATABASE_URL = os.getenv("DATABASE_URL")  # Store this in your .env

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Connected to PostgreSQL on Render")
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
