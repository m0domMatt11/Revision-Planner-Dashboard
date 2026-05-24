from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import sqlite3 as sql
from database import initialise_db, add_user, fetch_user_id, delete_user, reset_user_data

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
    user_id = user_id.get("user_id", None) if user_id else None
    if n_clicks > 0 and user_id is not None:
        conn = sql.connect('revision_planner.db')
        cursor = conn.cursor()
        query = "SELECT subject, SUM(duration) as total_duration FROM Log WHERE user_id = ? GROUP BY subject"
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
    Output("log-button", "children"),
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
            return dash.no_update, "Please select a subject to log.", dash.no_update, dash.no_update
        start_time = pd.Timestamp.now().isoformat()
        return "Stop Logging", f"Logging started for {subject} at {start_time}. Click the button again to stop logging.", {"start_time": start_time}, dash.no_update
    else:  # Stop logging on even clicks
        end_time = pd.Timestamp.now().isoformat()
        start_time = pd.Timestamp(start_time_var.get("start_time", None)) if start_time_var else None
        user_id = user_id.get("user_id", None) if user_id else None
        if start_time is None:
            return dash.no_update, "Logging was not started. Please click the button to start logging.", dash.no_update, dash.no_update
        duration = (pd.Timestamp(end_time) - pd.Timestamp(start_time)).total_seconds() // 60  # Duration in minutes
        duration = str(int(duration))  # Convert duration to string for database storage
        start_time = str(start_time)  # Convert start_time to string for database storage
        user_id = str(user_id)  # Convert user_id to string for database storage
        subject = str(subject)  # Convert subject to string for database storage
        conn = sql.connect('revision_planner.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Log (user_id, subject, date, duration) VALUES (?, ?, ?, ?)", (user_id, subject, start_time, duration))
        conn.commit()
        conn.close()
        return "Start Logging", f"Logging stopped for {subject} at {end_time}. Duration: {duration} minutes.", dash.no_update, {"end_time": end_time}

# Define the components for the deeper analysis
Graph_Of_Weekely_Revision = dcc.Graph(id="weekly-revision-graph")
Update_Weekly_Graph_Button = html.Button("Update Weekly Graph", id="update-weekly-graph-button", n_clicks=0)


@callback(
    Output("weekly-revision-graph", "figure"),
    Input("update-weekly-graph-button", "n_clicks"),
    State("user-id", "data"),
    prevent_initial_call=True
)
def update_weekly_graph(n_clicks, user_id):
    user_id = user_id.get("user_id", None) if user_id else None
    
    if n_clicks > 0 and user_id is not None:
        conn = sql.connect('revision_planner.db')
        
        # 1. Fetch raw daily data from SQLite
        query = "SELECT date, SUM(duration) as total_duration FROM Log WHERE user_id = ? GROUP BY date"
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        
        if df.empty:
            return px.line(title="Weekly Revision Time")
        
        # 2. Convert to datetime object
        df['date'] = pd.to_datetime(df['date'])
        
        # 3. Option 1: Group by week directly using pd.Grouper (Keeps it as a DataFrame)
        weekly_data = df.groupby(pd.Grouper(key='date', freq='W-MON'))['total_duration'].sum().reset_index()
        
        # 4. Generate the Plotly figure
        fig = px.line(weekly_data, x='date', y='total_duration', title="Weekly Revision Time", markers=True)
        return fig
    else:
        return px.line(title="Weekly Revision Time")


# Define the components for the settings tab

markdownSettings = dcc.Markdown(""" In the settings tab, you can manage your account and data. Use the buttons below to delete your account or reset your revision data. Please note that these actions are irreversible, so proceed with caution. """, className="settings-markdown")
delete_account_button = html.Button("Delete Account", id="delete-account-button", n_clicks=0)
reset_data_button = html.Button("Reset Data", id="reset-data-button", n_clicks=0)
message = html.P(id="settings-message")

@callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("settings-message", "children", allow_duplicate=True),
    Input("delete-account-button", "n_clicks"),
    State("user-id", "data"),
    allow_duplicate=True,
    prevent_initial_call="initial_duplicate"
)
def delete_account(n_clicks, user_id):
    if n_clicks > 0:
        user_id = user_id.get("user_id", None) if user_id else None
        if user_id is not None:
            delete_user(user_id)
            return "/", "Account deleted successfully. Please refresh the page to log in again."
        else:
            return dash.no_update, "User ID not found. Unable to delete account."
    return dash.no_update, dash.no_update

@callback(
    Output("settings-message", "children", allow_duplicate=True),
    Input("reset-data-button", "n_clicks"),
    State("user-id", "data"),
    allow_duplicate=True,
    prevent_initial_call="initial_duplicate"
)
def reset_data(n_clicks, user_id):
    if n_clicks > 0:
        user_id = user_id.get("user_id", None) if user_id else None
        if user_id is not None:
            reset_user_data(user_id)
            return "Data reset successfully. All your revision logs have been deleted."
        else:
            return "User ID not found. Unable to reset data."
    return dash.no_update



# Define the tabs for the home page
tabs = dbc.Tabs([
    dbc.Tab([markdown, pieChart, updateButton], label="Home", tab_id="tab-1"),
    dbc.Tab([subject_Dropdown, Log_Button, Log_Message], label="Log", tab_id="tab-2"),
    dbc.Tab([Graph_Of_Weekely_Revision, Update_Weekly_Graph_Button], label="Deeper Analysis", tab_id="tab-3"),
    dbc.Tab([markdownSettings, delete_account_button, reset_data_button, message], label="Settings", tab_id="tab-4")
], id = "home-tabs", active_tab="tab-1")

layout = html.Div([tabs, 
                   html.Div(id="home-content")], className="home-page")