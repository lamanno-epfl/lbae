# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to select and visualize lipids according to pre-existing 
annotations, or directly using m/z ranges."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html, clientside_callback
import logging
import dash
import json
import pandas as pd
from dash.dependencies import Input, Output, State, ALL
import dash_mantine_components as dmc
import numpy as np
from scipy.ndimage import gaussian_filter
import pickle
import os
import re
import PyPDF2
import io
from flask import send_file
# os.environ['OMP_NUM_THREADS'] = '1'
from dash.long_callback import DiskcacheLongCallbackManager

# LBAE imports
from app import app, figures, data, atlas, lipizone_data, cache_flask
import plotly.express as px

# ==================================================================================================
# --- Constants
# ==================================================================================================

# Path to the ID cards
ID_CARDS_PATH = "./data/ID_cards"

# ==================================================================================================
# --- Helper functions
# ==================================================================================================

from modules.figures import black_aba_contours, is_light_color, clean_filenamePD

# ==================================================================================================
# --- Layout
# ==================================================================================================

def return_layout(basic_config, slice_index):
    """Return the layout for the page."""
    # Create treemap data
    df_treemap, node_colors = lipizone_data.create_treemap_data_lipizones()
    
    page = html.Div(
        style={
            "position": "absolute",
            "top": "0px",
            "right": "0px",
            "bottom": "0px",
            "left": "6rem",
            "background-color": "#1d1c1f",
        },
        children=[
            dcc.Store(id="lipizone-tutorial-step", data=0),
            dcc.Store(id="lipizone-tutorial-completed", storage_type="local", data=False),
            # Add tutorial button under welcome text
            html.Div(
                id="lipizone-start-tutorial-target",
                style={
                    "position": "fixed",
                    "top": "0.9em",
                    "left": "21.3em",
                    "zIndex": 2100,
                    "backgroundColor": "transparent",
                    "border": "3px solid #1fafc8",
                    "borderRadius": "4px",
                    "cursor": "pointer",
                },
                children=[
                    dbc.Button(
                        "Start Tutorial",
                        id="lipizone-start-tutorial-btn",
                        color="info",
                        size="sm",
                        className="tutorial-start-btn",
                        style={
                            "borderRadius": "4px",
                            "backgroundColor": "transparent",
                            "border": "none",
                            "fontWeight": "bold",
                        }
                    )
                ]
            ),

            html.Div(
                className="fixed-aspect-ratio",
                style={"background-color": "#1d1c1f"},
                children=[
                    # Main visualization
                    dcc.Graph(
                        id="page-6-graph-heatmap-mz-selection",
                        config=basic_config | {
                            "toImageButtonOptions": {
                                "format": "png",
                                "filename": "brain_lipizone_selection",
                                "scale": 2,
                            },
                            "scrollZoom": True
                        },
                        style={
                            "width": "77%",
                            "height": "100%",
                            "position": "absolute",
                            "left": "20%",
                            "top": "0",
                            "background-color": "#1d1c1f",
                        },
                        figure=figures.build_lipid_heatmap_from_image(
                            figures.all_sections_lipizones_image(
                                hex_colors_to_highlight=None, # all lipizones
                                brain_id="ReferenceAtlas"),
                            return_base64_string=False,
                            draw=False,
                            type_image="RGB",
                            return_go_image=False,
                        )
                    ),
                    # OffCanvas panel for ID cards
                    dbc.Offcanvas(
                        id="id-cards-panel",
                        is_open=False,  # Closed by default
                        backdrop=False,
                        placement="end",
                        style={
                            "width": "calc(100% - 6rem)",
                            "height": "100vh",
                            "backgroundColor": "#1d1c1f",
                            "padding": "0",
                            "overflow": "hidden",
                        },
                        children=[
                            dbc.Card(
                                style={
                                    "width": "100%",
                                    "height": "100%",
                                    "margin": "0",
                                    "backgroundColor": "#1d1c1f",
                                },
                                children=[
                                    dbc.CardHeader(
                                        className="d-flex justify-content-between align-items-center",
                                        style={
                                            "backgroundColor": "#1d1c1f",
                                            "color": "white",
                                            "border": "none",
                                            "padding": "1rem",
                                        },
                                        children=[
                                            html.H3(
                                                "Lipizones ID Cards",
                                                style={
                                                    "margin": "0",
                                                    "color": "white",
                                                    "fontSize": "1.8rem",
                                                }
                                            ),
                                            dmc.Button(
                                                children="Hide ID Cards",
                                                id="close-id-cards-panel",
                                                variant="filled",
                                                color="red",
                                                radius="md",
                                                size="md",
                                            ),
                                        ]
                                    ),
                                    # PDF viewer container only
                                    html.Div(
                                        id="pdf-viewer-container",
                                        style={
                                            "width": "100%",
                                            "height": "calc(100% - 4rem)",
                                            "backgroundColor": "#1d1c1f",
                                            "display": "flex",
                                            "justifyContent": "center",
                                            "alignItems": "center",
                                        },
                                        children=[
                                            html.Div(
                                                "Select lipizones to view their ID cards",
                                                style={
                                                    "color": "white",
                                                    "fontSize": "1.2rem",
                                                    "textAlign": "center",
                                                }
                                            )
                                        ]
                                    ),
                                ]
                            ),
                        ],
                    ),
                    # Hover text
                    dmc.Text(
                        "",
                        id="page-6-graph-hover-text",
                        size="xl",
                        align="center",
                        color="cyan",
                        class_name="mt-5",
                        weight=500,
                        style={
                            "width": "auto",
                            "position": "absolute",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "top": "1em",
                            "fontSize": "1.5em",
                            "textAlign": "center",
                            "zIndex": 1000,
                            "backgroundColor": "rgba(0, 0, 0, 0.7)",
                            "padding": "0.5em 2em",
                            "borderRadius": "8px",
                            "minWidth": "200px",
                            "display": "block",
                        },
                    ),
                    # Title
                    html.H4(
                        "Visualize Lipizones",
                        style={
                            "color": "white",
                            "marginBottom": "15px",
                            "fontSize": "1.2em",
                            "fontWeight": "500",
                            "position": "absolute",
                            "left": "1%",
                            "top": "1em",
                        }
                    ),
                    # Left panel with treemap and controls
                    html.Div(
                        style={
                            "width": "20%",
                            "height": "95%",
                            "position": "absolute",
                            "left": "0",
                            "top": "3em",
                            "background-color": "#1d1c1f",
                            "display": "flex",
                            "flexDirection": "column",
                            "padding": "10px",
                        },
                        children=[
                            # Select All button
                            dmc.Button(
                                children="Select All Lipizones",
                                id="page-6-select-all-lipizones-button",
                                variant="filled",
                                color="cyan",
                                radius="md",
                                size="sm",
                                style={
                                    "marginBottom": "5px",
                                },
                            ),
                            html.Div(
                                id="lipizone-treemap-container",  # Add this ID
                                style={
                                    "height": "40%",
                                    "background-color": "#1d1c1f",
                                },
                                children=[
                                    dcc.Graph(
                                        id="page-6-lipizones-treemap",
                                        figure=lipizone_data.create_treemap_figure_lipizones(df_treemap, node_colors),
                                        style={
                                            "height": "100%",  # Make it fill the container
                                            "background-color": "#1d1c1f",
                                        },
                                        config={'displayModeBar': False}
                                    ),
                                ]
                            ),
                            # Current selection text
                            html.Div(
                                id="page-6-current-selection-text",
                                style={
                                    "padding": "10px",
                                    "color": "white",
                                    "fontSize": "0.9em",
                                    "backgroundColor": "#2c2c2c",
                                    "borderRadius": "5px",
                                    "marginTop": "10px",
                                },
                                children=["Click on a node in the tree to select all lipizones under it"]
                            ),
                            # Add selection buttons group
                            html.Div(
                                style={
                                    "marginTop": "10px",
                                    "display": "flex",
                                    "flexDirection": "row",
                                    "gap": "10px",
                                    "width": "100%",  # Take full width of container
                                },
                                children=[
                                    dmc.Button(
                                        children="Add selection",
                                        id="page-6-add-selection-button",
                                        variant="outline",
                                        color="cyan",
                                        radius="md",
                                        size="sm",
                                        style={
                                            "flex": "1",
                                            "maxWidth": "50%",  # Ensure button doesn't exceed half the container
                                        },
                                    ),
                                    dmc.Button(
                                        children="Clear selection",
                                        id="page-6-clear-selection-button",
                                        variant="outline",
                                        color="red",
                                        radius="md",
                                        size="sm",
                                        style={
                                            "flex": "1",
                                            "maxWidth": "50%",  # Ensure button doesn't exceed half the container
                                        },
                                    ),
                                ]
                            ),
                            # Selected lipizones badges
                            html.Div(
                                id="page-6-selected-lipizones-badges",
                                style={
                                    "height": "30%",
                                    "overflowY": "auto",
                                    "padding": "10px",
                                    "marginTop": "10px",
                                    "backgroundColor": "#2c2c2c",
                                    "borderRadius": "5px",
                                },
                                children=[
                                    html.H6("Selected Lipizones", style={"color": "white", "marginBottom": "10px"}),
                                ]
                            ),
                            # View ID Cards button in bottom left, cyan
                            html.Div(
                                style={
                                    "marginTop": "50px",
                                    "display": "flex",
                                    "flexDirection": "row",
                                    "gap": "10px",
                                    "width": "100%",  # Take full width of container
                                },
                                children=[
                                    dmc.Button(
                                        "View ID Cards",
                                        id="view-id-cards-btn",
                                        variant="filled",
                                        color="cyan",
                                        radius="md",
                                        size="sm",
                                        style={
                                            "flex": "1",
                                            "maxWidth": "100%",  # Ensure button doesn't exceed half the container
                                        },
                                    )
                                ]
                            ),
                        ],
                    ),
                    # Controls for section mode and aba annotations
                    html.Div(
                        style={
                            "left": "25%",
                            "top": "3.5em",
                            "position": "fixed",
                            "z-index": 1000,
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.5rem",
                            "alignItems": "center",
                        },
                        children=[
                            # Sections mode control
                            dmc.SegmentedControl(
                                id="page-6-sections-mode",
                                value="one",
                                data=[
                                    {"value": "one", "label": "One section"},
                                    {"value": "all", "label": "All sections"},
                                ],
                                color="cyan",
                                disabled=True,
                                size="xs",
                                style={
                                    "width": "20em",
                                    "border": "1px solid rgba(255, 255, 255, 0.1)",
                                    "borderRadius": "4px",
                                }
                            ),
                            # Allen Brain Atlas switch
                            html.Div(
                                id="page-6-annotations-container",
                                style={
                                    "display": "flex",
                                    "flexDirection": "row",
                                    "alignItems": "left",
                                    "justifyContent": "left",
                                    "width": "20em",
                                },
                                children=[
                                    dmc.Switch(
                                        id="page-6-toggle-annotations",
                                        checked=False,
                                        color="cyan",
                                        radius="xl",
                                        size="sm",
                                    ),
                                    html.Span(
                                        "Allen Brain Atlas Annotations",
                                        style={
                                            "color": "white",
                                            "marginLeft": "10px",
                                            "whiteSpace": "nowrap",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Controls at the bottom right
                    # html.Div(
                    #     style={
                    #         "right": "1rem",
                    #         "bottom": "1rem",
                    #         "position": "fixed",
                    #         "z-index": 1000,
                    #         "display": "flex",
                    #         "flexDirection": "column",
                    #         "gap": "0.5rem",
                    #     },
                    #     children=[
                    #         dmc.Button(
                    #             children="Download data",
                    #             id="page-6-download-data-button",
                    #             variant="filled",
                    #             disabled=False,
                    #             color="cyan",
                    #             radius="md",
                    #             size="sm",
                    #             style={"width": "150px"},
                    #         ),
                    #         dmc.Button(
                    #             children="Download image",
                    #             id="page-6-download-image-button",
                    #             variant="filled",
                    #             disabled=False,
                    #             color="cyan",
                    #             radius="md",
                    #             size="sm",
                    #             style={"width": "150px"},
                    #         ),
                    #     ],
                    # ),
                    # dcc.Download(id="page-6-download-data"),
                    
                    # Tutorial Popovers with adjusted positions
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Lipizones Exploration",
                                    dbc.Button(
                                        "×",
                                        id="lipizone-tutorial-close-1",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "Welcome to the Lipizones page! Lipizones are lipid-based spatial territories in the brain. They often align with known cell-type distributions but also highlight distal axonal projections and metabolic compartments. By exploring lipizones, you can uncover key organizational principles of the brain, including connectivity, cytoarchitecture, and developmental patterning. Feel free to zoom in and out on the visualization displayed and to move the brain around by clicking and dragging.",
                                        style={"color": "#333", "marginBottom": "15px"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipizone-tutorial-prev-1",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                                disabled=True,
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipizone-tutorial-next-1",
                                                color="primary",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between"},
                                    ),
                                ]
                            ),
                        ],
                        id="lipizone-tutorial-popover-1",
                        target="lipizone-start-tutorial-target",
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8"
                        }
                    ),
                    # --- All Lipizones Button ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Display All Lipizones",
                                    dbc.Button(
                                        "×",
                                        id="lipizone-tutorial-close-2",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "This button displays all lipizones in the current slice by default. If you want to focus on specific lipizones, remember to first clear the current selection using the appropriate button.",
                                        style={"color": "#333", "marginBottom": "15px"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipizone-tutorial-prev-2",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipizone-tutorial-next-2",
                                                color="primary",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between"},
                                    ),
                                ]
                            ),
                        ],
                        id="lipizone-tutorial-popover-2",
                        target="page-6-select-all-lipizones-button",
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8"
                        },
                    ),
                    # --- Lipizones Selection ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Navigate Lipizones Hierarchy",
                                    dbc.Button(
                                        "×",
                                        id="lipizone-tutorial-close-3",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "Use the treemap to explore and select lipizones from a hierarchical structure. Lipizones are defined as 539 spatial clusters computed through an iterative bipartite splitter. You can navigate the hierarchy freely and stop at any level of detail. Once you're satisfied with the selection, you can add those lipizones for visualization.",
                                        style={"color": "#333", "marginBottom": "15px"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipizone-tutorial-prev-3",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipizone-tutorial-next-3",
                                                color="primary",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between"},
                                    ),
                                ]
                            ),
                        ],
                        id="lipizone-tutorial-popover-3",
                        target="lipizone-treemap-container",  # dropdown menu
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8"
                        },
                    ),
                    # --- Add Selection Button ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Visualize Selected Lipizones",
                                    dbc.Button(
                                        "×",
                                        id="lipizone-tutorial-close-4",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "After selecting the desired lipizones from the treemap, click this button to add them to the current view. The display will update accordingly to show your selection.",
                                        style={"color": "#333", "marginBottom": "15px"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipizone-tutorial-prev-4",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipizone-tutorial-next-4",
                                                color="primary",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between"},
                                    ),
                                ]
                            ),
                        ],
                        id="lipizone-tutorial-popover-4",
                        target="page-6-add-selection-button",  # dropdown menu
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8"
                        },
                    ),
                    # --- Clear Selection Button ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Reset the Brain View",
                                    dbc.Button(
                                        "×",
                                        id="lipizone-tutorial-close-5",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "Use this button to remove all currently selected lipizones and return to an empty brain view. This is helpful if you want to start over or explore a new subset.",
                                        style={"color": "#333", "marginBottom": "15px"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipizone-tutorial-prev-5",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipizone-tutorial-next-5",
                                                color="primary",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between"},
                                    ),
                                ]
                            ),
                        ],
                        id="lipizone-tutorial-popover-5",
                        target="page-6-clear-selection-button",  # dropdown menu
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8"
                        },
                    ),
                    # --- View ID Cards Button ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "View Lipizones ID Cards",
                                    dbc.Button(
                                        "×",
                                        id="lipizone-tutorial-close-6",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "You can view the ID Card of any selected lipizone. This is a one-page PDF that summarizes key statistics and characteristics of the lipizone, serving as a detailed reference for further analysis or documentation.",
                                        style={"color": "#333", "marginBottom": "15px"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipizone-tutorial-prev-6",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipizone-tutorial-next-6",
                                                color="primary",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between"},
                                    ),
                                ]
                            ),
                        ],
                        id="lipizone-tutorial-popover-6",
                        target="view-id-cards-btn",  # dropdown menu
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8"
                        },
                    ),
                    # --- One vs All Sections ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "View All Slices at Once",
                                    dbc.Button(
                                        "×",
                                        id="lipizone-tutorial-close-7",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "You can switch to a view that shows all brain sections at once. In this mode, only the first selected lipid will be displayed to keep the view clean and interpretable.",
                                        style={"color": "#333", "marginBottom": "15px"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipizone-tutorial-prev-7",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipizone-tutorial-next-7",
                                                color="primary",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between"},
                                    ),
                                ]
                            ),
                        ],
                        id="lipizone-tutorial-popover-7",
                        target="page-6-sections-mode",  # sections mode switch
                        placement="bottom",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8"
                        },
                    ),
                    # --- Annotations ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Overlay Anatomical Contours",
                                    dbc.Button(
                                        "×",
                                        id="lipizone-tutorial-close-8",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "You can enable the Allen Brain Atlas annotations to overlay anatomical labels directly on the slices. This helps you navigate the brain and interpret lipid signals in their biological context.",
                                        style={"color": "#333", "marginBottom": "15px"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipizone-tutorial-prev-8",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipizone-tutorial-next-8",
                                                color="primary",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between"},
                                    ),
                                ]
                            ),
                        ],
                        id="lipizone-tutorial-popover-8",
                        target="page-6-toggle-annotations",  # annotations switch
                        placement="bottom",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8"
                        },
                    ),
                    # --- Brain Slider ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Navigate Along Brain Anterior-Posterior Axis",
                                    dbc.Button(
                                        "×",
                                        id="lipizone-tutorial-close-9",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "In the single-section view, you can navigate through the brain by selecting different slices along the rostro-caudal (front-to-back) axis. This allows detailed inspection of lipid signals at specific anatomical levels.",
                                        style={"color": "#333", "marginBottom": "15px"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipizone-tutorial-prev-9",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipizone-tutorial-next-9",
                                                color="primary",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between"},
                                    ),
                                ]
                            ),
                        ],
                        id="lipizone-tutorial-popover-9",
                        target="main-paper-slider",  # slider
                        placement="top",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8"
                        },
                    ),
                    # --- Brain Chips ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Choose Experimental Condition",
                                    dbc.Button(
                                        "×",
                                        id="lipizone-tutorial-close-10",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "You can choose which mouse brain to view. Brain1 is the reference brain used for the atlas, but you can also explore Brain2, control male and female brains, and pregnant brains to see how lipid distributions differ across biological conditions. M stands for male, F for female.",
                                        style={"color": "#333", "marginBottom": "15px"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipizone-tutorial-prev-10",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Finish",
                                                id="lipizone-tutorial-finish",
                                                color="success",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between"},
                                    ),
                                ]
                            ),
                        ],
                        id="lipizone-tutorial-popover-10",
                        target="main-brain",  # brain switch
                        placement="left",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8"
                        },
                    ),
                ],
            ),
        ],
    )
    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================

