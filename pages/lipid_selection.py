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
from app import app, figures, data, cache_flask, atlas, grid_data

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
                # Add a store component to hold the slider style
                dcc.Store(id="page-2-main-slider-style", data={"display": "block"}),

                dcc.Store(id="lipid-tutorial-step", data=0),
                dcc.Store(id="lipid-tutorial-completed", storage_type="local", data=False),

                # Add tutorial button under welcome text
                html.Div(
                    id="lipid-start-tutorial-target",
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
                            id="lipid-start-tutorial-btn",
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
                            id="page-2-graph-heatmap-mz-selection",
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
                                "height": "100%",
                                "width": "100%",
                                "position": "absolute",
                                "left": 0,
                                "top": 0,
                                "bottom": 0,
                                "right": 0,
                                "background-color": "#1d1c1f",
                            },
                            figure=figures.compute_heatmap_per_lipid(
                                slice_index,
                                "HexCer 42:2;O2",
                                cache_flask=cache_flask,
                            ),
                        ),
                        # Allen Brain Atlas switch (independent)
                        html.Div(
                            id="page-2-annotations-container",
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
                                    id="page-2-toggle-annotations",
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
                                            id="page-2-dropdown-lipids",
                                            data=data.return_lipid_options(),
                                            value=['HexCer 42:2;O2'],
                                            searchable=True,
                                            nothingFound="No lipid found",
                                            radius="md",
                                            # size="xs",
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
                                            id="page-2-rgb-group",
                                            style={
                                                "display": "flex", 
                                                "alignItems": "center", 
                                                "marginLeft": "15px"
                                            },
                                            children=[
                                                dmc.Switch(
                                                    id="page-2-rgb-switch",
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
                        # Sections mode control
                        dmc.SegmentedControl(
                            id="page-2-sections-mode",
                            value="one",
                            data=[
                                {"value": "one", "label": "One section"},
                                {"value": "all", "label": "All sections"},
                            ],
                            color="cyan",
                            disabled=True,
                            size="xs",
                            style={
                                "position": "absolute",
                                "left": "1%",
                                "top": "9em",
                                "width": "20em",
                                "border": "1px solid rgba(255, 255, 255, 0.1)",
                                "borderRadius": "4px",
                            }
                        ),
                        dmc.Text(
                            id="page-2-badge-input",
                            children="Now displaying:",
                            class_name="position-absolute",
                            style={"right": "1%", "top": "1em"},
                        ),
                        dmc.Badge(
                            id="page-2-badge-lipid-1",
                            children="name-lipid-1",
                            color="red",
                            variant="filled",
                            class_name="d-none",
                            style={"right": "1%", "top": "4em"},
                        ),
                        dmc.Badge(
                            id="page-2-badge-lipid-2",
                            children="name-lipid-2",
                            color="teal",
                            variant="filled",
                            class_name="d-none",
                            style={"right": "1%", "top": "6em"},
                        ),
                        dmc.Badge(
                            id="page-2-badge-lipid-3",
                            children="name-lipid-3",
                            color="blue",
                            variant="filled",
                            class_name="d-none",
                            style={"right": "1%", "top": "8em"},
                        ),
                        dmc.Text(
                            "",
                            id="page-2-graph-hover-text",
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
                        dmc.Group(
                            position="right",
                            direction="row",
                            style={
                                "right": "1rem",
                                "bottom": "0.5rem",
                                "position": "fixed",
                                "z-index": 1000,
                            },
                            class_name="position-absolute",
                            spacing=0,
                            children=[
                                dmc.Button(
                                    children="Download data",
                                    id="page-2-download-data-button",
                                    variant="filled",
                                    disabled=False,
                                    color="cyan",
                                    radius="md",
                                    size="xs",
                                    compact=False,
                                    loading=False,
                                    class_name="mt-1",
                                    style={"margin-right": "0.5rem"},
                                ),
                                dmc.Button(
                                    children="Download image",
                                    id="page-2-download-image-button",
                                    variant="filled",
                                    disabled=False,
                                    color="cyan",
                                    radius="md",
                                    size="xs",
                                    compact=False,
                                    loading=False,
                                    class_name="mt-1",
                                ),
                            ],
                        ),
                        dcc.Download(id="page-2-download-data"),

                        # Tutorial Popovers with adjusted positions
                        dbc.Popover(
                            [
                                dbc.PopoverHeader(
                                    "Lipid Exploration",
                                    style={"fontWeight": "bold"}
                                ),
                                dbc.PopoverBody(
                                    [
                                        html.P(
                                            "Welcome to Lipid Exploration. This view lets you examine how lipid distributions vary across mouse brain sections. You can use anatomical overlays from the Allen Brain Atlas to better interpret spatial patterns and identify regional features.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        dbc.Button("Next", id="lipid-tutorial-next-1", color="primary", size="sm", className="float-end")
                                    ]
                                ),
                            ],
                            id="lipid-tutorial-popover-1",
                            target="lipid-start-tutorial-target",
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
                                dbc.PopoverHeader("Choose Up to 3 Lipids", style={"fontWeight": "bold"}),
                                dbc.PopoverBody(
                                    [
                                        html.P(
                                            "Select up to three lipids from the 172 confidently annotated. Lipids are grouped by family, and some appear under a “Multiple matches” category if they matched different molecules.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        dbc.Button("Next", id="lipid-tutorial-next-2", color="primary", size="sm", className="float-end")
                                    ]
                                ),
                            ],
                            id="lipid-tutorial-popover-2",
                            target="page-2-dropdown-lipids",  # dropdown menu
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
                                dbc.PopoverHeader("Color Map Options", style={"fontWeight": "bold"}),
                                dbc.PopoverBody(
                                    [
                                        html.P(
                                            "When one lipid is selected, you can choose to display it using either the viridis colormap or the red channel of the RGB space. If two or three lipids are selected, the visualization automatically switches to RGB mode, where each lipid is mapped to a different channel: red for the first, green for the second, and blue for the third.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        dbc.Button("Next", id="lipid-tutorial-next-3", color="primary", size="sm", className="float-end")
                                    ]
                                ),
                            ],
                            id="lipid-tutorial-popover-3",
                            target="page-2-rgb-switch",  # rgb switch
                            placement="bottom",
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
                                dbc.PopoverHeader("View All Slices at Once", style={"fontWeight": "bold"}),
                                dbc.PopoverBody(
                                    [
                                        html.P(
                                            "You can switch to a view that shows all brain sections at once. In this mode, only the first selected lipid will be displayed to keep the view clean and interpretable.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        dbc.Button("Next", id="lipid-tutorial-next-4", color="primary", size="sm", className="float-end")
                                    ]
                                ),
                            ],
                            id="lipid-tutorial-popover-4",
                            target="page-2-sections-mode",  # sections mode switch
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
                                dbc.PopoverHeader("Overlay Anatomical Contours", style={"fontWeight": "bold"}),
                                dbc.PopoverBody(
                                    [
                                        html.P(
                                            "You can enable the Allen Brain Atlas annotations to overlay anatomical labels directly on the slices. This helps you navigate the brain and interpret lipid signals in their biological context.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        dbc.Button("Next", id="lipid-tutorial-next-5", color="primary", size="sm", className="float-end")
                                    ]
                                ),
                            ],
                            id="lipid-tutorial-popover-5",
                            target="page-2-toggle-annotations",  # annotations switch
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
                                dbc.PopoverHeader("Navigate Along Brain Anterior-Posterior Axis", style={"fontWeight": "bold"}),
                                dbc.PopoverBody(
                                    [
                                        html.P(
                                            "In the single-section view, you can navigate through the brain by selecting different slices along the rostro-caudal (front-to-back) axis. This allows detailed inspection of lipid signals at specific anatomical levels.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        dbc.Button("Next", id="lipid-tutorial-next-6", color="primary", size="sm", className="float-end")
                                    ]
                                ),
                            ],
                            id="lipid-tutorial-popover-6",
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
                                dbc.PopoverHeader("Choose Experimental Condition", style={"fontWeight": "bold"}),
                                dbc.PopoverBody(
                                    [
                                        html.P(
                                            "You can choose which mouse brain to view. Brain1 is the reference brain used for the atlas, but you can also explore Brain2, control male and female brains, and pregnant brains to see how lipid distributions differ across biological conditions.",
                                            style={"color": "#333", "marginBottom": "15px"}
                                        ),
                                        dbc.Button("Finish", id="lipid-tutorial-finish", color="success", size="sm", className="float-end")
                                    ]
                                ),
                            ],
                            id="lipid-tutorial-popover-7",
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
        ),
    )

    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================

@app.callback(
    Output("page-2-graph-hover-text", "children"),
    Input("page-2-graph-heatmap-mz-selection", "hoverData"),
    Input("main-slider", "data"),
)
def page_2_hover(hoverData, slice_index):
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
    Output("page-2-graph-heatmap-mz-selection", "figure"),
    Output("page-2-badge-input", "children"),

    Input("main-slider", "data"),
    Input("page-2-selected-lipid-1", "data"),
    Input("page-2-selected-lipid-2", "data"),
    Input("page-2-selected-lipid-3", "data"),
    Input("page-2-rgb-switch", "checked"),
    Input("page-2-sections-mode", "value"),
    Input("main-brain", "value"),
    Input("page-2-toggle-annotations", "checked"),

    State("page-2-badge-input", "children"),
)
def page_2_plot_graph_heatmap_mz_selection(
    slice_index,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    rgb_mode,
    sections_mode,
    brain_id,
    annotations_checked,
    graph_input,
):
    """This callback plots the heatmap of the selected lipid(s)."""
    logging.info("Entering function to plot heatmap or RGB depending on lipid selection")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    
    overlay = data.get_aba_contours(slice_index) if annotations_checked else None

    # Handle annotations toggle separately to preserve figure state
    if id_input == "page-2-toggle-annotations":
        if lipid_1_index >= 0 or lipid_2_index >= 0 or lipid_3_index >= 0:
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
        
            # If all sections view is requested, only use first lipid
            if sections_mode == "all":
                active_lipids = [name for name in ll_lipid_names if name is not None]
                first_lipid = active_lipids[0] if active_lipids else "HexCer 42:2;O2"
                image = grid_data.retrieve_grid_image(
                    lipid=first_lipid,
                    sample=brain_id
                )
                return(figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay),
                        "Now displaying:")
            
            if rgb_mode and sections_mode != "all":
                return (
                    figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lipid_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    ),
                    "Now displaying:",
                )
            else:
                # Check that only one lipid is selected for colormap mode
                active_lipids = [name for name in ll_lipid_names if name is not None]
                if len(active_lipids) == 1:
                    image = figures.compute_image_per_lipid(
                        slice_index,
                        RGB_format=False,
                        lipid_name=active_lipids[0],
                        cache_flask=cache_flask,
                    )
                    return (
                        figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                        ),
                        "Now displaying:",
                    )
                else:
                    # If multiple lipids and not in RGB mode, force RGB mode (except in all sections mode)
                    if sections_mode != "all":
                        return (
                            figures.compute_rgb_image_per_lipid_selection(
                                slice_index,
                                ll_lipid_names=ll_lipid_names,
                                cache_flask=cache_flask,
                                overlay=overlay,
                            ),
                            "Now displaying:",
                        )
                    else:
                        # In all sections mode, use only first lipid
                        first_lipid = active_lipids[0] if active_lipids else "HexCer 42:2;O2"
                        image = grid_data.retrieve_grid_image(
                            lipid=first_lipid,
                            sample=brain_id
                        )
                        return(figures.build_lipid_heatmap_from_image(
                                    image, 
                                    return_base64_string=False,
                                    overlay=overlay),
                                "Now displaying:")

        return dash.no_update

    # If a lipid selection has been done
    if (
        id_input == "page-2-selected-lipid-1"
        or id_input == "page-2-selected-lipid-2"
        or id_input == "page-2-selected-lipid-3"
        or id_input == "page-2-rgb-switch"
        or id_input == "page-2-sections-mode"
        or id_input == "main-brain"
        or id_input == "main-slider"
    ):
        if lipid_1_index >= 0 or lipid_2_index >= 0 or lipid_3_index >= 0:
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

            # If all sections view is requested
            if sections_mode == "all":
                active_lipids = [name for name in ll_lipid_names if name is not None]
                # Use first available lipid for all sections view
                first_lipid = active_lipids[0] if active_lipids else "HexCer 42:2;O2"
                image = grid_data.retrieve_grid_image(
                    lipid=first_lipid,
                    sample=brain_id
                )
                
                return(figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay),
                        "Now displaying:")
            
            # Handle normal display mode (RGB or colormap)
            else:
                active_lipids = [name for name in ll_lipid_names if name is not None]
                if rgb_mode:
                    return (
                        figures.compute_rgb_image_per_lipid_selection(
                            slice_index,
                            ll_lipid_names=ll_lipid_names,
                            cache_flask=cache_flask,
                            overlay=overlay,
                        ),
                        "Now displaying:",
                    )
                else:
                    # If not in RGB mode, use first lipid only
                    first_lipid = active_lipids[0] if active_lipids else "HexCer 42:2;O2"
                    image = figures.compute_image_per_lipid(
                        slice_index,
                        RGB_format=False,
                        lipid_name=first_lipid,
                        cache_flask=cache_flask,
                    )
                    return (
                        figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                        ),
                        "Now displaying:",
                    )
        elif (
            id_input == "main-slider" and graph_input == "Now displaying:"
        ):
            logging.info(f"No lipid has been selected, the current lipid is HexCer 42:2;O2 and the slice is {slice_index}")
            return (
                figures.compute_heatmap_per_lipid(slice_index, 
                                                "HexCer 42:2;O2",
                                                cache_flask=cache_flask,
                                                overlay=overlay),
                "Now displaying:",
            )
        else:
            # No lipid has been selected
            logging.info(f"No lipid has been selected, the current lipid is HexCer 42:2;O2 and the slice is {slice_index}")
            return (
                figures.compute_heatmap_per_lipid(slice_index, 
                                                "HexCer 42:2;O2",
                                                cache_flask=cache_flask,
                                                overlay=overlay),
                "Now displaying:",
            )

    # If no trigger, the page has just been loaded, so load new figure with default parameters
    else:
        return (
            figures.compute_heatmap_per_lipid(slice_index, 
                                            "HexCer 42:2;O2",
                                            cache_flask=cache_flask,
                                            overlay=overlay),
            "Now displaying:",
        )

