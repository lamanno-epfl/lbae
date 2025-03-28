# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to select and visualize lipid programs according to pre-existing 
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

# LBAE imports
from app import app, program_figures, program_data, cache_flask, atlas

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
                dcc.Graph(
                    id="page-2bis-graph-heatmap-mz-selection",
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
                    figure=program_figures.compute_heatmap_per_lipid(
                        slice_index,
                        "PC",
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
                        dmc.Text("Choose up to 3 lipid programs", size="lg"),
                        dmc.Group(
                            spacing="xs",
                            align="flex-start",
                            children=[
                                dmc.MultiSelect(
                                    id="page-2bis-dropdown-lps",
                                    data=program_data.return_lipid_options(),
                                    value=['PC'],
                                    searchable=True,
                                    nothingFound="No LP found",
                                    radius="md",
                                    size="xs",
                                    placeholder="Choose up to 3 LPs",
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
                                    id="page-2bis-rgb-button",
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
                                    id="page-2bis-colormap-button",
                                    variant="filled",
                                    color="cyan",
                                    radius="md",
                                    size="xs",
                                    disabled=True,
                                    compact=False,
                                    loading=False,
                                ),
                            ],
                        ),
                    ],
                ),
                dmc.Text(
                    id="page-2bis-badge-input",
                    children="Current input: ",
                    class_name="position-absolute",
                    style={"right": "1%", "top": "1em"},
                ),
                dmc.Badge(
                    id="page-2bis-badge-lp-1",
                    children="name-lp-1",
                    color="red",
                    variant="filled",
                    class_name="d-none",
                    style={"right": "1%", "top": "4em"},
                ),
                dmc.Badge(
                    id="page-2bis-badge-lp-2",
                    children="name-lp-2",
                    color="teal",
                    variant="filled",
                    class_name="d-none",
                    style={"right": "1%", "top": "6em"},
                ),
                dmc.Badge(
                    id="page-2bis-badge-lp-3",
                    children="name-lp-3",
                    color="blue",
                    variant="filled",
                    class_name="d-none",
                    style={"right": "1%", "top": "8em"},
                ),
                dmc.Text(
                    "",
                    id="page-2bis-graph-hover-text",
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
                    id="page-2bis-toggle-annotations",
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
                            id="page-2bis-download-data-button",
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
                            id="page-2bis-download-image-button",
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
                dcc.Download(id="page-2bis-download-data"),
            ],
        ),
    )

    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================

