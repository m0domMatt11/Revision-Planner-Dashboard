from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import sqlite3 as sql

dash.register_page(__name__, path='/home')


# Define the components for the home tab
markdown = dcc.Markdown(""" Welcome to your personal revision tracking dashboard! 
                        Here you can track your revision progress, log your study sessions, and analyze your performance over time. 
                        Use the tabs above to navigate through different sections of the dashboard. Happy revising! """, className="home-markdown")
pieChart = dcc.Graph(id="home-pie-chart")
updateButton = html.Button("Update Chart", id="update-chart-button", n_clicks=0)

@callback(
    Output("home-pie-chart", "figure"),
    Input("update-chart-button", "n_clicks"),
    State("user-id", "data"),
    prevent_initial_call=True
)
def update_pie_chart(n_clicks, user_id):
    if n_clicks > 0 and user_id is not None:
        conn = sql.connect('revision_planner.db')
        cursor = conn.cursor()
        query = "SELECT subject, SUM(duration) as total_duration FROM Log GROUP BY subject WHERE user_id = ?"
        df = pd.read_sql_query(query, conn, params=(user_id,))  # Using the user_id from the state
        conn.close()
        if df.empty:
            return px.pie(values=[1], names=["No data"], title="Revision Time Distribution")
        fig = px.pie(df, values='total_duration', names='subject', title="Revision Time Distribution")
        return fig
    else:
        return px.pie(values=[1], names=["No data"], title="Revision Time Distribution")

# Define components for the Log Tab

subjects = ["Math", 
            "Science", 
            "History", 
            "EnglishLiterature",
            "EnglishLanguage",
            "Geography", "ComputerScience", 
            "Art", 
            "Music", 
            "P.E", 
            "French", 
            "Spanish", 
            "German",
            "Biology",
            "Chemistry",
            "Physics",]

subject_Dropdown = dcc.Dropdown( id="subject-dropdown", options=[{"label": subject, "value": subject} for subject in subjects], placeholder="Select Subject")
Log_Button = html.Button("Start Logging", id="log-button", n_clicks=0)
Log_Message = html.P(id="log-message")

@callback(
    Output("log-message", "children"),
    Output("Start-Time", "data"),
    Output("End-Time", "data"),
    Input("log-button", "n_clicks"),
    State("subject-dropdown", "value"),
    State("user-id", "data"),
    State("Start-Time", "data"),
    State("End-Time", "data"),
    prevent_initial_call=True
)
def handle_logging(n_clicks, subject, user_id, start_time_var, end_time_var):
    if n_clicks % 2 == 1:  # Start logging on odd clicks
        if subject is None:
            return "Please select a subject to log.", dash.no_update, dash.no_update
        start_time = pd.Timestamp.now().isoformat()
        return f"Logging started for {subject} at {start_time}. Click the button again to stop logging.", {"start_time": start_time}, dash.no_update
    else:  # Stop logging on even clicks
        end_time = pd.Timestamp.now().isoformat()
        start_time = start_time_var.get("start_time") if start_time_var else None
        if start_time is None:
            return "Logging was not started. Please click the button to start logging.", dash.no_update, dash.no_update
        duration = (pd.Timestamp(end_time) - pd.Timestamp(start_time)).total_seconds() // 60  # Duration in minutes
        conn = sql.connect('revision_planner.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Log (user_id, subject, date, duration) VALUES (?, ?, ?, ?)", (user_id, subject, start_time, duration))
        conn.commit()
        conn.close()
        return f"Logging stopped for {subject} at {end_time}. Duration: {duration} minutes.", dash.no_update, {"end_time": end_time}










tabs = dbc.Tabs([
    dbc.Tab([markdown, pieChart, updateButton], label="Home", tab_id="tab-1"),
    dbc.Tab([subject_Dropdown, Log_Button, Log_Message], label="Log", tab_id="tab-2"),
    dbc.Tab([], label="Deeper Analysis", tab_id="tab-3"),
    dbc.Tab([], label="Settings", tab_id="tab-4")
], id = "home-tabs", active_tab="tab-1")

layout = html.Div([tabs, 
                   html.Div(id="home-content")], className="home-page")