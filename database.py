import os
import sqlite3 as sql
import pandas as pd
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "database", "revision_planner.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_connection():
    conn = sql.connect(DB_PATH, timeout=15)
    return conn


def initialise_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Log
                    (Log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    subject TEXT,
                    date TEXT,
                    duration INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(user_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS ExamDates
                    (user_id INTEGER,
                    subject TEXT,
                    exam_date TEXT,
                    PRIMARY KEY(user_id, subject),
                    FOREIGN KEY(user_id) REFERENCES users(user_id))''')
        conn.commit()

def add_user(username, password):
    with get_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return "User added successfully"
        except sql.IntegrityError:
            return "Username already exists"

def fetch_user_id(username):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        user_id = c.fetchone()
        return user_id[0] if user_id else None

def delete_user(user_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM Log WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM ExamDates WHERE user_id = ?", (user_id,))
        conn.commit()
        

def reset_user_data(user_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM Log WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM ExamDates WHERE user_id = ?", (user_id,))
        conn.commit()


def add_or_update_exam_date(user_id, subject, exam_date):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO ExamDates (user_id, subject, exam_date)
                          VALUES (?, ?, ?)
                          ON CONFLICT(user_id, subject) DO UPDATE SET exam_date=excluded.exam_date""",
                       (user_id, subject, exam_date))
        conn.commit()


def fetch_exam_dates(user_id):
    with get_connection() as conn:
        query = "SELECT subject, exam_date FROM ExamDates WHERE user_id = ?"
        df = pd.read_sql_query(query, conn, params=(user_id,))
        return df


def fetch_user_data(username, password):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        return user

def fetch_pie_chart_data(user_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT subject, SUM(duration) as total_duration FROM Log WHERE user_id = ? GROUP BY subject"
            df = pd.read_sql_query(query, conn, params=(user_id,))  # Using the user_id from the state
            return df
        
def add_log(user_id, subject, start_time, duration):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Log (user_id, subject, date, duration) VALUES (?, ?, ?, ?)", (user_id, subject, start_time, duration))
        conn.commit()

def fetch_weekly_data(user_id):
    with get_connection() as conn:
        # 1. Fetch raw daily data from SQLite
        query = "SELECT date, subject, duration FROM Log WHERE user_id = ?"
        df = pd.read_sql_query(query, conn, params=(user_id,))
        return df
    