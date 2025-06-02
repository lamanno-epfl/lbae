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
                        # Add tutorial button under welcome text
                        html.Div(
                            id="sidebar-tutorial-target",
                            style={
                                "position": "relative",
                                "width": "10rem",
                                "height": "4rem",
                                "margin": "1rem auto",
                                "zIndex": 1000,
                                "backgroundColor": "transparent",
                                "border": "3px solid #00bfff",
                                "borderRadius": "4px",
                                "boxShadow": "0 0 15px rgba(0, 191, 255, 0.7)",
                                "cursor": "pointer",
                            },
                            children=[
                                dbc.Button(
                                    "Start Tutorial",
                                    id="start-tutorial-btn",
                                    color="info",
                                    size="sm",
                                    style={
                                        "position": "absolute",
                                        "top": "50%",
                                        "left": "50%",
                                        "transform": "translate(-50%, -50%)",
                                        "zIndex": 1001,
                                        "width": "100%",
                                        "height": "100%",
                                        "borderRadius": "4px",
                                        "backgroundColor": "transparent",
                                        "border": "none",
                                        "color": "#00bfff",
                                        "fontWeight": "bold",
                                    }
                                )
                            ]
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
                                    # # Add docs tutorial target
                                    # html.Div(
                                    #     id="docs-tutorial-target",
                                    #     style={
                                    #         "position": "absolute",
                                    #         "left": "20px",
                                    #         "bottom": "20px",
                                    #         "width": "40px",
                                    #         "height": "40px",
                                    #         "zIndex": 1000,
                                    #         "backgroundColor": "rgba(0,191,255,0.1)",
                                    #         "border": "3px solid #00bfff",
                                    #         "borderRadius": "50%",
                                    #         "boxShadow": "0 0 15px rgba(0, 191, 255, 0.7)",
                                    #         "cursor": "pointer",
                                    #     }
                                    # ),
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
            
            # Store for tracking tutorial state
            dcc.Store(id="tutorial-step", data=0),
            dcc.Store(id="tutorial-completed", storage_type="local", data=False),
            dcc.Store(id="tutorial-trigger", data=True),  # Add trigger store
            
            # Toast notifications trigger
            dcc.Store(id="trigger-toast", data=True),
            # Alerts/info Offcanvas panel
            dcc.Store(id="alerts-panel-open", data=True),
            
            # Tutorial target elements with highlight effect
            html.Div(
                id="home-tutorial-target",
                style={
                    "position": "absolute",
                    "top": "20px",
                    "left": "20px",
                    "width": "40px",
                    "height": "40px",
                    "zIndex": 1000,
                    # "backgroundColor": "rgba(0,191,255,0.1)",
                    # "border": "3px solid #00bfff",
                    # "borderRadius": "50%",
                    # "boxShadow": "0 0 15px rgba(0, 191, 255, 0.7)",
                    "cursor": "pointer",
                }
            ),
            html.Div(
                id="docs-tutorial-target",
                style={
                    "position": "absolute",
                    "left": "20px",
                    "bottom": "20px",
                    "width": "40px",
                    "height": "40px",
                    "zIndex": 1000,
                    # "backgroundColor": "rgba(0,191,255,0.1)",
                    # "border": "3px solid #00bfff",
                    # "borderRadius": "50%",
                    # "boxShadow": "0 0 15px rgba(0, 191, 255, 0.7)",
                    "cursor": "pointer",
                }
            ),
            
            # Tutorial Popovers with adjusted positions
            dbc.Popover(
                [
                    dbc.PopoverHeader("Welcome to the Lipid Brain Atlas Explorer!"),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "Let's take a quick tour of the main features. Click 'Next' to continue.",
                                style={"color": "#333", "marginBottom": "15px"}
                            ),
                            dbc.Button("Next", id="tutorial-next-1", color="primary", size="sm", className="float-end")
                        ]
                    ),
                ],
                id="tutorial-popover-1",
                target="sidebar-tutorial-target",
                placement="right",
                is_open=False,
                style={"zIndex": 2000}
            ),
            
            dbc.Popover(
                [
                    dbc.PopoverHeader("Navigation"),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "Use the sidebar on the left to navigate between different pages and explore the atlas.",
                                style={"color": "#333", "marginBottom": "15px"}
                            ),
                            dbc.Button("Next", id="tutorial-next-2", color="primary", size="sm", className="float-end")
                        ]
                    ),
                ],
                id="tutorial-popover-2",
                target="sidebar-tutorial-target",
                placement="right",
                is_open=False,
                style={"zIndex": 2000}
            ),
            
            dbc.Popover(
                [
                    dbc.PopoverHeader("Home Button"),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "Click the home icon at the top left to return to this page anytime.",
                                style={"color": "#333", "marginBottom": "15px"}
                            ),
                            dbc.Button("Next", id="tutorial-next-3", color="primary", size="sm", className="float-end")
                        ]
                    ),
                ],
                id="tutorial-popover-3",
                target="home-tutorial-target",
                placement="bottom",
                is_open=False,
                style={"zIndex": 2000}
            ),
            
            dbc.Popover(
                [
                    dbc.PopoverHeader("Documentation"),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "Find detailed documentation, GitHub repository links, and publication information at the bottom left.",
                                style={"color": "#333", "marginBottom": "15px"}
                            ),
                            dbc.Button("Finish", id="tutorial-finish", color="success", size="sm", className="float-end")
                        ]
                    ),
                ],
                id="tutorial-popover-4",
                target="docs-tutorial-target",
                placement="top",
                is_open=False,
                style={"zIndex": 2000}
            ),
            
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
            # Floating button to re-open the panel (only visible if the panel is closed)
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
    [Input("show-alerts-panel-btn", "n_clicks"),
     Input("alerts-offcanvas", "is_open")],
    State("alerts-panel-open", "data"),
    prevent_initial_call=True,
)
def toggle_alerts_panel(show_click, offcanvas_is_open, current_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "show-alerts-panel-btn" and show_click:
        return True
    elif trigger_id == "alerts-offcanvas":
        return offcanvas_is_open
    return dash.no_update

# Sync the store state to the Offcanvas and show button
@app.callback(
    [Output("alerts-offcanvas", "is_open"),
     Output("show-alerts-panel-btn-container", "style")],
    Input("alerts-panel-open", "data"),
    prevent_initial_call=True,
)
def sync_alerts_panel(is_open):
    if is_open is None:
        return dash.no_update, dash.no_update
    btn_style = {"display": "block", "position": "fixed", "top": "20px", "right": "20px", "zIndex": 2100} if not is_open else {"display": "none"}
    return is_open, btn_style

# Use clientside callback for tutorial step updates
app.clientside_callback(
    """
    function(start, next1, next2, next3, finish) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered.length) {
            return window.dash_clientside.no_update;
        }
        
        const trigger_id = ctx.triggered[0].prop_id.split('.')[0];
        
        if (trigger_id === 'start-tutorial-btn' && start) {
            return 1;
        } else if (trigger_id === 'tutorial-next-1' && next1) {
            return 2;
        } else if (trigger_id === 'tutorial-next-2' && next2) {
            return 3;
        } else if (trigger_id === 'tutorial-next-3' && next3) {
            return 4;
        } else if (trigger_id === 'tutorial-finish' && finish) {
            return 0;
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("tutorial-step", "data"),
    [Input("start-tutorial-btn", "n_clicks"),
     Input("tutorial-next-1", "n_clicks"),
     Input("tutorial-next-2", "n_clicks"),
     Input("tutorial-next-3", "n_clicks"),
     Input("tutorial-finish", "n_clicks")],
    prevent_initial_call=True,
)

# Use clientside callback for popover visibility
app.clientside_callback(
    """
    function(step) {
        if (step === undefined || step === null) {
            return [false, false, false, false];
        }
        return [
            step === 1,
            step === 2,
            step === 3,
            step === 4
        ];
    }
    """,
    [Output(f"tutorial-popover-{i}", "is_open") for i in range(1, 5)],
    Input("tutorial-step", "data"),
    prevent_initial_call=True,
)

# Use clientside callback for tutorial completion
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            return true;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("tutorial-completed", "data"),
    Input("tutorial-finish", "n_clicks"),
    prevent_initial_call=True,
)