@app.callback(
    Output("page-6-current-treemap-selection", "data"),
    Output("page-6-current-selection-text", "children"),
    Input("page-6-lipizones-treemap", "clickData"),
)
def update_current_selection(click_data):
    """Store the current treemap selection."""
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    if not click_data:
        return None, "Click on a node in the tree to select all lipizones under it"
    
    clicked_label = click_data["points"][0]["label"] # 1_1
    current_path = click_data["points"][0]["id"] # /1/
    
    # Filter hierarchy based on the clicked node's path
    filtered = lipizone_data.df_hierarchy_lipizones.copy()
    # Get the level of the clicked node
    path_columns = ['level_1_name', 'level_2_name', 'level_3_name', 'level_4_name', 'subclass_name', 'lipizone_names']
    
    # Apply filters based on the entire path up to the clicked node
    for i, value in enumerate(current_path.split("/")):
        if i < len(path_columns):
            column = path_columns[i]
            filtered = filtered[filtered[column].astype(str) == str(value)]
    
    # Get all lipizones under this node
    lipizones = sorted(filtered["lipizone_names"].unique())
    if lipizones:
        return lipizones, f"Selected: {clicked_label} ({len(lipizones)} lipizones)"
    
    return None, "Click on a node in the tree to select all lipizones under it"

