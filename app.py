from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from database import initialise_db
import os
import sys
import threading
import webview

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Dash(__name__, 
        use_pages=True,
        external_stylesheets=[dbc.themes.LUX],
        pages_folder=os.path.join(BASE_DIR, "pages"),
        assets_folder=os.path.join(BASE_DIR, "assets")
    )


app.layout = html.Div([
    dcc.Store(id='user-id', storage_type='session'),
    dcc.Store(id="Start-Time", storage_type='session'),
    dcc.Store(id="End-Time", storage_type='session'),
    dcc.Store(id="Exam-Date", storage_type='local'),
    dcc.Location(id="url", refresh=True),
    dash.page_container
])

def run_dash():
    app.run(debug=False, port=8050, use_reloader=False)

if __name__ == '__main__':
    initialise_db()
    
    dash_thread = threading.Thread(target=run_dash)
    dash_thread.daemon = True
    dash_thread.start()

    webview.create_window(
        title="Revision Tracker",
        url="http://127.0.0.1:8050",
        width=1200,
        height=800,
        resizable=True
    )

    webview.start()
