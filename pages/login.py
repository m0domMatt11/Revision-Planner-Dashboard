from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash_bootstrap_components as dbc
import dash
import plotly.express as px
import pandas as pd
import sqlite3 as sql
from database import initialise_db, add_user, fetch_user_id, fetch_user_data

dash.register_page(__name__, path='/')

layout = html.Div([
    dbc.Card([
        dbc.CardBody([
    html.H1("Revision Tracker", className="login-title"),
    html.P("Please log in to access your revision plans and track your progress.", className="subtitle"),
    dcc.Dropdown(
        id="Login-dropdown",
        options = [
            {"label": "Login", "value": "Login"},
            {"label": "Sign Up", "value": "Sign Up"}
        ],
        multi=False,
        className="login-dropdown",
        placeholder="Select Login or Sign Up"
    ),
    dbc.Input(id="username", placeholder="Enter your username", type="text", className="login-input"),
    dbc.Input(id="password", placeholder="Enter your password", type="password", className="login-input"),
    dbc.Button("Submit", id="submit-button", n_clicks=0, className="login-button"),
    html.P(id="login-message", className="Confirmation-message")

])
    ], className="login-card")
], className="login-page")

@callback(
    Output("url", "pathname"),
    Output("user-id", "data"),
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
        return dash.no_update, dash.no_update, "Please fill in all fields."
    
    if login_type == "Sign Up":
        message = add_user(username, password)
        if message == "User added successfully":
            user_id = fetch_user_id(username)
            return "/home", {"user_id": user_id}, ""
        else:
            return dash.no_update, dash.no_update, message
    elif login_type == "Login":
        user = fetch_user_data(username, password)
        if user:
            user_id = fetch_user_id(username)
            return "/home", {"user_id": user_id}, ""
        else:
            return dash.no_update, dash.no_update, "Invalid username or password. Please try again."

    return dash.no_update, dash.no_update, ""