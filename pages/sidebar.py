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
        # Navigation to different pages
        dmc.Center(
            style={"height": "75%"},
            children=[
                dbc.Nav(
                    vertical=True,
                    pills=True,
                    children=[
                        # SUPER-TAB: MOLECULES
                        html.Div(
                            className="super-tab my-4",
                            children=[
                                dbc.NavLink(
                                    href="#",
                                    active="exact",
                                    children=[
                                        html.I(
                                            id="sidebar-molecules",
                                            className="icon-lipid fs-5 has-submenu",
                                            style={"margin-left": "0.7em"},
                                        )
                                    ],
                                ),
                                # Sub-menu for MOLECULES
                                html.Div(
                                    className="sub-menu",
                                    children=[
                                        html.Div(
                                            className="sub-menu-header",
                                            children=[html.H6("MOLECULES", className="mb-2 px-3")]
                                        ),
                                        dbc.NavLink(
                                            "Lipids",
                                            href="/lipid-selection",
                                            active="exact",
                                        ),
                                        dbc.NavLink(
                                            "M/Z Peaks",
                                            href="/peak-selection",
                                            active="exact",
                                        ),
                                    ],
                                ),
                            ],
                            id="super-tab-molecules",
                        ),
                        
                        # PROGRAMS (as a 1-option dropdown)
                        html.Div(
                            className="super-tab my-4",
                            children=[
                                dbc.NavLink(
                                    href="#",
                                    active="exact",
                                    children=[
                                        html.I(
                                            id="sidebar-programs",
                                            className="icon-lipid fs-5 has-submenu",
                                            style={"margin-left": "0.7em"},
                                        )
                                    ],
                                ),
                                # Sub-menu for PROGRAMS
                                html.Div(
                                    className="sub-menu",
                                    children=[
                                        dbc.NavLink(
                                            "Lipid Programs",
                                            href="/lp-selection",
                                            active="exact",
                                        ),
                                    ],
                                ),
                            ],
                            id="super-tab-programs",
                        ),
                        
                        # REGION ANALYSIS (as a 1-option dropdown)
                        html.Div(
                            className="super-tab my-4",
                            children=[
                                dbc.NavLink(
                                    href="#",
                                    active="exact",
                                    children=[
                                        html.I(
                                            id="sidebar-region-analysis",
                                            className="icon-chart-bar fs-5 has-submenu",
                                            style={"margin-left": "0.7em"},
                                        )
                                    ],
                                ),
                                # Sub-menu for REGION ANALYSIS
                                html.Div(
                                    className="sub-menu",
                                    children=[
                                        dbc.NavLink(
                                            "Differential Analysis",
                                            href="/region-analysis",
                                            active="exact",
                                        ),
                                    ],
                                ),
                            ],
                            id="super-tab-region-analysis",
                        ),
                        
                        # SUPER-TAB: LIPIZONES
                        html.Div(
                            className="super-tab my-4",
                            children=[
                                dbc.NavLink(
                                    href="#",
                                    active="exact",
                                    children=[
                                        html.I(
                                            id="sidebar-lipizones",
                                            className="icon-lipid fs-5 has-submenu",
                                            style={"margin-left": "0.7em"},
                                        )
                                    ],
                                ),
                                # Sub-menu for LIPIZONES
                                html.Div(
                                    className="sub-menu",
                                    children=[
                                        html.Div(
                                            className="sub-menu-header",
                                            children=[html.H6("LIPIZONES", className="mb-2 px-3")]
                                        ),
                                        dbc.NavLink(
                                            "Lipizones",
                                            href="/lipizones-selection",
                                            active="exact",
                                        ),
                                        dbc.NavLink(
                                            "ID Cards",
                                            href="/lipizones-id-cards",
                                            active="exact",
                                        ),
                                    ],
                                ),
                            ],
                            id="super-tab-lipizones",
                        ),
                        
                        # SUPER-TAB: COMPARISONS
                        html.Div(
                            className="super-tab my-4",
                            children=[
                                dbc.NavLink(
                                    href="#",
                                    active="exact",
                                    children=[
                                        html.I(
                                            id="sidebar-comparisons",
                                            className="icon-chart-bar fs-5 has-submenu",
                                            style={"margin-left": "0.7em"},
                                        )
                                    ],
                                ),
                                # Sub-menu for COMPARISONS
                                html.Div(
                                    className="sub-menu",
                                    children=[
                                        html.Div(
                                            className="sub-menu-header",
                                            children=[html.H6("COMPARISONS", className="mb-2 px-3")]
                                        ),
                                        dbc.NavLink(
                                            "Lipizones vs Cell Types",
                                            href="/lipizones-vs-celltypes",
                                            active="exact",
                                        ),
                                        dbc.NavLink(
                                            "Lipids vs Genes",
                                            href="/lipids-vs-genes",
                                            active="exact",
                                        ),
                                    ],
                                ),
                            ],
                            id="super-tab-comparisons",
                        ),
                        
                        # SUPER-TAB: 3D EXPLORATION
                        html.Div(
                            className="super-tab my-4",
                            children=[
                                dbc.NavLink(
                                    href="#",
                                    active="exact",
                                    children=[
                                        html.I(
                                            id="sidebar-3d",
                                            className="icon-3d fs-5 has-submenu",
                                            style={"margin-left": "0.7em"},
                                        )
                                    ],
                                ),
                                # Sub-menu for 3D EXPLORATION
                                html.Div(
                                    className="sub-menu",
                                    children=[
                                        html.Div(
                                            className="sub-menu-header",
                                            children=[html.H6("3D EXPLORATION", className="mb-2 px-3")]
                                        ),
                                        dbc.NavLink(
                                            "3D Lipids",
                                            href="/3D-exploration",
                                            active="exact",
                                        ),
                                        dbc.NavLink(
                                            "3D Lipizones",
                                            href="/3D-lipizones",
                                            active="exact",
                                        ),
                                    ],
                                ),
                            ],
                            id="super-tab-3d",
                        ),
                        
                        # Documentation and Copyright at the bottom
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
        ),
    ],
)

# Lipid Brain Atlas Explorer documentation
# To be updated with the paper content. Website designed by Colas Droin, updated by Francesca Venturi and Luca Fusar Bassini
