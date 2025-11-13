import sqlite3
from datetime import datetime

DB_NAME = "data.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 100,
            monthly_sent INTEGER NOT NULL DEFAULT 0
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recognitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            recipient_id INTEGER,
            credits INTEGER,
            timestamp TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS endorsements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recognition_id INTEGER,
            endorser_id INTEGER,
            UNIQUE(recognition_id, endorser_id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS redemptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            credits INTEGER,
            voucher_value INTEGER,
            timestamp TEXT
        );
    """)

    conn.commit()
    conn.close()
