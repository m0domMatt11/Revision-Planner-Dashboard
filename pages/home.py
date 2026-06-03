from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import sqlite3 as sql
from database import delete_user, reset_user_data, fetch_pie_chart_data, add_log, fetch_weekly_data, fetch_exam_dates, add_or_update_exam_date
import plotly.graph_objects as go
from datetime import date
import datetime as dt

dash.register_page(__name__, path='/home')

def style_figure(fig):
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Roboto",
            color="#111827",
            size=14
        ),
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        ),
         title={
            "x": 0.5,
            "xanchor": "center",
            "font": {
                "family": "Inter",
                "size": 24,
                "color": "#111827"
            }
        },
    )
    return fig


# Define the components for the home tab
markdown1 = dcc.Markdown(""" Welcome to your personal revision tracking dashboard!""", className="home-markdown")
markdown2 = dcc.Markdown("""Here you can track your revision progress, log your study sessions, and analyze your performance over time.""", className="home-markdown")
markdown3 = dcc.Markdown("""Use the tabs above to navigate through different sections of the dashboard. Happy revising! """, className="home-markdown")
pieChart = dcc.Graph(id="home-pie-chart", style={"height": "300px"})

@callback(
    Output("home-pie-chart", "figure"),
    Input("user-id", "data"),
    Input("log-update", "data"),
    prevent_initial_call=False
)
def update_pie_chart(user_id, log_update):
    user_id = user_id.get("user_id", None) if user_id else None
    if user_id is not None:
        df = fetch_pie_chart_data(user_id)
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
            "English Literature",
            "English Language",
            "Geography", 
            "ComputerScience", 
            "Art", 
            "Music", 
            "P.E", 
            "French", 
            "Spanish", 
            "German",
            "Biology",
            "Chemistry",
            "Physics"
            ]

subject_Dropdown = dcc.Dropdown( id="subject-dropdown", options=[{"label": subject, "value": subject} for subject in subjects], placeholder="Select Subject")
Log_Button = html.Button("Start Logging", id="log-button", n_clicks=0)
Log_Message = html.P(id="log-message")