@app.callback(
    Output("page-2bis-graph-hover-text", "children"),
    Input("page-2bis-graph-heatmap-mz-selection", "hoverData"),
    Input("main-slider", "data"),
)
def page_2bis_hover(hoverData, slice_index):
    """This callback is used to update the text displayed when hovering over the slice image."""
    acronym_mask = program_data.acronyms_masks[slice_index]
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
    Output("page-2bis-graph-heatmap-mz-selection", "figure"),
    Output("page-2bis-badge-input", "children"),
    
    Input("main-slider", "data"),
    Input("page-2bis-selected-lp-1", "data"),
    Input("page-2bis-selected-lp-2", "data"),
    Input("page-2bis-selected-lp-3", "data"),
    Input("page-2bis-rgb-button", "n_clicks"),
    Input("page-2bis-colormap-button", "n_clicks"),
    Input("page-2bis-toggle-annotations", "checked"),
    
    State("page-2bis-badge-input", "children"),
)
def page_2bis_plot_graph_heatmap_mz_selection(
    slice_index,
    lp_1_index,
    lp_2_index,
    lp_3_index,
    n_clicks_button_rgb,
    n_clicks_button_colormap,
    annotations_checked,
    graph_input,
):
    """This callback plots the heatmap of the selected LP(s)."""
    # print(f"\n========== page_2bis_plot_graph_heatmap_mz_selection ==========")
    logging.info("Entering function to plot heatmap or RGB depending on LP selection")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    
    overlay = program_data.get_aba_contours(slice_index) if annotations_checked else None

    # Handle annotations toggle separately to preserve figure state
    if id_input == "page-2bis-toggle-annotations":
        if lp_1_index >= 0 or lp_2_index >= 0 or lp_3_index >= 0:
            ll_lp_names = [
                program_data.get_annotations().iloc[index]["name"]
                
                if index != -1
                else None
                for index in [lp_1_index, lp_2_index, lp_3_index]
            ]
    
            if graph_input == "Current input: " + "LP selection RGB":
                return (
                    program_figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lp_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    ),
                    graph_input,
                )

            elif graph_input == "Current input: " + "LP selection colormap":
                if ll_lp_names.count(None) == len(ll_lp_names) - 1 and None in ll_lp_names:
                    nonull_ll_lp_names = [x for x in ll_lp_names if x is not None][0]
                    image = program_figures.compute_image_per_lipid(
                        slice_index,
                        RGB_format=False,
                        lipid_name=nonull_ll_lp_names,
                        cache_flask=cache_flask,
                    )
                    return (
                        program_figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                        ),
                        "Current input: " + "LP selection colormap",
                    )
                else:
                    return (
                        program_figures.compute_rgb_image_per_lipid_selection(
                            slice_index,
                            ll_lipid_names=ll_lp_names,
                            cache_flask=cache_flask,
                            overlay=overlay,
                        ),
                        "Current input: " + "LP selection RGB",
                    )

        return dash.no_update

    # If a lp selection has been done
    if (
        id_input == "page-2bis-selected-lp-1"
        or id_input == "page-2bis-selected-lp-2"
        or id_input == "page-2bis-selected-lp-3"
        or id_input == "page-2bis-rgb-button"
        or id_input == "page-2bis-colormap-button"
        or (
            (id_input == "main-slider")
            and (
                graph_input == "Current input: " + "LP selection colormap"
                or graph_input == "Current input: " + "LP selection RGB"
            )
        )
    ):
        if lp_1_index >= 0 or lp_2_index >= 0 or lp_3_index >= 0:
            ll_lp_names = [
                program_data.get_annotations().iloc[index]["name"]
                if index != -1
                else None
                for index in [lp_1_index, lp_2_index, lp_3_index]
            ]

            # Check if the current plot must be a heatmap
            if (
                id_input == "page-2bis-colormap-button"
                or (
                    id_input == "main-slider"
                    and graph_input == "Current input: " + "LP selection colormap"
                )
            ):
                # you also need to check that only one lipid is selected
                if ll_lp_names.count(None) == len(ll_lp_names) - 1 and None in ll_lp_names:
                    nonull_ll_lp_names = [x for x in ll_lp_names if x is not None][0]
                    image = program_figures.compute_image_per_lipid(
                        slice_index,
                        RGB_format=False,
                        lipid_name=nonull_ll_lp_names,
                        cache_flask=cache_flask,
                    )
                    return (
                        program_figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                        ),
                    "Current input: " + "LP selection colormap",
                )
                else:
                    logging.info("Trying to plot a heatmap for more than one LP, not possible. Return the rgb plot instead")
                    return (
                        program_figures.compute_rgb_image_per_lipid_selection(
                            slice_index,
                            ll_lipid_names=ll_lp_names,
                            cache_flask=cache_flask,
                            overlay=overlay,
                        ),
                        "Current input: " + "LP selection RGB",
                    )

            # Or if the current plot must be an RGB image
            elif (
                id_input == "page-2bis-rgb-button"
                or (
                    id_input == "main-slider"
                    and graph_input == "Current input: " + "LP selection RGB"
                )
                or (
                    id_input == "page-2bis-toggle-apply-transform"
                    and graph_input == "Current input: " + "LP selection RGB"
                )
            ):
                return (
                    program_figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lp_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    ),
                    "Current input: " + "LP selection RGB",
                )

            # Plot RBG By default
            else:
                logging.info("Right before calling the graphing function")
                return (
                    program_figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lp_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    ),
                    "Current input: " + "LP selection RGB",
                )
        elif (
            id_input == "main-slider" and graph_input == "Current input: "
        ):
            return (
                program_figures.compute_heatmap_per_lipid(slice_index, 
                                                "PC",
                                                cache_flask=cache_flask,
                                                overlay=overlay),
                "Current input: " + "PC",
            )
        else:
            # No lipid has been selected, return image from boundaries
            return (
                program_figures.compute_heatmap_per_lipid(slice_index, 
                                                "PC",
                                                # lb, hb, 
                                                cache_flask=cache_flask,
                                                overlay=overlay),
                "Current input: " + "PC",
            )
            
    # If no trigger, the page has just been loaded, so load new figure with default parameters
    else:
        return dash.no_update


