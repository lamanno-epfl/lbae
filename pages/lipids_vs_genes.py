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
# threadpoolctl import threadpool_limits, threadpool_info
#threadpool_limits(limits=8)
import os
os.environ['OMP_NUM_THREADS'] = '6'

# LBAE imports
from app import app, figures, data, atlas, celltype_data

# ==================================================================================================
# --- Data
# ==================================================================================================

# sample_data = lipizone_data.sample_data.retrieve_sample_data(brain_id)
# color_masks = sample_data["color_masks"]
# grayscale_image = sample_data["grayscale_image"]
# rgb_image = sample_data["grid_image"][:, :, :3]  # remove transparency channel for now

df_genes = pd.read_csv('./data/gene_data/Single_Nuc_Cluster_Avg_Expression.csv.gz', index_col=0)
df_genes.index = df_genes.index.str.split('=').str[1]
df_genes = df_genes[df_genes.index.isin(celltype_data.df_hierarchy_celltypes['cell_type'])]

# ==================================================================================================
# --- Helper functions
# ==================================================================================================

def get_gene_options(slice_index):
    """This function returns the list of genes for a given slice index."""
    celltype_in_section = list(celltype_data.retrieve_section_data(int(slice_index))['color_masks'].keys())
    df_genes_in_section = df_genes[df_genes.index.isin(celltype_in_section)]
    df_genes_in_section = df_genes_in_section.loc[:, (df_genes_in_section != 0).any(axis=0)]
    return df_genes_in_section.columns.tolist()

# ==================================================================================================
# --- Layout
# ==================================================================================================


