# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the layout for the sidebar of the app."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import html
import dash_mantine_components as dmc

# ==================================================================================================
# --- Layout
# ==================================================================================================

layout = html.Div(
    className="sidebar",
    children=[
        # dmc.Group(
        #    children=[
        # Header with logo
        dbc.Nav(
            className="sidebar-header",
            vertical=True,
            pills=True,
            children=[
                dbc.NavLink(
                    href="/",
                    active="exact",
                    className="d-flex justify-content-center align-items-center",
                    children=[
                        html.I(id="sidebar-title", className="icon-brain fs-3 m-auto pl-1"),
                    ],
                ),
            ],
        ),
        dbc.Tooltip(
            children="Return to homepage and documentation.",
            target="sidebar-title",
            placement="right",
        ),
        # Navebar to different pages
        dmc.Center(
            style={"height": "75%"},
            children=[
                dbc.Nav(
                    vertical=True,
                    pills=True,
                    children=[
                        # Link to page 2
                        dbc.NavLink(
                            href="/lipid-selection",
                            active="exact",
                            children=[
                                html.I(
                                    id="sidebar-page-2",
                                    className="icon-lipid fs-5",
                                    style={"margin-left": "0.7em"},
                                )
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children=(
                                "LIPIDS"
                            ),
                            target="sidebar-page-2",
                            placement="right",
                        ),
                        # Link to page for peak-selection
                        dbc.NavLink(
                            href="/peak-selection",
                            active="exact",
                            children=[
                                html.I(
                                    id="sidebar-page-peak",
                                    className="icon-lipid fs-5",
                                    style={"margin-left": "0.7em"},
                                )
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children=(
                                "M/Z PEAKS"
                            ),
                            target="sidebar-page-peak",
                            placement="right",
                        ),
                        # Link to page 5 (lp-selection)
                        dbc.NavLink(
                            href="/lp-selection",
                            active="exact",
                            children=[
                                html.I(
                                    id="sidebar-page-2bis",
                                    className="icon-lipid fs-5",
                                    style={"margin-left": "0.7em"},
                                )
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children=(
                                "PROGRAMS"
                            ),
                            target="sidebar-page-2bis",
                            placement="right",
                        ),
                        # Link to page 6
                        dbc.NavLink(
                            href="/lipizones-selection",
                            active="exact",
                            children=[
                                html.I(
                                    id="sidebar-page-6",
                                    className="icon-lipid fs-5",
                                    style={"margin-left": "0.7em"},
                                )
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children=(
                                "LIPIZONES"
                            ),
                            target="sidebar-page-6",
                            placement="right",
                        ),
                        # Link to page 6bis
                        dbc.NavLink(
                            href="/lipizones-vs-celltypes",
                            active="exact",
                            children=[
                                html.I(
                                    id="sidebar-page-6bis",
                                    className="icon-lipid fs-5",
                                    style={"margin-left": "0.7em"},
                                )
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children=(
                                "LIPIZONES VS CELL TYPES"
                            ),
                            target="sidebar-page-6bis",
                            placement="right",
                        ),
                        # Link to page 6tris
                        dbc.NavLink(
                            href="/lipids-vs-genes",
                            active="exact",
                            children=[
                                html.I(
                                    id="sidebar-page-6tris",
                                    className="icon-lipid fs-5",
                                    style={"margin-left": "0.7em"},
                                )
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children=(
                                "LIPIDS VS GENES"
                            ),
                            target="sidebar-page-6tris",
                            placement="right",
                        ),
                        # Link to page 3
                        dbc.NavLink(
                            href="/region-analysis",
                            active="exact",
                            children=[
                                html.I(
                                    id="sidebar-page-3",
                                    className="icon-chart-bar fs-5",
                                    style={"margin-left": "0.7em"},
                                )
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children="DIFFERENTIAL ANALYSIS",
                            target="sidebar-page-3",
                            placement="right",
                        ),
                        # Link to page 4
                        dbc.NavLink(
                            href="/3D-exploration",
                            active="exact",
                            # disabled=True,
                            children=[
                                html.I(
                                    id="sidebar-page-4",
                                    className="icon-3d fs-5",
                                    style={"margin-left": "0.7em"},
                                )
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children="3D LIPIDS",
                            target="sidebar-page-4",
                            placement="right",
                        ),
                        # Link to ID Cards
                        dbc.NavLink(
                            href="/lipizones-id-cards",
                            active="exact",
                            children=[
                                html.I(
                                    id="sidebar-page-id-cards",
                                    className="icon-chart-bar fs-5",
                                    style={"margin-left": "0.7em"},
                                )
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children="ID CARDS",
                            target="sidebar-page-id-cards",
                            placement="right",
                        ),
                        # Link to 3D Lipizones
                        dbc.NavLink(
                            href="/3D-lipizones",
                            active="exact",
                            children=[
                                html.I(
                                    id="sidebar-page-3d-lipizones",
                                    className="icon-3d fs-5",
                                    style={"margin-left": "0.7em"},
                                )
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children="3D LIPIZONES",
                            target="sidebar-page-3d-lipizones",
                            placement="right",
                        ),
                        # Link to documentation
                        html.Div(
                            className="sidebar-bottom",
                            children=[
                                dbc.NavLink(
                                    id="sidebar-documentation",
                                    n_clicks=0,
                                    active="exact",
                                    children=[
                                        html.I(
                                            id="sidebar-documentation-inside",
                                            className="icon-library mb-3 fs-3",
                                            style={"margin-left": "0.5rem"},
                                        )
                                    ],
                                ),
                                dbc.Tooltip(
                                    children="DOCUMENTATION",
                                    target="sidebar-documentation-inside",
                                    placement="right",
                                ),
                                html.H4(
                                    id="sidebar-copyright",
                                    className="icon-cc mb-3 mt-3 fs-2",
                                    style={"color": "#dee2e6", "margin-left": "0.5rem"},
                                ),
                                dbc.Tooltip(
                                    children="Copyright EPFL 2025",
                                    target="sidebar-copyright",
                                    placement="right",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            #    ),
            # ],
        ),
    ],
)

# Lipid Brain Atlas Explorer documentation
# To be updated with the paper content. Website designed by Colas Droin, updated by Francesca Venturi and Luca Fusar Bassini