@app.callback(
    Output("page-6-all-selected-lipizones", "data"),
    Input("page-6-select-all-lipizones-button", "n_clicks"),
    Input("page-6-add-selection-button", "n_clicks"),
    Input("page-6-clear-selection-button", "n_clicks"),
    State("page-6-current-treemap-selection", "data"),
    State("page-6-all-selected-lipizones", "data"),
    prevent_initial_call=True
)
def handle_selection_changes(
    select_all_clicks,
    add_clicks,
    clear_clicks,
    current_selection,
    all_selected_lipizones,
):
    """Handle all selection changes."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    # Get which button was clicked
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Handle select all button
    if triggered_id == "page-6-select-all-lipizones-button":
        all_lipizones = {"names": [], "indices": []}
        for lipizone_name in lipizone_data.df_hierarchy_lipizones["lipizone_names"].unique():
            lipizone_indices = lipizone_data.df_hierarchy_lipizones.index[
                lipizone_data.df_hierarchy_lipizones["lipizone_names"] == lipizone_name
            ].tolist()
            if lipizone_indices:
                all_lipizones["names"].append(lipizone_name)
                all_lipizones["indices"].extend(lipizone_indices[:1])
        return all_lipizones
    
    # Handle clear button
    elif triggered_id == "page-6-clear-selection-button":
        return {"names": [], "indices": []}
    
    # Handle add button
    elif triggered_id == "page-6-add-selection-button":
        if not current_selection:
            return all_selected_lipizones or {"names": [], "indices": []}
        
        # Initialize all_selected_lipizones if it's empty
        all_selected_lipizones = all_selected_lipizones or {"names": [], "indices": []}
        
        # Add each lipizone that isn't already selected
        for lipizone_name in current_selection:
            if lipizone_name not in all_selected_lipizones["names"]:
                # Find the indices for this lipizone
                lipizone_indices = lipizone_data.df_hierarchy_lipizones.index[
                    lipizone_data.df_hierarchy_lipizones["lipizone_names"] == lipizone_name
                ].tolist()
                
                if lipizone_indices:
                    all_selected_lipizones["names"].append(lipizone_name)
                    all_selected_lipizones["indices"].extend(lipizone_indices[:1])
        
        return all_selected_lipizones
    
    return dash.no_update

@app.callback(
    Output("page-6-graph-hover-text", "children"),
    Input("page-6-graph-heatmap-mz-selection", "hoverData"),
    Input("main-slider", "data"),
)
def page_6_hover(hoverData, slice_index):
    """This callback is used to update the text displayed when hovering over the slice image."""
    acronym_mask = data.acronyms_masks[slice_index]
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            x = hoverData["points"][0]["x"]
            y = hoverData["points"][0]["y"]
            try:
                return atlas.dic_acronym_name[acronym_mask[y, x]]
            except:
                return "Undefined"
    return dash.no_update

@app.callback(
    Output("page-6-graph-hover-text", "style"),
    Input("page-6-sections-mode", "value"),
)
def hide_hover_text(sections_mode):
    """This callback hides the hover text when in all-sections mode."""
    base_style = {
        "width": "auto",
        "position": "absolute",
        "left": "50%",
        "transform": "translateX(-50%)",
        "top": "1em",
        "fontSize": "1.5em",
        "textAlign": "center",
        "zIndex": 1000,
        "backgroundColor": "rgba(0, 0, 0, 0.7)",
        "padding": "0.5em 2em",
        "borderRadius": "8px",
        "minWidth": "200px",
    }
    
    if sections_mode == "all":
        return {**base_style, "display": "none"}
    return {**base_style, "display": "block"}

@app.callback(
    Output("page-6-sections-mode", "disabled"),
    Input("page-6-all-selected-lipizones", "data"),
)
def page_6_active_sections_control(all_selected_lipizones):
    """This callback enables/disables the sections mode control based on lipizone selection."""
    # Enable control if at least one lipizone is selected
    if all_selected_lipizones and len(all_selected_lipizones.get("names", [])) > 0:
        return False
    return True

# @app.callback(
#     Output("page-6-graph-heatmap-mz-selection", "figure"),
#     Input("main-slider", "data"),
#     Input("page-6-all-selected-lipizones", "data"),
#     Input("page-6-sections-mode", "value"),
#     Input("main-brain", "value"),
#     Input("page-6-toggle-annotations", "checked"),
# )
# def page_6_plot_graph_heatmap_mz_selection(
#     slice_index,
#     all_selected_lipizones,
#     sections_mode,
#     brain_id,
#     annotations_checked,
# ):
#     """This callback plots the heatmap of the selected lipid(s)."""
#     logging.info("Entering function to plot heatmap or RGB depending on lipid selection")
#     # Find out which input triggered the function
#     id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    
#     overlay = black_aba_contours(data.get_aba_contours(slice_index)) if annotations_checked else None

#     # Get the names of all selected lipizones
#     selected_lipizone_names = all_selected_lipizones.get("names", [])
    
#     # Define hex_colors_to_highlight using all selected lipizones
#     hex_colors_to_highlight = [lipizone_data.lipizone_to_color[name] for name in selected_lipizone_names if name in lipizone_data.lipizone_to_color]
    
#     # Handle annotations toggle separately to preserve figure state
#     # the annotations can only be displayed if one section is selected
#     if id_input == "page-6-toggle-annotations":
#         # Check if we have any selected lipizones
        
#         # Try to get the section data for the current slice and brain
#         try:
#             hybrid_image = figures.one_section_lipizones_image(
#                 slice_index,
#                 hex_colors_to_highlight=hex_colors_to_highlight,
#             )
            
#             return figures.build_lipid_heatmap_from_image(
#                 hybrid_image,
#                 return_base64_string=False,
#                 draw=False,
#                 type_image="RGB",
#                 return_go_image=False,
#                 overlay=overlay,
#             )
#         except KeyError as e:
#             # If section data not found, fall back to the hybrid image
#             logging.warning(f"Section data not found: {e}. Displaying all lipizones.")
#             return figures.build_lipid_heatmap_from_image(
#                 # compute_hybrid_image(hex_colors_to_highlight, brain_id),
#                 figures.one_section_lipizones_image(
#                     slice_index,
#                     hex_colors_to_highlight=None, # all lipizones
#                 ),
#                 return_base64_string=False,
#                 draw=False,
#                 type_image="RGB",
#                 return_go_image=False,
#                 overlay=overlay,
#             )
    
#     # If a lipid selection has been done
#     if (
#         id_input == "page-6-all-selected-lipizones"
#         or id_input == "page-6-sections-mode"
#         or id_input == "main-brain"
#         or id_input == "main-slider"
#     ):
        
#         if sections_mode == "one":
#             # Try to get the section data for the current slice and brain
#             hybrid_image = figures.one_section_lipizones_image(
#                 slice_index=slice_index,
#                 hex_colors_to_highlight=hex_colors_to_highlight,
#             )
            
#             return figures.build_lipid_heatmap_from_image(
#                 hybrid_image,
#                 return_base64_string=False,
#                 draw=False,
#                 type_image="RGB",
#                 return_go_image=False,
#                 overlay=overlay,
#             )

#         # Or if the current plot must be all sections
#         elif sections_mode == "all":
#             image = figures.all_sections_lipizones_image(
#                 hex_colors_to_highlight=hex_colors_to_highlight,
#                 brain_id=brain_id
#             )
#             if brain_id == "ReferenceAtlas" or brain_id == "SecondAtlas":
#                 image = np.pad(image, ((200, 200), (0, 0), (0, 0)), mode='edge')
#             else:
#                 image = np.pad(image, ((800, 800), (0, 0), (0, 0)), mode='edge')
#             return figures.build_lipid_heatmap_from_image(
#                 image,
#                 return_base64_string=False,
#                 draw=False,
#                 type_image="RGB",
#                 return_go_image=False,
#             )
#         else:
#             # it should never happen
#             logging.info("Section mode is neither 'one-section' nor 'all-sections'. Displaying default all lipizones and all sections")
#             return figures.build_lipid_heatmap_from_image(
#                 # compute_hybrid_image(hex_colors_to_highlight, brain_id),
#                 figures.all_sections_lipizones_image(
#                     hex_colors_to_highlight=None, # all lipizones
#                     brain_id=brain_id),
#                 return_base64_string=False,
#                 draw=False,
#                 type_image="RGB",
#                 return_go_image=False,
#                 overlay=overlay,
#             )

#     # If no trigger, the page has just been loaded, so load new figure with default parameters
#     else:
#         return dash.no_update


from dash.long_callback import DiskcacheLongCallbackManager  # ok if not used directly
from app import long_callback_limiter

@app.long_callback(
    Output("page-6-graph-heatmap-mz-selection", "figure"),
    inputs=[
        Input("main-slider", "data"),
        Input("page-6-all-selected-lipizones", "data"),
        Input("page-6-sections-mode", "value"),
        Input("main-brain", "value"),
        Input("page-6-toggle-annotations", "checked"),
    ],
    prevent_initial_call=True,
)
def page_6_plot_graph_heatmap_mz_selection_long(
    slice_index,
    all_selected_lipizones,
    sections_mode,
    brain_id,
    annotations_checked,
):
    with long_callback_limiter:
        logging.info("Entering page_3_plot_heatmap_long (with semaphore)")
        # Selected lipizones → hex colors (None means “show all”)
        selected_names = (all_selected_lipizones or {}).get("names", []) or []
        hex_colors_to_highlight = (
            [lipizone_data.lipizone_to_color[n] for n in selected_names if n in lipizone_data.lipizone_to_color]
            if selected_names else None
        )

        # Annotations only for single-section view
        overlay = (
            black_aba_contours(data.get_aba_contours(slice_index))
            if (annotations_checked and sections_mode == "one") else None
        )

        if sections_mode == "all":
            image = figures.all_sections_lipizones_image(
                hex_colors_to_highlight=hex_colors_to_highlight,
                brain_id=brain_id
            )
            if brain_id in ("ReferenceAtlas", "SecondAtlas"):
                image = np.pad(image, ((200, 200), (0, 0), (0, 0)), mode="edge")
            else:
                image = np.pad(image, ((800, 800), (0, 0), (0, 0)), mode="edge")

            return figures.build_lipid_heatmap_from_image(
                image,
                return_base64_string=False,
                draw=False,
                type_image="RGB",
                return_go_image=False,
            )

        # sections_mode == "one"
        hybrid_image = figures.one_section_lipizones_image(
            slice_index=slice_index,
            hex_colors_to_highlight=hex_colors_to_highlight,
        )
        return figures.build_lipid_heatmap_from_image(
            hybrid_image,
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )

# Add callback to update badges
@app.callback(
    Output("page-6-selected-lipizones-badges", "children"),
    Input("page-6-all-selected-lipizones", "data"),
)
def update_selected_lipizones_badges(all_selected_lipizones):
    """Update the badges showing selected lipizones with their corresponding colors."""
    children = [html.H6("Selected Lipizones", style={"color": "white", "marginBottom": "10px"})]
    
    if all_selected_lipizones and "names" in all_selected_lipizones:
        for name in all_selected_lipizones["names"]:
            # Get the color for this lipizone, default to cyan if not found
            lipizone_color = lipizone_data.lipizone_to_color.get(name, "#00FFFF")

            # Determine if the background color is light or dark
            is_light = is_light_color(lipizone_color)
            text_color = "black" if is_light else "white"
            
            # Create a style that uses the lipizone's color
            badge_style = {
                "margin": "2px",
                "backgroundColor": lipizone_color,
                "color": text_color,  # Use black text for better contrast
                "border": "none",
            }
            
            children.append(
                dmc.Badge(
                    name,
                    variant="filled",
                    size="sm",
                    style=badge_style,
                )
            )
    
    return children

@app.callback(
    Output("page-6-toggle-annotations", "disabled"),
    Input("page-6-sections-mode", "value"),
)
def page_6_toggle_annotations_visibility(sections_mode):
    """This callback enables/disables the annotations toggle based on sections mode."""
    # Only enable annotations toggle when in "one" section mode
    return sections_mode != "one"

@app.callback(
    Output("page-6-hide-store", "data"),
    Input("page-6-sections-mode", "value"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def compute_page6_hide(lipizone_sections_mode, pathname):
    if pathname == "/lipizones-selection":
        return "d-none" if (lipizone_sections_mode == "all") else ""
    return ""

# Use clientside callback for tutorial step updates
app.clientside_callback(
    """
    function(start, next1, next2, next3, next4, next5, next6, next7, next8, next9, finish,
             prev1, prev2, prev3, prev4, prev5, prev6, prev7, prev8, prev9, prev10,
             close1, close2, close3, close4, close5, close6, close7, close8, close9) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered.length) {
            return window.dash_clientside.no_update;
        }
        const trigger_id = ctx.triggered[0].prop_id.split('.')[0];

        // Close (×) always resets to 0
        if (trigger_id.startsWith('lipizone-tutorial-close-')) {
            return 0;
        }

        // Start
        if (trigger_id === 'lipizone-start-tutorial-btn' && start) {
            return 1;
        }

        // Next buttons
        if (trigger_id === 'lipizone-tutorial-next-1' && next1) { return 2; }
        if (trigger_id === 'lipizone-tutorial-next-2' && next2) { return 3; }
        if (trigger_id === 'lipizone-tutorial-next-3' && next3) { return 4; }
        if (trigger_id === 'lipizone-tutorial-next-4' && next4) { return 5; }
        if (trigger_id === 'lipizone-tutorial-next-5' && next5) { return 6; }
        if (trigger_id === 'lipizone-tutorial-next-6' && next6) { return 7; }
        if (trigger_id === 'lipizone-tutorial-next-7' && next7) { return 8; }
        if (trigger_id === 'lipizone-tutorial-next-8' && next8) { return 9; }
        if (trigger_id === 'lipizone-tutorial-next-9' && next9) { return 10; }
        if (trigger_id === 'lipizone-tutorial-finish' && finish) { return 0; }

        // Previous buttons
        if (trigger_id === 'lipizone-tutorial-prev-2' && prev2) { return 1; }
        if (trigger_id === 'lipizone-tutorial-prev-3' && prev3) { return 2; }
        if (trigger_id === 'lipizone-tutorial-prev-4' && prev4) { return 3; }
        if (trigger_id === 'lipizone-tutorial-prev-5' && prev5) { return 4; }
        if (trigger_id === 'lipizone-tutorial-prev-6' && prev6) { return 5; }
        if (trigger_id === 'lipizone-tutorial-prev-7' && prev7) { return 6; }
        if (trigger_id === 'lipizone-tutorial-prev-8' && prev8) { return 7; }
        if (trigger_id === 'lipizone-tutorial-prev-9' && prev9) { return 8; }
        if (trigger_id === 'lipizone-tutorial-prev-10' && prev10) { return 9; }

        return window.dash_clientside.no_update;
    }
    """,
    Output("lipizone-tutorial-step", "data"),

    [Input("lipizone-start-tutorial-btn", "n_clicks"),
     Input("lipizone-tutorial-next-1", "n_clicks"),
     Input("lipizone-tutorial-next-2", "n_clicks"),
     Input("lipizone-tutorial-next-3", "n_clicks"),
     Input("lipizone-tutorial-next-4", "n_clicks"),
     Input("lipizone-tutorial-next-5", "n_clicks"),
     Input("lipizone-tutorial-next-6", "n_clicks"),
     Input("lipizone-tutorial-next-7", "n_clicks"),
     Input("lipizone-tutorial-next-8", "n_clicks"),
     Input("lipizone-tutorial-next-9", "n_clicks"),
     Input("lipizone-tutorial-finish", "n_clicks"),
     Input("lipizone-tutorial-prev-1", "n_clicks"),
     Input("lipizone-tutorial-prev-2", "n_clicks"),
     Input("lipizone-tutorial-prev-3", "n_clicks"),
     Input("lipizone-tutorial-prev-4", "n_clicks"),
     Input("lipizone-tutorial-prev-5", "n_clicks"),
     Input("lipizone-tutorial-prev-6", "n_clicks"),
     Input("lipizone-tutorial-prev-7", "n_clicks"),
     Input("lipizone-tutorial-prev-8", "n_clicks"),
     Input("lipizone-tutorial-prev-9", "n_clicks"),
     Input("lipizone-tutorial-prev-10", "n_clicks"),
     Input("lipizone-tutorial-close-1", "n_clicks"),
     Input("lipizone-tutorial-close-2", "n_clicks"),
     Input("lipizone-tutorial-close-3", "n_clicks"),
     Input("lipizone-tutorial-close-4", "n_clicks"),
     Input("lipizone-tutorial-close-5", "n_clicks"),
     Input("lipizone-tutorial-close-6", "n_clicks"),
     Input("lipizone-tutorial-close-7", "n_clicks"),
     Input("lipizone-tutorial-close-8", "n_clicks"),
     Input("lipizone-tutorial-close-9", "n_clicks"),
     Input("lipizone-tutorial-close-10", "n_clicks"),
     ],
    prevent_initial_call=True,
)

# Use clientside callback for popover visibility
app.clientside_callback(
    """
    function(step) {
        if (step === undefined || step === null) {
            return [false, false, false, false, false, false, false, false, false, false];
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
            step === 9,
            step === 10,
        ];
    }
    """,
    [Output(f"lipizone-tutorial-popover-{i}", "is_open") for i in range(1, 11)],
    Input("lipizone-tutorial-step", "data"),
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
    Output("lipizone-tutorial-completed", "data"),
    Input("lipizone-tutorial-finish", "n_clicks"),
    prevent_initial_call=True,
)

@app.callback(
    Output("page-6-pdf-viewer-container", "children"),
    Output("page-6-pdf-viewer-container", "style"),
    Input("page-6-all-selected-lipizones", "data"),
    Input("page-6-toggle-pdf-view", "n_clicks"),
    State("page-6-pdf-viewer-container", "style"),
)
def update_pdf_viewer(all_selected_lipizones, n_clicks, current_style):
    """Update the PDF viewer based on the selected lipizones and toggle button."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Handle toggle button click
    if triggered_id == "page-6-toggle-pdf-view":
        if current_style["display"] == "none":
            current_style["display"] = "block"
        else:
            current_style["display"] = "none"
        return dash.no_update, current_style
    
    # Handle lipizone selection
    if not all_selected_lipizones or not all_selected_lipizones.get("names") or len(all_selected_lipizones["names"]) == 0:
        return html.Div(
            "Select lipizones to view their ID cards", 
            style={
                "color": "white", 
                "textAlign": "center", 
                "marginTop": "20%"
            }
        ), current_style
    
    # Get all selected lipizones and clean their names
    safe_lipizone_names = [clean_filenamePD(name) for name in all_selected_lipizones["names"]]
    
    # Check if any PDFs exist
    pdf_exists = False
    for filename in safe_lipizone_names:
        pdf_path = os.path.join(ID_CARDS_PATH, f"lipizone_ID_card_{filename}.pdf")
        if os.path.exists(pdf_path):
            pdf_exists = True
            break
    
    if not pdf_exists:
        return html.Div(
            "No ID cards found for the selected lipizones. Please ensure the ID cards are available in the data directory.", 
            style={
                "color": "white", 
                "textAlign": "center", 
                "marginTop": "20%",
                "padding": "20px"
            }
        ), current_style
    
    # Join the filenames with commas for the URL
    filenames_param = ','.join(safe_lipizone_names)
    
    # Create iframe with PDF viewer
    return html.Iframe(
        src=f"/merged-id-cards-pdf/{filenames_param}?toolbar=1&navpanes=1&scrollbar=1&statusbar=1",
        style={
            "width": "100%",
            "height": "100%",
            "border": "none",
            "backgroundColor": "#1d1c1f",
        }
    ), current_style

