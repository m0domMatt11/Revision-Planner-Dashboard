from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from database import initialise_db

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.LUX])
app.layout = html.Div([
    dcc.Store(id='user-id', storage_type='session'),
    dcc.Store(id="Start-Time", storage_type='session'),
    dcc.Store(id="End-Time", storage_type='session'),
    dcc.Store(id="Exam-Date", storage_type='local'),
    dcc.Location(id="url", refresh=True),
    dash.page_container
])

if __name__ == '__main__':
    initialise_db()
    app.run(debug=True)
