from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from database import initialise_db

app = Dash(__name__, use_pages=True)
app.layout = html.Div([
    dcc.Location(id="url", refresh=True),
    html.H1("Revision Planner"),
    dash.page_container
])

if __name__ == '__main__':
    initialise_db()
    app.run(debug=True)