@app.callback(
    Output("page-2-badge-lipid-1", "children"),
    Output("page-2-badge-lipid-2", "children"),
    Output("page-2-badge-lipid-3", "children"),
    Output("page-2-selected-lipid-1", "data"),
    Output("page-2-selected-lipid-2", "data"),
    Output("page-2-selected-lipid-3", "data"),
    Output("page-2-badge-lipid-1", "class_name"),
    Output("page-2-badge-lipid-2", "class_name"),
    Output("page-2-badge-lipid-3", "class_name"),
    Output("page-2-dropdown-lipids", "value"),
    Input("page-2-dropdown-lipids", "value"),
    Input("page-2-badge-lipid-1", "class_name"),
    Input("page-2-badge-lipid-2", "class_name"),
    Input("page-2-badge-lipid-3", "class_name"),
    Input("main-slider", "data"),
    Input("page-2-sections-mode", "value"),
    Input("page-2-rgb-switch", "checked"),
    State("page-2-selected-lipid-1", "data"),
    State("page-2-selected-lipid-2", "data"),
    State("page-2-selected-lipid-3", "data"),
    State("page-2-badge-lipid-1", "children"),
    State("page-2-badge-lipid-2", "children"),
    State("page-2-badge-lipid-3", "children"),
    State("main-brain", "value"),
)
def page_2_add_toast_selection(
    l_lipid_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    sections_mode,
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
    if len(id_input) == 0 or (id_input == "page-2-dropdown-lipids" and l_lipid_names is None):
        default_lipid = "SM 34:1;O2"
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
            class_name_badge_1 = "position-absolute"
            return header_1, "", "", lipid_1_index, -1, -1, class_name_badge_1, "d-none", "d-none", [default_lipid]
        else:
            return "", "", "", -1, -1, -1, "d-none", "d-none", "d-none", []

    # If RGB is turned off or sections mode is "all", keep only the first lipid
    if (id_input == "page-2-rgb-switch" and not rgb_switch) or (id_input == "page-2-sections-mode" and sections_mode == "all"):
        active_lipids = []
        if header_1 and lipid_1_index != -1:
            active_lipids.append((header_1, lipid_1_index))
        elif header_2 and lipid_2_index != -1:
            active_lipids.append((header_2, lipid_2_index))
        elif header_3 and lipid_3_index != -1:
            active_lipids.append((header_3, lipid_3_index))
            
        if active_lipids:
            first_lipid, first_index = active_lipids[0]
            return (first_lipid, "", "", first_index, -1, -1, 
                    "position-absolute", "d-none", "d-none", [first_lipid])
        return dash.no_update

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
        class_name_badge_1, class_name_badge_2, class_name_badge_3 = "d-none", "d-none", "d-none"
        
        # Fill slots in order with remaining lipids
        # If in all sections mode, only fill the first slot
        if sections_mode == "all" and remaining_lipids:
            header_1 = remaining_lipids[0][0]
            lipid_1_index = remaining_lipids[0][1]
            class_name_badge_1 = "position-absolute"
            return (
                header_1,
                "",
                "",
                lipid_1_index,
                -1,
                -1,
                class_name_badge_1,
                "d-none",
                "d-none",
                [header_1]
            )
        else:
            for idx, (lipid_name, lipid_idx) in enumerate(remaining_lipids):
                if idx == 0:
                    header_1 = lipid_name
                    lipid_1_index = lipid_idx
                    class_name_badge_1 = "position-absolute"
                elif idx == 1:
                    header_2 = lipid_name
                    lipid_2_index = lipid_idx
                    class_name_badge_2 = "position-absolute"
                elif idx == 2:
                    header_3 = lipid_name
                    lipid_3_index = lipid_idx
                    class_name_badge_3 = "position-absolute"
                
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
    if (id_input == "page-2-dropdown-lipids" and l_lipid_names is not None) or id_input == "main-slider":
        # If a new slice has been selected
        if id_input == "main-slider":
            # Update indices for existing lipids
            for header in [header_1, header_2, header_3]:
                if header and len(header.split(" ")) == 2:
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
                
                l_lipid_loc = [
                    l_lipid_loc_temp[i]
                    for i, x in enumerate(
                        data.get_annotations().iloc[l_lipid_loc_temp]["slice"] == slice_index
                    )
                    if x
                ]
                
                lipid_index = l_lipid_loc[0] if len(l_lipid_loc) > 0 else -1

                if header_1 == header:
                    lipid_1_index = lipid_index
                elif header_2 == header:
                    lipid_2_index = lipid_index
                elif header_3 == header:
                    lipid_3_index = lipid_index

            # If in all sections mode, keep only first lipid
            if sections_mode == "all":
                current_lipids = []
                if header_1:
                    current_lipids.append(header_1)
                elif header_2:
                    current_lipids.append(header_2)
                elif header_3:
                    current_lipids.append(header_3)
                    
                if current_lipids:
                    return (
                        current_lipids[0],
                        "",
                        "",
                        lipid_1_index if header_1 else (lipid_2_index if header_2 else lipid_3_index),
                        -1,
                        -1,
                        "position-absolute",
                        "d-none",
                        "d-none",
                        current_lipids[:1]
                    )

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
        elif id_input == "page-2-dropdown-lipids":
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

                # If in all sections mode, only allow one lipid
                if sections_mode == "all":
                    header_1 = lipid_string
                    lipid_1_index = lipid_index
                    class_name_badge_1 = "position-absolute"
                    return (
                        header_1,
                        "",
                        "",
                        lipid_1_index,
                        -1,
                        -1,
                        class_name_badge_1,
                        "d-none",
                        "d-none",
                        [header_1]
                    )

                # If lipid already exists, update its index
                if header_1 == lipid_string:
                    lipid_1_index = lipid_index
                elif header_2 == lipid_string:
                    lipid_2_index = lipid_index
                elif header_3 == lipid_string:
                    lipid_3_index = lipid_index
                # If it's a new lipid, fill the first available slot
                else:
                    if class_name_badge_1 == "d-none":
                        header_1 = lipid_string
                        lipid_1_index = lipid_index
                        class_name_badge_1 = "position-absolute"
                    elif class_name_badge_2 == "d-none":
                        header_2 = lipid_string
                        lipid_2_index = lipid_index
                        class_name_badge_2 = "position-absolute"
                    elif class_name_badge_3 == "d-none":
                        header_3 = lipid_string
                        lipid_3_index = lipid_index
                        class_name_badge_3 = "position-absolute"
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
#     Output("page-2-download-data", "data"),
#     Input("page-2-download-data-button", "n_clicks"),
#     State("page-2-selected-lipid-1", "data"),
#     State("page-2-selected-lipid-2", "data"),
#     State("page-2-selected-lipid-3", "data"),
#     State("main-slider", "data"),
#     State("page-2-badge-input", "children"),
#     prevent_initial_call=True,
# )
# def page_2_download(
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
#         graph_input == "Now displaying:"
#         or graph_input == "Now displaying:"
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
    Output("page-2-rgb-switch", "checked"),
    Input("page-2-selected-lipid-1", "data"),
    Input("page-2-selected-lipid-2", "data"),
    Input("page-2-selected-lipid-3", "data"),
    Input("page-2-sections-mode", "value"),
    State("page-2-rgb-switch", "checked"),
)
def page_2_auto_toggle_rgb(lipid_1_index, lipid_2_index, lipid_3_index, sections_mode, current_rgb_state):
    """This callback automatically toggles the RGB switch when multiple lipids are selected."""
    # Force RGB off when in all sections mode
    if sections_mode == "all":
        return False
        
    active_lipids = [x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x != -1]
    # Only turn on RGB automatically when going from 1 to multiple lipids
    # Don't turn it off when going from multiple to 1
    if len(active_lipids) > 1:
        return True
    return current_rgb_state  # Keep current state otherwise

