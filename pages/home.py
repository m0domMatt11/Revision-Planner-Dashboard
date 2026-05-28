from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import sqlite3 as sql
from database import initialise_db, add_user, fetch_user_id, delete_user, reset_user_data

dash.register_page(__name__, path='/home')

def style_figure(fig):
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Inter",
            color="#111827",
            size=14
        ),
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        ),
        title_x=0.5
    )
    return fig


# Define the components for the home tab
markdown = dcc.Markdown(""" Welcome to your personal revision tracking dashboard! 
                        Here you can track your revision progress, log your study sessions, and analyze your performance over time. 
                        Use the tabs above to navigate through different sections of the dashboard. Happy revising! """, className="home-markdown")
pieChart = dcc.Graph(id="home-pie-chart", style={"height": "300px"})
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
            fig = px.pie(values=[1], names=["No data"], title="Revision Time Distribution")
            fig = style_figure(fig)
            return fig
        fig = px.pie(df, 
                    values='total_duration',
                    names='subject', 
                    title="Revision Time Distribution",)
        fig = style_figure(fig)
        return fig
    else:
        fig = px.pie(values=[1], 
                    names=["No data"],
                    title="Revision Time Distribution",)
        fig = style_figure(fig)
        return fig

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
Graph_Of_Weekely_Revision = dcc.Graph(id="weekly-revision-graph", style={"height": "300px"})
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
        query = "SELECT date, duration FROM Log WHERE user_id = ?"
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        
        if df.empty:
            fig = px.line(title="Weekly Revision Time")
            fig = style_figure(fig)
            return fig
        
        # 2. Convert to datetime object
        df['date'] = pd.to_datetime(df['date'])
        df["duration"] = pd.to_numeric(df["duration"])
    
        weekly_data = (df.set_index("date").resample("W")["duration"].sum().reset_index()) 
        # 4. Generate the Plotly figure
        fig = px.line(weekly_data,
                    x='date', 
                    y='duration', 
                    title="Weekly Revision Time", 
                    markers=True,)
        

        # Further styling
        fig.update_traces(line=dict(width=4), marker=dict(size=8))
        fig.update_xaxes(title="Week")
        fig.update_yaxes(title="Minutes Revised")

        # Genral Graph Styling
        fig = style_figure(fig)

        return fig
    else:
        fig = px.line(title="Weekly Revision Time")
        fig = style_figure(fig)
        return fig


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

home_tab = dbc.Tab(
    label="Home",
    tab_id="tab-1",
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([markdown]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([pieChart, updateButton]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=9,
                ),
            ],
            className="home-tab-content",
        )
    ],
)

Log_Tab = dbc.Tab(
    label="Log",
    tab_id="tab-2",
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([subject_Dropdown,
                                      html.Br(),
                                      Log_Button,
                                      html.Br(),
                                      html.Br(),
                                      Log_Message]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=9,
                ),
            ],
            className="log-tab-content",
        justify="center")
    ],
)

Analysis_Tab = dbc.Tab(
    label="Analysis",
    tab_id="tab-3",
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([Graph_Of_Weekely_Revision]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=10,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([Update_Weekly_Graph_Button]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=2,
                ),
            ],
            className="analysis-tab-content",
        )
    ],
)

Settings_Tab = dbc.Tab(
    label="Settings",
    tab_id="tab-4",
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([markdownSettings]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([delete_account_button, html.Br(), html.Br(), reset_data_button, html.Br(), html.Br(), message]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=6,
                ),
            ],
            className="settings-tab-content",
        )
    ],
)



# Wrap the tabs finally
tabs = dbc.Tabs([
    home_tab,
    Log_Tab,
    Analysis_Tab,
    Settings_Tab
], id = "home-tabs", active_tab="tab-1")

layout = html.Div([
    html.Div([
        html.H1("Revision Planner", className="dashboard-title"),
        html.P("Track your revision progress and stay consistent.", className="dashboard-subtitle"),  
        tabs
    ], className="dashboard-container")
], className="home-page")