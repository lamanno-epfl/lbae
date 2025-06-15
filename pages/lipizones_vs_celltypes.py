# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""This file contains the page used to select and visualize lipids according to pre-existing
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
from tqdm import tqdm
from scipy.ndimage import gaussian_filter

# threadpoolctl import threadpool_limits, threadpool_info
# threadpool_limits(limits=8)
import os

os.environ["OMP_NUM_THREADS"] = "6"
import pickle
import plotly.express as px

# LBAE imports
from app import app, figures, data, atlas, lipizone_data, celltype_data

# ==================================================================================================
# --- Helper functions
# ==================================================================================================

from modules.figures import is_light_color, black_aba_contours

# ==================================================================================================
# --- Layout
# ==================================================================================================


def return_layout(basic_config, slice_index):
    """Return the layout for the page."""
    # Create treemap data
    df_treemap_lipizones, node_colors_lipizones = (
        lipizone_data.create_treemap_data_lipizones()
    )
    df_treemap_celltypes, node_colors_celltypes = (
        celltype_data.create_treemap_data_celltypes(slice_index=slice_index)
    )

    # Get celltype pixel counts for the current slice
    section_data_celltypes = celltype_data.retrieve_section_data(int(slice_index))
    color_masks_celltypes = section_data_celltypes["color_masks"]
    celltype_pixel_counts = {
        celltype: np.sum(mask) for celltype, mask in color_masks_celltypes.items()
    }
    max_pixels = max(celltype_pixel_counts.values()) if celltype_pixel_counts else 1

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
            # Add the warning alert at the top of the page
            dmc.Alert(
                title="Important Notice",
                color="red",
                children=html.Div([
                    "Please refresh this page when coming from a different one.",
                    html.Br(),
                    "This ensures the slider properly responds to user interactions."
                ], style={"textAlign": "left"}),
                id="page-6bis-refresh-alert",
                withCloseButton=True,
                style={
                    "position": "fixed",
                    "top": "15%",
                    "left": "50%",
                    "transform": "translate(-50%, -50%)",
                    "width": "500px",
                    "backgroundColor": "#2d1d1d",
                    "color": "#ffd6d6",
                    "borderLeft": "5px solid #ff4d4f",
                    "zIndex": 2000,
                    "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)",
                    "borderRadius": "8px",
                    "textAlign": "center",
                },
            ),
            dcc.Store(id="lipicell-tutorial-step", data=0),
            dcc.Store(
                id="lipicell-tutorial-completed", storage_type="local", data=False
            ),
            # Add tutorial button under welcome text
            html.Div(
                id="lipicell-start-tutorial-target",
                style={
                    "position": "fixed",
                    "top": "0.9em",
                    "left": "21.3em",
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
                        id="lipicell-start-tutorial-btn",
                        color="info",
                        size="sm",
                        className="tutorial-start-btn",
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
            html.Div(
                className="fixed-aspect-ratio",
                style={"background-color": "#1d1c1f"},
                children=[
                    # Main visualization
                    dcc.Graph(
                        id="page-6bis-graph-heatmap-mz-selection",
                        config=basic_config
                        | {
                            "toImageButtonOptions": {
                                "format": "png",
                                "filename": "brain_lipizone_selection",
                                "scale": 2,
                            },
                            "scrollZoom": True,
                        },
                        style={
                            "width": "60%",  # Reduced from 80% to give more balanced space
                            "height": "95%",
                            "position": "absolute",
                            "left": "20%",  # Center it between the two side panels
                            "top": "0",
                            "background-color": "#1d1c1f",
                        },
                        figure=figures.build_lipid_heatmap_from_image(
                            figures.compute_image_lipizones_celltypes(
                                {
                                    "names": list(
                                        lipizone_data.lipizone_to_color.keys()
                                    ),
                                    "indices": [],
                                },
                                {
                                    "names": list(
                                        celltype_data.celltype_to_color.keys()
                                    ),
                                    "indices": [],
                                },
                                slice_index,
                            ),
                            return_base64_string=False,
                            draw=False,
                            type_image="RGB",
                            return_go_image=False,
                        ),
                    ),
                    # Allen Brain Atlas switch (independent)
                    html.Div(
                        style={
                            "position": "absolute",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "top": "0.5em",
                            "z-index": 1000,
                            "display": "flex",
                            "flexDirection": "row",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "padding": "0.5em 2em",
                        },
                        children=[
                            dmc.Switch(
                                id="page-6bis-toggle-annotations",
                                checked=False,
                                color="cyan",
                                radius="xl",
                                size="sm",
                            ),
                            html.Span(
                                "Allen Brain Atlas Annotations",
                                style={
                                    "color": "white",
                                    "marginLeft": "10px",  # Changed from marginRight to marginLeft
                                    "whiteSpace": "nowrap",
                                },
                            ),
                        ],
                    ),
                    # Hover text
                    dmc.Text(
                        "",
                        id="page-6bis-graph-hover-text",
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
                        },
                    ),
                    # Left panel with lipizones treemap and controls
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
                        },
                    ),
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
                                id="page-6bis-select-all-lipizones-button",
                                variant="filled",
                                color="cyan",
                                radius="md",
                                size="sm",
                                style={
                                    "marginBottom": "5px",
                                },
                            ),
                            # Lipizones treemap visualization
                            html.Div(
                                id="lipizone-treemap-container",  # Add this ID
                                style={
                                    "height": "40%",
                                    "background-color": "#1d1c1f",
                                },
                                children=[
                                    dcc.Graph(
                                        id="page-6bis-lipizones-treemap",
                                        figure=lipizone_data.create_treemap_figure_lipizones(
                                            df_treemap_lipizones, node_colors_lipizones
                                        ),
                                        style={
                                            "height": "100%",
                                            "background-color": "#1d1c1f",
                                        },
                                        config={"displayModeBar": False},
                                    ),
                                ],
                            ),
                            # Current selection text
                            html.Div(
                                id="page-6bis-current-lipizone-selection-text",
                                style={
                                    "padding": "10px",
                                    "color": "white",
                                    "fontSize": "0.9em",
                                    "backgroundColor": "#2c2c2c",
                                    "borderRadius": "5px",
                                    "marginTop": "10px",
                                },
                                children=[
                                    "Click on a node in the tree to select all lipizones under it"
                                ],
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
                                        id="page-6bis-add-lipizone-selection-button",
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
                                        id="page-6bis-clear-lipizone-selection-button",
                                        variant="outline",
                                        color="red",
                                        radius="md",
                                        size="sm",
                                        style={
                                            "flex": "1",
                                            "maxWidth": "50%",  # Ensure button doesn't exceed half the container
                                        },
                                    ),
                                ],
                            ),
                            # Selected lipizones badges
                            html.Div(
                                id="selected-lipizones-badges",
                                style={
                                    "height": "30%",
                                    "overflowY": "auto",
                                    "padding": "10px",
                                    "marginTop": "10px",
                                    "backgroundColor": "#2c2c2c",
                                    "borderRadius": "5px",
                                },
                                children=[
                                    html.H6(
                                        "Selected Lipizones",
                                        style={
                                            "color": "white",
                                            "marginBottom": "10px",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Right panel with celltypes treemap and controls
                    # Title
                    html.H4(
                        "Visualize Cell Types",
                        style={
                            "color": "white",
                            "marginBottom": "15px",
                            "fontSize": "1.2em",
                            "fontWeight": "500",
                            "position": "absolute",
                            "right": "1%",
                            "top": "1em",
                        },
                    ),
                    html.Div(
                        style={
                            "width": "20%",
                            "height": "95%",
                            "position": "absolute",
                            "right": "0",
                            "top": "3em",
                            "background-color": "#1d1c1f",
                            "display": "flex",
                            "flexDirection": "column",
                            "padding": "10px",
                        },
                        children=[
                            # Select All button
                            dmc.Button(
                                children="Select All Cell Types",
                                id="page-6bis-select-all-celltypes-button",
                                variant="filled",
                                color="cyan",
                                radius="md",
                                size="sm",
                                style={
                                    "marginBottom": "5px",
                                },
                            ),
                            # Celltypes treemap visualization
                            html.Div(
                                id="celltype-treemap-container",  # Add this ID
                                style={
                                    "height": "40%",
                                    "background-color": "#1d1c1f",
                                },
                                children=[
                                    dcc.Graph(
                                        id="page-6bis-celltypes-treemap",
                                        figure=celltype_data.create_treemap_figure_celltypes(
                                            df_treemap_celltypes, node_colors_celltypes
                                        ),
                                        style={
                                            "height": "100%",
                                            "background-color": "#1d1c1f",
                                        },
                                        config={"displayModeBar": False},
                                    ),
                                ],
                            ),
                            # Current selection text
                            html.Div(
                                id="page-6bis-current-celltype-selection-text",
                                style={
                                    "padding": "10px",
                                    "color": "white",
                                    "fontSize": "0.9em",
                                    "backgroundColor": "#2c2c2c",
                                    "borderRadius": "5px",
                                    "marginTop": "10px",
                                },
                                children=[
                                    "Click on a node in the tree to select all cell types under it"
                                ],
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
                                        id="page-6bis-add-celltype-selection-button",
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
                                        id="page-6bis-clear-celltype-selection-button",
                                        variant="outline",
                                        color="red",
                                        radius="md",
                                        size="sm",
                                        style={
                                            "flex": "1",
                                            "maxWidth": "50%",  # Ensure button doesn't exceed half the container
                                        },
                                    ),
                                ],
                            ),
                            # Selected celltypes badges
                            html.Div(
                                id="selected-celltypes-badges",
                                style={
                                    "height": "30%",
                                    "overflowY": "auto",
                                    "padding": "10px",
                                    "marginTop": "10px",
                                    "backgroundColor": "#2c2c2c",
                                    "borderRadius": "5px",
                                },
                                children=[
                                    html.H6(
                                        "Selected Cell Types",
                                        style={
                                            "color": "white",
                                            "marginBottom": "10px",
                                        },
                                    ),
                                ],
                            ),
                            # Add pixel count filter slider
                            html.Div(
                                [
                                    html.Label(
                                        "Filter by minimum pixel count:",
                                        style={
                                            "color": "white",
                                            "marginTop": "10px",  # Reduced from 20px
                                            "marginBottom": "5px",  # Reduced from 10px
                                        },
                                    ),
                                    dcc.Slider(
                                        id="page-6bis-celltype-pixel-filter",
                                        min=0,
                                        max=max_pixels,
                                        step=int(max_pixels / 100),  # 100 steps
                                        value=0,
                                        marks={
                                            "0": {
                                                "label": "0",
                                                "style": {"color": "white"},
                                            },
                                            str(max_pixels): {
                                                "label": str(max_pixels),
                                                "style": {"color": "white"},
                                            },
                                        },
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": True,
                                        },
                                        className="slider-white",
                                    ),
                                ],
                                style={"padding": "5px"},
                            ),  # Reduced from 10px
                        ],
                    ),
                    # # Controls at the bottom right
                    # html.Div(
                    #     style={
                    #         "right": "1rem",
                    #         "bottom": "1rem",
                    #         "position": "fixed",
                    #         "z-index": 1000,
                    #         "display": "flex",
                    #         "flexDirection": "row",  # Changed from column to row
                    #         "gap": "0.5rem",
                    #     },
                    #     children=[
                    #         dmc.Button(
                    #             children="Download data",
                    #             id="page-6bis-download-data-button",
                    #             variant="filled",
                    #             disabled=False,
                    #             color="cyan",
                    #             radius="md",
                    #             size="sm",
                    #             style={"width": "150px"},
                    #         ),
                    #         dmc.Button(
                    #             children="Download image",
                    #             id="page-6bis-download-image-button",
                    #             variant="filled",
                    #             disabled=False,
                    #             color="cyan",
                    #             radius="md",
                    #             size="sm",
                    #             style={"width": "150px"},
                    #         ),
                    #     ],
                    # ),
                    # dcc.Download(id="page-6bis-download-data"),
                    # Tutorial Popovers with adjusted positions
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Lipizones vs Cell Types",
                                    dbc.Button(
                                        "×",
                                        id="lipicell-tutorial-close-1",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"},
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "Welcome to the Lipizones vs Cell Types page! This view allows you to compare the spatial distribution of lipizones with mapped brain cell types. By exploring both layers together, you can identify shared spatial patterns and assess how well lipid-based territories align with cellular architecture. This comparison is valuable for uncovering underlying biological structure, functional organization, and potential relationships between lipizones and cell-type diversity.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-1",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                                disabled=True,
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-1",
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
                        id="lipicell-tutorial-popover-1",
                        target="lipicell-start-tutorial-target",
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
                        },
                    ),
                    # --- All Lipizones Button ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Display All Lipizones",
                                    dbc.Button(
                                        "×",
                                        id="lipicell-tutorial-close-2",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"},
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "This button displays all lipizones in the current slice by default. If you want to focus on specific lipizones, remember to first clear the current selection using the appropriate button.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-2",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-2",
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
                        id="lipicell-tutorial-popover-2",
                        target="page-6bis-select-all-lipizones-button",
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
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
                                        id="lipicell-tutorial-close-3",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"},
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "Use the treemap to explore and select lipizones from a hierarchical structure. Lipizones are defined as 539 spatial clusters computed through an iterative bipartite splitter. You can navigate the hierarchy freely and stop at any level of detail. Once you're satisfied with the selection, you can add those lipizones for visualization.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-3",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-3",
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
                        id="lipicell-tutorial-popover-3",
                        target="lipizone-treemap-container",  # dropdown menu
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
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
                                        id="lipicell-tutorial-close-4",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"},
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "After selecting the desired lipizones from the treemap, click this button to add them to the current view. The display will update accordingly to show your selection.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-4",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-4",
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
                        id="lipicell-tutorial-popover-4",
                        target="page-6bis-add-lipizone-selection-button",  # dropdown menu
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
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
                                        id="lipicell-tutorial-close-5",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"},
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "Use this button to remove all currently selected lipizones and return to an empty brain view. This is helpful if you want to start over or explore a new subset.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-5",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-5",
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
                        id="lipicell-tutorial-popover-5",
                        target="page-6bis-clear-lipizone-selection-button",  # dropdown menu
                        placement="right",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
                        },
                    ),
                    # --- Cell Types Selection ---
                    # --- All Cell Types Button ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Display All Cell Types",
                                    dbc.Button(
                                        "×",
                                        id="lipicell-tutorial-close-6",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"},
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "This button displays all available cell types in the current brain slice. It's the default view when you open the page. If you want to focus on specific cell types, make sure to clear the selection first before adding a subset.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-6",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-6",
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
                        id="lipicell-tutorial-popover-6",
                        target="page-6bis-select-all-celltypes-button",
                        placement="left",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
                        },
                    ),
                    # --- Cell Types Selection ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Navigate Cell Types Hierarchy",
                                    dbc.Button(
                                        "×",
                                        id="lipicell-tutorial-close-7",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"},
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "Use the treemap to explore and select from the set of mapped cell types. The cell type data originates from the work of the Macosko group at the Broad Institute, who identified and characterized a wide range of cell types in the mouse brain, including newly described populations with regional specializations. While the hierarchy may be less intuitive to navigate compared to the lipizones, it reflects the richness and complexity of the dataset. For further clarity and naming details, we encourage users to consult their original publications and accompanying data resources.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-7",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-7",
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
                        id="lipicell-tutorial-popover-7",
                        target="celltype-treemap-container",
                        placement="left",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
                        },
                    ),
                    # --- Add Selection Button ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Visualize Selected Cell Types",
                                    dbc.Button(
                                        "×",
                                        id="lipicell-tutorial-close-8",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"},
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "After choosing your cell types from the treemap, click this button to add them to the view. The selected cell types will be displayed alongside the lipizones, enabling visual comparison in the current slice.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-8",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-8",
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
                        id="lipicell-tutorial-popover-8",
                        target="page-6bis-add-celltype-selection-button",  # dropdown menu
                        placement="left",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
                        },
                    ),
                    # --- Clear Selection Button ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Reset Cell Type View",
                                    dbc.Button(
                                        "×",
                                        id="lipicell-tutorial-close-9",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"},
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "Click here to remove all currently selected cell types and return to an empty view. This allows you to reset your selection and choose new ones as needed.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-9",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-9",
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
                        id="lipicell-tutorial-popover-9",
                        target="page-6bis-clear-celltype-selection-button",  # dropdown menu
                        placement="left",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
                        },
                    ),
                    # --- Filter by Pixel Count ---
                    dbc.Popover(
                        [
                            dbc.PopoverHeader(
                                [
                                    "Filter Sparse Cell Types",
                                    dbc.Button(
                                        "×",
                                        id="lipicell-tutorial-close-10",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ],
                                style={"fontWeight": "bold"},
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "Use this slider to filter out cell types with low pixel counts in the current slice. This helps improve interpretability, as spatial correlation between lipizones and cell types is meaningful only when cell type presence is sufficiently dense in the region being examined.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-10",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-10",
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
                        id="lipicell-tutorial-popover-10",
                        target="page-6bis-celltype-pixel-filter",  # dropdown menu
                        placement="left",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
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
                                        id="lipicell-tutorial-close-11",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ], style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "You can enable the Allen Brain Atlas annotations to overlay anatomical labels directly on the slices. This helps you navigate the brain and interpret lipid signals in their biological context.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-11",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Next",
                                                id="lipicell-tutorial-next-11",
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
                        id="lipicell-tutorial-popover-11",
                        target="page-6bis-toggle-annotations",  # annotations switch
                        placement="bottom",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
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
                                        id="lipicell-tutorial-close-12",
                                        color="link",
                                        className="float-end",
                                        style={"color": "#666", "fontSize": "1.2rem", "padding": "0 0.5rem"},
                                    ),
                                ], style={"fontWeight": "bold"}
                            ),
                            dbc.PopoverBody(
                                [
                                    html.P(
                                        "In the single-section view, you can navigate through the brain by selecting different slices along the rostro-caudal (front-to-back) axis. This allows detailed inspection of lipid signals at specific anatomical levels.",
                                        style={"color": "#333", "marginBottom": "15px"},
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Previous",
                                                id="lipicell-tutorial-prev-12",
                                                color="secondary",
                                                size="sm",
                                                className="float-start",
                                            ),
                                            dbc.Button(
                                                "Finish",
                                                id="lipicell-tutorial-finish",
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
                        id="lipicell-tutorial-popover-12",
                        target="main-paper-slider",  # slider
                        placement="top",
                        is_open=False,
                        style={
                            "zIndex": 9999,
                            "border": "2px solid #1fafc8",
                            "boxShadow": "0 0 15px 2px #1fafc8",
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
    Output("page-6bis-celltypes-treemap", "figure"),
    Input("main-slider", "data"),
    prevent_initial_call=True,
)
def update_celltype_treemap(slice_index):
    """Update the celltype treemap when the slice changes."""
    # Create new treemap data for celltypes with the current slice
    df_treemap_celltypes, node_colors_celltypes = (
        celltype_data.create_treemap_data_celltypes(slice_index=slice_index)
    )
    # Create and return the new figure
    return celltype_data.create_treemap_figure_celltypes(
        df_treemap_celltypes, node_colors_celltypes
    )


@app.callback(
    Output("page-6bis-current-lipizone-treemap-selection", "data"),
    Output("page-6bis-current-lipizone-selection-text", "children"),
    Input("page-6bis-lipizones-treemap", "clickData"),
    prevent_initial_call=True,
)
def update_current_lipizone_selection(click_data):
    """Store the current treemap selection for lipizones."""
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    if not click_data:
        return None, "Click on a node in the tree to select all lipizones under it"

    clicked_label = click_data["points"][0]["label"]
    current_path = click_data["points"][0]["id"]

    # Filter hierarchy based on the clicked node's path
    filtered = lipizone_data.df_hierarchy_lipizones.copy()

    # Get the level of the clicked node
    path_columns = [
        "level_1_name",
        "level_2_name",
        "level_3_name",
        "level_4_name",
        "subclass_name",
        "lipizone_names",
    ]

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
    Output("page-6bis-current-celltype-treemap-selection", "data"),
    Output("page-6bis-current-celltype-selection-text", "children"),
    Input("page-6bis-celltypes-treemap", "clickData"),
    Input("main-slider", "data"),
    prevent_initial_call=True,
)
def update_current_celltype_selection(click_data, slice_index):
    """Store the current treemap selection for celltypes."""
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    if not click_data:
        return None, "Click on a node in the tree to select all cell types under it"

    clicked_label = click_data["points"][0]["label"]
    current_path = click_data["points"][0]["id"]

    celltype_in_section = list(
        celltype_data.retrieve_section_data(int(slice_index))["color_masks"].keys()
    )
    # Filter the DataFrame
    filtered = celltype_data.df_hierarchy_celltypes[
        celltype_data.df_hierarchy_celltypes["cell_type"].isin(celltype_in_section)
    ]

    # Get the level of the clicked node
    path_columns = [
        "level_1",
        "level_2",
        "level_3",
        "level_4",
        "level_5",
        "level_6",
        "level_7",
        "level_8",
        "level_9",
        "level_10",
        "cell_type",
    ]

    # Apply filters based on the entire path up to the clicked node
    for i, value in enumerate(current_path.split("/")):
        if i < len(path_columns):
            column = path_columns[i]
            filtered = filtered[filtered[column].astype(str) == str(value)]

    # Get all cell types under this node that are present in the current slice
    celltypes = sorted(filtered["cell_type"].unique())

    if celltypes:
        return celltypes, f"Selected: {clicked_label} ({len(celltypes)} cell types)"

    return None, "Click on a node in the tree to select all cell types under it"


@app.callback(
    Output("page-6bis-all-selected-lipizones", "data"),
    Input("page-6bis-select-all-lipizones-button", "n_clicks"),
    Input("page-6bis-add-lipizone-selection-button", "n_clicks"),
    Input("page-6bis-clear-lipizone-selection-button", "n_clicks"),
    State("page-6bis-current-lipizone-treemap-selection", "data"),
    State("page-6bis-all-selected-lipizones", "data"),
    prevent_initial_call=True,
)
def handle_lipizone_selection_changes(
    select_all_clicks,
    add_clicks,
    clear_clicks,
    current_selection,
    all_selected_lipizones,
):
    """Handle all lipizone selection changes."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    # Get which button was clicked
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Handle select all button
    if triggered_id == "page-6bis-select-all-lipizones-button":
        all_lipizones = {"names": [], "indices": []}
        for lipizone_name in lipizone_data.df_hierarchy_lipizones[
            "lipizone_names"
        ].unique():
            lipizone_indices = lipizone_data.df_hierarchy_lipizones.index[
                lipizone_data.df_hierarchy_lipizones["lipizone_names"] == lipizone_name
            ].tolist()
            if lipizone_indices:
                all_lipizones["names"].append(lipizone_name)
                all_lipizones["indices"].extend(lipizone_indices[:1])
        return all_lipizones

    # Handle clear button
    elif triggered_id == "page-6bis-clear-lipizone-selection-button":
        return {"names": [], "indices": []}

    # Handle add button
    elif triggered_id == "page-6bis-add-lipizone-selection-button":
        if not current_selection:
            return all_selected_lipizones or {"names": [], "indices": []}

        # Initialize all_selected_lipizones if it's empty
        all_selected_lipizones = all_selected_lipizones or {"names": [], "indices": []}

        # Add each lipizone that isn't already selected
        for lipizone_name in current_selection:
            if lipizone_name not in all_selected_lipizones["names"]:
                # Find the indices for this lipizone
                lipizone_indices = lipizone_data.df_hierarchy_lipizones.index[
                    lipizone_data.df_hierarchy_lipizones["lipizone_names"]
                    == lipizone_name
                ].tolist()

                if lipizone_indices:
                    all_selected_lipizones["names"].append(lipizone_name)
                    all_selected_lipizones["indices"].extend(lipizone_indices[:1])

        return all_selected_lipizones

    return dash.no_update


@app.callback(
    Output("page-6bis-all-selected-celltypes", "data"),
    Output("page-6bis-celltype-pixel-filter", "max"),
    Output("page-6bis-celltype-pixel-filter", "step"),
    Output("page-6bis-celltype-pixel-filter", "marks"),
    Output("page-6bis-celltype-pixel-filter", "value"),
    Input("page-6bis-select-all-celltypes-button", "n_clicks"),
    Input("page-6bis-add-celltype-selection-button", "n_clicks"),
    Input("page-6bis-clear-celltype-selection-button", "n_clicks"),
    Input("main-slider", "data"),
    Input("page-6bis-celltype-pixel-filter", "value"),
    State("page-6bis-current-celltype-treemap-selection", "data"),
    State("page-6bis-all-selected-celltypes", "data"),
    prevent_initial_call=True,
)
def handle_celltype_selection_changes(
    select_all_clicks,
    add_clicks,
    clear_clicks,
    slice_index,
    min_pixels,
    current_selection,
    all_selected_celltypes,
):
    """Handle all celltype selection changes."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    # Get which input triggered the callback
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Get the available celltypes and their masks in the current slice
    section_data = celltype_data.retrieve_section_data(int(slice_index))
    color_masks = section_data["color_masks"]

    # Calculate pixel counts for each celltype
    celltype_pixel_counts = {
        celltype: np.sum(mask) for celltype, mask in color_masks.items()
    }

    # Calculate max pixels for this slice
    max_pixels = max(celltype_pixel_counts.values()) if celltype_pixel_counts else 1
    step = max(1, int(max_pixels / 100))  # 100 steps
    marks = {
        "0": {"label": "0", "style": {"color": "white"}},
        str(max_pixels): {"label": str(max_pixels), "style": {"color": "white"}},
    }

    # Filter celltypes based on pixel count
    available_celltypes = [
        celltype
        for celltype, count in celltype_pixel_counts.items()
        if count >= min_pixels
    ]

    # If slice changed, reset slider to 0 and show all celltypes
    if triggered_id == "main-slider":
        # Filter the DataFrame
        filtered_df = celltype_data.df_hierarchy_celltypes[
            celltype_data.df_hierarchy_celltypes["cell_type"].isin(available_celltypes)
        ]

        # Create the all_celltypes dictionary with only celltypes from the current slice
        all_celltypes = {"names": [], "indices": []}
        for celltype_name in filtered_df["cell_type"].unique():
            celltype_indices = celltype_data.df_hierarchy_celltypes.index[
                celltype_data.df_hierarchy_celltypes["cell_type"] == celltype_name
            ].tolist()
            if celltype_indices:
                all_celltypes["names"].append(celltype_name)
                all_celltypes["indices"].extend(celltype_indices[:1])
        return all_celltypes, max_pixels, step, marks, 0

    # If slider value changed, filter current selection
    elif triggered_id == "page-6bis-celltype-pixel-filter":
        # Filter the DataFrame
        filtered_df = celltype_data.df_hierarchy_celltypes[
            celltype_data.df_hierarchy_celltypes["cell_type"].isin(available_celltypes)
        ]

        # Create the all_celltypes dictionary with only celltypes that meet the pixel threshold
        all_celltypes = {"names": [], "indices": []}
        for celltype_name in filtered_df["cell_type"].unique():
            celltype_indices = celltype_data.df_hierarchy_celltypes.index[
                celltype_data.df_hierarchy_celltypes["cell_type"] == celltype_name
            ].tolist()
            if celltype_indices:
                all_celltypes["names"].append(celltype_name)
                all_celltypes["indices"].extend(celltype_indices[:1])
        return all_celltypes, max_pixels, step, marks, min_pixels

    # Handle select all button
    elif triggered_id == "page-6bis-select-all-celltypes-button":
        # Filter the DataFrame
        filtered_df = celltype_data.df_hierarchy_celltypes[
            celltype_data.df_hierarchy_celltypes["cell_type"].isin(available_celltypes)
        ]

        # Create the all_celltypes dictionary with only celltypes that meet the pixel threshold
        all_celltypes = {"names": [], "indices": []}
        for celltype_name in filtered_df["cell_type"].unique():
            celltype_indices = celltype_data.df_hierarchy_celltypes.index[
                celltype_data.df_hierarchy_celltypes["cell_type"] == celltype_name
            ].tolist()
            if celltype_indices:
                all_celltypes["names"].append(celltype_name)
                all_celltypes["indices"].extend(celltype_indices[:1])
        return all_celltypes, max_pixels, step, marks, min_pixels

    # Handle clear button
    elif triggered_id == "page-6bis-clear-celltype-selection-button":
        return {"names": [], "indices": []}, max_pixels, step, marks, min_pixels

    # Handle add button
    elif triggered_id == "page-6bis-add-celltype-selection-button":
        if not current_selection:
            return (
                all_selected_celltypes or {"names": [], "indices": []},
                max_pixels,
                step,
                marks,
                min_pixels,
            )

        # Initialize all_selected_celltypes if it's empty
        all_selected_celltypes = all_selected_celltypes or {"names": [], "indices": []}

        # Add each celltype that isn't already selected and meets the pixel threshold
        for celltype_name in current_selection:
            if (
                celltype_name not in all_selected_celltypes["names"]
                and celltype_name in available_celltypes
            ):
                # Find the indices for this celltype
                celltype_indices = celltype_data.df_hierarchy_celltypes.index[
                    celltype_data.df_hierarchy_celltypes["cell_type"] == celltype_name
                ].tolist()

                if celltype_indices:
                    all_selected_celltypes["names"].append(celltype_name)
                    all_selected_celltypes["indices"].extend(celltype_indices[:1])

        return all_selected_celltypes, max_pixels, step, marks, min_pixels

    return (
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )


@app.callback(
    Output("page-6bis-graph-hover-text", "children"),
    Input("page-6bis-graph-heatmap-mz-selection", "hoverData"),
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
    Output("page-6bis-graph-heatmap-mz-selection", "figure"),
    Input("main-slider", "data"),
    Input("page-6bis-all-selected-lipizones", "data"),
    Input("page-6bis-all-selected-celltypes", "data"),
    Input("page-6bis-toggle-annotations", "checked"),
    prevent_initial_call=True,
)
def page_6_plot_graph_heatmap_mz_selection(
    slice_index,
    all_selected_lipizones,
    all_selected_celltypes,
    annotations_checked,
):
    """This callback plots the heatmap of the selected lipid(s)."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    # Get which input triggered the callback
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    input_id = ctx.triggered[0]["prop_id"].split(".")[1]

    # Handle annotations overlay
    overlay = (
        black_aba_contours(data.get_aba_contours(slice_index))
        if annotations_checked
        else None
    )

    # If annotations toggle was triggered, preserve current selections
    if triggered_id == "page-6bis-toggle-annotations":
        lipizones_celltypes_image = figures.compute_image_lipizones_celltypes(
            all_selected_lipizones, all_selected_celltypes, slice_index
        )

        fig = figures.build_lipid_heatmap_from_image(
            lipizones_celltypes_image,
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )

        return fig

    # Handle other triggers (slider, selections, brain change)
    if (
        all_selected_lipizones and len(all_selected_lipizones.get("names", [])) > 0
    ) or (all_selected_celltypes and len(all_selected_celltypes.get("names", [])) > 0):
        lipizones_celltypes_image = figures.compute_image_lipizones_celltypes(
            all_selected_lipizones, all_selected_celltypes, slice_index
        )

        fig = figures.build_lipid_heatmap_from_image(
            lipizones_celltypes_image,
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )

        return fig

    else:
        # No selections, use default color for choroid plexus
        hex_colors_to_highlight = ["#f75400"]
        fig = figures.build_lipid_heatmap_from_image(
            figures.compute_image_lipizones_celltypes(
                {"names": list(lipizone_data.lipizone_to_color.keys()), "indices": []},
                {"names": list(celltype_data.celltype_to_color.keys()), "indices": []},
                slice_index,
            ),
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )

        return fig


# Add callback to update badges
@app.callback(
    Output("selected-lipizones-badges", "children"),
    Input("page-6bis-all-selected-lipizones", "data"),
)
def update_selected_lipizones_badges(all_selected_lipizones):
    """Update the badges showing selected lipizones with their corresponding colors."""
    # Get the count of selected lipizones
    count = (
        len(all_selected_lipizones.get("names", [])) if all_selected_lipizones else 0
    )

    children = [
        html.H6(
            f"Selected Lipizones ({count})",
            style={"color": "white", "marginBottom": "10px"},
        )
    ]

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
    Output("selected-celltypes-badges", "children"),
    Input("page-6bis-all-selected-celltypes", "data"),
)
def update_selected_celltypes_badges(all_selected_celltypes):
    """Update the badges showing selected celltypes with their corresponding colors."""
    # Get the count of selected celltypes
    count = (
        len(all_selected_celltypes.get("names", [])) if all_selected_celltypes else 0
    )

    children = [
        html.H6(
            f"Selected Cell Types ({count})",
            style={"color": "white", "marginBottom": "10px"},
        )
    ]

    if all_selected_celltypes and "names" in all_selected_celltypes:
        for name in all_selected_celltypes["names"]:
            # Get the color for this celltype, default to cyan if not found
            celltype_color = celltype_data.celltype_to_color.get(name, "#00FFFF")

            # Convert RGB tuple string to CSS color
            if isinstance(celltype_color, str) and celltype_color.startswith("("):
                # Parse the RGB values from the string tuple
                rgb_values = [float(x) for x in celltype_color.strip("()").split(",")]
                # Convert from 0-1 range to 0-255 range and format as CSS rgb()
                css_color = f"rgb({int(rgb_values[0] * 255)}, {int(rgb_values[1] * 255)}, {int(rgb_values[2] * 255)})"
            else:
                # If it's already a hex color or other format, use as is
                css_color = celltype_color

            # Create a style that uses the celltype's color
            badge_style = {
                "margin": "2px",
                "backgroundColor": css_color,
                "color": "black",  # Use black text for better contrast
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

# Use clientside callback for tutorial step updates
app.clientside_callback(
    """
    function(start, next1, next2, next3, next4, next5, next6, next7, next8, next9, next10, next11, finish,
             prev1, prev2, prev3, prev4, prev5, prev6, prev7, prev8, prev9, prev10, prev11, prev12,
             close1, close2, close3, close4, close5, close6, close7, close8, close9, close10, close11) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered.length) {
            return window.dash_clientside.no_update;
        }
        const trigger_id = ctx.triggered[0].prop_id.split('.')[0];

        // Close (×) always resets to 0
        if (trigger_id.startsWith('lipicell-tutorial-close-')) {
            return 0;
        }

        // Start
        if (trigger_id === 'lipicell-start-tutorial-btn' && start) {
            return 1;
        }

        // Next buttons
        if (trigger_id === 'lipicell-tutorial-next-1' && next1) { return 2; }
        if (trigger_id === 'lipicell-tutorial-next-2' && next2) { return 3; }
        if (trigger_id === 'lipicell-tutorial-next-3' && next3) { return 4; }
        if (trigger_id === 'lipicell-tutorial-next-4' && next4) { return 5; }
        if (trigger_id === 'lipicell-tutorial-next-5' && next5) { return 6; }
        if (trigger_id === 'lipicell-tutorial-next-6' && next6) { return 7; }
        if (trigger_id === 'lipicell-tutorial-next-7' && next7) { return 8; }
        if (trigger_id === 'lipicell-tutorial-next-8' && next8) { return 9; }
        if (trigger_id === 'lipicell-tutorial-next-9' && next9) { return 10; }
        if (trigger_id === 'lipicell-tutorial-next-10' && next10) { return 11; }
        if (trigger_id === 'lipicell-tutorial-next-11' && next11) { return 12; }
        if (trigger_id === 'lipicell-tutorial-finish' && finish) { return 0; }

        // Previous buttons
        if (trigger_id === 'lipicell-tutorial-prev-2' && prev2) { return 1; }
        if (trigger_id === 'lipicell-tutorial-prev-3' && prev3) { return 2; }
        if (trigger_id === 'lipicell-tutorial-prev-4' && prev4) { return 3; }
        if (trigger_id === 'lipicell-tutorial-prev-5' && prev5) { return 4; }
        if (trigger_id === 'lipicell-tutorial-prev-6' && prev6) { return 5; }
        if (trigger_id === 'lipicell-tutorial-prev-7' && prev7) { return 6; }
        if (trigger_id === 'lipicell-tutorial-prev-8' && prev8) { return 7; }
        if (trigger_id === 'lipicell-tutorial-prev-9' && prev9) { return 8; }
        if (trigger_id === 'lipicell-tutorial-prev-10' && prev10) { return 9; }
        if (trigger_id === 'lipicell-tutorial-prev-11' && prev11) { return 10; }
        if (trigger_id === 'lipicell-tutorial-prev-12' && prev12) { return 11; }

        return window.dash_clientside.no_update;
    }
    """,
    Output("lipicell-tutorial-step", "data"),

    [Input("lipicell-start-tutorial-btn", "n_clicks"),
     Input("lipicell-tutorial-next-1", "n_clicks"),
     Input("lipicell-tutorial-next-2", "n_clicks"),
     Input("lipicell-tutorial-next-3", "n_clicks"),
     Input("lipicell-tutorial-next-4", "n_clicks"),
     Input("lipicell-tutorial-next-5", "n_clicks"),
     Input("lipicell-tutorial-next-6", "n_clicks"),
     Input("lipicell-tutorial-next-7", "n_clicks"),
     Input("lipicell-tutorial-next-8", "n_clicks"),
     Input("lipicell-tutorial-next-9", "n_clicks"),
     Input("lipicell-tutorial-next-10", "n_clicks"),
     Input("lipicell-tutorial-next-11", "n_clicks"),
     Input("lipicell-tutorial-finish", "n_clicks"),
     Input("lipicell-tutorial-prev-1", "n_clicks"),
     Input("lipicell-tutorial-prev-2", "n_clicks"),
     Input("lipicell-tutorial-prev-3", "n_clicks"),
     Input("lipicell-tutorial-prev-4", "n_clicks"),
     Input("lipicell-tutorial-prev-5", "n_clicks"),
     Input("lipicell-tutorial-prev-6", "n_clicks"),
     Input("lipicell-tutorial-prev-7", "n_clicks"),
     Input("lipicell-tutorial-prev-8", "n_clicks"),
     Input("lipicell-tutorial-prev-9", "n_clicks"),
     Input("lipicell-tutorial-prev-10", "n_clicks"),
     Input("lipicell-tutorial-prev-11", "n_clicks"),
     Input("lipicell-tutorial-prev-12", "n_clicks"),
     Input("lipicell-tutorial-close-1", "n_clicks"),
     Input("lipicell-tutorial-close-2", "n_clicks"),
     Input("lipicell-tutorial-close-3", "n_clicks"),
     Input("lipicell-tutorial-close-4", "n_clicks"),
     Input("lipicell-tutorial-close-5", "n_clicks"),
     Input("lipicell-tutorial-close-6", "n_clicks"),
     Input("lipicell-tutorial-close-7", "n_clicks"),
     Input("lipicell-tutorial-close-8", "n_clicks"),
     Input("lipicell-tutorial-close-9", "n_clicks"),
     Input("lipicell-tutorial-close-10", "n_clicks"),
     Input("lipicell-tutorial-close-11", "n_clicks"),
     Input("lipicell-tutorial-close-12", "n_clicks"),
     ],
    prevent_initial_call=True,
)

# Use clientside callback for popover visibility
app.clientside_callback(
    """
    function(step) {
        if (step === undefined || step === null) {
            return [false, false, false, false, false, false, false, false, false, false, false, false];
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
            step === 11,
            step === 12,
        ];
    }
    """,
    [Output(f"lipicell-tutorial-popover-{i}", "is_open") for i in range(1, 13)],
    Input("lipicell-tutorial-step", "data"),
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
    Output("lipicell-tutorial-completed", "data"),
    Input("lipicell-tutorial-finish", "n_clicks"),
    prevent_initial_call=True,
)