@app.callback(
    Output("page-2bis-badge-lp-1", "children"),
    Output("page-2bis-badge-lp-2", "children"),
    Output("page-2bis-badge-lp-3", "children"),
    Output("page-2bis-selected-lp-1", "data"),
    Output("page-2bis-selected-lp-2", "data"),
    Output("page-2bis-selected-lp-3", "data"),
    Output("page-2bis-badge-lp-1", "class_name"),
    Output("page-2bis-badge-lp-2", "class_name"),
    Output("page-2bis-badge-lp-3", "class_name"),
    Input("page-2bis-dropdown-lps", "value"),
    Input("page-2bis-badge-lp-1", "class_name"),
    Input("page-2bis-badge-lp-2", "class_name"),
    Input("page-2bis-badge-lp-3", "class_name"),
    Input("main-slider", "data"),
    State("page-2bis-selected-lp-1", "data"),
    State("page-2bis-selected-lp-2", "data"),
    State("page-2bis-selected-lp-3", "data"),
    State("page-2bis-badge-lp-1", "children"),
    State("page-2bis-badge-lp-2", "children"),
    State("page-2bis-badge-lp-3", "children"),
)
def page_2bis_add_toast_selection(
    l_lp_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    lp_1_index,
    lp_2_index,
    lp_3_index,
    header_1,
    header_2,
    header_3,
):
    """This callback adds the selected LP to the selection."""
    logging.info("Entering function to update LP data")
    # print("\n================ page_2bis_add_toast_selection ================")
    
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    # if page-2bis-dropdown-lps is called while there's no lipid name defined, it means the page
    # just got loaded
    if len(id_input) == 0 or (id_input == "page-2bis-dropdown-lps" and l_lp_names is None):
        # Initialize with PC as the default lipid
        default_lp = "PC"
        # Find lipid location for the default lipid
        # name, structure = default_lp.split(" ")
        name = default_lp
        l_lp_loc = (
            program_data.get_annotations()
            .index[
                (program_data.get_annotations()["name"] == name)
                # & (program_data.get_annotations()["structure"] == structure)
                & (program_data.get_annotations()["slice"] == slice_index)
            ]
            .tolist()
        )
        
        # If no match for current slice, try to find it in any slice
        if len(l_lp_loc) == 0:
            l_lp_loc = (
                program_data.get_annotations()
                .index[
                    (program_data.get_annotations()["name"] == name)
                    # & (program_data.get_annotations()["structure"] == structure)
                ]
                .tolist()
            )[:1]
        
        # Set default lipid if found
        if len(l_lp_loc) > 0:
            lp_1_index = l_lp_loc[0]
            header_1 = default_lp
            class_name_badge_1 = "position-absolute"
            return header_1, "", "", lp_1_index, -1, -1, class_name_badge_1, "d-none", "d-none"
        else:
            # Fallback if lipid not found
            return "", "", "", -1, -1, -1, "d-none", "d-none", "d-none", # None

    # If one or several lipids have been deleted
    if l_lp_names is not None:
        if len(l_lp_names) < len(
            [x for x in [lp_1_index, lp_2_index, lp_3_index] if x != -1]
        ):
            logging.info("One or several LPs have been deleter. Cleaning LP badges now.")
            for idx_header, header in enumerate([header_1, header_2, header_3]):
                found = False
                for lp_name in l_lp_names:
                    if lp_name == header:
                        found = True
                if not found:
                    if idx_header == 0:
                        header_1 = ""
                        lp_1_index = -1
                        class_name_badge_1 = "d-none"
                    if idx_header == 1:
                        header_2 = ""
                        lp_2_index = -1
                        class_name_badge_2 = "d-none"
                    if idx_header == 2:
                        header_3 = ""
                        lp_3_index = -1
                        class_name_badge_3 = "d-none"

            return (
                header_1,
                header_2,
                header_3,
                lp_1_index,
                lp_2_index,
                lp_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
            )

    # Otherwise, update selection or add lipid
    if (
        id_input == "page-2bis-dropdown-lps" and l_lp_names is not None
    ) or id_input == "main-slider":

        # If a new slice has been selected
        if id_input == "main-slider":
            # for each lipid, get lipid name, structure and cation
            for header in [header_1, header_2, header_3]:
                name = header
            
                # Find lipid location
                l_lp_loc_temp = (
                    program_data.get_annotations()
                    .index[
                        (program_data.get_annotations()["name"] == name)
                    ]
                    .tolist()
                )
                l_lp_loc = [
                    l_lp_loc_temp[i]
                    for i, x in enumerate(
                        program_data.get_annotations().iloc[l_lp_loc_temp]["slice"] == slice_index
                    )
                    if x
                ]
                
                # Record location and lipid name
                lp_index = l_lp_loc[0] if len(l_lp_loc) > 0 else -1

                # If lipid has already been selected before, replace the index
                if header_1 == header:
                    lp_1_index = lp_index
                elif header_2 == header:
                    lp_2_index = lp_index
                elif header_3 == header:
                    lp_3_index = lp_index

            logging.info("Returning updated LP data")
            return (
                header_1,
                header_2,
                header_3,
                lp_1_index,
                lp_2_index,
                lp_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
                # None,
            )

        # If lipids have been added from dropdown menu
        elif id_input == "page-2bis-dropdown-lps":
            # Get the lp name
            name = l_lp_names[-1]
            
            # Find lipid location
            l_lp_loc = (
                program_data.get_annotations()
                .index[
                    (program_data.get_annotations()["name"] == name)
                    & (program_data.get_annotations()["slice"] == slice_index)
                ]
                .tolist()
            )
            
            # If several lipids correspond to the selection, we have a problem...
            if len(l_lp_loc) > 1:
                logging.warning("More than one LP corresponds to the selection")
                l_lp_loc = [l_lp_loc[-1]]

            if len(l_lp_loc) < 1:
                logging.warning("No LP annotation exist. Taking another slice annotation")
                l_lp_loc = (
                    program_data.get_annotations()
                    .index[
                        (program_data.get_annotations()["name"] == name)
                    ]
                    .tolist()
                )[:1]
                # return dash.no_update

            # Record location and lipid name
            lp_index = l_lp_loc[0]
            lp_string = l_lp_names[-1]

            change_made = False

            # If lipid has already been selected before, replace the index
            if header_1 == lp_string:
                lp_1_index = lp_index
                change_made = True
            elif header_2 == lp_string:
                lp_2_index = lp_index
                change_made = True
            elif header_3 == lp_string:
                lp_3_index = lp_index
                change_made = True

            # If it's a new LP selection, fill the first available header
            if lp_string not in [header_1, header_2, header_2]:
                # Check first slot available
                if class_name_badge_1 == "d-none":
                    header_1 = lp_string
                    lp_1_index = lp_index
                    class_name_badge_1 = "position-absolute"
                elif class_name_badge_2 == "d-none":
                    header_2 = lp_string
                    lp_2_index = lp_index
                    class_name_badge_2 = "position-absolute"
                elif class_name_badge_3 == "d-none":
                    header_3 = lp_string
                    lp_3_index = lp_index
                    class_name_badge_3 = "position-absolute"
                else:
                    logging.warning("More than 3 LPs have been selected")
                    return dash.no_update
                change_made = True

            if change_made:
                logging.info(
                    "Changes have been made to the LP selection or indexation,"
                    + " propagating callback."
                )
                return (
                    header_1,
                    header_2,
                    header_3,
                    lp_1_index,
                    lp_2_index,
                    lp_3_index,
                    class_name_badge_1,
                    class_name_badge_2,
                    class_name_badge_3,
                    # None,
                )
            else:
                return dash.no_update

    return dash.no_update