@app.callback(
    Output("page-2-sections-mode", "disabled"),
    Input("page-2-selected-lipid-1", "data"),
    Input("page-2-selected-lipid-2", "data"),
    Input("page-2-selected-lipid-3", "data"),
)
def page_2_active_sections_control(lipid_1_index, lipid_2_index, lipid_3_index):
    """This callback enables/disables the sections mode control based on lipid selection."""
    # Get the current lipid selection
    active_lipids = [x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x != -1]
    # Enable control if at least one lipid is selected
    return len(active_lipids) == 0

clientside_callback(
    """
    function(n_clicks){
        if(n_clicks > 0){
            domtoimage.toBlob(document.getElementById('page-2-graph-heatmap-mz-selection'))
                .then(function (blob) {
                    window.saveAs(blob, 'lipid_selection_plot.png');
                }
            );
        }
    }
    """,
    Output("page-2-download-image-button", "n_clicks"),
    Input("page-2-download-image-button", "n_clicks"),
)
"""This clientside callback is used to download the current heatmap."""

@app.callback(
    Output("page-2-main-slider-style", "data"),
    Output("page-2-graph-hover-text", "style"),
    Output("page-2-annotations-container", "style"),
    Input("page-2-sections-mode", "value"),
)
def page_2_toggle_elements_visibility(sections_mode):
    """This callback toggles the visibility of elements based on sections mode."""
    if sections_mode == "all":
        # Hide elements
        return {"display": "none"}, {"display": "none"}, {"display": "none"}
    else:
        # Show elements
        return (
            {"display": "block"}, 
            {
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
            {
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
            }
        )

# Add a separate callback just for the RGB group visibility
@app.callback(
    Output("page-2-rgb-group", "style"),
    Input("page-2-sections-mode", "value"),
)
def page_2_toggle_rgb_group_visibility(sections_mode):
    """Controls the visibility of the RGB group."""
    if sections_mode == "all":
        return {"display": "none"}
    else:
        return {"display": "flex", "alignItems": "center", "marginLeft": "15px"}

# A callback that writes the "hide" or "show" decision into page-2-hide-store:
@app.callback(
    Output("page-2-hide-store", "data"),
    Input("page-2-sections-mode", "value"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def compute_page2_hide(lipid_sections_mode, pathname):
    # Only take action if we're really on /lipid-selection
    if pathname == "/lipid-selection":
        return "d-none" if (lipid_sections_mode == "all") else ""
    # If we're not on that page, leave the store unchanged (or send back "")
    return ""


# Use clientside callback for tutorial step updates
app.clientside_callback(
    """
    function(start, next1, next2, next3, next4, next5, next6, finish) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered.length) {
            return window.dash_clientside.no_update;
        }
        const trigger_id = ctx.triggered[0].prop_id.split('.')[0];
        if (trigger_id === 'lipid-start-tutorial-btn' && start) {
            return 1;
        } else if (trigger_id === 'lipid-tutorial-next-1' && next1) {
            return 2;
        } else if (trigger_id === 'lipid-tutorial-next-2' && next2) {
            return 3;
        } else if (trigger_id === 'lipid-tutorial-next-3' && next3) {
            return 4;
        } else if (trigger_id === 'lipid-tutorial-next-4' && next4) {
            return 5;
        } else if (trigger_id === 'lipid-tutorial-next-5' && next5) {
            return 6;
        } else if (trigger_id === 'lipid-tutorial-next-6' && next6) {
            return 7;
        } else if (trigger_id === 'lipid-tutorial-finish' && finish) {
            return 0;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("lipid-tutorial-step", "data"),
    [Input("lipid-start-tutorial-btn", "n_clicks"),
     Input("lipid-tutorial-next-1", "n_clicks"),
     Input("lipid-tutorial-next-2", "n_clicks"),
     Input("lipid-tutorial-next-3", "n_clicks"),
     Input("lipid-tutorial-next-4", "n_clicks"),
     Input("lipid-tutorial-next-5", "n_clicks"),
     Input("lipid-tutorial-next-6", "n_clicks"),
     Input("lipid-tutorial-finish", "n_clicks")],
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
    [Output(f"lipid-tutorial-popover-{i}", "is_open") for i in range(1, 8)],
    Input("lipid-tutorial-step", "data"),
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
    Output("lipid-tutorial-completed", "data"),
    Input("lipid-tutorial-finish", "n_clicks"),
    prevent_initial_call=True,
)