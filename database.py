import os
import sqlite3 as sql
import pandas as pd

if getattr(__import__('sys'), 'frozen', False) and hasattr(__import__('sys'), '_MEIPASS'):
    BASE_DIR = __import__('sys')._MEIPASS
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
        conn.commit()
        

def reset_user_data(user_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM Log WHERE user_id = ?", (user_id,))
        conn.commit()


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