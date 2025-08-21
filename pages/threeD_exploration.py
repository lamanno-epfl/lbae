# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to explore and compare lipid expression in three-dimensional
brain structures.
- Adds missing stores and alert component
- Fixes region-3 delete bug
- Simplifies lipid dropdown refresh (no dead "add lipid" button dependency)
- Makes "Display" button require at least one region AND a lipid
- Only reveals 3D view when a lipid is selected
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html, clientside_callback
import logging
import dash_draggable
from dash.dependencies import Input, Output, State
import numpy as np
import dash
import dash_mantine_components as dmc
import copy

# LBAE imports
from app import app, data, figures, atlas, cache_flask
# import os
# os.environ['OMP_NUM_THREADS'] = '1'

# ==================================================================================================
# --- Layout
# ==================================================================================================


def return_layout(basic_config, slice_index):
    page = html.Div(
        # This style is needed for keeping background color when reducing image size
        style={
            "position": "fixed",
            "top": "0",
            "right": "0",
            "bottom": "0",
            "left": "6rem",
            "background-color": "#1d1c1f",
            "overflow": "auto",
        },
        children=[
            # --- Needed state stores (were missing) ---
            dcc.Store(id="page-4-last-selected-regions", data=[]),
            dcc.Store(id="page-4-selected-region-1", data=""),
            dcc.Store(id="page-4-selected-region-2", data=""),
            dcc.Store(id="page-4-selected-region-3", data=""),

            # React grid for nice responsivity pattern
            dash_draggable.ResponsiveGridLayout(
                id="draggable",
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
                    # x sets the lateral position, y the vertical one, w is in columns (whose size
                    # depends on the dimension), h is in rows (30px)
                    # nb columns go 12->12->10->6->4->2
                    "xxl": [
                        {"i": "page-4-card-region-selection", "x": 3, "y": 0, "w": 6, "h": 16},
                        {"i": "page-4-card-lipid-selection", "x": 3, "y": 16, "w": 6, "h": 10},
                    ],
                    "lg": [
                        {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 12, "h": 15},
                        {"i": "page-4-card-lipid-selection", "x": 0, "y": 14, "w": 12, "h": 10},
                    ],
                    "md": [
                        {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 10, "h": 15},
                        {"i": "page-4-card-lipid-selection", "x": 6, "y": 0, "w": 10, "h": 12},
                    ],
                    "sm": [
                        {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 6, "h": 19},
                        {"i": "page-4-card-lipid-selection", "x": 0, "y": 19, "w": 6, "h": 11},
                    ],
                    "xs": [
                        {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 4, "h": 14},
                        {"i": "page-4-card-lipid-selection", "x": 0, "y": 0, "w": 4, "h": 11},
                    ],
                    "xxs": [
                        {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 2, "h": 9},
                        {"i": "page-4-card-lipid-selection", "x": 0, "y": 0, "w": 2, "h": 10},
                    ],
                },
                children=[
                    dbc.Card(
                        id="page-4-card-region-selection",
                        style={"width": "100%", "height": "100%", "background-color": "#1d1c1f"},
                        children=[
                            dbc.CardBody(
                                className="h-100",
                                style={"background-color": "#1d1c1f"},
                                children=[
                                    html.Div(
                                        className="d-flex",
                                        children=[
                                            html.Div(
                                                style={"display": "inline-block", "width": "70%"},
                                                children=[
                                                    dmc.Center(
                                                        dmc.Text(
                                                            "Select up to 3 brain structures. To see the whole brain, select root",
                                                            size="xl",
                                                        )
                                                    ),
                                                    dcc.Graph(
                                                        id="page-4-graph-region-selection",
                                                        config=basic_config,
                                                        style={},
                                                        figure=figures.compute_treemaps_figure(),
                                                    ),
                                                ],
                                            ),
                                            dmc.Group(
                                                direction="column",
                                                style={"display": "inline-block", "width": "30%"},
                                                align="center",
                                                class_name="ml-5",
                                                children=[
                                                    dmc.Center(
                                                        dmc.Text(
                                                            "Select lipid(s)",
                                                            size="xl",
                                                            class_name="mb-5 pb-5 ",
                                                        )
                                                    ),
                                                    dmc.Select(
                                                        id="page-4-dropdown-lipids",
                                                        data=data.return_lipid_options(),
                                                        searchable=True,
                                                        nothingFound="No lipid found",
                                                        radius="md",
                                                        size="xs",
                                                        placeholder="Choose a lipid",
                                                        clearable=True,
                                                        transitionDuration=150,
                                                        transition="pop-top-left",
                                                        transitionTimingFunction="ease",
                                                        style={
                                                            "width": "20em",
                                                        },
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        children=[
                                            html.Div(
                                                style={
                                                    "width": "calc(70% - 1.75rem)",
                                                    "display": "inline-block",
                                                },
                                                children=[
                                                    dmc.Button(
                                                        children="Please choose a structure above",
                                                        id="page-4-add-structure-button",
                                                        disabled=True,
                                                        variant="filled",
                                                        radius="md",
                                                        size="xs",
                                                        color="cyan",
                                                        compact=False,
                                                        loading=False,
                                                        fullWidth=True,
                                                        class_name="mr-5",
                                                    ),
                                                    dmc.Button(
                                                        children=(
                                                            "Display lipid expression in the"
                                                            " selected structure(s)"
                                                        ),
                                                        id="page-4-display-button",
                                                        disabled=True,
                                                        variant="filled",
                                                        radius="md",
                                                        size="xs",
                                                        color="cyan",
                                                        compact=False,
                                                        loading=False,
                                                        fullWidth=True,
                                                        class_name="mr-5 mt-1",
                                                    ),
                                                    # --- small alert to guide user if no lipid selected ---
                                                    dmc.Alert(
                                                        "Please choose a lipid above first.",
                                                        id="page-4-alert",
                                                        color="red",
                                                        withCloseButton=False,
                                                        variant="light",
                                                        style={"marginTop": "0.75rem", "display": "none"},
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    dbc.Card(
                        style={
                            "maxWidth": "100%",
                            "margin": "0 auto",
                            "width": "100%",
                            "height": "100%",
                        },
                        id="page-4-card-lipid-selection",
                        children=[
                            dbc.CardBody(
                                style={"background-color": "#1d1c1f"},
                                className="pt-1",
                                children=[
                                    dmc.Group(
                                        direction="row",
                                        grow=True,
                                        align="flex-start",
                                        children=[
                                            dmc.Group(
                                                direction="column",
                                                grow=True,
                                                class_name="ml-5",
                                                spacing="xs",
                                                children=[
                                                    dmc.Center(
                                                        class_name="w-100",
                                                        children=dmc.Text(
                                                            "Brain structure selection",
                                                            size="xl",
                                                        ),
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-region-1",
                                                        header="name-region-1",
                                                        dismissable=True,
                                                        is_open=False,
                                                        bodyClassName="p-0",
                                                        header_class_name=(
                                                            "d-flex justify-content-center ml-2"
                                                        ),
                                                        style={"margin": "auto"},
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-region-2",
                                                        header="name-region-2",
                                                        dismissable=True,
                                                        is_open=False,
                                                        bodyClassName="p-0",
                                                        header_class_name=(
                                                            "d-flex justify-content-center ml-2"
                                                        ),
                                                        style={"margin": "auto"},
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-region-3",
                                                        header="name-region-3",
                                                        dismissable=True,
                                                        header_class_name=(
                                                            "d-flex justify-content-center ml-2"
                                                        ),
                                                        bodyClassName="p-0",
                                                        style={"margin": "auto"},
                                                    ),
                                                ],
                                            ),
                                            dmc.Group(
                                                direction="column",
                                                grow=True,
                                                class_name="ml-5",
                                                spacing="xs",
                                                children=[
                                                    dmc.Center(
                                                        class_name="w-100",
                                                        children=dmc.Text(
                                                            "Lipid selection",
                                                            size="xl",
                                                        ),
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-lipid-1",
                                                        header="",
                                                        dismissable=True,
                                                        is_open=False,
                                                        bodyClassName="p-0",
                                                        header_class_name=(
                                                            "d-flex justify-content-center ml-2"
                                                        ),
                                                        style={"margin": "auto"},
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-lipid-2",
                                                        header="",
                                                        dismissable=True,
                                                        is_open=False,
                                                        bodyClassName="p-0",
                                                        header_class_name=(
                                                            "d-flex justify-content-center ml-2"
                                                        ),
                                                        style={"margin": "auto"},
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-lipid-3",
                                                        header="",
                                                        dismissable=True,
                                                        header_class_name=(
                                                            "d-flex justify-content-center ml-2"
                                                        ),
                                                        is_open=False,
                                                        bodyClassName="p-0",
                                                        style={
                                                            "margin": "auto",
                                                        },
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            dbc.Modal(
                                id="page-4-modal-volume",
                                is_open=False,
                                size="xl",
                                children=[
                                    dbc.ModalHeader(
                                        style={
                                            "background-color": "#1d1c1f",
                                        },
                                        children=[
                                            dbc.ModalTitle(
                                                "Lipid selection interpolated in 3D",
                                                style={"color": "white"},
                                            ),
                                        ],
                                    ),
                                    dbc.ModalBody(
                                        style={
                                            "background-color": "#1d1c1f",
                                        },
                                        children=[
                                            dbc.Spinner(
                                                color="light",
                                                show_initially=False,
                                                children=[
                                                    html.Div(
                                                        className="fixed-aspect-ratio",
                                                        id="page-4-graph-volume-parent",
                                                        children=[
                                                            dcc.Graph(
                                                                id="page-4-graph-volume",
                                                                config=basic_config
                                                                | {
                                                                    "toImageButtonOptions": {
                                                                        "format": "png",
                                                                        "filename": "brain_volume",
                                                                        "scale": 2,
                                                                    }
                                                                },
                                                                style={
                                                                    "width": "100%",
                                                                    "height": "100%",
                                                                    "position": "absolute",
                                                                    "left": "0",
                                                                },
                                                                className="d-none",
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            dbc.Modal(
                                id="page-4-modal-heatmap",
                                is_open=False,
                                scrollable=False,
                                size="xl",
                                style={
                                    "maxWidth": "100%",
                                    "margin": "0 auto",
                                    "width": "100%",
                                    "height": "100%",
                                },
                                children=[
                                    dbc.ModalHeader(
                                        style={
                                            "background-color": "#1d1c1f",
                                        },
                                        children=[
                                            dbc.ModalTitle(
                                                "Lipid expression comparison",
                                                style={"color": "white"},
                                            ),
                                            dmc.Button(
                                                children="Download plot",
                                                id="page-4-download-clustergram-button",
                                                disabled=True,
                                                variant="filled",
                                                radius="md",
                                                size="xs",
                                                color="cyan",
                                                compact=False,
                                                loading=False,
                                                style={
                                                    "position": "absolute",
                                                    "right": "5rem",
                                                },
                                            ),
                                        ],
                                    ),
                                    dbc.ModalBody(
                                        className="d-flex justify-content-center flex-column",
                                        style={
                                            "background-color": "#1d1c1f",
                                        },
                                        children=[
                                            dbc.Progress(
                                                id="page-4-progress-bar-structure",
                                                style={"width ": "100%"},
                                                color="#338297",
                                            ),
                                            dcc.Slider(
                                                id="page-4-slider-percentile",
                                                min=0,
                                                max=99,
                                                value=80,
                                                marks={
                                                    0: {"label": "No filtering"},
                                                    25: {"label": "25%"},
                                                    50: {"label": "50%"},
                                                    75: {"label": "75%"},
                                                    99: {
                                                        "label": "99%",
                                                        "style": {"color": "#f50"},
                                                    },
                                                },
                                            ),
                                            html.Div(
                                                className="d-flex justify-content-center",
                                                style={"margin-top": "-5rem"},
                                                children=[
                                                    dcc.Graph(
                                                        id="page-4-graph-heatmap",
                                                        config=basic_config
                                                        | {
                                                            "toImageButtonOptions": {
                                                                "format": "png",
                                                                "filename": "brain_lipid_selection",
                                                                "scale": 2,
                                                            }
                                                        },
                                                        style={
                                                            "height": "100%",
                                                        },
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
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
    Output("page-4-alert", "style"),
    Output("page-4-graph-volume", "style"),
    Input("page-4-display-button", "n_clicks"),
    State("page-4-toast-lipid-1", "header"),
    prevent_initial_call=True,
)
def page_4_display_volume(n_clicks, lipid_header):
    """Reveal/hide the 3D volume canvas. Requires a lipid selection."""
    if not n_clicks:
        return dash.no_update
    if lipid_header and lipid_header.strip():
        return (
            {"display": "none"},
            {"width": "100%", "height": "100%", "position": "absolute", "left": "0"},
        )
    # No lipid selected
    return ({}, {"display": "none"})


@app.callback(
    Output("page-4-add-structure-button", "children"),
    Output("page-4-add-structure-button", "disabled"),
    Input("page-4-graph-region-selection", "clickData"),
    Input("page-4-selected-region-1", "data"),
    Input("page-4-selected-region-2", "data"),
    Input("page-4-selected-region-3", "data"),
)
def page_4_click(clickData, region_1_id, region_2_id, region_3_id):
    """Update the label/state of the 'add structure' button based on selections."""
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-4-graph-region-selection":
        if clickData is not None and "points" in clickData:
            label = clickData["points"][0]["label"]
            return "Add " + label + " to selection", False
        return "Please choose a structure above", True

    if region_1_id != "" and region_2_id != "" and region_3_id != "":
        return "Delete some structures to select new ones", True

    if region_1_id != "" or region_2_id != "" or region_3_id != "":
        return "Please choose a structure above", True

    return dash.no_update


@app.callback(
    Output("page-4-toast-region-1", "header"),
    Output("page-4-toast-region-2", "header"),
    Output("page-4-toast-region-3", "header"),
    Output("page-4-selected-region-1", "data"),
    Output("page-4-selected-region-2", "data"),
    Output("page-4-selected-region-3", "data"),
    Output("page-4-toast-region-1", "is_open"),
    Output("page-4-toast-region-2", "is_open"),
    Output("page-4-toast-region-3", "is_open"),
    Output("page-4-last-selected-regions", "data"),
    Input("page-4-add-structure-button", "n_clicks"),
    Input("page-4-toast-region-1", "is_open"),
    Input("page-4-toast-region-2", "is_open"),
    Input("page-4-toast-region-3", "is_open"),
    State("page-4-selected-region-1", "data"),
    State("page-4-selected-region-2", "data"),
    State("page-4-selected-region-3", "data"),
    State("page-4-toast-region-1", "header"),
    State("page-4-toast-region-2", "header"),
    State("page-4-toast-region-3", "header"),
    State("page-4-last-selected-regions", "data"),
    State("page-4-add-structure-button", "children"),
)
def page_4_add_toast_region_selection(
    clicked_add,
    bool_toast_1,
    bool_toast_2,
    bool_toast_3,
    region_1_id,
    region_2_id,
    region_3_id,
    header_1,
    header_2,
    header_3,
    l_selected_regions,
    label_region,
):
    """Add/remove regions via toasts and 'add structure'."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", "", "", "", "", "", False, False, False, []

    id_input = ctx.triggered[0]["prop_id"].split(".")[0]
    value_input = ctx.triggered[0]["prop_id"].split(".")[1]

    # Delete from toast close
    if value_input == "is_open":
        if id_input == "page-4-toast-region-1":
            if region_1_id in l_selected_regions:
                l_selected_regions.remove(region_1_id)
            header_1 = ""
            region_1_id = ""
        elif id_input == "page-4-toast-region-2":
            if region_2_id in l_selected_regions:
                l_selected_regions.remove(region_2_id)
            header_2 = ""
            region_2_id = ""
        elif id_input == "page-4-toast-region-3":
            if region_3_id in l_selected_regions:
                l_selected_regions.remove(region_3_id)
            header_3 = ""
            region_3_id = ""
        else:
            logging.warning("Unexpected toast id in region removal")

        return (
            header_1,
            header_2,
            header_3,
            region_1_id,
            region_2_id,
            region_3_id,
            bool_toast_1,
            bool_toast_2,
            bool_toast_3,
            l_selected_regions,
        )

    # Add region
    if id_input == "page-4-add-structure-button":
        if label_region != "Please choose a structure above":
            region = label_region.split("Add ")[1].split(" to selection")[0]
            region_id = atlas.dic_name_acronym[region]
            if region_id not in l_selected_regions:
                l_selected_regions.append(region_id)
                if not bool_toast_1:
                    header_1 = region
                    region_1_id = region_id
                    bool_toast_1 = True
                elif not bool_toast_2:
                    header_2 = region
                    region_2_id = region_id
                    bool_toast_2 = True
                elif not bool_toast_3:
                    header_3 = region
                    region_3_id = region_id
                    bool_toast_3 = True
                else:
                    logging.warning("More than 3 regions selected")
                    return dash.no_update

                return (
                    header_1,
                    header_2,
                    header_3,
                    region_1_id,
                    region_2_id,
                    region_3_id,
                    bool_toast_1,
                    bool_toast_2,
                    bool_toast_3,
                    l_selected_regions,
                )
        # shouldn't be clickable otherwise
        return "", "", "", "", "", "", False, False, False, []

    return dash.no_update

from app import long_callback_limiter
# Function to plot page-4-graph-volume when its state get updated
@app.long_callback(
    output=Output("page-4-graph-volume", "figure"),
    inputs=[
        Input("page-4-display-button", "n_clicks"),
    ],
    state=[
        State("page-4-modal-volume", "is_open"),
        State("page-4-toast-lipid-1", "header"),
        State("page-4-last-selected-regions", "data"),
        State("page-4-selected-region-1", "data"),
        State("page-4-selected-region-2", "data"),
        State("page-4-selected-region-3", "data"),
        State("main-brain", "value"),
    ],
    running=[
        (Output("page-4-graph-volume", "className"), "d-none", ""),
    ],
    prevent_initial_call=True,
    cache_args_to_ignore=[0],  # Ignore n_clicks in caching
)
def page_4_plot_graph_volume(
    n_clicks_button_display,
    is_open_modal,
    name_lipid_1,
    l_selected_regions,
    name_region_1,
    name_region_2,
    name_region_3,
    brain,
):
    """Plot the 3D volume for the selected lipid within selected structures."""
    with long_callback_limiter:
        logging.info("Entering page_3_plot_heatmap_long (with semaphore)")
        if not is_open_modal:
            logging.info("Modal closed, deleting graph")
            return {}

        # Build the ID set for selected regions (include descendants)
        set_id = set([])
        for acronym in l_selected_regions:
            set_id = set_id.union(atlas.dic_acronym_children_id[acronym])
        if len(set_id) == 0:
            set_id = None  # whole brain

        decrease_resolution_factor = 2
        logging.info(
            "For the computation of 3D volume, decrease_resolution_factor is "
            + str(decrease_resolution_factor)
        )

        return figures.compute_3D_volume_figure(
            lipid_name=name_lipid_1,
            annotation_path=None,
            set_id_regions=set_id,
            downsample_factor=decrease_resolution_factor,
            opacity=0.1,
            surface_count=40,
            colorscale="Inferno",
        )


@app.callback(
    Output("page-4-dropdown-lipids", "data"),
    Output("page-4-dropdown-lipids", "value"),
    Input("page-4-dropdown-lipids", "value"),
    Input("main-brain", "value"),
    prevent_initial_call=True,
)
def page_4_handle_dropdowns(name, brain):
    """Refresh lipid options on brain change; otherwise leave selection alone."""
    trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if trigger == "main-brain":
        return data.return_lipid_options(), None
    return dash.no_update


@app.callback(
    Output("page-4-toast-lipid-1", "header"),
    Input("page-4-dropdown-lipids", "value"),
    Input("page-4-toast-lipid-1", "is_open"),
    State("page-4-toast-lipid-1", "header"),
    Input("main-brain", "value"),
)
def page_4_add_toast_selection(selected_lipid, is_open, current_header, brain):
    """Track the chosen lipid in the toast header; clear when toast closed or brain changes."""
    trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # User closed the toast → clear lipid
    if trigger == "page-4-toast-lipid-1" and not is_open:
        return ""

    # New lipid picked
    if trigger == "page-4-dropdown-lipids" and selected_lipid:
        return selected_lipid

    # Brain changed → clear lipid selection
    if trigger == "main-brain":
        return ""

    return dash.no_update


@app.callback(
    Output("page-4-display-button", "disabled"),
    Input("page-4-selected-region-1", "data"),
    Input("page-4-selected-region-2", "data"),
    Input("page-4-selected-region-3", "data"),
    Input("page-4-toast-lipid-1", "header"),
)
def page_4_active_display(region_1_id, region_2_id, region_3_id, lipid_header):
    """Enable 'Display' only if there's at least one region AND a lipid."""
    has_region = any(x for x in [region_1_id, region_2_id, region_3_id])
    has_lipid = bool(lipid_header and lipid_header.strip())
    return not (has_region and has_lipid)


@app.callback(
    Output("page-4-modal-volume", "is_open"),
    Input("page-4-display-button", "n_clicks"),
    [State("page-4-modal-volume", "is_open")],
)
def page_4_toggle_modal_volume(n1, is_open):
    """Always open the modal when the Display button is clicked."""
    if n1:
        return True
    return is_open


clientside_callback(
    """
    function(n_clicks){
        if(n_clicks > 0){
            domtoimage.toBlob(document.getElementById('page-4-graph-heatmap'))
                .then(function (blob) {
                    window.saveAs(blob, 'clustergram.png');
                }
            );
        }
    }
    """,
    Output("page-4-download-clustergram-button", "n_clicks"),
    Input("page-4-download-clustergram-button", "n_clicks"),
)
"""This clientside callback allows to download the clustergram figure as a png file."""