# # TODO: This callback must be completely rewritten to be able to download the data
# @app.callback(
#     Output("page-2bis-download-data", "data"),
#     Input("page-2bis-download-data-button", "n_clicks"),
#     State("page-2bis-selected-lp-1", "data"),
#     State("page-2bis-selected-lp-2", "data"),
#     State("page-2bis-selected-lp-3", "data"),
#     State("main-slider", "data"),
#     State("page-2bis-badge-input", "children"),
#     prevent_initial_call=True,
# )
# def page_2bis_download(
#     n_clicks,
#     lp_1_index,
#     lp_2_index,
#     lp_3_index,
#     slice_index,
#     graph_input,
# ):
#     """This callback is used to generate and download the data in proper format."""

#     # Current input is LP selection
#     if (
#         graph_input == "Current input: " + "LP selection colormap"
#         or graph_input == "Current input: " + "LP selection RGB"
#     ):
#         l_lps_indexes = [
#             x for x in [lp_1_index, lp_2_index, lp_3_index] if x is not None and x != -1
#         ]
#         # If lipids has been selected from the dropdown, filter them in the df and download them
#         if len(l_lps_indexes) > 0:

#             def to_excel(bytes_io):
#                 xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
#                 program_data.get_annotations().iloc[l_lps_indexes].to_excel(
#                     xlsx_writer, index=False, sheet_name="Selected lipid programs"
#                 )
#                 for i, index in enumerate(l_lps_indexes):
#                     name = (
#                         program_data.get_annotations().iloc[index]["name"]
#                         # + " "
#                         # + program_data.get_annotations().iloc[index]["structure"]
#                     )

