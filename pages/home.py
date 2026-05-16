from dash import Dash, html, dcc, Input, Output, State, callback_context, callback
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

dash.register_page(__name__, path='/home')

layout = html.Div([
    html.H1("Welcome to your Revision Planner Dashboard!"),
], className="home-page")