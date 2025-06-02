# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the home page of the app. """

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
from in_app_documentation.documentation import return_documentation
from app import app
import visdcc
from user_agents import parse

# ==================================================================================================
# --- Layout
# ==================================================================================================

layout = (
    html.Div(
        id="home-content",
        style={
            "position": "absolute",
            "top": "0px",
            "right": "0px",
            "bottom": "0px",
            "left": "6rem",
            "height": "100vh",
            "background-color": "#1d1c1f",
            "overflow": "hidden",
        },
        children=[
            dmc.Center(
                dmc.Group(
                    direction="column",
                    align="stretch",
                    class_name="mt-4",
                    children=[
                        dmc.Text(
                            "Welcome to the Lipid Brain Atlas Explorer",
                            style={
                                "fontSize": 40,
                                "color": "#dee2e6",
                            },
                            align="center",
                        ),
                    ],
                ),
            ),
            dmc.Center(
                class_name="w-100",
                style={
                    "height": "calc(100vh - 90px)",
                    "overflow": "hidden",
                },
                children=[
                    dmc.Group(
                        class_name="mt-3",
                        direction="column",
                        align="center",
                        position="center",
                        children=[
                            html.Div(
                                children=[
                                    dbc.Spinner(
                                        color="info",
                                        spinner_style={
                                            "width": "3rem",
                                            "height": "3rem",
                                            "position": "absolute",
                                        },
                                        children=[
                                            html.Video(
                                                id="brain-video",
                                                src="/assets/lba01mp4.mp4",
                                                autoPlay=True,
                                                loop=True,
                                                muted=True,
                                                controls=False,
                                                style={
                                                    "width": "100%",
                                                    "height": "100%",
                                                    "objectFit": "cover",
                                                },
                                            ),
                                        ],
                                    ),
                                ],
                                style={
                                    "height": "100%",
                                    "width": "100%",
                                },
                            ),
                        ],
                    ),
                ],
            ),

            dcc.Store(id="dcc-store-mobile"),
            dcc.Store(id="dcc-store-browser"),
            
            # Toast notifications trigger
            dcc.Store(id="trigger-toast", data=True),
            # Alerts/info Offcanvas panel
            dcc.Store(id="alerts-panel-open", data=True),
            dbc.Offcanvas(
                id="alerts-offcanvas",
                is_open=True,
                placement="end",
                style={
                    "width": "350px",
                    "zIndex": 2000,
                    "backgroundColor": "#1d1c1f",
                    "color": "white",
                },
                # title="Information & Alerts",
                children=[
                    html.H5("Information & Alerts", style={"color": "white", "fontWeight": 700, "fontSize": "1.3rem", "marginTop": "1rem"}),
                    # Info banners at the top
                    dmc.Alert(
                        title="Documentation",
                        color="cyan",
                        children=[
                            "Please find the documentation available at the bottom left corner of the website."
                        ],
                        style={"marginBottom": "1rem", "backgroundColor": "#232f3e", "color": "#e3f6ff", "borderLeft": "5px solid #00bfff"},
                    ),
                    dmc.Alert(
                        title="Tutorial Video",
                        color="cyan",
                        children=[
                            "In each of the pages you will navigate, you will find some instructions. In case you want to be guided a bit more, please find a tutorial video clicking on the camera-icon on the sidebar!"
                        ],
                        style={"marginBottom": "1.5rem", "backgroundColor": "#232f3e", "color": "#e3f6ff", "borderLeft": "5px solid #00bfff"},
                    ),
                    dmc.Alert(
                        title="Mobile Device Warning",
                        color="red",
                        children=[
                            "Do not use this website on mobile devices.",
                        ],
                        style={"marginBottom": "1rem", "backgroundColor": "#2d1d1d", "color": "#ffd6d6", "borderLeft": "5px solid #ff4d4f"},
                    ),
                    dmc.Alert(
                        title="Safari Browser Warning",
                        color="yellow",
                        children=[
                            "Safari browser may cause performance issues.",
                        ],
                        style={"marginBottom": "1rem", "backgroundColor": "#2d2a1d", "color": "#fffbe6", "borderLeft": "5px solid #ffe066"},
                    ),
                    # Add more info/badges here if needed
                ],
            ),
            # Floating button to re-open the panel (always visible)
            html.Div(
                id="show-alerts-panel-btn-container",
                style={
                    "position": "fixed",
                    "top": "20px",
                    "right": "20px",
                    "zIndex": 2100,
                    "display": "block",
                },
                children=[
                    dbc.Button(
                        "Show Info & Alerts",
                        id="show-alerts-panel-btn",
                        color="info",
                        size="sm",
                    ),
                ],
            ),
        ],
    ),
)

# ==================================================================================================
# --- Callbacks
# ==================================================================================================

app.clientside_callback(
    """
    function(trigger) {
        browserInfo = navigator.userAgent;
        return browserInfo
    }
    """,
    Output("dcc-store-browser", "data"),
    Input("dcc-store-browser", "data"),
)

# --- Callbacks for alerts/info panel ---
@app.callback(
    Output("alerts-panel-open", "data"),
    Input("show-alerts-panel-btn", "n_clicks"),
    Input("alerts-offcanvas", "is_open"),
    State("alerts-panel-open", "data"),
    prevent_initial_call=True,
)
def toggle_alerts_panel(show_click, offcanvas_is_open, current_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_open
    btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if btn_id == "show-alerts-panel-btn":
        return True
    elif btn_id == "alerts-offcanvas":
        return offcanvas_is_open
    return current_open

# Sync the store state to the Offcanvas and show button
@app.callback(
    Output("alerts-offcanvas", "is_open"),
    Output("show-alerts-panel-btn-container", "style"),
    Input("alerts-panel-open", "data"),
)
def sync_alerts_panel(is_open):
    btn_style = {"display": "block", "position": "fixed", "top": "20px", "right": "20px", "zIndex": 2100} if not is_open else {"display": "none"}
    return is_open, btn_style