#                     # Need to clean name to use it as a sheet name
#                     name = name.replace(":", "").replace("/", "")
#                     lb = float(program_data.get_annotations().iloc[index]["min"]) - 10**-2
#                     hb = float(program_data.get_annotations().iloc[index]["max"]) + 10**-2
#                     x, y = program_figures.compute_spectrum_high_res(
#                         slice_index,
#                         lb,
#                         hb,
#                         plot=False,
#                         # standardization=apply_transform,
#                         cache_flask=cache_flask,
#                     )
#                     df = pd.DataFrame.from_dict({"m/z": x, "Intensity": y})
#                     df.to_excel(xlsx_writer, index=False, sheet_name=name[:31])
#                 xlsx_writer.save()
#             return dcc.send_data_frame(to_excel, "my_lipid_selection.xlsx")

#     return dash.no_update

clientside_callback(
    """
    function(n_clicks){
        if(n_clicks > 0){
            domtoimage.toBlob(document.getElementById('page-2bis-graph-heatmap-mz-selection'))
                .then(function (blob) {
                    window.saveAs(blob, 'lipid_selection_plot.png');
                }
            );
        }
    }
    """,
    Output("page-2bis-download-image-button", "n_clicks"),
    Input("page-2bis-download-image-button", "n_clicks"),
)
"""This clientside callback is used to download the current heatmap."""


@app.callback(
    Output("page-2bis-rgb-button", "disabled"),
    Output("page-2bis-colormap-button", "disabled"),
    Input("page-2bis-selected-lp-1", "data"),
    Input("page-2bis-selected-lp-2", "data"),
    Input("page-2bis-selected-lp-3", "data"),
)
def page_2bis_active_download(lp_1_index, lp_2_index, lp_3_index):
    """This callback is used to toggle on/off the display rgb and colormap buttons."""
    logging.info("Enabled rgb and colormap buttons")
    # Get the current LP selection
    l_lps_indexes = [
        x for x in [lp_1_index, lp_2_index, lp_3_index] if x is not None and x != -1
    ]

    # If lipids has been selected from the dropdown, activate button
    if len(l_lps_indexes) > 0:
        return False, False
    else:
        return True, True