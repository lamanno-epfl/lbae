# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to explore lipizones visualization."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html
import dash_draggable
import dash_mantine_components as dmc

# LBAE imports
from app import app, figures, data, storage, cache_flask

# ==================================================================================================
# --- Layout
# ==================================================================================================


def return_layout(basic_config, slice_index):
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
            # React grid for nice responsivity pattern
            dash_draggable.ResponsiveGridLayout(
                id="draggable-lipizones",
                clearSavedLayout=True,
                isDraggable=False,
                isResizable=False,
                containerPadding=[0, 0],
                breakpoints={
                    "xxl": 1600,
                    "lg": 1200,
                    "md": 996,
                    "sm": 768,
                    "xs": 480,
                    "xxs": 0,
                },
                gridCols={
                    "xxl": 12,
                    "lg": 12,
                    "md": 10,
                    "sm": 6,
                    "xs": 4,
                    "xxs": 2,
                },
                style={
                    "background-color": "#1d1c1f",
                },
                layouts={
                    "xxl": [
                        {"i": "lipizones-card", "x": 0, "y": 0, "w": 12, "h": 26},
                    ],
                    "lg": [
                        {"i": "lipizones-card", "x": 0, "y": 0, "w": 12, "h": 26},
                    ],
                    "md": [
                        {"i": "lipizones-card", "x": 0, "y": 0, "w": 10, "h": 26},
                    ],
                    "sm": [
                        {"i": "lipizones-card", "x": 0, "y": 0, "w": 6, "h": 26},
                    ],
                    "xs": [
                        {"i": "lipizones-card", "x": 0, "y": 0, "w": 4, "h": 26},
                    ],
                    "xxs": [
                        {"i": "lipizones-card", "x": 0, "y": 0, "w": 2, "h": 26},
                    ],
                },
                children=[
                    dbc.Card(
                        id="lipizones-card",
                        style={"width": "100%", "height": "100%", "background-color": "#1d1c1f"},
                        children=[
                            dbc.CardBody(
                                [
                                    dcc.Graph(
                                        id="lipizones-graph",
                                        figure=figures.compute_lipizones_figure(),
                                        config={"displayModeBar": True},
                                        style={"height": "100%"},
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
    return page