# Add route for serving merged PDFs
@app.server.route('/merged-id-cards-pdf/<path:filenames>')
def serve_merged_pdf(filenames):
    try:
        # Check if ID cards directory exists
        if not os.path.exists(ID_CARDS_PATH):
            logging.error(f"ID cards directory not found at {ID_CARDS_PATH}")
            return "ID cards directory not found. Please ensure the data directory is properly set up.", 404

        # Split filenames and construct full paths
        pdf_paths = []
        # split the filenames by comma, but not by comma+space
        split_filenames = re.split(r',(?! )', filenames)
        for filename in split_filenames:
            pdf_path = os.path.join(ID_CARDS_PATH, f"lipizone_ID_card_{filename}.pdf")
            if os.path.exists(pdf_path):
                pdf_paths.append(pdf_path)
            else:
                logging.warning(f"PDF file not found: {pdf_path}")
        
        if not pdf_paths:
            return "No PDFs found for the selected lipizones. Please ensure the ID cards are available in the data directory.", 404
        
        # If only one PDF, serve it directly
        if len(pdf_paths) == 1:
            return send_file(pdf_paths[0])
        
        # Merge PDFs
        merger = PyPDF2.PdfMerger()
        for pdf_path in pdf_paths:
            try:
                merger.append(pdf_path)
            except Exception as e:
                logging.error(f"Error appending PDF {pdf_path}: {e}")
                continue
        
        if len(merger.pages) == 0:
            return "No valid PDFs could be merged. Please check the PDF files in the data directory.", 404
        
        # Write to BytesIO
        output = io.BytesIO()
        merger.write(output)
        merger.close()
        
        # Prepare for sending
        output.seek(0)
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=False,
            download_name='merged_id_cards.pdf'
        )
    except Exception as e:
        logging.error(f"Error serving merged PDF: {e}")
        return f"Error serving PDFs: {str(e)}. Please check the server logs for more details.", 500

