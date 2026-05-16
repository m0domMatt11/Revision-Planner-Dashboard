from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash_bootstrap_components as dbc
import dash
import plotly.express as px
import pandas as pd
import sqlite3 as sql
from database import initialise_db, add_user

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1("Welcome to the Revision Planner Dashboard!"),
    html.P("Please log in to access your revision plans and track your progress."),
    dcc.Dropdown(
        id="Login-dropdown",
        options = [
            {"label": "Login", "value": "Login"},
            {"label": "Sign Up", "value": "Sign Up"}
        ],
        multi=False
    ),
    dbc.Input(id="username", placeholder="Enter your username", type="text"),
    dbc.Input(id="password", placeholder="Enter your password", type="password"),
    html.Button("Submit", id="submit-button", n_clicks=0),
    html.P(id="login-message")

], className="login-page")

@callback(
    Output("url", "pathname"),
    Output("login-message", "children"),
    Input("submit-button", "n_clicks"),
    State("Login-dropdown", "value"),
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True
)
def handle_login(n_clicks, login_type, username, password):
    # Check for missing inputs before database queries
    if not login_type or not username or not password:
        return dash.no_update, "Please fill in all fields."
    
    if login_type == "Sign Up":
        message = add_user(username, password)
        if message == "User added successfully":
            return "/home", ""
        else:
            return dash.no_update, message
    elif login_type == "Login":
        conn = sql.connect('revision_planner.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            return "/home", ""
        else:
            return dash.no_update, "Invalid username or password. Please try again."
    
    return dash.no_update, dash.no_update