@callback(
    Output("log-button", "children"),
    Output("log-message", "children"),
    Output("Start-Time", "data"),
    Output("End-Time", "data"),
    Output("log-update", "data"),
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
            return dash.no_update, "Please select a subject to log.", dash.no_update, dash.no_update, dash.no_update
        start_time = pd.Timestamp.now().isoformat()
        readable_start_time = str(pd.to_datetime(start_time).strftime('%d %B, %I:%M %p'))
        return "Stop Logging", f"Logging started for {subject} at {readable_start_time}. Click the button again to stop logging.", {"start_time": start_time}, dash.no_update, dash.no_update
    else:  # Stop logging on even clicks
        end_time = pd.Timestamp.now().isoformat()
        start_time = pd.Timestamp(start_time_var.get("start_time", None)) if start_time_var else None
        user_id = user_id.get("user_id", None) if user_id else None
        if start_time is None:
            return dash.no_update, "Logging was not started. Please click the button to start logging.", dash.no_update, dash.no_update, dash.no_update
        duration = (pd.Timestamp(end_time) - pd.Timestamp(start_time)).total_seconds() // 60  # Duration in minutes
        duration = str(int(duration))  # Convert duration to string for database storage
        start_time = str(start_time)  # Convert start_time to string for database storage
        user_id = str(user_id)  # Convert user_id to string for database storage
        subject = str(subject)  # Convert subject to string for database storage
        add_log(user_id, subject, start_time, duration)
        readable_end_time = str(pd.to_datetime(end_time).strftime('%d %B, %I:%M %p')) 
        return "Start Logging", f"Logging stopped for {subject} at {readable_end_time}. Duration: {duration} minutes.", dash.no_update, {"end_time": end_time}, pd.Timestamp.now().isoformat()

# Define the components for the deeper analysis
Graph_Of_Weekely_Revision = dcc.Graph(id="weekly-revision-graph", style={"height": "300px"})
Table_Of_Total_Times = html.Div(dash.dash_table.DataTable(id="total-revision", page_size=10), className="revision-table")


@callback(
    Output("weekly-revision-graph", "figure"),
    Input("user-id", "data"),
    Input("log-update", "data"),
    prevent_initial_call=False
)
def update_weekly_graph(user_id, log_update):
    user_id = user_id.get("user_id", None) if user_id else None
    
    if user_id is not None:
        df = fetch_weekly_data(user_id)
        if df.empty:
            fig = px.bar(title="Weekly Revision Time")
            fig = style_figure(fig)
            return fig
        
        # 2. Convert to datetime object
        df['date'] = pd.to_datetime(df['date'])
        df["duration"] = pd.to_numeric(df["duration"])

        # 3. Group by week and subject, summing durations for stacked bar chart
        df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
        df['week_end'] = df['week'] + pd.Timedelta(days=6)
        df['week_label'] = (
            df['week'].dt.strftime('%d %b')
            + ' - '
            + df['week_end'].dt.strftime('%d %b')
            )
        weekly_data = df.groupby(['week', 'week_label','subject'])['duration'].sum().reset_index()
        weekly_data = weekly_data.sort_values('week')
        fig = px.bar(weekly_data, x='week_label', y='duration', color='subject', title="Weekly Revision Time", labels={"duration": "Minutes Revised", "week_label": "Week"}, barmode='stack',     category_orders={
        "week_label": weekly_data['week_label'].drop_duplicates().tolist()
    })
  
        # Furher styling for better readability
        fig.update_xaxes(title="Week")
        fig.update_yaxes(title="Minutes Revised")
        # Genral Graph Styling
        fig = style_figure(fig)

        return fig
    else:
        fig = px.bar(title="Weekly Revision Time")
        fig = style_figure(fig)
        return fig
    

@callback(
    Output("total-revision", "data"),
    Output("total-revision", "columns"),
    Input("log-update", "data"),
    Input("user-id", "data"),
    prevent_initial_call=False
)
def update_table(log_update, user_id):
    user_id = user_id.get("user_id", None) if user_id else None
    if user_id is not None:
        df = fetch_pie_chart_data(user_id)
        columns = [{"name": i, "id": i} for i in df.columns]
        return df.to_dict("records"), columns
    else:
        return dash.no_update, dash.no_update
    

# Define components for the days left to exam analysis

subject_dropdown = dcc.Dropdown(
    id="subject-dropdown-analysis",
    options=[{"label": subject, "value": subject} for subject in subjects],
    placeholder="Select Subject to then input exam date"
)
Date_Picker = dcc.DatePickerSingle(
    id="exam-date-picker",
    placeholder="Select Exam Date",
    display_format="YYYY-MM-DD",
    min_date_allowed=date.today(),
    initial_visible_month=date.today()
)
confirm_button = html.Button("Confirm Exam Date", id="confirm-exam-date-button", n_clicks=0)
comfirmation_message = html.P(id="exam-date-confirmation-message", className="Confirmation-message")
days_left_bar = dcc.Graph(id="days-left-bar", style={"height": "300px"})

@callback(
    Output("exam-date-confirmation-message", "children"),
    Output("exam-date-refresh", "data"),
    Input("confirm-exam-date-button", "n_clicks"),
    State("subject-dropdown-analysis", "value"),
    State("exam-date-picker", "date"),
    State("user-id", "data"),
    prevent_initial_call=True
)
def save_exam_date(n_clicks, subject, exam_date, user_id):
    user_id = user_id.get("user_id", None) if user_id else None
    if n_clicks > 0:
        if user_id is None:
            return "Please log in to save exam dates.", dash.no_update
        if not subject or not exam_date:
            return "Please select a subject and exam date.", dash.no_update
        add_or_update_exam_date(user_id, subject, exam_date)
        return "Exam date confirmed!", pd.Timestamp.now().isoformat()
    return dash.no_update, dash.no_update


@callback(
    Output("days-left-bar", "figure"),
    Input("user-id", "data"),
    Input("exam-date-refresh", "data"),
    prevent_initial_call=False
)
def update_days_left_chart(user_id, refresh_trigger):
    user_id = user_id.get("user_id", None) if user_id else None
    if user_id is not None:
        df = fetch_exam_dates(user_id)
        if not df.empty:
            df["exam_date"] = pd.to_datetime(df["exam_date"])
            now = pd.Timestamp.now().normalize()
            future_df = df[df["exam_date"] >= now].copy()
            if not future_df.empty:
                future_df["Days Left"] = (future_df["exam_date"] - now).dt.days
                df_chart = future_df[["subject", "Days Left"]].rename(columns={"subject": "Subject"})
                fig = px.bar(df_chart, x="Subject", y="Days Left", title="Days Left Until Exam")
                fig.update_xaxes(title="Subject")
                fig.update_yaxes(title="Days Left")
                fig = style_figure(fig)
                return fig
    fig = px.bar(title="Days Left Until Exam")
    fig = style_figure(fig)
    return fig


@callback(
    Output("subject-dropdown-analysis", "value"),
    Output("exam-date-picker", "date"),
    Input("user-id", "data"),
    prevent_initial_call=False
)
def restore_exam_date_fields(user_id):
    user_id = user_id.get("user_id", None) if user_id else None
    if user_id is not None:
        df = fetch_exam_dates(user_id)
        if not df.empty:
            df["exam_date"] = pd.to_datetime(df["exam_date"])
            now = pd.Timestamp.now().normalize()
            future_df = df[df["exam_date"] >= now].copy()
            if not future_df.empty:
                nearest = future_df.sort_values("exam_date").iloc[0]
                return nearest["subject"], str(nearest["exam_date"].date())
    return None, None
    
# Define the components for the settings tab

markdownSettings1 = dcc.Markdown(""" In the settings tab, you can manage your account and data.""", className="settings-markdown")
markdownSettings2 = dcc.Markdown("""Use the buttons below to delete your account or reset your revision data.""", className="settings-markdown")
markdownSettings3 = dcc.Markdown("""Please note that these actions are irreversible, so proceed with caution.""", className="settings-markdowm")

delete_account_button = html.Button("Delete Account", id="delete-account-button", n_clicks=0)
reset_data_button = html.Button("Reset Data", id="reset-data-button", n_clicks=0)
checkbox = dcc.Checklist(id = "confirmation-check", options=[{"label": "Confirm Action", "value": 1 }], className="Confirmation-Checkbox")
message = html.P(id="settings-message", className="Confirmation-message")

@callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("settings-message", "children", allow_duplicate=True),
    Input("delete-account-button", "n_clicks"),
    Input("confirmation-check", "value"),
    State("user-id", "data"),
    allow_duplicate=True,
    prevent_initial_call="initial_duplicate"
)
def delete_account(n_clicks,checkbox_value, user_id):
    if n_clicks > 0:
        if checkbox_value and 1 in checkbox_value:
            user_id = user_id.get("user_id", None) if user_id else None
            if user_id is not None:
                delete_user(user_id)
                return "/", "Account deleted successfully. Please refresh the page to log in again."
            else:
                return dash.no_update, "User ID not found. Unable to delete account."
        else:
            return dash.no_update, "Please confirm that you want to complete this action."
    return dash.no_update, dash.no_update