# Callback to toggle the OffCanvas panel
@app.callback(
    Output("id-cards-panel", "is_open"),
    [Input("view-id-cards-btn", "n_clicks"), Input("close-id-cards-panel", "n_clicks")],
    [State("id-cards-panel", "is_open")],
)
def toggle_id_cards_panel(open_click, close_click, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "view-id-cards-btn" or button_id == "close-id-cards-panel":
        return not is_open
    return is_open

# Callback to update the PDF viewer
@app.callback(
    Output("pdf-viewer-container", "children"),
    Input("page-6-all-selected-lipizones", "data"),
)
def update_pdf_viewer(all_selected_lipizones):
    if not all_selected_lipizones or not all_selected_lipizones.get("names") or len(all_selected_lipizones["names"]) == 0:
        return html.Div(
            "Select lipizones to view their ID cards",
            style={
                "color": "white",
                "fontSize": "1.2rem",
                "textAlign": "center",
            }
        )
    cleaned_filenames = [clean_filenamePD(name) for name in all_selected_lipizones["names"]]
    filenames_str = ",".join(cleaned_filenames)
    return html.Iframe(
        src=f"/merged-id-cards-pdf/{filenames_str}",
        style={
            "width": "100%",
            "height": "100%",
            "border": "none",
        }
    )