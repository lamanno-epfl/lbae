# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to explore the lipid data from either pre-existing annotated 
structures or human-selected in the app.

Updates:
- Added toggle switch for Allen Brain Atlas annotations overlay
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html, clientside_callback
from dash.dependencies import Input, Output, State
import dash
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import logging
import dash_draggable
from numba import njit
import dash_mantine_components as dmc

# LBAE imports
from app import app, figures, data, storage, atlas, cache_flask
import config
from modules.tools.image import convert_image_to_base64
from config import l_colors

# ==================================================================================================
# --- Layout
# ==================================================================================================

# Variables for React grid layout
HEIGHT_PLOTS = 300
N_LINES = int(np.ceil(HEIGHT_PLOTS / 30))

# Layout of the page
def return_layout(basic_config, slice_index=1):
    page = html.Div(
        style={
            "position": "absolute",
            "top": "0px",
            "right": "0px",
            "bottom": "0px",
            "left": "6rem",
            "background-color": "#1d1c1f",
            "overflow": "hidden",
        },
        children=[
            html.Div(
                className="fixed-aspect-ratio",
                style={
                    "background-color": "#1d1c1f",
                },
                children=[
                    dmc.Group(
                        children=dcc.Graph(
                            id="page-3-graph-heatmap-mz-selection",
                            config=basic_config
                            | {
                                "toImageButtonOptions": {
                                    "format": "png",
                                    "filename": "annotated_brain_slice",
                                    "scale": 2,
                                }
                            },
                            style={
                                "width": "95%",
                                "height": "95%",
                                "position": "absolute",
                                "left": "2.5%",
                            },
                            figure = figures.compute_rgb_image_per_lipid_selection(
                                        slice_index,
                                        ll_lipid_names=["SM 34:1;O2", None, None],
                                        cache_flask=cache_flask,
                                    ).update_layout(
                                        dragmode="drawclosedpath",
                                        newshape=dict(
                                            fillcolor=l_colors[0],
                                            opacity=0.7,
                                            line=dict(color="white", width=1),
                                        ),
                                        autosize=True,
                                    ),
                        ),
                    ),
                    dmc.Group(
                        direction="column",
                        spacing=0,
                        style={
                            "left": "1%",
                            "top": "1em",
                        },
                        class_name="position-absolute",
                        children=[
                            dmc.Text("Choose up to 3 lipids", size="lg"),
                            dmc.Group(
                                spacing="xs",
                                align="flex-start",
                                children=[
                                    dmc.MultiSelect(
                                        id="page-3-dropdown-lipids",
                                        data=data.return_lipid_options(),
                                        value=['SM 34:1;O2'],
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
                                ],
                            ),
                        ],
                    ),
                    dmc.Group(
                        direction="row",
                        position="center",
                        style={
                            "top": "1em",
                        },
                        class_name="position-absolute w-100",
                        children=[
                            dmc.Switch(
                                id="page-3-toggle-annotations",
                                label="Allen Brain Atlas Annotations",
                                checked=False,
                                color="cyan",
                                radius="xl",
                                size="sm",
                            ),
                        ],
                    ),
                    dmc.Text(
                        id="page-3-badge-input",
                        children="Colors: NA",
                        class_name="position-absolute",
                        style={"left": "1%", "top": "7em"},
                    ),
                    dmc.Badge(
                        id="page-3-badge-lipid-1",
                        children="name-lipid-1",
                        color="red",
                        variant="filled",
                        class_name="d-none",
                        style={"left": "1%", "top": "13em"},
                    ),
                    dmc.Badge(
                        id="page-3-badge-lipid-2",
                        children="name-lipid-2",
                        color="teal",
                        variant="filled",
                        class_name="d-none",
                        style={"left": "1%", "top": "15em"},
                    ),
                    dmc.Badge(
                        id="page-3-badge-lipid-3",
                        children="name-lipid-3",
                        color="blue",
                        variant="filled",
                        class_name="d-none",
                        style={"left": "1%", "top": "17em"},
                    ),
                    # dmc.Text(
                    #     "Hovered region: ",
                    #     id="page-3-graph-hover-text",
                    #     size="lg",
                    #     align="center",
                    #     color="cyan",
                    #     class_name="mt-5",
                    #     weight=500,
                    #     style={
                    #         "width": "100%",
                    #         "position": "absolute",
                    #         "top": "7%",
                    #     },
                    # ),
                    dmc.Button(
                        children="Compute spectral analysis",
                        id="page-3-button-compute-spectra",
                        variant="filled",
                        color="cyan",
                        radius="md",
                        size="xs",
                        disabled=True,
                        compact=False,
                        loading=False,
                        style={
                            "right": "1%",
                            "top": "3em",
                        },
                        class_name="position-absolute",
                    ),
                    dmc.Group(
                        direction="column",
                        spacing=0,
                        style={
                            "left": "1%",
                            "bottom": "8em",
                        },
                        class_name="position-absolute",
                        children=[
                            dmc.Text("Draw a region or choose a structure below", size="lg"),
                            dmc.Group(
                                spacing="xs",
                                align="flex-start",
                                children=[
                                    dmc.MultiSelect(
                                        id="page-3-dropdown-brain-regions",
                                        data=[
                                            {
                                                "label": atlas.dic_acronym_name[node],
                                                "value": atlas.dic_acronym_name[node],
                                            }
                                            for node in atlas.dic_existing_masks[slice_index]
                                        ],
                                        searchable=True,
                                        nothingFound="No structure found",
                                        radius="md",
                                        size="xs",
                                        placeholder="Choose brain structure",
                                        clearable=False,
                                        maxSelectedValues=3,
                                        transitionDuration=150,
                                        transition="pop-top-left",
                                        transitionTimingFunction="ease",
                                        style={
                                            "width": "20em",
                                        },
                                    ),
                                    dmc.Button(
                                        children="Reset",
                                        id="page-3-reset-button",
                                        variant="filled",
                                        color="cyan",
                                        radius="md",
                                        size="xs",
                                        disabled=False,
                                        compact=False,
                                        loading=False,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                children=[
                    dbc.Offcanvas(
                        id="page-4-drawer-region-selection",
                        backdrop=False,
                        placement="end",
                        style={
                            "width": "calc(100% - 6rem)",
                            "height": "100%",
                            "background-color": "#1d1c1f",
                        },
                        children=[
                            dash_draggable.ResponsiveGridLayout(
                                id="draggable",
                                clearSavedLayout=True,
                                isDraggable=False,
                                isResizable=False,
                                containerPadding=[2, 2],
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
                                layouts={
                                    # x sets the lateral position, y the vertical one,
                                    # w is in columns (whose size depends on the dimension),
                                    # h is in rows (30px)
                                    # nb columns go 12->12->10->6->4->2
                                    "xxl": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 0,
                                            "w": 12,
                                            "h": N_LINES*2,
                                        },
                                    ],
                                    "lg": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 0,
                                            "w": 12,
                                            "h": N_LINES*2,
                                        },
                                    ],
                                    "md": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 0,
                                            "w": 10,
                                            "h": N_LINES*2,
                                        },
                                    ],
                                    "sm": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 0,
                                            "w": 6,
                                            "h": N_LINES*2,
                                        },
                                    ],
                                    "xs": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 0,
                                            "w": 4,
                                            "h": N_LINES*2,
                                        },
                                    ],
                                    "xxs": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 0,
                                            "w": 2,
                                            "h": N_LINES*2,
                                        },
                                    ],
                                },
                                children=[
                                    dbc.Card(
                                        id="page-3-card-spectrum",
                                        style={
                                            "maxWidth": "100%",
                                            "margin": "0 auto",
                                            "width": "100%",
                                            "height": "100%",
                                        },
                                        children=[
                                            dbc.CardHeader(
                                                "High-resolution spectrum for current selection",
                                                style={
                                                    "background-color": "#1d1c1f",
                                                    "color": "white",
                                                },
                                            ),
                                            dbc.CardBody(
                                                className="loading-wrapper py-0 my-0",
                                                style={
                                                    "background-color": "#1d1c1f",
                                                },
                                                children=[
                                                    html.Div(
                                                        children=[
                                                            dbc.Spinner(
                                                                color="dark",
                                                                children=[
                                                                    html.Div(
                                                                        className="px-5",
                                                                        children=[
                                                                            html.Div(
                                                                                id="page-3-alert",
                                                                                className=(
                                                                                    "text-center"
                                                                                    " my-5"
                                                                                ),
                                                                                style={
                                                                                    "display": "none"
                                                                                },
                                                                                children=html.Strong(
                                                                                    children=(
                                                                                        "Please"
                                                                                        " draw at"
                                                                                        " least one"
                                                                                        " region on"
                                                                                        " the heatmap"
                                                                                        " and click"
                                                                                        " on 'compute"
                                                                                        " spectra'."
                                                                                    ),
                                                                                    style={
                                                                                        "color": "#df5034"
                                                                                    },
                                                                                ),
                                                                            ),
                                                                            html.Div(
                                                                                id="page-3-alert-2",
                                                                                className=(
                                                                                    "text-center"
                                                                                    " my-2"
                                                                                ),
                                                                                style={
                                                                                    "display": (
                                                                                        "none"
                                                                                    )
                                                                                },
                                                                                children=[
                                                                                    html.Strong(
                                                                                        children=(
                                                                                            "Too many"
                                                                                            " regions"
                                                                                            " selected,"
                                                                                            " please"
                                                                                            " reset"
                                                                                            " the annotations."
                                                                                        ),
                                                                                        style={
                                                                                            "color": "#df5034"
                                                                                        },
                                                                                    ),
                                                                                ],
                                                                            ),
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        id="page-3-graph-spectrum-per-pixel-wait"
                                                                    ),
                                                                    dcc.Graph(
                                                                        id="page-3-graph-spectrum-per-pixel",
                                                                        style={
                                                                            "height": HEIGHT_PLOTS
                                                                        }
                                                                        | {"display": "none"},
                                                                        config=basic_config
                                                                        | {
                                                                            "toImageButtonOptions": {
                                                                                "format": "png",
                                                                                "filename": "spectrum_from_custom_region",
                                                                                "scale": 2,
                                                                            }
                                                                        },
                                                                    ),
                                                                    # dmc.Button(
                                                                    #     children=(
                                                                    #         "Download spectrum data"
                                                                    #     ),
                                                                    #     id="page-3-download-data-button",
                                                                    #     disabled=False,
                                                                    #     variant="filled",
                                                                    #     radius="md",
                                                                    #     size="xs",
                                                                    #     color="cyan",
                                                                    #     compact=False,
                                                                    #     loading=False,
                                                                    #     style={
                                                                    #         "position": "absolute",
                                                                    #         "top": "0.7rem",
                                                                    #         "left": "27rem",
                                                                    #     },
                                                                    # ),
                                                                    dmc.Button(
                                                                        children="Close panel",
                                                                        id="page-4-close-drawer-region-selection",
                                                                        variant="filled",
                                                                        disabled=False,
                                                                        color="red",
                                                                        radius="md",
                                                                        size="xs",
                                                                        compact=False,
                                                                        loading=False,
                                                                        style={
                                                                            "position": "absolute",
                                                                            "top": "0.7rem",
                                                                            "right": "1rem",
                                                                        },
                                                                        class_name="w-25",
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
                            dmc.Center(
                                class_name="w-100",
                                children=[
                                    dcc.Download(id="page-3-download-data"),
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


# @app.callback(
#     Output("page-3-graph-hover-text", "children"),
#     Input("page-3-graph-heatmap-mz-selection", "hoverData"),
#     Input("main-slider", "data"),
# )
# def page_3_hover(hoverData, slice_index):
#     """This callback is used to update the text displayed when hovering over the slice image."""
#     print("hoverData:", hoverData)
#     coords_csv_x = pd.read_csv("/data/francesca/lbae/assets/sectionid_to_rostrocaudal_slider_sorted.csv")
#     slice_z_coords = coords_csv_x[coords_csv_x['SectionID'] == slice_index]['xccf'].iloc[0]
#     # If there is a region hovered, find out the region name with the current coordinates
#     if hoverData is not None:
#         if len(hoverData["points"]) > 0:
#             # rostro-caudal axis
#             z = int(slice_z_coords*40) # int(slice_index) - 1 # --> from 0 to 528
#             print("z: ", z)
            
#             x = hoverData["points"][0]["x"] # --> from 0 to 456
#             print("x: ", x)
#             y = hoverData["points"][0]["y"] # --> from 0 to 320
#             print("y: ", y)

#             # slice_coor_rescaled = np.asarray(
#             #     atlas.array_coordinates[x, y, z], # array_coordinates_warped_data[x, y, z] * 1000 / atlas.resolution).round(0)
#             #     dtype=np.int16,
#             # )
#             # print("slice_coor_rescaled:", slice_coor_rescaled)
#             try:
#                 label = atlas.labels[(x, y, z)] # atlas.labels[tuple(slice_coor_rescaled)]
#             except:
#                 label = "undefined"
#             return "Hovered region: " + label

#     return dash.no_update


@app.callback(
    Output("page-3-graph-heatmap-mz-selection", "relayoutData"),
    Input("page-3-reset-button", "n_clicks"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def page_3_reset_layout(cliked_reset, url):
    """This callback is used to reset the layout of the heatmap when navigating to this page."""
    print("\n============ page_3_reset_layout =============")
    print("dash.callback_context.triggered\n:", dash.callback_context.triggered)
    return {}


@app.callback(
    Output("page-3-graph-heatmap-mz-selection", "figure"), # -----------------
    Output("page-3-badge-input", "children"),
    Output("dcc-store-color-mask", "data"),
    Output("dcc-store-reset", "data"),
    Output("dcc-store-shapes-and-masks", "data"),

    Input("page-3-graph-heatmap-mz-selection", "relayoutData"),
    Input("main-slider", "data"), # ------------------------------------------
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-dropdown-brain-regions", "value"),
    Input("url", "pathname"),
    Input("page-3-selected-lipid-1", "data"),
    Input("page-3-selected-lipid-2", "data"),
    Input("page-3-selected-lipid-3", "data"),
    Input("page-3-toggle-annotations", "checked"),
    
    State("dcc-store-color-mask", "data"),
    State("dcc-store-reset", "data"),
    State("dcc-store-shapes-and-masks", "data"),
    State("page-3-badge-input", "children"),
    prevent_initial_call=True,
)
def page_3_plot_heatmap(
    relayoutData,
    slice_index,
    cliked_reset,
    l_mask_name,
    url,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    annotations_checked,
    l_color_mask,
    reset,
    l_shapes_and_masks,
    graph_input,
):
    """This callback plots the heatmap of the selected lipid(s)."""
    print("\n============ page_3_plot_heatmap =============")
    print("dash.callback_context.triggered\n:", dash.callback_context.triggered)
    logging.info("Entering page_3_plot_heatmap")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    print(f"id_input: {id_input}")    
    print("value_input:", value_input)
    
    # Define overlay based on annotations toggle
    overlay = None if annotations_checked else None

    # If a lipid selection has been done
    if (
        id_input == "page-3-selected-lipid-1"
        or id_input == "page-3-selected-lipid-2"
        or id_input == "page-3-selected-lipid-3"
        # or id_input == "page-3-rgb-button"
        or id_input == "page-3-colormap-button"
        or id_input == "page-3-toggle-annotations"
        or (
            (id_input == "main-slider")
            and graph_input == "Colors: "
            # (
            #     graph_input == "Colors: " + "Lipid selection colormap"
            #     or graph_input == "Colors: "
            # )
        )
    ):
        if lipid_1_index >= 0 or lipid_2_index >= 0 or lipid_3_index >= 0:
            ll_lipid_names = [
                # [
                    ' '.join([
                        data.get_annotations().iloc[index]["name"].split('_')[i] + ' ' 
                        + data.get_annotations().iloc[index]["structure"].split('_')[i] 
                        for i in range(len(data.get_annotations().iloc[index]["name"].split('_')))
                        ])
                # ]
                if index != -1
                else None
                for index in [lipid_1_index, lipid_2_index, lipid_3_index]
            ]
            print("ll_lipid_names:", ll_lipid_names)
            
            # Or if the current plot must be an RGB image
            if (
                # id_input == "page-3-rgb-button"
                # or (
                    id_input == "main-slider"
                    and graph_input == "Colors: "
                # )
            ):
                fig = figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lipid_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    )
                fig.update_layout(
                    dragmode="drawclosedpath",
                    newshape=dict(
                        fillcolor=l_colors[0],
                        opacity=0.7,
                        line=dict(color="white", width=1),
                    ),
                    autosize=True,
                )
                return fig, "Colors: ", [], True, [],

            # Plot RBG By default
            else:
                logging.info("Right before calling the graphing function")
                fig = figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lipid_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    )
                fig.update_layout(
                    dragmode="drawclosedpath",
                    newshape=dict(
                        fillcolor=l_colors[0],
                        opacity=0.7,
                        line=dict(color="white", width=1),
                    ),
                    autosize=True,
                )
                return fig, "Colors: ", [], True, []
        
        elif (
            id_input == "main-slider" and graph_input == "Colors: "
        ):
            print(f"No lipid has been selected, the current lipid is SM 34:1;O2 and the slice is {slice_index}")
            fig = figures.compute_rgb_image_per_lipid_selection(
                    slice_index,
                    ll_lipid_names=["SM 34:1;O2", None, None],
                    cache_flask=cache_flask,
                    overlay=overlay,
                )
            fig.update_layout(
                dragmode="drawclosedpath",
                newshape=dict(
                    fillcolor=l_colors[0],
                    opacity=0.7,
                    line=dict(color="white", width=1),
                ),
                autosize=True,
            )
            return fig, "Colors: " + "SM 34:1;O2", [], True, []

        else:
            # No lipid has been selected
            print(slice_index)
            fig = figures.compute_rgb_image_per_lipid_selection(
                    slice_index,
                    ll_lipid_names=["SM 34:1;O2", None, None],
                    cache_flask=cache_flask,
                    overlay=overlay,
                )
            fig.update_layout(
                dragmode="drawclosedpath",
                newshape=dict(
                    fillcolor=l_colors[0],
                    opacity=0.7,
                    line=dict(color="white", width=1),
                ),
                autosize=True,
            )
            return fig, "Colors: " + "SM 34:1;O2", [], True, []
    
    # ------------------------------------------------------------------------------------------------
    # If a new slice is loaded or the page just got loaded
    # do nothing because of automatic relayout of the heatmap which is automatically triggered when
    # the page is loaded
    if lipid_1_index >= 0 or lipid_2_index >= 0 or lipid_3_index >= 0:
        ll_lipid_names = [
            # [
                ' '.join([
                    data.get_annotations().iloc[index]["name"].split('_')[i] + ' ' 
                    + data.get_annotations().iloc[index]["structure"].split('_')[i] 
                    for i in range(len(data.get_annotations().iloc[index]["name"].split('_')))
                    ])
            # ]
            if index != -1
            else None
            for index in [lipid_1_index, lipid_2_index, lipid_3_index]
        ]
    else:
        ll_lipid_names = ["SM 34:1;O2", None, None]
    
    # Drawing or selecting a brain region
    if (
        # id_input == "main-slider" # or
        len(id_input) == 0
        or id_input == "page-3-reset-button"
        or id_input == "url"
    ):
        fig = figures.compute_rgb_image_per_lipid_selection(
                slice_index,
                ll_lipid_names=ll_lipid_names, # ["SM 34:1;O2", None, None],
                cache_flask=cache_flask,
                overlay=overlay,
            )
        fig.update_layout(
            dragmode="drawclosedpath",
            newshape=dict(
                fillcolor=l_colors[0],
                opacity=0.7,
                line=dict(color="white", width=1),
            ),
            autosize=True,
        )
        return fig, "Colors: ", [], True, []

    # Fix bug with automatic relayout
    if value_input == "relayoutData" and relayoutData == {"autosize": True}:
        return dash.no_update

    # Fix other bug with automatic dropdown selection
    if (
        id_input == "page-3-dropdown-brain-regions"
        and relayoutData is None
        and cliked_reset is None
        and (l_mask_name is None or len(l_mask_name) == 0)
    ):
        fig = figures.compute_rgb_image_per_lipid_selection(
                slice_index,
                ll_lipid_names=ll_lipid_names, # ["SM 34:1;O2", None, None],
                cache_flask=cache_flask,
                overlay=overlay,
            )
        fig.update_layout(
            dragmode="drawclosedpath",
            newshape=dict(
                fillcolor=l_colors[0],
                opacity=0.7,
                line=dict(color="white", width=1),
            ),
            autosize=True,
        )
        return fig, "Colors: ", [], True, []

    # If the user selected a new mask or drew on the plot
    if id_input == "page-3-graph-heatmap-mz-selection" or id_input == "page-3-dropdown-brain-regions":
        # Check that a mask has actually been selected
        if l_mask_name is not None or relayoutData is not None:
            # Rebuild figure
            fig = figures.compute_rgb_image_per_lipid_selection(
                slice_index,
                ll_lipid_names=ll_lipid_names, # ["SM 34:1;O2", None, None],
                cache_flask=cache_flask,
                overlay=overlay,
            )
            color_idx = None
            col_next = None
            if l_mask_name is not None:
                # If a mask has been selected
                if len(l_mask_name) > 0:
                    for idx_mask, mask_name in enumerate(l_mask_name):
                        id_name = atlas.dic_name_acronym[mask_name]
                        
                        if id_name in atlas.dic_existing_masks[slice_index]:

                            mask3D = atlas.get_atlas_mask(id_name) # this gives the 3d mask
                            # TODO
                            coords_csv_x = pd.read_csv("/data/francesca/lbae/assets/sectionid_to_rostrocaudal_slider_sorted.csv")
                            slice_z_coords = coords_csv_x[coords_csv_x['SectionID'] == slice_index]['xccf'].iloc[0]
                            mask2D = mask3D[int(slice_z_coords*40), :, :] ######
                            # projected_mask = atlas.get_projected_mask_and_spectrum(
                            #     slice_index - 1, mask_name, MAIA_correction=False
                            # )[0]
                        else:
                            logging.warning("The mask " + str(mask_name) + " couldn't be found")

                        # Build a list of empty images and add selected lipids for each channel
                        # print("projected_mask:", projected_mask.shape)
                        # normalized_projected_mask = projected_mask / np.max(projected_mask)
                        # print("normalized_projected_mask:", normalized_projected_mask.shape)

                        # Correct bug with atlas projection
                        # normalized_projected_mask[:, :10] = 0

                        if idx_mask < len(l_color_mask):
                            color_rgb = l_color_mask[idx_mask]
                        else:
                            color_idx = len(l_color_mask)
                            if relayoutData is not None:
                                if "shapes" in relayoutData:
                                    color_idx += len(relayoutData["shapes"])
                            color = config.l_colors[color_idx % 4][1:]
                            color_rgb = [int(color[i : i + 2], 16) for i in (0, 2, 4)] + [255]
                            l_color_mask.append(color_rgb)

                        l_images = [
                            mask2D * color
                            # normalized_projected_mask * color
                            for c, color in zip(["r", "g", "b", "a"], color_rgb)
                        ]
                        
                        # Reoder axis to match plotly go.image requirements
                        array_image = np.moveaxis(np.array(l_images, dtype=np.uint8), 0, 2)

                        # Convert image to string to save space (new image as each mask must have a
                        # different color)
                        base64_string = convert_image_to_base64(
                            array_image, optimize=True, format="webp", type="RGBA"
                        )
                        fig.add_trace(
                            go.Image(visible=True, source=base64_string, hoverinfo="skip")
                        )
                        fig.update_layout(
                            dragmode="drawclosedpath",
                        )

                        if id_input == "page-3-dropdown-brain-regions" and color_idx is not None:
                            # Save in l_shapes_and_masks
                            l_shapes_and_masks.append(["mask", mask_name, base64_string, color_idx])

            # If a region has been drawn by the user
            if relayoutData is not None:
                if "shapes" in relayoutData:
                    if len(relayoutData["shapes"]) > 0:
                        print("not reset or value_input==relayoutData:", not reset or value_input == "relayoutData")
                        if not reset or value_input == "relayoutData":
                            if "path" in relayoutData["shapes"][-1]:
                                fig["layout"]["shapes"] = relayoutData["shapes"]  #
                                col_next = config.l_colors[
                                    (len(relayoutData["shapes"]) + len(l_color_mask)) % 4
                                ]

                                # compute color and save in l_shapes_and_masks
                                if id_input == "page-3-graph-heatmap-mz-selection":
                                    color_idx_for_registration = len(l_color_mask)
                                    if relayoutData is not None:
                                        if "shapes" in relayoutData:
                                            color_idx_for_registration += len(
                                                relayoutData["shapes"]
                                            )
                                    l_shapes_and_masks.append(
                                        [
                                            "shape",
                                            None,
                                            relayoutData["shapes"][-1],
                                            color_idx_for_registration - 1,
                                        ]
                                    )
            # Update col_next
            if color_idx is not None and col_next is None:
                col_next = config.l_colors[(color_idx + 1) % 4]
            elif col_next is None:
                col_next = config.l_colors[0]
            fig.update_layout(
                dragmode="drawclosedpath",
                newshape=dict(
                    fillcolor=col_next,
                    opacity=0.7,
                    line=dict(color="white", width=1),
                ),
            )

            # Update drag mode
            if relayoutData is not None:
                if "shapes" in relayoutData:
                    if len(relayoutData["shapes"]) + len(l_color_mask) > 3:
                        fig.update_layout(dragmode=False)
            if len(l_color_mask) > 3:
                fig.update_layout(dragmode=False)

            # Return figure and corresponding data
            return fig, "Colors: ", l_color_mask, False, l_shapes_and_masks

    # either graph is already here
    return dash.no_update

@app.callback(
    Output("page-3-badge-lipid-1", "children"),
    Output("page-3-badge-lipid-2", "children"),
    Output("page-3-badge-lipid-3", "children"),
    Output("page-3-selected-lipid-1", "data"),
    Output("page-3-selected-lipid-2", "data"),
    Output("page-3-selected-lipid-3", "data"),
    Output("page-3-badge-lipid-1", "class_name"),
    Output("page-3-badge-lipid-2", "class_name"),
    Output("page-3-badge-lipid-3", "class_name"),

    Input("page-3-dropdown-lipids", "value"),
    Input("page-3-badge-lipid-1", "class_name"),
    Input("page-3-badge-lipid-2", "class_name"),
    Input("page-3-badge-lipid-3", "class_name"),
    Input("main-slider", "data"),

    State("page-3-selected-lipid-1", "data"),
    State("page-3-selected-lipid-2", "data"),
    State("page-3-selected-lipid-3", "data"),
    State("page-3-badge-lipid-1", "children"),
    State("page-3-badge-lipid-2", "children"),
    State("page-3-badge-lipid-3", "children"),
)
def page_3_add_toast_selection(
    l_lipid_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    header_1,
    header_2,
    header_3,
):
    """This callback adds the selected lipid to the selection."""
    logging.info("Entering function to update lipid data")
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    # if page-3-dropdown-lipids is called while there's no lipid name defined, it means the page
    # just got loaded
    if len(id_input) == 0 or (id_input == "page-3-dropdown-lipids" and l_lipid_names is None):
        # Initialize with SM 34:1;O2 as the default lipid
        default_lipid = "SM 34:1;O2"
        # Find lipid location for the default lipid
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
        
        # If no match for current slice, try to find it in any slice
        if len(l_lipid_loc) == 0:
            l_lipid_loc = (
                data.get_annotations()
                .index[
                    (data.get_annotations()["name"] == name)
                    & (data.get_annotations()["structure"] == structure)
                ]
                .tolist()
            )[:1]
        
        # Set default lipid if found
        if len(l_lipid_loc) > 0:
            lipid_1_index = l_lipid_loc[0]
            header_1 = default_lipid
            class_name_badge_1 = "position-absolute"
            return header_1, "", "", lipid_1_index, -1, -1, class_name_badge_1, "d-none", "d-none"
        else:
            # Fallback if lipid not found
            return "", "", "", -1, -1, -1, "d-none", "d-none", "d-none", # None

    # If one or several lipids have been deleted
    if l_lipid_names is not None:
        if len(l_lipid_names) < len(
            [x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x != -1]
        ):
            logging.info("One or several lipids have been deleter. Cleaning lipid badges now.")
            for idx_header, header in enumerate([header_1, header_2, header_3]):
                found = False
                for lipid_name in l_lipid_names:
                    if lipid_name == header:
                        found = True
                if not found:
                    if idx_header == 0:
                        header_1 = ""
                        lipid_1_index = -1
                        class_name_badge_1 = "d-none"
                    if idx_header == 1:
                        header_2 = ""
                        lipid_2_index = -1
                        class_name_badge_2 = "d-none"
                    if idx_header == 2:
                        header_3 = ""
                        lipid_3_index = -1
                        class_name_badge_3 = "d-none"

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
            )

    # Otherwise, update selection or add lipid
    if (
        id_input == "page-3-dropdown-lipids" and l_lipid_names is not None
    ) or id_input == "main-slider":
        # If a new slice has been selected
        if id_input == "main-slider":
            for header in [header_1, header_2, header_3]:
                # if len(header) > 1:
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
                # print(f"l_lipid_loc_temp: {l_lipid_loc_temp}")
                l_lipid_loc = [
                    l_lipid_loc_temp[i]
                    for i, x in enumerate(
                        data.get_annotations().iloc[l_lipid_loc_temp]["slice"] == slice_index
                    )
                    if x
                ]
                # Record location and lipid name
                lipid_index = l_lipid_loc[0] if len(l_lipid_loc) > 0 else -1

                # If lipid has already been selected before, replace the index
                if header_1 == header:
                    lipid_1_index = lipid_index
                elif header_2 == header:
                    lipid_2_index = lipid_index
                elif header_3 == header:
                    lipid_3_index = lipid_index

            logging.info("Returning updated lipid data")
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
                # None,
            )

        # If lipids have been added from dropdown menu
        elif id_input == "page-3-dropdown-lipids":
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
            print(f"l_lipid_loc: {l_lipid_loc}")

            # If several lipids correspond to the selection, we have a problem...
            if len(l_lipid_loc) > 1:
                logging.warning("More than one lipid corresponds to the selection")
                l_lipid_loc = [l_lipid_loc[-1]]

            if len(l_lipid_loc) < 1:
                logging.warning("No lipid annotation exist. Taking another slice annotation")
                l_lipid_loc = (
                    data.get_annotations()
                    .index[
                        (data.get_annotations()["name"] == name)
                        & (data.get_annotations()["structure"] == structure)
                    ]
                    .tolist()
                )[:1]
                # return dash.no_update

            # Record location and lipid name
            lipid_index = l_lipid_loc[0]
            lipid_string = l_lipid_names[-1]

            change_made = False

            # If lipid has already been selected before, replace the index
            if header_1 == lipid_string:
                lipid_1_index = lipid_index
                change_made = True
            elif header_2 == lipid_string:
                lipid_2_index = lipid_index
                change_made = True
            elif header_3 == lipid_string:
                lipid_3_index = lipid_index
                change_made = True

            # If it's a new lipid selection, fill the first available header
            if lipid_string not in [header_1, header_2, header_2]:
                # Check first slot available
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
                change_made = True

            if change_made:
                logging.info(
                    "Changes have been made to the lipid selection or indexation,"
                    + " propagating callback."
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
                    # None,
                )
            else:
                return dash.no_update

    return dash.no_update

@app.callback(
    Output("page-3-dropdown-brain-regions", "data"),
    Input("main-slider", "data"),
)
def page_3_update_dropdown_option(slice_index):
    """This callback updates the dropdown options for the brain regions."""

    if slice_index is not None:
        return [
            {"label": atlas.dic_acronym_name[node], "value": atlas.dic_acronym_name[node]}
            for node in atlas.dic_existing_masks[slice_index]
        ]
    else:
        return dash.no_update

@app.callback(
    Output("page-3-dropdown-brain-regions", "disabled"),
    Input("page-3-dropdown-brain-regions", "value"),
    Input("page-3-reset-button", "n_clicks"),
    prevent_initial_call=True,
)
def page_3_disable_dropdown(l_selection, clicked_reset): 
    """This callback disables the dropdown options for the brain regions if more than four regions
    have already been selected."""

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-3-reset-button":
        return False

    if l_selection is not None:
        if len(l_selection) > 0 and len(l_selection) < 4:
            return False
        elif len(l_selection) >= 4:
            return True
    return dash.no_update


@app.callback(
    Output("page-3-dropdown-brain-regions", "value"),
    Input("page-3-reset-button", "n_clicks"),
    Input("main-slider", "data"),
    prevent_initial_call=True,
)
def page_3_empty_dropdown(clicked_reset, slice_index): # 
    """This callback empties the dropdown options for the brain regions when clicking reset or
    changing slice."""
    return []


@app.callback(
    Output("page-3-button-compute-spectra", "disabled"),
    Input("page-3-graph-heatmap-mz-selection", "relayoutData"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-dropdown-brain-regions", "value"),
    prevent_initial_call=True,
)
def page_3_button_compute_spectra(relayoutData, clicked_reset, mask):
    """This callback disables the button to compute spectra if no region has been selected or
    drawn."""
    print("\n============ page_3_button_compute_spectra =============")
    print("dash.callback_context.triggered\n:", dash.callback_context.triggered)
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    
    # In case of reset, disable button
    if id_input == "page-3-reset-button":
        return True

    # If at least one mask, activate button
    if mask is not None:
        if mask != []:
            return False

    # If at least one drawn shape, activate button
    if relayoutData is not None:
        if "shapes" in relayoutData:
            if len(relayoutData["shapes"]) > 0:
                return False

    return True

@app.callback(
    Output("page-3-graph-spectrum-per-pixel", "style"),
    Output("page-3-alert-2", "style"),
    # Output("page-3-graph-heatmap-per-lipid", "style"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    State("page-3-dropdown-brain-regions", "value"),
    State("page-3-graph-heatmap-mz-selection", "relayoutData"),
    prevent_initial_call=True,
)
def page_3_display_high_res_mz_plot(clicked_reset, clicked_compute, mask, relayoutData):
    """This callback displays the m/z plot and heatmap when clicking on the compute spectra
    button (and hide the corresponding alert)."""
    print("\n============ page_3_display_high_res_mz_plot =============")
    print("dash.callback_context.triggered\n:", dash.callback_context.triggered)
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # If reset button has been clicked, hide all plot
    if id_input == "page-3-reset-button":
        return {"display": "none"}, {"display": "none"} # , {"display": "none"}

    # If the button to compute spectra has been clicked, display the plots
    elif id_input == "page-3-button-compute-spectra":
        logging.info("Compute spectra button has been clicked")

        # If at least one mask, display the plots
        if mask is not None:
            if mask != []:
                logging.info("One or several masks have been selected, displaying graphs")
                return (
                    {"height": HEIGHT_PLOTS},
                    {"display": "none"},
                    # {
                    #     "height": 2 * HEIGHT_PLOTS,
                    #     "background-color": "#1d1c1f",
                    # },
                )

        # If at least one drawn region, display the plots
        if relayoutData is not None:
            if "shapes" in relayoutData:
                if len(relayoutData["shapes"]) > 0:
                    if len(relayoutData["shapes"]) <= 4:
                        logging.info("One or several shapes have been selected, displaying graphs")
                        return (
                            {"height": HEIGHT_PLOTS},
                            {"display": "none"},
                            # {
                            #     "height": 2 * HEIGHT_PLOTS,
                            #     "background-color": "#1d1c1f",
                            # },
                        )
                    else:
                        return {"display": "none"}, {} # , {"display": "none"}

    return dash.no_update

@app.callback(
    Output("dcc-store-list-mz-spectra", "data"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    Input("page-3-dcc-store-path-heatmap", "data"),
    Input("page-3-reset-button", "n_clicks"),
    Input("url", "pathname"),
    Input("main-slider", "data"),
    State("page-3-dropdown-brain-regions", "value"),
    State("dcc-store-shapes-and-masks", "data"),
    State("page-3-graph-heatmap-mz-selection", "relayoutData"),
    State("session-id", "data"),
    prevent_initial_call=True,
)
def page_3_record_spectra(
    clicked_compute,
    l_paths,
    cliked_reset,
    url,
    slice_index,
    l_mask_name,
    l_shapes_and_masks,
    relayoutData,
    session_id,
):
    """This callback is used to compute and record the average spectrum of the selected
    region(s)."""
    print("\n============ page_3_record_spectra =============")
    print("dash.callback_context.triggered\n:", dash.callback_context.triggered)
    print("l_shapes_and_masks: ", len(l_shapes_and_masks))
    print("relayoutData: ", relayoutData)
    
    # Deactivated switches
    as_enrichment = False
    log_transform = False

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    print("id_input: ", id_input)
    print("value_input: ", value_input)

    # If a new slice is loaded or the page just got loaded, do nothing because
    # of automatic relayout of the heatmap which is automatically triggered when the page is loaded
    if len(id_input) == 0 or (value_input == "relayoutData" and relayoutData == {"autosize": True}):
        return dash.no_update

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button": # or id_input == "url":
        return []

    # If the user clicked on the button after drawing a region and/or selecting a structure
    elif id_input == "page-3-button-compute-spectra" and len(l_shapes_and_masks) > 0:
        logging.info("Starting to compute spectrum")

        # l_spectra = global_spectrum_store(
        #     slice_index, l_shapes_and_masks, l_mask_name, relayoutData, as_enrichment, log_transform
        # )

        # if l_spectra is not None:
        #     if l_spectra != []:
        #         logging.info("Spectra computed, returning it now")
        #         # Return a dummy variable to indicate that the spectrum has been computed and
        #         # trigger the callback
        #         return "ok"
        # logging.warning("A bug appeared during spectrum computation")
        return "ok"

    return []


@app.callback(
    Output("page-3-graph-spectrum-per-pixel", "figure"),
    Input("page-3-reset-button", "n_clicks"),
    Input("dcc-store-list-mz-spectra", "data"),
    Input("main-slider", "data"),
    State("page-3-dropdown-brain-regions", "value"),
    State("dcc-store-shapes-and-masks", "data"),
    State("page-3-graph-heatmap-mz-selection", "relayoutData"),
    prevent_initial_call=True,
)
def page_3_plot_spectrum(
    cliked_reset,
    l_spectra,
    slice_index,
    l_mask_name,
    l_shapes_and_masks,
    relayoutData,
):
    """This callback is used to plot the spectra of the selected region(s)."""
    print("\n============ page_3_plot_spectrum =============")
    print("dash.callback_context.triggered\n:", dash.callback_context.triggered)
    print("l_shapes_and_masks: ", l_shapes_and_masks)
    print("relayoutData: ", relayoutData)

    # Deactivated switches
    as_enrichment = False
    log_transform = False

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # If a new slice is loaded or the page just got loaded, do nothing
    if len(id_input) == 0:
        return dash.no_update

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button" or l_spectra is None or l_spectra == []:
        return go.Figure() # figures.return_empty_spectrum()

    # Do nothing if l_spectra is None or []
    elif id_input == "dcc-store-list-mz-spectra":
        if len(l_spectra) > 0 or l_spectra == "ok":
            logging.info("Starting spectra plotting now")
            fig_mz = go.Figure()

            # # Compute the average spectra
            # l_spectra = global_spectrum_store(
            #     slice_index,
            #     l_shapes_and_masks,
            #     l_mask_name,
            #     relayoutData,
            #     as_enrichment,
            #     log_transform,
            # )
            # ll_idx_labels = global_lipid_index_store(data, slice_index, l_spectra)
            # for idx_spectra, (spectrum, l_idx_labels) in enumerate(zip(l_spectra, ll_idx_labels)):
            #     # Find color of the current spectrum
            #     col = config.l_colors[idx_spectra % 4]

            #     # Compute (again) the numpy array of the spectrum
            #     grah_scattergl_data = np.array(spectrum, dtype=np.float32)

            #     # Two different functions so that's there's a unique output for each numba function
            #     l_idx_kept = return_idx_sup(l_idx_labels)
            #     l_idx_unkept = return_idx_inf(l_idx_labels)

            #     # Pad annotated trace with zeros
            #     (
            #         grah_scattergl_data_padded_annotated,
            #         array_index_padding,
            #     ) = add_zeros_to_spectrum(
            #         grah_scattergl_data[:, l_idx_kept],
            #         pad_individual_peaks=True,
            #         padding=10**-4,
            #     )
            #     l_mz_with_lipids = grah_scattergl_data_padded_annotated[0, :]
            #     l_intensity_with_lipids = grah_scattergl_data_padded_annotated[1, :]
            #     l_idx_labels_kept = l_idx_labels[l_idx_kept]

            #     # @njit # We need to wait for the support of np.insert, still relatively fast anyway
            #     def pad_l_idx_labels(l_idx_labels_kept, array_index_padding):
            #         pad = 0
            #         # The initial condition in the loop is only evaluated once so no problem with
            #         # insertion afterwards
            #         for i in range(len(l_idx_labels_kept)):
            #             # Array_index_padding[i] will be 0 or 2 (peaks are padded with 2 zeros, one
            #             # on each side)
            #             for j in range(array_index_padding[i]):
            #                 # i+1 instead of i plus insert on the right of the element i
            #                 l_idx_labels_kept = np.insert(l_idx_labels_kept, i + 1 + pad, -1)
            #                 pad += 1
            #         return l_idx_labels_kept

            #     l_idx_labels_kept = list(pad_l_idx_labels(l_idx_labels_kept, array_index_padding))

            #     # Rebuild lipid name from structure, cation, etc.
            #     l_labels_all_lipids = data.compute_l_labels(slice_index)
            #     l_labels = [
            #         l_labels_all_lipids[idx] if idx != -1 else "" for idx in l_idx_labels_kept
            #     ]

            #     # Add annotated trace to plot
            #     fig_mz.add_trace(
            #         go.Scattergl(
            #             x=l_mz_with_lipids,
            #             y=l_intensity_with_lipids,
            #             visible=True,
            #             marker_color=col,
            #             name="Annotated peaks",
            #             showlegend=True,
            #             fill="tozeroy",
            #             hovertemplate="Lipid: %{text}<extra></extra>",
            #             text=l_labels,
            #         )
            #     )

            #     # Pad not annotated traces peaks with zeros
            #     grah_scattergl_data_padded, array_index_padding = add_zeros_to_spectrum(
            #         grah_scattergl_data[:, l_idx_unkept],
            #         pad_individual_peaks=True,
            #         padding=10**-4,
            #     )
            #     l_mz_without_lipids = grah_scattergl_data_padded[0, :]
            #     l_intensity_without_lipids = grah_scattergl_data_padded[1, :]

            #     # Add not-annotated trace to plot.
            #     fig_mz.add_trace(
            #         go.Scattergl(
            #             x=l_mz_without_lipids,
            #             y=l_intensity_without_lipids,
            #             visible=True,
            #             marker_color=col,
            #             name="Unknown peaks",
            #             showlegend=True,
            #             fill="tozeroy",
            #             opacity=0.2,
            #             hoverinfo="skip",
            #             # text=l_idx_labels_kept,
            #         )
            #     )

            # # Define figure layout
            # fig_mz.update_layout(
            #     margin=dict(t=5, r=0, b=10, l=0),
            #     showlegend=True,
            #     xaxis=dict(title="m/z"),
            #     yaxis=dict(title="Intensity"),
            #     template="plotly_dark",
            #     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.1),
            # )
            # fig_mz.layout.plot_bgcolor = "rgba(0,0,0,0)"
            # fig_mz.layout.paper_bgcolor = "rgba(0,0,0,0)"

            # logging.info("Spectra plotted. Returning it now")

            # Return dummy variable for ll_idx_labels to confirm that it has been computed
            return fig_mz

    return dash.no_update

# clientside_callback(
#     """
#     function(n_clicks){
#         if(n_clicks > 0){
#             domtoimage.toBlob(document.getElementById('page-3-graph-heatmap-per-lipid'))
#                 .then(function (blob) {
#                     window.saveAs(blob, 'heatmap_comparison.png');
#                 }
#             );
#         }
#     }
#     """,
#     Output("page-3-download-heatmap-button", "n_clicks"),
#     Input("page-3-download-heatmap-button", "n_clicks"),
# )
# """This clientside callback allows to download the main heatmap as a png file."""

# clientside_callback(
#     """
#     function(n_clicks){
#         if(n_clicks > 0){
#             domtoimage.toBlob(document.getElementById('page-3-div-graph-lipid-comparison'))
#                 .then(function (blob) {
#                     window.saveAs(blob, 'plot_region_selection.png');
#                 }
#             );
#         }
#     }
#     """,
#     Output("page-3-download-plot-button", "n_clicks"),
#     Input("page-3-download-plot-button", "n_clicks"),
# )
# """This clientside callback allows to download the heatmap used to show differential lipid 
# expression in the selected regions as a png file."""

@app.callback(
    Output("page-4-drawer-region-selection", "is_open"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    Input("page-4-close-drawer-region-selection", "n_clicks"),
    State("page-4-drawer-region-selection", "is_open"),
)
def toggle_offcanvas(n1, n2, is_open): #  
    """This callback is used to open the drawer containing the lipid expression analysis of the
    selected region."""
    if n1 or n2: #  
        return not is_open
    return is_open