@callback(
    Output("settings-message", "children", allow_duplicate=True),
    Output("subject-dropdown-analysis", "value"),
    Output("exam-date-picker", "date"),
    Output("days-left-bar", "figure"),
    Input("reset-data-button", "n_clicks"),
    Input("confirmation-check", "value"),
    State("user-id", "data"),
    allow_duplicate=True,
    prevent_initial_call="initial_duplicate"
)
def reset_data(n_clicks, checkbox_value, user_id):
    if n_clicks > 0:
        if checkbox_value and 1 in checkbox_value:
            user_id = user_id.get("user_id", None) if user_id else None
            if user_id is not None:
                reset_user_data(user_id)
                fig = px.bar(title="Days Left Until Exam")
                fig = style_figure(fig)
                return "Data reset successfully. All your revision logs and exam dates have been deleted.", None, None, fig
            else:
                return "User ID not found. Unable to reset data.", dash.no_update, dash.no_update, dash.no_update
        else:
            return "Please confirm that you want to complete this action", dash.no_update, dash.no_update, dash.no_update
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update



# Define the tabs for the home page

home_tab = dbc.Tab(
    label="Home",
    tab_id="tab-1",
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([markdown1, html.Br(), markdown2, html.Br(), markdown3]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([pieChart]),
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
                    xs=12, lg=6,
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
                    xs=12, lg=12,
                )
            ],
            className="analysis-tab-content",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([Table_Of_Total_Times]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=12,
                )
            ],
            className="analysis-tab-content",
        )
    ],
)

exam_date_tab = dbc.Tab(
    label="Exam Date Analysis",
    tab_id="tab-4",
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([subject_dropdown, html.Br(), Date_Picker, html.Br(), confirm_button, html.Br(), comfirmation_message]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=4,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([days_left_bar]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=8,
                ),
            ],
            className="exam-date-tab-content",
        )
    ],
)


Settings_Tab = dbc.Tab(
    label="Settings",
    tab_id="tab-5",
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([markdownSettings1, html.Br(), markdownSettings2, html.Br(), markdownSettings3]),
                        className="dashboard-card",
                    ),
                    xs=12, lg=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([delete_account_button, html.Br(), html.Br(), reset_data_button, html.Br(), html.Br(), checkbox, html.Br(), html.Br(),message]),
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
    exam_date_tab,
    Settings_Tab
], id = "home-tabs", active_tab="tab-1")

layout = html.Div([
    html.Div([
        html.H1("Revision Planner", className="dashboard-title"),
        html.P("Track your revision progress and stay consistent.", className="dashboard-subtitle"),  
        tabs
    ], className="dashboard-container")
], className="home-page")