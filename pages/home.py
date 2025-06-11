# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""This file contains the home page of the app."""

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
                            id="home-tutorial-target",
                            style={
                                "position": "fixed",
                                "top": "20px",
                                "left": "115px",
                                "zIndex": 2100,
                                # "width": "10rem",
                                # "height": "3rem",
                                "backgroundColor": "transparent",
                                "border": "3px solid #1fafc8",
                                "borderRadius": "4px",
                                # "boxShadow": "0 0 15px rgba(0, 191, 255, 0.7)",
                                "cursor": "pointer",
                            },
                            children=[
                                dbc.Button(
                                    "Start Tutorial",
                                    id="home-start-tutorial-btn",
                                    color="info",
                                    size="sm",
                                    className="home-tutorial-start-btn",
                                    style={
                                        # "width": "100%",
                                        # "height": "100%",
                                        "borderRadius": "4px",
                                        "backgroundColor": "transparent",
                                        "border": "none",
                                        # "color": "#00ffff",
                                        "fontWeight": "bold",
                                    },
                                )
                            ],
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
                                                src="/assets/lba02mp4.mp4",
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
            dcc.Store(id="home-tutorial-step", data=0),
            dcc.Store(id="home-tutorial-completed", storage_type="local", data=False),
            dcc.Store(id="tutorial-trigger", data=True),  # Add trigger store
            # Toast notifications trigger
            dcc.Store(id="trigger-toast", data=True),
            # Alerts/info Offcanvas panel
            dcc.Store(id="alerts-panel-open", data=True),
            # Tutorial target elements with highlight effect
            html.Div(
                id="brain-tutorial-target",
                style={
                    "position": "absolute",
                    "top": "20px",
                    "left": "20px",
                    "width": "40px",
                    "height": "40px",
                    "zIndex": 1000,
                    "cursor": "pointer",
                },
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
                    "cursor": "pointer",
                },
            ),
            # # --- New: Sidebar icon tutorial targets (invisible, just for popover targets) ---
            # html.Div(id="sidebar-molecules-tutorial-target"),
            # html.Div(id="sidebar-programs-tutorial-target"),
            # html.Div(id="sidebar-region-analysis-tutorial-target"),
            # html.Div(id="sidebar-lipizones-tutorial-target"),
            # html.Div(id="sidebar-comparisons-tutorial-target"),
            # html.Div(id="sidebar-3d-tutorial-target"),
            # # --- End new tutorial targets ---
            # Tutorial Popovers with adjusted positions
            dbc.Popover(
                [
                    dbc.PopoverHeader(
                        "Welcome to the Lipid Brain Atlas Explorer!",
                        style={"fontWeight": "bold"},
                    ),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "This tool lets you explore the mouse brain lipidome in 2D and 3D, across different conditions. You can inspect lipid patterns, analyze spatial clusters (lipizones), and uncover metabolic organization in the brain. Use the sidebar to navigate key features — let’s go over them!",
                                style={"color": "#333", "marginBottom": "15px"},
                            ),
                            dbc.Button(
                                "Next",
                                id="home-tutorial-next-1",
                                color="primary",
                                size="sm",
                                className="float-end",
                            ),
                        ]
                    ),
                ],
                id="home-tutorial-popover-1",
                target="home-tutorial-target",
                placement="right",
                is_open=False,
                style={
                    "zIndex": 9999,
                    "border": "2px solid #1fafc8",
                    "boxShadow": "0 0 15px 2px #1fafc8",
                },
            ),
            # --- Home Button (now points to sidebar brain icon) ---
            dbc.Popover(
                [
                    dbc.PopoverHeader("Home Page", style={"fontWeight": "bold"}),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "This is the Home Page, where general information and alerts are displayed. Click this brain icon to return to this page anytime.",
                                style={"color": "#333", "marginBottom": "15px"},
                            ),
                            dbc.Button(
                                "Next",
                                id="home-tutorial-next-2",
                                color="primary",
                                size="sm",
                                className="float-end",
                            ),
                        ]
                    ),
                ],
                id="home-tutorial-popover-2",
                target="sidebar-title",  # <-- brain icon in sidebar
                placement="right",
                is_open=False,
                style={
                    "zIndex": 9999,
                    "border": "2px solid #1fafc8",
                    "boxShadow": "0 0 15px 2px #1fafc8",
                },
                offset=40,
            ),
            # --- Molecules ---
            dbc.Popover(
                [
                    dbc.PopoverHeader("Molecules", style={"fontWeight": "bold"}),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "Explore raw lipid data from 172 imputed lipids and ~1400 m/z peaks. Data is preprocessed using uMAIA and shown across brain sections.",
                                style={"color": "#333", "marginBottom": "15px"},
                            ),
                            dbc.Button(
                                "Next",
                                id="home-tutorial-next-3",
                                color="primary",
                                size="sm",
                                className="float-end",
                            ),
                        ]
                    ),
                ],
                id="home-tutorial-popover-3",
                target="sidebar-molecules",  # molecules icon
                placement="right",
                is_open=False,
                style={
                    "zIndex": 9999,
                    "border": "2px solid #1fafc8",
                    "boxShadow": "0 0 15px 2px #1fafc8",
                },
                offset=40,
            ),
            # --- Lipid Programs ---
            dbc.Popover(
                [
                    dbc.PopoverHeader("Lipid Programs", style={"fontWeight": "bold"}),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "This tab shows computed features from lipid data — including NMF embeddings and Lipid Programs that reflect biological lipid modules.",
                                style={"color": "#333", "marginBottom": "15px"},
                            ),
                            dbc.Button(
                                "Next",
                                id="home-tutorial-next-4",
                                color="primary",
                                size="sm",
                                className="float-end",
                            ),
                        ]
                    ),
                ],
                id="home-tutorial-popover-4",
                target="sidebar-programs",  # lipid programs icon
                placement="right",
                is_open=False,
                style={
                    "zIndex": 9999,
                    "border": "2px solid #1fafc8",
                    "boxShadow": "0 0 15px 2px #1fafc8",
                },
                offset=40,
            ),
            # --- Differential Analysis ---
            dbc.Popover(
                [
                    dbc.PopoverHeader(
                        "Differential Analysis", style={"fontWeight": "bold"}
                    ),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "Compare brain regions using volcano plots to find lipids with significant expression differences.",
                                style={"color": "#333", "marginBottom": "15px"},
                            ),
                            dbc.Button(
                                "Next",
                                id="home-tutorial-next-5",
                                color="primary",
                                size="sm",
                                className="float-end",
                            ),
                        ]
                    ),
                ],
                id="home-tutorial-popover-5",
                target="sidebar-region-analysis",  # region analysis icon
                placement="right",
                is_open=False,
                style={
                    "zIndex": 9999,
                    "border": "2px solid #1fafc8",
                    "boxShadow": "0 0 15px 2px #1fafc8",
                },
                offset=40,
            ),
            # --- Lipizones ---
            dbc.Popover(
                [
                    dbc.PopoverHeader("Lipizones", style={"fontWeight": "bold"}),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "Lipizones are spatial lipid clusters that reveal organization in gray and white matter. They highlight metabolic zones related to connectivity, cell types, and development.",
                                style={"color": "#333", "marginBottom": "15px"},
                            ),
                            dbc.Button(
                                "Next",
                                id="home-tutorial-next-6",
                                color="primary",
                                size="sm",
                                className="float-end",
                            ),
                        ]
                    ),
                ],
                id="home-tutorial-popover-6",
                target="sidebar-lipizones",  # lipizones icon
                placement="right",
                is_open=False,
                style={
                    "zIndex": 9999,
                    "border": "2px solid #1fafc8",
                    "boxShadow": "0 0 15px 2px #1fafc8",
                },
                offset=40,
            ),
            # --- Comparisons ---
            dbc.Popover(
                [
                    dbc.PopoverHeader("Comparisons", style={"fontWeight": "bold"}),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "Cross-compare lipid levels with gene expression or lipizones with cell types to spot shared spatial patterns.",
                                style={"color": "#333", "marginBottom": "15px"},
                            ),
                            dbc.Button(
                                "Next",
                                id="home-tutorial-next-7",
                                color="primary",
                                size="sm",
                                className="float-end",
                            ),
                        ]
                    ),
                ],
                id="home-tutorial-popover-7",
                target="sidebar-comparisons",  # comparisons icon
                placement="right",
                is_open=False,
                style={
                    "zIndex": 9999,
                    "border": "2px solid #1fafc8",
                    "boxShadow": "0 0 15px 2px #1fafc8",
                },
                offset=40,
            ),
            # --- 3D Exploration ---
            dbc.Popover(
                [
                    dbc.PopoverHeader("3D Exploration", style={"fontWeight": "bold"}),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "See lipid and lipizone patterns in 3D, mapped across the whole brain for immersive exploration.",
                                style={"color": "#333", "marginBottom": "15px"},
                            ),
                            dbc.Button(
                                "Next",
                                id="home-tutorial-next-8",
                                color="primary",
                                size="sm",
                                className="float-end",
                            ),
                        ]
                    ),
                ],
                id="home-tutorial-popover-8",
                target="sidebar-3d",  # 3d icon
                placement="right",
                is_open=False,
                style={
                    "zIndex": 9999,
                    "border": "2px solid #1fafc8",
                    "boxShadow": "0 0 15px 2px #1fafc8",
                },
                offset=40,
            ),
            # --- Documentation (now points to book icon) ---
            dbc.Popover(
                [
                    dbc.PopoverHeader("Documentation", style={"fontWeight": "bold"}),
                    dbc.PopoverBody(
                        [
                            html.P(
                                "This button provides a detailed introduction to the LBA Explorer, including key concepts and a set of useful links. It’s a great place to learn the background behind the project and find reference materials.",
                                style={"color": "#333", "marginBottom": "15px"},
                            ),
                            dbc.Button(
                                "Finish",
                                id="home-tutorial-finish",
                                color="success",
                                size="sm",
                                className="float-end",
                            ),
                        ]
                    ),
                ],
                id="home-tutorial-popover-9",
                target="sidebar-documentation-inside",  # <-- book icon in sidebar
                placement="right",
                is_open=False,
                style={
                    "zIndex": 9999,
                    "border": "2px solid #1fafc8",
                    "boxShadow": "0 0 15px 2px #1fafc8",
                },
                offset=40,
            ),
            dbc.Offcanvas(
                id="alerts-offcanvas",
                is_open=True,
                placement="end",
                style={
                    "width": "350px",
                    "zIndex": 9999,
                    "backgroundColor": "#1d1c1f",
                    "color": "white",
                },
                # title="Information & Alerts",
                children=[
                    html.H5(
                        "Information & Alerts",
                        style={
                            "color": "white",
                            "fontWeight": 700,
                            "fontSize": "1.3rem",
                            "marginTop": "1rem",
                        },
                    ),
                    # Info banners at the top
                    dmc.Alert(
                        title="Documentation",
                        color="cyan",
                        children=[
                            "Please find the documentation available at the bottom left corner of the website."
                        ],
                        style={
                            "marginBottom": "1rem",
                            "backgroundColor": "#232f3e",
                            "color": "#e3f6ff",
                            "borderLeft": "5px solid #1fafc8",
                        },
                    ),
                    dmc.Alert(
                        title="Mobile Device Warning",
                        color="red",
                        children=[
                            "Do not use this website on mobile devices.",
                        ],
                        style={
                            "marginBottom": "1rem",
                            "backgroundColor": "#2d1d1d",
                            "color": "#ffd6d6",
                            "borderLeft": "5px solid #ff4d4f",
                        },
                    ),
                    dmc.Alert(
                        title="Safari Browser Warning",
                        color="yellow",
                        children=[
                            "Safari browser may cause performance issues.",
                        ],
                        style={
                            "marginBottom": "1rem",
                            "backgroundColor": "#2d2a1d",
                            "color": "#fffbe6",
                            "borderLeft": "5px solid #ffe066",
                        },
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
    [Input("show-alerts-panel-btn", "n_clicks"), Input("alerts-offcanvas", "is_open")],
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
    [
        Output("alerts-offcanvas", "is_open"),
        Output("show-alerts-panel-btn-container", "style"),
    ],
    Input("alerts-panel-open", "data"),
    prevent_initial_call=True,
)
def sync_alerts_panel(is_open):
    if is_open is None:
        return dash.no_update, dash.no_update
    btn_style = (
        {
            "display": "block",
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "zIndex": 2100,
        }
        if not is_open
        else {"display": "none"}
    )
    return is_open, btn_style


# Use clientside callback for tutorial step updates
app.clientside_callback(
    """
    function(start, next1, next2, next3, next4, next5, next6, next7, next8, finish) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered.length) {
            return window.dash_clientside.no_update;
        }
        const trigger_id = ctx.triggered[0].prop_id.split('.')[0];
        if (trigger_id === 'home-start-tutorial-btn' && start) {
            return 1;
        } else if (trigger_id === 'home-tutorial-next-1' && next1) {
            return 2;
        } else if (trigger_id === 'home-tutorial-next-2' && next2) {
            return 3;
        } else if (trigger_id === 'home-tutorial-next-3' && next3) {
            return 4;
        } else if (trigger_id === 'home-tutorial-next-4' && next4) {
            return 5;
        } else if (trigger_id === 'home-tutorial-next-5' && next5) {
            return 6;
        } else if (trigger_id === 'home-tutorial-next-6' && next6) {
            return 7;
        } else if (trigger_id === 'home-tutorial-next-7' && next7) {
            return 8;
        } else if (trigger_id === 'home-tutorial-next-8' && next8) {
            return 9;
        } else if (trigger_id === 'home-tutorial-finish' && finish) {
            return 0;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("home-tutorial-step", "data"),
    [
        Input("home-start-tutorial-btn", "n_clicks"),
        Input("home-tutorial-next-1", "n_clicks"),
        Input("home-tutorial-next-2", "n_clicks"),
        Input("home-tutorial-next-3", "n_clicks"),
        Input("home-tutorial-next-4", "n_clicks"),
        Input("home-tutorial-next-5", "n_clicks"),
        Input("home-tutorial-next-6", "n_clicks"),
        Input("home-tutorial-next-7", "n_clicks"),
        Input("home-tutorial-next-8", "n_clicks"),
        Input("home-tutorial-finish", "n_clicks"),
    ],
    prevent_initial_call=True,
)

# Use clientside callback for popover visibility
app.clientside_callback(
    """
    function(step) {
        if (step === undefined || step === null) {
            return [false, false, false, false, false, false, false, false, false];
        }
        return [
            step === 1,
            step === 2,
            step === 3,
            step === 4,
            step === 5,
            step === 6,
            step === 7,
            step === 8,
            step === 9
        ];
    }
    """,
    [Output(f"home-tutorial-popover-{i}", "is_open") for i in range(1, 10)],
    Input("home-tutorial-step", "data"),
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
    Output("home-tutorial-completed", "data"),
    Input("home-tutorial-finish", "n_clicks"),
    prevent_initial_call=True,
)