def return_layout(basic_config, slice_index):
    page = (
        html.Div(
            style={
                "position": "absolute",
                "top": "0px",
                "right": "0px",
                "bottom": "0px",
                "left": "6rem",
                "background-color": "#1d1c1f",
                "overflow": "hidden",  # Prevent any scrolling
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
                    id="page-6tris-refresh-alert",
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
                # Add a store component to hold the slider style
                dcc.Store(id="page-6tris-main-slider-style", data={"display": "block"}),
                dcc.Store(id="lipigene-tutorial-step", data=0),
                dcc.Store(id="lipigene-tutorial-completed", storage_type="local", data=False),

                # Add tutorial button under welcome text
                html.Div(
                    id="lipigene-start-tutorial-target",
                    style={
                        "position": "fixed",
                        "top": "0.9em",
                        "left": "20.3em",
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
                            id="lipigene-start-tutorial-btn",
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
                            }
                        )
                    ]
                ),
                html.Div(
                    className="fixed-aspect-ratio",
                    style={
                        "background-color": "#1d1c1f",
                        "position": "absolute",
                        "top": "0",
                        "left": "0",
                        "right": "0",
                        "bottom": "0",
                        "overflow": "hidden",
                    },
                    children=[
                        dcc.Graph(
                            id="page-6tris-graph-heatmap-mz-selection",
                            config=basic_config
                            | {
                                "toImageButtonOptions": {
                                    "format": "png",
                                    "filename": "brain_lipid_selection",
                                    "scale": 2,
                                },"scrollZoom": True
                            }
                            | {"staticPlot": False},
                            style={
                                "height": "100vh",
                                "width": "100%",
                                "position": "absolute",
                                "left": "0",
                                "top": "0",
                                "background-color": "#1d1c1f",
                            },
                            figure=figures.build_lipid_heatmap_from_image(
                                figures.compute_image_lipids_genes(
                                    all_selected_lipids=["HexCer 42:2;O2"],
                                    all_selected_genes=["Mbp=ENSMUSG00000041607"],
                                    slice_index=slice_index,
                                    df_genes=df_genes,
                                    rgb_mode_lipids=False,
                                    ),
                                return_base64_string=False,
                                draw=False,
                                type_image="RGB",
                                return_go_image=False,
                            ),
                        ),
                        # Allen Brain Atlas switch (independent)
                        html.Div(
                            id="page-6tris-annotations-container",
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
                                    id="page-6tris-toggle-annotations",
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
                        # Title
                        html.H4(
                            "Visualize Lipids",
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
                        html.H4(
                            "Visualize Genes",
                            style={
                                "color": "white",
                                "marginBottom": "15px",
                                "fontSize": "1.2em",
                                "fontWeight": "500",
                                "position": "absolute",
                                "right": "1%",
                                "top": "1em",
                            }
                        ),
                        # Lipid selection controls group
                        dmc.Group(
                            direction="column",
                            spacing=0,
                            style={
                                "left": "1%",
                                "top": "3.5em",
                                "position": "absolute",
                            },
                            children=[
                                dmc.Text("Choose up to 3 lipids", size="lg"),
                                dmc.Group(
                                    spacing="xs",
                                    align="center",
                                    children=[
                                        dmc.MultiSelect(
                                            id="page-6tris-dropdown-lipids",
                                            data=data.return_lipid_options(),
                                            value=['HexCer 42:2;O2'],
                                            searchable=True,
                                            nothingFound="No lipid found",
                                            radius="md",
                                            size="xs",
                                            placeholder="Choose up to 3 lipids",
                                            clearable=False,
                                            maxSelectedValues=3,
                                            transitionDuration=150,
                                            transition="pop-top-left",
                                            transitionTimingFunction="ease",
                                            style={
                                                "width": "20em",
                                            },
                                        ),
                                        html.Div(
                                            id="page-6tris-rgb-group",
                                            style={
                                                "display": "flex", 
                                                "alignItems": "center", 
                                                "marginLeft": "15px"
                                            },
                                            children=[
                                                dmc.Switch(
                                                    id="page-6tris-rgb-switch",
                                                    checked=False,
                                                    color="cyan",
                                                    radius="xl",
                                                    size="sm",
                                                ),
                                                html.Span(
                                                    "Display as RGB",
                                                    style={
                                                        "color": "white",
                                                        "marginLeft": "8px",
                                                        "fontWeight": "500",
                                                        "fontSize": "14px",
                                                    },
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        # Gene selection controls group
                        dmc.Group(
                            direction="column",
                            spacing=0,
                            style={
                                "right": "1%",
                                "top": "3.5em",
                                "position": "absolute",
                            },
                            children=[
                                dmc.Text("Choose up to 3 genes", size="lg"),
                                dmc.Group(
                                    spacing="xs",
                                    align="center",
                                    children=[
                                        dmc.MultiSelect(
                                            id="page-6tris-dropdown-genes",
                                            data=get_gene_options(slice_index),# data.return_gene_options(),
                                            value=["Mbp=ENSMUSG00000041607"],
                                            searchable=True,
                                            nothingFound="No gene found",
                                            radius="md",
                                            size="xs",
                                            placeholder="Choose up to 3 genes",
                                            clearable=False,
                                            maxSelectedValues=3,
                                            transitionDuration=150,
                                            transition="pop-top-right",
                                            transitionTimingFunction="ease",
                                            style={
                                                "width": "20em",
                                            },
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        # Title and badges group on the left side
                        dmc.Group(
                            direction="column",
                            spacing=0,
                            style={
                                "left": "1%",
                                "top": "12em",  # Adjusted to be below the lipid selection
                                "position": "absolute",
                            },
                            children=[
                                dmc.Text(
                                    id="page-6tris-badge-input",
                                    children="Lipids selected",
                                    size="lg",
                                ),
                                dmc.Badge(
                                    id="page-6tris-badge-lipid-1",
                                    children="name-lipid-1",
                                    color="red",
                                    variant="filled",
                                    class_name="d-none mt-2",
                                ),
                                dmc.Badge(
                                    id="page-6tris-badge-lipid-2",
                                    children="name-lipid-2",
                                    color="teal",
                                    variant="filled",
                                    class_name="d-none mt-2",
                                ),
                                dmc.Badge(
                                    id="page-6tris-badge-lipid-3",
                                    children="name-lipid-3",
                                    color="blue",
                                    variant="filled",
                                    class_name="d-none mt-2",
                                ),
                            ],
                        ),
                        # Title and badges group for genes on the right side
                        dmc.Group(
                            direction="column",
                            spacing=0,
                            style={
                                "right": "1%",
                                "top": "12em",  # Adjusted to be below the gene selection
                                "position": "absolute",
                            },
                            children=[
                                dmc.Text(
                                    id="page-6tris-badge-input-genes",
                                    children="Genes selected:",
                                    size="lg",
                                ),
                                # First gene badge and slider
                                html.Div(
                                    style={"display": "flex", "flexDirection": "column", "alignItems": "center"},
                                    children=[
                                        dmc.Badge(
                                            id="page-6tris-badge-gene-1",
                                            children="name-gene-1",
                                            color="orange",
                                            variant="filled",
                                            class_name="d-none mt-2",
                                            style={"textAlign": "center"},
                                        ),
                                        dmc.Slider(
                                            id="page-6tris-gene-slider-1",
                                            min=0,
                                            max=1,
                                            step=0.1,
                                            value=0,
                                            marks=[{"value": 0, "label": "Min"}, {"value": 1, "label": "Max"}],
                                            labelAlwaysOn=False,
                                            size="sm",
                                            color="orange",
                                            class_name="d-none mt-2",
                                            style={"width": "220px"}
                                        ),
                                    ]
                                ),
                                # Second gene badge and slider with more space
                                html.Div(
                                    style={"display": "flex", "flexDirection": "column", "alignItems": "center"},
                                    children=[
                                        dmc.Badge(
                                            id="page-6tris-badge-gene-2",
                                            children="name-gene-2",
                                            color="green",
                                            variant="filled",
                                            class_name="d-none mt-4",
                                            style={"textAlign": "center"},
                                        ),
                                        dmc.Slider(
                                            id="page-6tris-gene-slider-2",
                                            min=0,
                                            max=1,
                                            step=0.1,
                                            value=0,
                                            marks=[{"value": 0, "label": "Min"}, {"value": 1, "label": "Max"}],
                                            labelAlwaysOn=False,
                                            size="sm",
                                            color="green",
                                            class_name="d-none mt-2",
                                            style={"width": "220px"}
                                        ),
                                    ]
                                ),
                                # Third gene badge and slider with more space
                                html.Div(
                                    style={"display": "flex", "flexDirection": "column", "alignItems": "center"},
                                    children=[
                                        dmc.Badge(
                                            id="page-6tris-badge-gene-3",
                                            children="name-gene-3",
                                            color="blue",
                                            variant="filled",
                                            class_name="d-none mt-4",
                                            style={"textAlign": "center"},
                                        ),
                                        dmc.Slider(
                                            id="page-6tris-gene-slider-3",
                                            min=0,
                                            max=1,
                                            step=0.1,
                                            value=0,
                                            marks=[{"value": 0, "label": "Min"}, {"value": 1, "label": "Max"}],
                                            labelAlwaysOn=False,
                                            size="sm",
                                            color="blue",
                                            class_name="d-none mt-2",
                                            style={"width": "220px"}
                                        ),
                                    ]
                                ),
                            ],
                        ),
                        dmc.Text(
                            "",
                            id="page-6tris-graph-hover-text",
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
                        # dmc.Group(
                        #     position="right",
                        #     direction="row",
                        #     style={
                        #         "right": "1rem",
                        #         "bottom": "0.5rem",
                        #         "position": "fixed",
                        #         "z-index": 1000,
                        #     },
                        #     class_name="position-absolute",
                        #     spacing=0,
                        #     children=[
                        #         dmc.Button(
                        #             children="Download data",
                        #             id="page-6tris-download-data-button",
                        #             variant="filled",
                        #             disabled=False,
                        #             color="cyan",
                        #             radius="md",
                        #             size="xs",
                        #             compact=False,
                        #             loading=False,
                        #             class_name="mt-1",
                        #             style={"margin-right": "0.5rem"},
                        #         ),
                        #         dmc.Button(
                        #             children="Download image",
                        #             id="page-6tris-download-image-button",
                        #             variant="filled",
                        #             disabled=False,
                        #             color="cyan",
                        #             radius="md",
                        #             size="xs",
                        #             compact=False,
                        #             loading=False,
                        #             class_name="mt-1",
                        #         ),
                        #     ],
                        # ),
                        # dcc.Download(id="page-6tris-download-data"),
                        
                        # Tutorial Popovers with adjusted positions
                        dbc.Popover(
                            [
                                dbc.PopoverHeader(
                                    [
                                        "Lipizones vs Cell Types",
                                        dbc.Button(
                                            "×",
                                            id="lipigene-tutorial-close-1",
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
                                            "Welcome to the Lipids vs Genes page! This view allows you to compare spatial lipid expression with gene expression in the same brain slices. By overlaying these two layers of information, you can explore how molecular distributions align across omics levels, and identify possible relationships between lipid metabolism and gene activity in specific brain regions. Feel free to zoom in and out on the visualization displayed and to move the brain around by clicking and dragging.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "Previous",
                                                    id="lipigene-tutorial-prev-1",
                                                    color="secondary",
                                                    size="sm",
                                                    className="float-start",
                                                    disabled=True,
                                                ),
                                                dbc.Button(
                                                    "Next",
                                                    id="lipigene-tutorial-next-1",
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
                            id="lipigene-tutorial-popover-1",
                            target="lipigene-start-tutorial-target",
                            placement="right",
                            is_open=False,
                            style={
                                "zIndex": 9999,
                                "border": "2px solid #1fafc8",
                                "boxShadow": "0 0 15px 2px #1fafc8"
                            }
                        ),
                        # --- Lipid Selection ---
                        dbc.Popover(
                            [
                                dbc.PopoverHeader(
                                    [
                                        "Choose Up to 3 Lipids",
                                        dbc.Button(
                                            "×",
                                            id="lipigene-tutorial-close-2",
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
                                            "Select up to three lipids from the 172 confidently annotated. Lipids are grouped by family, and some appear under a 'Multiple matches' category if they matched different molecules.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "Previous",
                                                    id="lipigene-tutorial-prev-2",
                                                    color="secondary",
                                                    size="sm",
                                                    className="float-start",
                                                ),
                                                dbc.Button(
                                                    "Next",
                                                    id="lipigene-tutorial-next-2",
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
                            id="lipigene-tutorial-popover-2",
                            target="page-6tris-dropdown-lipids",  # dropdown menu
                            placement="bottom",
                            is_open=False,
                            style={
                                "zIndex": 9999,
                                "border": "2px solid #1fafc8",
                                "boxShadow": "0 0 15px 2px #1fafc8"
                            },
                        ),
                        # --- RGB Mode ---
                        dbc.Popover(
                            [
                                dbc.PopoverHeader(
                                    [
                                        "Color Map Options",
                                        dbc.Button(
                                            "×",
                                            id="lipigene-tutorial-close-3",
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
                                            "When one lipid is selected, you can choose to display it using either the viridis colormap or the red channel of the RGB space. If two or three lipids are selected, the visualization automatically switches to RGB mode, where each lipid is mapped to a different channel: red for the first, green for the second, and blue for the third.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "Previous",
                                                    id="lipigene-tutorial-prev-3",
                                                    color="secondary",
                                                    size="sm",
                                                    className="float-start",
                                                ),
                                                dbc.Button(
                                                    "Next",
                                                    id="lipigene-tutorial-next-3",
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
                            id="lipigene-tutorial-popover-3",
                            target="page-6tris-rgb-switch",  # rgb switch
                            placement="bottom",
                            is_open=False,
                            style={
                                "zIndex": 9999,
                                "border": "2px solid #1fafc8",
                                "boxShadow": "0 0 15px 2px #1fafc8"
                            },
                        ),
                        # --- Gene Selection ---
                        dbc.Popover(
                            [
                                dbc.PopoverHeader(
                                    [
                                        "Choose Up to 3 Genes",
                                        dbc.Button(
                                            "×",
                                            id="lipigene-tutorial-close-4",
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
                                            "Select up to three genes to display. You can compare their spatial expression with lipid signals to explore potential functional or anatomical relationships.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "Previous",
                                                    id="lipigene-tutorial-prev-4",
                                                    color="secondary",
                                                    size="sm",
                                                    className="float-start",
                                                ),
                                                dbc.Button(
                                                    "Next",
                                                    id="lipigene-tutorial-next-4",
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
                            id="lipigene-tutorial-popover-4",
                            target="page-6tris-dropdown-genes",  # dropdown menu
                            placement="bottom",
                            is_open=False,
                            style={
                                "zIndex": 9999,
                                "border": "2px solid #1fafc8",
                                "boxShadow": "0 0 15px 2px #1fafc8"
                            },
                        ),
                        # --- Gene Filtering ---
                        dbc.Popover(
                            [
                                dbc.PopoverHeader(
                                    [
                                        "Filter Low-Expression Regions",
                                        dbc.Button(
                                            "×",
                                            id="lipigene-tutorial-close-5",
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
                                            "For each selected gene, you'll see a slider that lets you set a minimum expression threshold. This filters out pixels with low gene expression, helping you focus only on regions where the gene is meaningfully expressed and removing background noise from the visualization.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "Previous",
                                                    id="lipigene-tutorial-prev-5",
                                                    color="secondary",
                                                    size="sm",
                                                    className="float-start",
                                                ),
                                                dbc.Button(
                                                    "Next",
                                                    id="lipigene-tutorial-next-5",
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
                            id="lipigene-tutorial-popover-5",
                            target="page-6tris-gene-slider-1",  # gene slider
                            placement="left",
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
                                            id="lipigene-tutorial-close-6",
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
                                            "You can enable the Allen Brain Atlas annotations to overlay anatomical labels directly on the slices. This helps you navigate the brain and interpret lipid signals in their biological context.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "Previous",
                                                    id="lipigene-tutorial-prev-6",
                                                    color="secondary",
                                                    size="sm",
                                                    className="float-start",
                                                ),
                                                dbc.Button(
                                                    "Next",
                                                    id="lipigene-tutorial-next-6",
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
                            id="lipigene-tutorial-popover-6",
                            target="page-6tris-toggle-annotations",  # annotations switch
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
                                            id="lipigene-tutorial-close-7",
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
                                            "In the single-section view, you can navigate through the brain by selecting different slices along the rostro-caudal (front-to-back) axis. This allows detailed inspection of lipid signals at specific anatomical levels.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "Previous",
                                                    id="lipigene-tutorial-prev-7",
                                                    color="secondary",
                                                    size="sm",
                                                    className="float-start",
                                                ),
                                                dbc.Button(
                                                    "Finish",
                                                    id="lipigene-tutorial-finish",
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
                            id="lipigene-tutorial-popover-7",
                            target="main-paper-slider",  # slider
                            placement="top",
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
        ),
    )

    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================

@app.callback(
    Output("page-6tris-graph-hover-text", "children"),
    Input("page-6tris-graph-heatmap-mz-selection", "hoverData"),
    Input("main-slider", "data"),
)
def page_6tris_hover(hoverData, slice_index):
    """This callback is used to update the text displayed when hovering over the slice image."""
    acronym_mask = data.acronyms_masks[slice_index]
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            x = hoverData["points"][0]["x"] # --> from 0 to 456
            y = hoverData["points"][0]["y"] # --> from 0 to 320
            # z = arr_z[y, x]
            try:
                return atlas.dic_acronym_name[acronym_mask[y, x]]
            except:
                return "Undefined"

    return dash.no_update

@app.callback(
    Output("page-6tris-graph-heatmap-mz-selection", "figure"),
    Output("page-6tris-badge-input", "children"),
    Output("page-6tris-badge-input-genes", "children"),

    Input("main-slider", "data"),
    Input("page-6tris-rgb-switch", "checked"),
    Input("page-6tris-selected-lipid-1", "data"),
    Input("page-6tris-selected-lipid-2", "data"),
    Input("page-6tris-selected-lipid-3", "data"),
    Input("page-6tris-toggle-annotations", "checked"),
    Input("main-brain", "value"),
    Input("page-6tris-selected-gene-1", "data"),
    Input("page-6tris-selected-gene-2", "data"),
    Input("page-6tris-selected-gene-3", "data"),
    Input("page-6tris-gene-threshold-1", "data"),
    Input("page-6tris-gene-threshold-2", "data"),
    Input("page-6tris-gene-threshold-3", "data"),

    State("page-6tris-badge-input", "children"),
    State("page-6tris-badge-input-genes", "children"),
)
def page_6tris_plot_graph_heatmap_mz_selection(
    slice_index,
    rgb_switch,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    annotations_checked,
    brain_id,
    gene_1_index,
    gene_2_index,
    gene_3_index,
    gene_threshold_1,
    gene_threshold_2,
    gene_threshold_3,
    graph_input,
    genes_input,
):
    """This callback plots the heatmap of the selected lipid(s) and gene(s)."""
    logging.info("Entering function to plot heatmap or RGB depending on lipid/gene selection")
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    
    overlay = data.get_aba_contours(slice_index) if annotations_checked else None

    # Get selected genes
    active_genes = []
    gene_thresholds = []
    if gene_1_index != -1 or gene_2_index != -1 or gene_3_index != -1:
        available_genes = get_gene_options(slice_index)
        gene_names = []
        if gene_1_index != -1 and gene_1_index < len(available_genes):
            gene_names.append(available_genes[gene_1_index])
            gene_thresholds.append(gene_threshold_1)
        if gene_2_index != -1 and gene_2_index < len(available_genes):
            gene_names.append(available_genes[gene_2_index])
            gene_thresholds.append(gene_threshold_2)
        if gene_3_index != -1 and gene_3_index < len(available_genes):
            gene_names.append(available_genes[gene_3_index])
            gene_thresholds.append(gene_threshold_3)
        active_genes = gene_names
    
    # Get selected lipids
    ll_lipid_names = [
            ' '.join([
                data.get_annotations().iloc[index]["name"].split('_')[i] + ' ' 
                + data.get_annotations().iloc[index]["structure"].split('_')[i] 
                for i in range(len(data.get_annotations().iloc[index]["name"].split('_')))
            ])
        if index != -1
        else None
        for index in [lipid_1_index, lipid_2_index, lipid_3_index]
    ]
    active_lipids = [name for name in ll_lipid_names if name is not None]
    
    # Auto-set RGB mode when multiple lipids are selected
    rgb_mode_lipids = rgb_switch
    
    # Handle annotations toggle separately to preserve figure state
    if id_input == "page-6tris-toggle-annotations":
        
        lipid_gene_image = figures.compute_image_lipids_genes(
                all_selected_lipids=active_lipids,
                all_selected_genes=active_genes,
                gene_thresholds=gene_thresholds,
                slice_index=slice_index,
                df_genes=df_genes,
                rgb_mode_lipids=rgb_mode_lipids,
            )
        fig = figures.build_lipid_heatmap_from_image(
            lipid_gene_image,
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )
        return fig, "Lipids selected", "Genes selected:"

    if id_input == "main-slider":
        lipid_gene_image = figures.compute_image_lipids_genes(
            all_selected_lipids=active_lipids,
            all_selected_genes=active_genes,
            gene_thresholds=[0] * len(active_genes),
            slice_index=slice_index,
            df_genes=df_genes,
            rgb_mode_lipids=rgb_mode_lipids,
        )
        fig = figures.build_lipid_heatmap_from_image(
            lipid_gene_image,
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )
        return fig, "Lipids selected", "Genes selected:"

    # If a gene selection or lipid selection has been modified
    if (
        id_input in ["page-6tris-selected-lipid-1", "page-6tris-selected-lipid-2", "page-6tris-selected-lipid-3", 
                     "page-6tris-selected-gene-1", "page-6tris-selected-gene-2", "page-6tris-selected-gene-3",
                     "page-6tris-rgb-switch", "page-6tris-gene-threshold-1", "page-6tris-gene-threshold-2", 
                     "page-6tris-gene-threshold-3"]
    ):
        # If both lipids and genes are selected, use the new function
        lipid_gene_image = figures.compute_image_lipids_genes(
            all_selected_lipids=active_lipids,
            all_selected_genes=active_genes,
            gene_thresholds=gene_thresholds,
            slice_index=slice_index,
            df_genes=df_genes,
            rgb_mode_lipids=rgb_mode_lipids,
        )
        fig = figures.build_lipid_heatmap_from_image(
            lipid_gene_image,
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )
        return fig, "Lipids selected", "Genes selected:"
        
    # If no trigger, the page has just been loaded, so load new figure with default parameters
    else:
        lipid_gene_image = figures.compute_image_lipids_genes(
            all_selected_lipids=["HexCer 42:2;O2"],
            all_selected_genes=["Xkr4=ENSMUSG00000051951"],
            gene_thresholds=[0],
            slice_index=slice_index,
            df_genes=df_genes,
            rgb_mode_lipids=False,
        )
        fig = figures.build_lipid_heatmap_from_image(
            lipid_gene_image,
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )
        return fig, "Lipids selected", "Genes selected:"

@app.callback(
    Output("page-6tris-badge-lipid-1", "children"),
    Output("page-6tris-badge-lipid-2", "children"),
    Output("page-6tris-badge-lipid-3", "children"),
    Output("page-6tris-selected-lipid-1", "data"),
    Output("page-6tris-selected-lipid-2", "data"),
    Output("page-6tris-selected-lipid-3", "data"),
    Output("page-6tris-badge-lipid-1", "class_name"),
    Output("page-6tris-badge-lipid-2", "class_name"),
    Output("page-6tris-badge-lipid-3", "class_name"),
    Output("page-6tris-dropdown-lipids", "value"),
    Input("page-6tris-dropdown-lipids", "value"),
    Input("page-6tris-badge-lipid-1", "class_name"),
    Input("page-6tris-badge-lipid-2", "class_name"),
    Input("page-6tris-badge-lipid-3", "class_name"),
    Input("main-slider", "data"),
    Input("page-6tris-rgb-switch", "checked"),
    State("page-6tris-selected-lipid-1", "data"),
    State("page-6tris-selected-lipid-2", "data"),
    State("page-6tris-selected-lipid-3", "data"),
    State("page-6tris-badge-lipid-1", "children"),
    State("page-6tris-badge-lipid-2", "children"),
    State("page-6tris-badge-lipid-3", "children"),
    State("main-brain", "value"),
)
def page_6tris_add_toast_selection_lipids(
    l_lipid_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    rgb_switch,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    header_1,
    header_2,
    header_3,
    brain_id,
):
    """This callback adds the selected lipid to the selection."""
    logging.info("Entering function to update lipid data")
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    
    # Initialize with default lipid if no selection exists
    if len(id_input) == 0 or (id_input == "page-6tris-dropdown-lipids" and l_lipid_names is None):
        default_lipid = "HexCer 42:2;O2"
        name, structure = default_lipid.split(" ")
        l_lipid_loc = (
            data.get_annotations()
            .index[
                (data.get_annotations()["name"] == name)
                & (data.get_annotations()["structure"] == structure)
                & (data.get_annotations()["slice"] == slice_index)
            ]
            .tolist()
        )
        
        if len(l_lipid_loc) == 0:
            l_lipid_loc = (
                data.get_annotations()
                .index[
                    (data.get_annotations()["name"] == name)
                    & (data.get_annotations()["structure"] == structure)
                ]
                .tolist()
            )[:1]
        
        if len(l_lipid_loc) > 0:
            lipid_1_index = l_lipid_loc[0]
            header_1 = default_lipid
            return header_1, "", "", lipid_1_index, -1, -1, "mt-2", "d-none mt-2", "d-none mt-2", [default_lipid]
        else:
            return "", "", "", -1, -1, -1, "d-none mt-2", "d-none mt-2", "d-none mt-2", []

    # Handle lipid deletion
    if l_lipid_names is not None and len(l_lipid_names) < len([x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x != -1]):
        logging.info("One or several lipids have been deleted. Reorganizing lipid badges.")
        
        # Create list of remaining lipids and their indices
        remaining_lipids = []
        for lipid_name in l_lipid_names:
            if len(lipid_name.split(" ")) == 2:
                name, structure = lipid_name.split(" ")
            else:   
                name = "_".join(lipid_name.split(" ")[::2])
                structure = "_".join(lipid_name.split(" ")[1::2])
                
            l_lipid_loc = (
                data.get_annotations()
                .index[
                    (data.get_annotations()["name"] == name)
                    & (data.get_annotations()["structure"] == structure)
                    & (data.get_annotations()["slice"] == slice_index)
                ]
                .tolist()
            )
            
            if len(l_lipid_loc) == 0:
                l_lipid_loc = (
                    data.get_annotations()
                    .index[
                        (data.get_annotations()["name"] == name)
                        & (data.get_annotations()["structure"] == structure)
                    ]
                    .tolist()
                )[:1]
                
            if len(l_lipid_loc) > 0:
                remaining_lipids.append((lipid_name, l_lipid_loc[0]))
        
        # Reset all slots
        header_1, header_2, header_3 = "", "", ""
        lipid_1_index, lipid_2_index, lipid_3_index = -1, -1, -1
        class_name_badge_1, class_name_badge_2, class_name_badge_3 = "d-none mt-2", "d-none mt-2", "d-none mt-2"
        
        # Fill slots in order with remaining lipids
        for idx, (lipid_name, lipid_idx) in enumerate(remaining_lipids):
            if idx == 0:
                header_1 = lipid_name
                lipid_1_index = lipid_idx
                class_name_badge_1 = "mt-2"
            elif idx == 1:
                header_2 = lipid_name
                lipid_2_index = lipid_idx
                class_name_badge_2 = "mt-2"
            elif idx == 2:
                header_3 = lipid_name
                lipid_3_index = lipid_idx
                class_name_badge_3 = "mt-2"
            
        return (
            header_1,
            header_2,
            header_3,
            lipid_1_index,
            lipid_2_index,
            lipid_3_index,
            class_name_badge_1,
            class_name_badge_2,
            class_name_badge_3,
            l_lipid_names
        )

    # Handle new lipid addition or slice change
    if (id_input == "page-6tris-dropdown-lipids" and l_lipid_names is not None) or id_input == "main-slider":
        # If a new slice has been selected
        if id_input == "main-slider":
            # Collect the selected lipids that need to be updated
            selected_lipids = []
            for i, header in enumerate([header_1, header_2, header_3]):
                if not header:
                    continue
                    
                try:
                    # Handle different formats of lipid names
                    if len(header.split(" ")) == 2:
                        name, structure = header.split(" ")
                    else:   
                        name = "_".join(header.split(" ")[::2])
                        structure = "_".join(header.split(" ")[1::2])
                
                    # Find lipid location
                    l_lipid_loc_temp = (
                        data.get_annotations()
                        .index[
                            (data.get_annotations()["name"] == name)
                            & (data.get_annotations()["structure"] == structure)
                        ]
                        .tolist()
                    )
                    
                    # Filter to only include lipids from the current slice
                    l_lipid_loc = [
                        l_lipid_loc_temp[i]
                        for i, x in enumerate(
                            data.get_annotations().iloc[l_lipid_loc_temp]["slice"] == slice_index
                        )
                        if x
                    ]
                    
                    lipid_index = l_lipid_loc[0] if len(l_lipid_loc) > 0 else -1
                    selected_lipids.append((header, lipid_index, i))
                except Exception as e:
                    logging.error(f"Error updating lipid index for {header}: {e}")
                    selected_lipids.append((header, -1, i))
            
            # Reset all values
            header_1, header_2, header_3 = "", "", ""
            lipid_1_index, lipid_2_index, lipid_3_index = -1, -1, -1
            class_name_badge_1, class_name_badge_2, class_name_badge_3 = "d-none mt-2", "d-none mt-2", "d-none mt-2"
            
            # Apply the found lipids to their original positions
            for lipid_name, lipid_idx, position in selected_lipids:
                if lipid_idx == -1:
                    continue  # Skip lipids not found in this slice
                    
                if position == 0:
                    header_1 = lipid_name
                    lipid_1_index = lipid_idx
                    class_name_badge_1 = "mt-2"
                elif position == 1:
                    header_2 = lipid_name
                    lipid_2_index = lipid_idx
                    class_name_badge_2 = "mt-2"
                elif position == 2:
                    header_3 = lipid_name
                    lipid_3_index = lipid_idx
                    class_name_badge_3 = "mt-2"
            
            # Return the updated values
            return (
                header_1,
                header_2,
                header_3,
                lipid_1_index,
                lipid_2_index,
                lipid_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
                [h for h in [header_1, header_2, header_3] if h]
            )

        # If lipids have been added from dropdown menu
        elif id_input == "page-6tris-dropdown-lipids":
            # Get the lipid name and structure
            if len(l_lipid_names[-1]) == 2:
                name, structure = l_lipid_names[-1].split(" ")
            else:   
                name = "_".join(l_lipid_names[-1].split(" ")[::2])
                structure = "_".join(l_lipid_names[-1].split(" ")[1::2])

            # Find lipid location
            l_lipid_loc = (
                data.get_annotations()
                .index[
                    (data.get_annotations()["name"] == name)
                    & (data.get_annotations()["structure"] == structure)
                    & (data.get_annotations()["slice"] == slice_index)
                ]
                .tolist()
            )
            
            if len(l_lipid_loc) < 1:
                l_lipid_loc = (
                    data.get_annotations()
                    .index[
                        (data.get_annotations()["name"] == name)
                        & (data.get_annotations()["structure"] == structure)
                    ]
                    .tolist()
                )[:1]

            if len(l_lipid_loc) > 0:
                lipid_index = l_lipid_loc[0]
                lipid_string = l_lipid_names[-1]

                # If lipid already exists, update its index
                if header_1 == lipid_string:
                    lipid_1_index = lipid_index
                elif header_2 == lipid_string:
                    lipid_2_index = lipid_index
                elif header_3 == lipid_string:
                    lipid_3_index = lipid_index
                # If it's a new lipid, fill the first available slot
                else:
                    if class_name_badge_1 == "d-none mt-2":
                        header_1 = lipid_string
                        lipid_1_index = lipid_index
                        class_name_badge_1 = "mt-2"
                    elif class_name_badge_2 == "d-none mt-2":
                        header_2 = lipid_string
                        lipid_2_index = lipid_index
                        class_name_badge_2 = "mt-2"
                    elif class_name_badge_3 == "d-none mt-2":
                        header_3 = lipid_string
                        lipid_3_index = lipid_index
                        class_name_badge_3 = "mt-2"
                    else:
                        logging.warning("More than 3 lipids have been selected")
                        return dash.no_update

                return (
                    header_1,
                    header_2,
                    header_3,
                    lipid_1_index,
                    lipid_2_index,
                    lipid_3_index,
                    class_name_badge_1,
                    class_name_badge_2,
                    class_name_badge_3,
                    l_lipid_names
                )

    return dash.no_update

# # TODO: This callback must be completely rewritten to be able to download the data
# @app.callback(
#     Output("page-6tris-download-data", "data"),
#     Input("page-6tris-download-data-button", "n_clicks"),
#     State("page-6tris-selected-lipid-1", "data"),
#     State("page-6tris-selected-lipid-2", "data"),
#     State("page-6tris-selected-lipid-3", "data"),
#     State("main-slider", "data"),
#     State("page-6tris-badge-input", "children"),
#     prevent_initial_call=True,
# )
# def page_6tris_download(
#     n_clicks,
#     lipid_1_index,
#     lipid_2_index,
#     lipid_3_index,
#     slice_index,
#     graph_input,
# ):
#     """This callback is used to generate and download the data in proper format."""

#     # Now displaying is lipid selection
#     if (
#         graph_input == "Lipids selected"
#         or graph_input == "Lipids selected"
#     ):
#         l_lipids_indexes = [
#             x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x is not None and x != -1
#         ]
#         # If lipids has been selected from the dropdown, filter them in the df and download them
#         if len(l_lipids_indexes) > 0:

#             def to_excel(bytes_io):
#                 xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
#                 data.get_annotations().iloc[l_lipids_indexes].to_excel(
#                     xlsx_writer, index=False, sheet_name="Selected lipids"
#                 )
#                 for i, index in enumerate(l_lipids_indexes):
#                     name = (
#                         data.get_annotations().iloc[index]["name"]
#                         + " "
#                         + data.get_annotations().iloc[index]["structure"]
#                     )

#                     # Need to clean name to use it as a sheet name
#                     name = name.replace(":", "").replace("/", "")
#                     lb = float(data.get_annotations().iloc[index]["min"]) - 10**-2
#                     hb = float(data.get_annotations().iloc[index]["max"]) + 10**-2
#                     x, y = figures.compute_spectrum_high_res(
#                         slice_index,
#                         lb,
#                         hb,
#                         plot=False,
#                         cache_flask=cache_flask,
#                     )
#                     df = pd.DataFrame.from_dict({"m/z": x, "Intensity": y})
#                     df.to_excel(xlsx_writer, index=False, sheet_name=name[:31])
#                 xlsx_writer.save()

#             return dcc.send_data_frame(to_excel, "my_lipid_selection.xlsx")

#     return dash.no_update

@app.callback(
    Output("page-6tris-rgb-switch", "checked"),
    Input("page-6tris-selected-lipid-1", "data"),
    Input("page-6tris-selected-lipid-2", "data"),
    Input("page-6tris-selected-lipid-3", "data"),
    State("page-6tris-rgb-switch", "checked"),
)
def page_6tris_auto_toggle_rgb(
    lipid_1_index, 
    lipid_2_index, 
    lipid_3_index, 
    current_rgb_state
):
    """This callback automatically toggles the RGB switch when multiple lipids are selected."""
        
    active_lipids = [x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x != -1]
    # Only turn on RGB automatically when going from 1 to multiple lipids
    # Don't turn it off when going from multiple to 1
    if len(active_lipids) > 1:
        return True
    return current_rgb_state  # Keep current state otherwise

@app.callback(
    Output("page-6tris-badge-gene-1", "children"),
    Output("page-6tris-badge-gene-2", "children"),
    Output("page-6tris-badge-gene-3", "children"),
    Output("page-6tris-selected-gene-1", "data"),
    Output("page-6tris-selected-gene-2", "data"),
    Output("page-6tris-selected-gene-3", "data"),
    Output("page-6tris-badge-gene-1", "class_name"),
    Output("page-6tris-badge-gene-2", "class_name"),
    Output("page-6tris-badge-gene-3", "class_name"),
    Output("page-6tris-gene-slider-1", "class_name"),
    Output("page-6tris-gene-slider-2", "class_name"),
    Output("page-6tris-gene-slider-3", "class_name"),
    Output("page-6tris-gene-slider-1", "min"),
    Output("page-6tris-gene-slider-1", "max"),
    Output("page-6tris-gene-slider-1", "value"),
    Output("page-6tris-gene-slider-1", "marks"),
    Output("page-6tris-gene-slider-2", "min"),
    Output("page-6tris-gene-slider-2", "max"),
    Output("page-6tris-gene-slider-2", "value"),
    Output("page-6tris-gene-slider-2", "marks"),
    Output("page-6tris-gene-slider-3", "min"),
    Output("page-6tris-gene-slider-3", "max"),
    Output("page-6tris-gene-slider-3", "value"),
    Output("page-6tris-gene-slider-3", "marks"),
    Output("page-6tris-dropdown-genes", "value"),
    Input("page-6tris-dropdown-genes", "value"),
    Input("page-6tris-badge-gene-1", "class_name"),
    Input("page-6tris-badge-gene-2", "class_name"),
    Input("page-6tris-badge-gene-3", "class_name"),
    Input("main-slider", "data"),
    State("page-6tris-selected-gene-1", "data"),
    State("page-6tris-selected-gene-2", "data"),
    State("page-6tris-selected-gene-3", "data"),
    State("page-6tris-badge-gene-1", "children"),
    State("page-6tris-badge-gene-2", "children"),
    State("page-6tris-badge-gene-3", "children"),
    State("main-brain", "value"),
)
def page_6tris_add_toast_selection_genes(
    l_gene_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    gene_1_index,
    gene_2_index,
    gene_3_index,
    header_1,
    header_2,
    header_3,
    brain_id,
):
    """This callback adds the selected gene to the selection."""
    logging.info("Entering function to update gene data")
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    
    # Get available genes for this slice
    available_genes = get_gene_options(slice_index)
    
    # Initialize default slider configurations
    default_slider_props = {
        "min": 0,
        "max": 1,
        "value": 0,
        "marks": [{"value": 0, "label": "Min"}, {"value": 1, "label": "Max"}]
    }
    
    # Calculate gene range functions for sliders
    def get_gene_slider_props(gene_name):
        if not gene_name or gene_name not in available_genes:
            return default_slider_props
        
        gene_values = df_genes[gene_name].values
        gene_values = gene_values[~np.isnan(gene_values)]
        
        if len(gene_values) == 0:
            return default_slider_props
        
        # min_val = np.min(gene_values)
        # max_val = np.max(gene_values)
        p01 = np.percentile(gene_values, 1)
        p99 = np.percentile(gene_values, 99)
        
        # Create 10 steps
        steps = np.round(np.linspace(p01, p99, 10), 2)
        
        marks = [
            {"value": p01, "label": f"{p01:.2f}"},
            {"value": p99, "label": f"{p99:.2f}"}
        ]
        
        return {
            "min": p01,
            "max": p99,
            "value": p01,  # start with minimum value (no filtering)
            "marks": marks
        }
    
    # Initialize with no genes if no selection exists
    if (l_gene_names is None) or (isinstance(l_gene_names, list) and len(l_gene_names) == 0):
        return (
            "", "", "",  # badge texts
            -1, -1, -1,  # gene indices
            "d-none mt-2", "d-none mt-4", "d-none mt-4",  # badge classes
            "d-none mt-2", "d-none mt-2", "d-none mt-2",  # slider classes
            *[prop for _ in range(3) for prop in default_slider_props.values()],  # slider props x3
            []  # dropdown value
        )
    # If l_gene_names is a non-empty list, initialize badges, indices, and sliders for those genes
    if isinstance(l_gene_names, list) and len(l_gene_names) > 0:
        # Reset all slots
        header_1, header_2, header_3 = "", "", ""
        gene_1_index, gene_2_index, gene_3_index = -1, -1, -1
        class_name_badge_1, class_name_badge_2, class_name_badge_3 = "d-none mt-2", "d-none mt-4", "d-none mt-4"
        class_name_slider_1, class_name_slider_2, class_name_slider_3 = "d-none mt-2", "d-none mt-2", "d-none mt-2"
        slider_props = [default_slider_props, default_slider_props, default_slider_props]
        for idx, gene_name in enumerate(l_gene_names):
            gene_idx = available_genes.index(gene_name) if gene_name in available_genes else -1
            if idx == 0 and gene_idx != -1:
                header_1 = gene_name
                gene_1_index = gene_idx
                class_name_badge_1 = "mt-2"
                class_name_slider_1 = "mt-2"
                slider_props[0] = get_gene_slider_props(gene_name)
            elif idx == 1 and gene_idx != -1:
                header_2 = gene_name
                gene_2_index = gene_idx
                class_name_badge_2 = "mt-4"
                class_name_slider_2 = "mt-2"
                slider_props[1] = get_gene_slider_props(gene_name)
            elif idx == 2 and gene_idx != -1:
                header_3 = gene_name
                gene_3_index = gene_idx
                class_name_badge_3 = "mt-4"
                class_name_slider_3 = "mt-2"
                slider_props[2] = get_gene_slider_props(gene_name)
        return (
            header_1, header_2, header_3,
            gene_1_index, gene_2_index, gene_3_index,
            class_name_badge_1, class_name_badge_2, class_name_badge_3,
            class_name_slider_1, class_name_slider_2, class_name_slider_3,
            slider_props[0]["min"], slider_props[0]["max"], slider_props[0]["value"], slider_props[0]["marks"],
            slider_props[1]["min"], slider_props[1]["max"], slider_props[1]["value"], slider_props[1]["marks"],
            slider_props[2]["min"], slider_props[2]["max"], slider_props[2]["value"], slider_props[2]["marks"],
            l_gene_names
        )

    return dash.no_update

# Add a callback to update the gene threshold values
@app.callback(
    Output("page-6tris-gene-threshold-1", "data"),
    Output("page-6tris-gene-threshold-2", "data"),
    Output("page-6tris-gene-threshold-3", "data"),
    Input("page-6tris-gene-slider-1", "value"),
    Input("page-6tris-gene-slider-2", "value"),
    Input("page-6tris-gene-slider-3", "value"),
)
def update_gene_thresholds(threshold_1, threshold_2, threshold_3):
    """Updates the gene threshold store values when sliders change."""
    return threshold_1, threshold_2, threshold_3

# clientside_callback(
#     """
#     function(n_clicks){
#         if(n_clicks > 0){
#             domtoimage.toBlob(document.getElementById('page-6tris-graph-heatmap-mz-selection'))
#                 .then(function (blob) {
#                     window.saveAs(blob, 'lipid_selection_plot.png');
#                 }
#             );
#         }
#     }
#     """,
#     Output("page-6tris-download-image-button", "n_clicks"),
#     Input("page-6tris-download-image-button", "n_clicks"),
# )
# """This clientside callback is used to download the current heatmap."""

# Use clientside callback for tutorial step updates
app.clientside_callback(
    """
    function(start, next1, next2, next3, next4, next5, next6, finish,
             prev1, prev2, prev3, prev4, prev5, prev6, prev7,
             close1, close2, close3, close4, close5, close6, close7) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered.length) {
            return window.dash_clientside.no_update;
        }
        const trigger_id = ctx.triggered[0].prop_id.split('.')[0];

        // Close (×) always resets to 0
        if (trigger_id.startsWith('lipigene-tutorial-close-')) {
            return 0;
        }

        // Start
        if (trigger_id === 'lipigene-start-tutorial-btn' && start) {
            return 1;
        }

        // Next buttons
        if (trigger_id === 'lipigene-tutorial-next-1' && next1) { return 2; }
        if (trigger_id === 'lipigene-tutorial-next-2' && next2) { return 3; }
        if (trigger_id === 'lipigene-tutorial-next-3' && next3) { return 4; }
        if (trigger_id === 'lipigene-tutorial-next-4' && next4) { return 5; }
        if (trigger_id === 'lipigene-tutorial-next-5' && next5) { return 6; }
        if (trigger_id === 'lipigene-tutorial-next-6' && next6) { return 7; }
        if (trigger_id === 'lipigene-tutorial-finish' && finish) { return 0; }

        // Previous buttons
        if (trigger_id === 'lipigene-tutorial-prev-2' && prev2) { return 1; }
        if (trigger_id === 'lipigene-tutorial-prev-3' && prev3) { return 2; }
        if (trigger_id === 'lipigene-tutorial-prev-4' && prev4) { return 3; }
        if (trigger_id === 'lipigene-tutorial-prev-5' && prev5) { return 4; }
        if (trigger_id === 'lipigene-tutorial-prev-6' && prev6) { return 5; }
        if (trigger_id === 'lipigene-tutorial-prev-7' && prev7) { return 6; }

        return window.dash_clientside.no_update;
    }
    """,
    Output("lipigene-tutorial-step", "data"),

    [Input("lipigene-start-tutorial-btn", "n_clicks"),
     Input("lipigene-tutorial-next-1", "n_clicks"),
     Input("lipigene-tutorial-next-2", "n_clicks"),
     Input("lipigene-tutorial-next-3", "n_clicks"),
     Input("lipigene-tutorial-next-4", "n_clicks"),
     Input("lipigene-tutorial-next-5", "n_clicks"),
     Input("lipigene-tutorial-next-6", "n_clicks"),
     Input("lipigene-tutorial-finish", "n_clicks"),
     Input("lipigene-tutorial-prev-1", "n_clicks"),
     Input("lipigene-tutorial-prev-2", "n_clicks"),
     Input("lipigene-tutorial-prev-3", "n_clicks"),
     Input("lipigene-tutorial-prev-4", "n_clicks"),
     Input("lipigene-tutorial-prev-5", "n_clicks"),
     Input("lipigene-tutorial-prev-6", "n_clicks"),
     Input("lipigene-tutorial-prev-7", "n_clicks"),
     Input("lipigene-tutorial-close-1", "n_clicks"),
     Input("lipigene-tutorial-close-2", "n_clicks"),
     Input("lipigene-tutorial-close-3", "n_clicks"),
     Input("lipigene-tutorial-close-4", "n_clicks"),
     Input("lipigene-tutorial-close-5", "n_clicks"),
     Input("lipigene-tutorial-close-6", "n_clicks"),
     Input("lipigene-tutorial-close-7", "n_clicks")],
    prevent_initial_call=True,
)

# Use clientside callback for popover visibility
app.clientside_callback(
    """
    function(step) {
        if (step === undefined || step === null) {
            return [false, false, false, false, false, false, false];
        }
        return [
            step === 1,
            step === 2,
            step === 3,
            step === 4,
            step === 5,
            step === 6,
            step === 7,
        ];
    }
    """,
    [Output(f"lipigene-tutorial-popover-{i}", "is_open") for i in range(1, 8)],
    Input("lipigene-tutorial-step", "data"),
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
    Output("lipigene-tutorial-completed", "data"),
    Input("lipigene-tutorial-finish", "n_clicks"),
    prevent_initial_call=True,
)