from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import sqlite3 as sql

def initialise_db():
    conn = sql.connect('revision_planner.db')
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
    conn.close()

def add_user(username, password):
    conn = sql.connect('revision_planner.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return "User added successfully"
    except sql.IntegrityError:
        return "Username already exists"
    finally:
        conn.close()