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
from app import app, figures, data, storage, cache_flask, atlas, grid_data

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
            },
            children=[
                html.Div(
                    className="fixed-aspect-ratio",
                    style={
                        "background-color": "#1d1c1f",
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
                                "width": "95%",
                                "height": "95%",
                                "position": "absolute",
                                "left": "0",
                                "top": "0",
                                "background-color": "#1d1c1f",
                            },
                            figure=figures.compute_heatmap_per_lipid(
                                slice_index,
                                "SM 34:1;O2",
                                cache_flask=cache_flask,
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
                                            id="page-2-dropdown-lipids",
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
                                        dmc.Button(
                                            children="Display as RGB",
                                            id="page-2-rgb-button",
                                            variant="filled",
                                            color="cyan",
                                            radius="md",
                                            size="xs",
                                            disabled=True,
                                            compact=False,
                                            loading=False,
                                        ),
                                        dmc.Button(
                                            children="Display as colormap",
                                            id="page-2-colormap-button",
                                            variant="filled",
                                            color="cyan",
                                            radius="md",
                                            size="xs",
                                            disabled=True,
                                            compact=False,
                                            loading=False,
                                        ),
                                        dmc.Button(
                                            children="Display all sections",
                                            id="page-2-all-sections-button",
                                            variant="filled",
                                            color="cyan",
                                            radius="md",
                                            size="xs",
                                            disabled=True,
                                            compact=False,
                                            loading=False,
                                        ),
                                        # dmc.Switch(
                                        #     id="page-2-toggle-apply-transform",
                                        #     label="Apply MAIA transform (if applicable)",
                                        #     checked=True,
                                        #     color="cyan",
                                        #     radius="xl",
                                        #     size="sm",
                                        # ),
                                    ],
                                ),
                            ],
                        ),
                        dmc.Text(
                            id="page-2-badge-input",
                            children="Current input: ",  #  + "m/z boundaries",
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
                        dmc.Switch(
                            id="page-2-toggle-annotations",
                            label="Allen Brain Atlas Annotations",
                            checked=False,
                            color="cyan",
                            radius="xl",
                            size="sm",
                            style={"left": "1%", "top": "20em"},
                            class_name="position-absolute",
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
def page_3_hover(hoverData, slice_index):
    """This callback is used to update the text displayed when hovering over the slice image."""
    # print("\n============ page_3_hover =============")
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
    Input("page-2-rgb-button", "n_clicks"),
    Input("page-2-colormap-button", "n_clicks"),
    Input("page-2-all-sections-button", "n_clicks"),
    Input("main-brain", "value"),
    # Input("page-2-button-bounds", "n_clicks"),
    Input("page-2-toggle-annotations", "checked"),

    # State("page-2-lower-bound", "value"),
    # State("page-2-upper-bound", "value"),
    State("page-2-badge-input", "children"),
)
def page_2_plot_graph_heatmap_mz_selection(
    slice_index,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    n_clicks_button_rgb,
    n_clicks_button_colormap,
    n_clicks_button_all_sections,
    brain_id,
    # n_clicks_button_bounds,
    # lb,
    # hb,
    annotations_checked,
    graph_input,
):
    """This callback plots the heatmap of the selected lipid(s)."""
    print(f"\n========== page_2_plot_graph_heatmap_mz_selection ==========")
    print('indices:', lipid_1_index, lipid_2_index, lipid_3_index)
    print(f"slice_index: {slice_index}")
    logging.info("Entering function to plot heatmap or RGB depending on lipid selection")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    print(f"id_input: {id_input}")    
    print("graph_input:", graph_input)
    print("brain_id:", brain_id)
    print("value_input:", value_input)

    overlay = data.get_aba_contours(slice_index) if annotations_checked else None

    # Handle annotations toggle separately to preserve figure state
    if id_input == "page-2-toggle-annotations":
        # print("annotations_checked:", annotations_checked)
        # print("lipid_1_index:", lipid_1_index)
        # print("lipid_2_index:", lipid_2_index)
        # print("lipid_3_index:", lipid_3_index)
        # print("overlay:", overlay.shape if overlay is not None else "None")
        if lipid_1_index >= 0 or lipid_2_index >= 0 or lipid_3_index >= 0:
            ll_lipid_names = [
                # [
                    ' '.join([
                        data.get_annotations().iloc[index]["name"].split('_')[i] + ' ' 
                        + data.get_annotations().iloc[index]["structure"].split('_')[i] 
                        for i in range(len(data.get_annotations().iloc[index]["name"].split('_')))
                    ])
                    # data.get_annotations().iloc[index]["name"]
                    # + " "
                    # + data.get_annotations().iloc[index]["structure"]
                    # + "_"
                    # + data.get_annotations().iloc[index]["cation"]
                # ]
                if index != -1
                else None
                for index in [lipid_1_index, lipid_2_index, lipid_3_index]
            ]
            print("ll_lipid_names:", ll_lipid_names)
            print("graph_input:", graph_input)

            if graph_input == "Current input: " + "Lipid selection RGB":
                print("returning option 1")
                return (
                    figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lipid_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    ),
                    graph_input,
                )

            elif graph_input == "Current input: " + "Lipid selection colormap":
                print("returning option 2")
                # you also need to check that only one lipid is selected
                if ll_lipid_names.count(None) == len(ll_lipid_names) - 1 and None in ll_lipid_names:
                    nonull_ll_lipid_names = [x for x in ll_lipid_names if x is not None][0]
                    image = figures.compute_image_per_lipid(
                        slice_index,
                        RGB_format=False,
                        lipid_name=nonull_ll_lipid_names,
                        cache_flask=cache_flask,
                    )
                    print("returning option 2.1")
                    return (
                        figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                        )
                        # figures.compute_heatmap_per_lipid_selection(
                        #     slice_index,
                        # # ll_lipid_bounds,
                        # # apply_transform=apply_transform,
                        # ll_lipid_names=ll_lipid_names,
                        # cache_flask=cache_flask,
                        ,
                        "Current input: " + "Lipid selection colormap",
                    )
                else:
                    print("returning option 2.2")
                    return (
                        figures.compute_rgb_image_per_lipid_selection(
                            slice_index,
                            ll_lipid_names=ll_lipid_names,
                            cache_flask=cache_flask,
                            overlay=overlay,
                        ),
                        "Current input: " + "Lipid selection RGB",
                    )

        return dash.no_update

    # If a lipid selection has been done
    if (
        id_input == "page-2-selected-lipid-1"
        or id_input == "page-2-selected-lipid-2"
        or id_input == "page-2-selected-lipid-3"
        or id_input == "page-2-rgb-button"
        or id_input == "page-2-colormap-button"
        or id_input == "page-2-all-sections-button"
        or id_input == "main-brain"
        or (
            (id_input == "main-slider") # or id_input == "page-2-toggle-apply-transform")
            and (
                graph_input == "Current input: " + "Lipid selection colormap"
                or graph_input == "Current input: " + "Lipid selection RGB"
                or graph_input == "Current input: " + "Lipid selection all sections"
            )
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
                    # data.get_annotations().iloc[index]["name"]
                    # + " "
                    # + data.get_annotations().iloc[index]["structure"]
                    # + "_"
                    # + data.get_annotations().iloc[index]["cation"]
                # ]
                if index != -1
                else None
                for index in [lipid_1_index, lipid_2_index, lipid_3_index]
            ]
            # print("ll_lipid_names:", ll_lipid_names)
            
            # Check if the current plot must be a heatmap
            if (
                id_input == "page-2-colormap-button"
                or (
                    id_input == "main-slider"
                    and graph_input == "Current input: " + "Lipid selection colormap"
                )
                # or (
                #     id_input == "page-2-toggle-apply-transform"
                #     and graph_input == "Current input: " + "Lipid selection colormap"
                # )
            ):
                # you also need to check that only one lipid is selected
                if ll_lipid_names.count(None) == len(ll_lipid_names) - 1 and None in ll_lipid_names:
                    nonull_ll_lipid_names = [x for x in ll_lipid_names if x is not None][0]
                    image = figures.compute_image_per_lipid(
                        slice_index,
                        RGB_format=False,
                        lipid_name=nonull_ll_lipid_names,
                        cache_flask=cache_flask,
                    )
                    return (
                        figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                        )
                        # figures.compute_heatmap_per_lipid_selection(
                        #     slice_index,
                        # # ll_lipid_bounds,
                        # # apply_transform=apply_transform,
                        # ll_lipid_names=ll_lipid_names,
                        # cache_flask=cache_flask,
                    ,
                    "Current input: " + "Lipid selection colormap",
                )
                else:
                    logging.info("Trying to plot a heatmap for more than one lipid, not possible. Return the rgb plot instead")
                    return (
                        figures.compute_rgb_image_per_lipid_selection(
                            slice_index,
                            ll_lipid_names=ll_lipid_names,
                            cache_flask=cache_flask,
                            overlay=overlay,
                        ),
                        "Current input: " + "Lipid selection RGB",
                    )

            # Or if the current plot must be an RGB image
            elif (
                id_input == "page-2-rgb-button"
                or (
                    id_input == "main-slider"
                    and graph_input == "Current input: " + "Lipid selection RGB"
                )
                # or (
                #     id_input == "page-2-toggle-apply-transform"
                #     and graph_input == "Current input: " + "Lipid selection RGB"
                # )
            ):
                return (
                    figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        # ll_lipid_bounds,
                        # apply_transform=apply_transform,
                        ll_lipid_names=ll_lipid_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    ),
                    "Current input: " + "Lipid selection RGB",
                )

            # Or if the current plot must be all sections
            elif (
                id_input == "page-2-all-sections-button"
                or (
                    id_input == "main-slider"
                    and graph_input == "Current input: " + "Lipid selection all sections"
                )
            ):
                print("--- option 1.4 ---")
                # Check that only one lipid is selected
                if ll_lipid_names.count(None) == len(ll_lipid_names) - 1 and None in ll_lipid_names:

                    print("INSIDE! brain_id:", brain_id)

                    nonull_ll_lipid_names = [x for x in ll_lipid_names if x is not None][0]
                    # Use the selected lipid instead of hardcoded one
                    image = grid_data.retrieve_grid_image(
                        lipid=nonull_ll_lipid_names,
                        sample=brain_id
                    )

                    return(figures.build_lipid_heatmap_from_image(
                                image, 
                                return_base64_string=False,
                                # overlay=overlay
                                ),
                            "Current input: " + "Lipid selection all sections")
                else:
                    print("--- option 1.4.2 ---")
                    logging.info("Trying to display all sections for more than one lipid, not possible. Using first selected lipid.")
                    # Get the first non-None lipid name
                    first_lipid = next((name for name in ll_lipid_names if name is not None), "SM 34:1;O2")
                    image = grid_data.retrieve_grid_image(
                        lipid=first_lipid,
                        sample=brain_id
                    )
                    
                    return(figures.build_lipid_heatmap_from_image(
                                image, 
                                return_base64_string=False,
                                overlay=overlay),
                            "Current input: " + "Lipid selection all sections")
            
            # Plot RBG By default
            else:
                logging.info("Right before calling the graphing function")
                return (
                    figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        # ll_lipid_bounds,
                        # apply_transform=apply_transform,
                        ll_lipid_names=ll_lipid_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    ),
                    "Current input: " + "Lipid selection RGB",
                )
        elif (
            id_input == "main-slider" and graph_input == "Current input: "
        ):
            print(f"No lipid has been selected, the current lipid is SM 34:1;O2 and the slice is {slice_index}")
            return (
                figures.compute_heatmap_per_lipid(slice_index, 
                                                "SM 34:1;O2",
                                                # lb, hb, 
                                                cache_flask=cache_flask,
                                                overlay=overlay),
                "Current input: " + "SM 34:1;O2",
            )
        else:
            # No lipid has been selected
            print(slice_index)
            return (
                figures.compute_heatmap_per_lipid(slice_index, 
                                                "SM 34:1;O2",
                                                # lb, hb, 
                                                cache_flask=cache_flask,
                                                overlay=overlay),
                "Current input: " + "SM 34:1;O2", # + "m/z boundaries"
            )

    # If no trigger, the page has just been loaded, so load new figure with default parameters
    else:
        return dash.no_update

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
    Input("page-2-dropdown-lipids", "value"),
    Input("page-2-badge-lipid-1", "class_name"),
    Input("page-2-badge-lipid-2", "class_name"),
    Input("page-2-badge-lipid-3", "class_name"),
    Input("main-slider", "data"),
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
    print("\n================ page_2_add_toast_selection ================")
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    # print(f"id_input: {id_input}")
    # print(f"value_input: {value_input}")
    # if page-2-dropdown-lipids is called while there's no lipid name defined, it means the page
    # just got loaded
    if len(id_input) == 0 or (id_input == "page-2-dropdown-lipids" and l_lipid_names is None):
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
        id_input == "page-2-dropdown-lipids" and l_lipid_names is not None
    ) or id_input == "main-slider":
        # If a new slice has been selected
        if id_input == "main-slider":
            # print(f"header_1: {header_1}")
            # print(f"header_2: {header_2}")
            # print(f"header_3: {header_3}")
            # for each lipid, get lipid name, structure and cation
            for header in [header_1, header_2, header_3]:
                # if len(header) > 1:
                if len(header.split(" ")) == 2:
                    name, structure = header.split(" ")
                else:   
                    name = "_".join(header.split(" ")[::2])
                    structure = "_".join(header.split(" ")[1::2])
                # print(f"name: {name}")
                # print(f"structure: {structure}")
            
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
                # print(f"l_lipid_loc: {l_lipid_loc}")
                # # Fill list with first annotation that exists if it can't find one for the
                # # current slice
                # if len(l_lipid_loc) == 0:
                #     l_lipid_loc = l_lipid_loc_temp[:1]

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
        elif id_input == "page-2-dropdown-lipids":
            # print(f"header_1: {header_1}")
            # print(f"header_2: {header_2}")
            # print(f"header_3: {header_3}")
            
            # Get the lipid name and structure
            # name, structure = l_lipid_names[-1].split(" ")

            # print(f"l_lipid_names[-1]: {l_lipid_names[-1]}")

            if len(l_lipid_names[-1]) == 2:
                name, structure = l_lipid_names[-1].split(" ")
            else:   
                name = "_".join(l_lipid_names[-1].split(" ")[::2])
                structure = "_".join(l_lipid_names[-1].split(" ")[1::2])
            print(f"name: {name}")
            print(f"structure: {structure}")

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
            # print(f"l_lipid_loc: {l_lipid_loc}")

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
            lipid_string = l_lipid_names[-1] # name + " " + structure ################################

            change_made = False

            # If lipid has already been selected before, replace the index
            if header_1 == lipid_string:
                # print("I am here")
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
    Output("page-2-download-data", "data"),
    Input("page-2-download-data-button", "n_clicks"),
    State("page-2-selected-lipid-1", "data"),
    State("page-2-selected-lipid-2", "data"),
    State("page-2-selected-lipid-3", "data"),
    State("main-slider", "data"),
    State("page-2-toggle-apply-transform", "checked"),
    State("page-2-badge-input", "children"),
    State("boundaries-low-resolution-mz-plot", "data"),
    State("page-2-lower-bound", "value"),
    State("page-2-upper-bound", "value"),
    prevent_initial_call=True,
)
def page_2_download(
    n_clicks,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    slice_index,
    apply_transform,
    graph_input,
    bound_high_res,
    lb,
    hb,
):
    """This callback is used to generate and download the data in proper format."""

    # Current input is lipid selection
    if (
        graph_input == "Current input: " + "Lipid selection colormap"
        or graph_input == "Current input: " + "Lipid selection RGB"
    ):
        l_lipids_indexes = [
            x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x is not None and x != -1
        ]
        # If lipids has been selected from the dropdown, filter them in the df and download them
        if len(l_lipids_indexes) > 0:

            def to_excel(bytes_io):
                xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                data.get_annotations().iloc[l_lipids_indexes].to_excel(
                    xlsx_writer, index=False, sheet_name="Selected lipids"
                )
                for i, index in enumerate(l_lipids_indexes):
                    name = (
                        data.get_annotations().iloc[index]["name"]
                        + " "
                        + data.get_annotations().iloc[index]["structure"]
                    )

                    # Need to clean name to use it as a sheet name
                    name = name.replace(":", "").replace("/", "")
                    lb = float(data.get_annotations().iloc[index]["min"]) - 10**-2
                    hb = float(data.get_annotations().iloc[index]["max"]) + 10**-2
                    x, y = figures.compute_spectrum_high_res(
                        slice_index,
                        lb,
                        hb,
                        plot=False,
                        standardization=apply_transform,
                        cache_flask=cache_flask,
                    )
                    df = pd.DataFrame.from_dict({"m/z": x, "Intensity": y})
                    df.to_excel(xlsx_writer, index=False, sheet_name=name[:31])
                xlsx_writer.save()

            return dcc.send_data_frame(to_excel, "my_lipid_selection.xlsx")

    # Current input is manual boundaries selection from input box
    if graph_input == "Current input: " + "m/z boundaries":
        lb, hb = float(lb), float(hb)
        if lb >= 400 and hb <= 1600 and hb - lb > 0 and hb - lb < 10:

            def to_excel(bytes_io):
                # Get spectral data
                mz, intensity = figures.compute_spectrum_high_res(
                    slice_index,
                    lb - 10**-2,
                    hb + 10**-2,
                    force_xlim=True,
                    standardization=apply_transform,
                    cache_flask=cache_flask,
                    plot=False,
                )

                # Turn to dataframe
                dataset = pd.DataFrame.from_dict({"m/z": mz, "Intensity": intensity})

                # Export to excel
                xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                dataset.to_excel(xlsx_writer, index=False, sheet_name="mz selection")
                xlsx_writer.save()

            return dcc.send_data_frame(to_excel, "my_boundaries_selection.xlsx")

    # Current input is boundaries from the low-res m/z plot
    elif graph_input == "Current input: " + "Selection from high-res m/z graph":
        if bound_high_res is not None:
            # Case the zoom is high enough
            if bound_high_res[1] - bound_high_res[0] <= 3:

                def to_excel(bytes_io):
                    # Get spectral data
                    bound_high_res = json.loads(bound_high_res)
                    mz, intensity = figures.compute_spectrum_high_res(
                        slice_index,
                        bound_high_res[0],
                        bound_high_res[1],
                        standardization=apply_transform,
                        cache_flask=cache_flask,
                        plot=False,
                    )

                    # Turn to dataframe
                    dataset = pd.DataFrame.from_dict({"m/z": mz, "Intensity": intensity})

                    # Export to excel
                    xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                    dataset.to_excel(xlsx_writer, index=False, sheet_name="mz selection")
                    xlsx_writer.save()

                return dcc.send_data_frame(to_excel, "my_boundaries_selection.xlsx")

    return dash.no_update

@app.callback(
    Output("page-2-rgb-button", "disabled"),
    Output("page-2-colormap-button", "disabled"),
    Output("page-2-all-sections-button", "disabled"),
    Input("page-2-selected-lipid-1", "data"),
    Input("page-2-selected-lipid-2", "data"),
    Input("page-2-selected-lipid-3", "data"),
)
def page_2_active_download(lipid_1_index, lipid_2_index, lipid_3_index):
    # print("lipid_1_index", lipid_1_index)
    # print("lipid_2_index", lipid_2_index)
    # print("lipid_3_index", lipid_3_index)
    """This callback is used to toggle on/off the display rgb and colormap buttons."""
    # logging.info("Enabled rgb and colormap buttons")
    # Get the current lipid selection
    l_lipids_indexes = [
        x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x is not None and x != -1
    ]
    # If lipids has been selected from the dropdown, activate button
    if len(l_lipids_indexes) > 0:
        # print("=============Disabled rgb and colormap buttons=============")
        return False, False, False
    else:
        # print("=============Enabled rgb and colormap buttons=============")
        return True, True, True

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
