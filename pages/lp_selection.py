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
import numpy as np
# threadpoolctl import threadpool_limits, threadpool_info
#threadpool_limits(limits=8)
import os
os.environ['OMP_NUM_THREADS'] = '6'

# LBAE imports
from app import app, program_figures, program_data, storage, cache_flask, atlas, grid_data

def cyan_aba_contours(overlay):
    cyan_overlay = overlay.copy()
    contour_mask = overlay[:, :, 3] > 0
    cyan_overlay[contour_mask] = [0, 255, 255, 200]  # RGB cyan with alpha=200
    return cyan_overlay

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
                dcc.Store(id="page-2bis-main-slider-style", data={"display": "block"}),
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
                                "height": "100vh",
                                "width": "100%",
                                "position": "absolute",
                                "left": "0",
                                "top": "0",
                                "background-color": "#1d1c1f",
                            },
                            figure=program_figures.compute_heatmap_per_lipid(
                                slice_index,
                                "mitochondrion",
                                cache_flask=cache_flask,
                                colormap_type="PuOr",
                            ),
                        ),
                        # Allen Brain Atlas switch (independent)
                        html.Div(
                            id="page-2bis-annotations-container",
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
                                    id="page-2bis-toggle-annotations",
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
                            "Visualize Lipid Programs",
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
                                dmc.Text("Choose up to 3 programs", size="lg"),
                                dmc.Group(
                                    spacing="xs",
                                    align="center",
                                    children=[
                                        dmc.MultiSelect(
                                            id="page-2bis-dropdown-programs",
                                            data=program_data.return_program_options(),
                                            value=['mitochondrion'],
                                            searchable=True,
                                            nothingFound="No lipid program found",
                                            radius="md",
                                            size="xs",
                                            placeholder="Choose up to 3 programs",
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
                                            id="page-2bis-rgb-group",
                                            style={
                                                "display": "flex", 
                                                "alignItems": "center", 
                                                "marginLeft": "15px"
                                            },
                                            children=[
                                                dmc.Switch(
                                                    id="page-2bis-rgb-switch",
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
                            id="page-2bis-sections-mode",
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
                            id="page-2bis-badge-input",
                            children="Now displaying:",
                            class_name="position-absolute",
                            style={"right": "1%", "top": "1em"},
                        ),
                        dmc.Badge(
                            id="page-2bis-badge-program-1",
                            children="name-program-1",
                            color="red",
                            variant="filled",
                            class_name="d-none",
                            style={"right": "1%", "top": "4em"},
                        ),
                        dmc.Badge(
                            id="page-2bis-badge-program-2",
                            children="name-program-2",
                            color="teal",
                            variant="filled",
                            class_name="d-none",
                            style={"right": "1%", "top": "6em"},
                        ),
                        dmc.Badge(
                            id="page-2bis-badge-program-3",
                            children="name-program-3",
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
    Input("page-2bis-selected-program-1", "data"),
    Input("page-2bis-selected-program-2", "data"),
    Input("page-2bis-selected-program-3", "data"),
    Input("page-2bis-rgb-switch", "checked"),
    Input("page-2bis-sections-mode", "value"),
    Input("main-brain", "value"),
    Input("page-2bis-toggle-annotations", "checked"),

    State("page-2bis-badge-input", "children"),
)
def page_2bis_plot_graph_heatmap_mz_selection(
    slice_index,
    program_1_index,
    program_2_index,
    program_3_index,
    rgb_mode,
    sections_mode,
    brain_id,
    annotations_checked,
    graph_input,
):
    """This callback plots the heatmap of the selected lipid program(s)."""
    logging.info("Entering function to plot heatmap or RGB depending on lipid selection")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    
    # overlay = program_data.get_aba_contours(slice_index) if annotations_checked else None
    overlay = cyan_aba_contours(program_data.get_aba_contours(slice_index)) if annotations_checked else None

    # Handle annotations toggle separately to preserve figure state
    if id_input == "page-2bis-toggle-annotations":
        if program_1_index >= 0 or program_2_index >= 0 or program_3_index >= 0:
            ll_program_names = [
                program_data.get_annotations().iloc[index]["name"]
                
                if index != -1
                else None
                for index in [program_1_index, program_2_index, program_3_index]
            ]
    
            # If all sections view is requested, only use first lipid
            if sections_mode == "all":
                active_programs = [name for name in ll_program_names if name is not None]
                first_program = active_programs[0] if active_programs else "mitochondrion"
                image = grid_data.retrieve_grid_image(
                    lipid=first_program,
                    sample=brain_id
                )
                return(program_figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                            colormap_type="PuOr"),
                        "Now displaying:")
            
            if rgb_mode and sections_mode != "all":
                return (
                    program_figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_program_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    ),
                    "Now displaying:",
                )
            else:
                # Check that only one lipid is selected for colormap mode
                active_programs = [name for name in ll_program_names if name is not None]
                if len(active_programs) == 1:
                    image = program_figures.compute_image_per_lipid(
                        slice_index,
                        RGB_format=False,
                        lipid_name=active_programs[0],
                        cache_flask=cache_flask,
                    )
                    return (
                        program_figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                            colormap_type="PuOr",
                        ),
                        "Now displaying:",
                    )
                else:
                    # If multiple lipids and not in RGB mode, force RGB mode (except in all sections mode)
                    if sections_mode != "all":
                        return (
                            program_figures.compute_rgb_image_per_lipid_selection(
                                slice_index,
                                ll_lipid_names=ll_program_names,
                                cache_flask=cache_flask,
                                overlay=overlay,
                            ),
                            "Now displaying:",
                        )
                    else:
                        # In all sections mode, use only first lipid
                        first_program = active_programs[0] if active_programs else "mitochondrion"
                        image = grid_data.retrieve_grid_image(
                            lipid=first_program,
                            sample=brain_id
                        )
                        return(program_figures.build_lipid_heatmap_from_image(
                                    image, 
                                    return_base64_string=False,
                                    overlay=overlay,
                                    colormap_type="PuOr"),
                                "Now displaying:")

        return dash.no_update

    # If a lipid selection has been done
    if (
        id_input == "page-2bis-selected-program-1"
        or id_input == "page-2bis-selected-program-2"
        or id_input == "page-2bis-selected-program-3"
        or id_input == "page-2bis-rgb-switch"
        or id_input == "page-2bis-sections-mode"
        or id_input == "main-brain"
        or id_input == "main-slider"
    ):
        if program_1_index >= 0 or program_2_index >= 0 or program_3_index >= 0:
            ll_program_names = [
                program_data.get_annotations().iloc[index]["name"]
                
                if index != -1
                else None
                for index in [program_1_index, program_2_index, program_3_index]
            ]

            # If all sections view is requested
            if sections_mode == "all":
                active_programs = [name for name in ll_program_names if name is not None]
                # Use first available lipid for all sections view
                first_program = active_programs[0] if active_programs else "mitochondrion"
                image = grid_data.retrieve_grid_image(
                    lipid=first_program,
                    sample=brain_id
                )
                
                return(program_figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                            colormap_type="PuOr"),
                        "Now displaying:")
            
            # Handle normal display mode (RGB or colormap)
            else:
                active_programs = [name for name in ll_program_names if name is not None]
                if rgb_mode:
                    return (
                        program_figures.compute_rgb_image_per_lipid_selection(
                            slice_index,
                            ll_lipid_names=ll_program_names,
                            cache_flask=cache_flask,
                            overlay=overlay,
                        ),
                        "Now displaying:",
                    )
                else:
                    # If not in RGB mode, use first lipid only
                    first_program = active_programs[0] if active_programs else "mitochondrion"
                    image = program_figures.compute_image_per_lipid(
                        slice_index,
                        RGB_format=False,
                        lipid_name=first_program,
                        cache_flask=cache_flask,
                    )
                    return (
                        program_figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                            colormap_type="PuOr",
                        ),
                        "Now displaying:",
                    )
        elif (
            id_input == "main-slider" and graph_input == "Now displaying:"
        ):
            logging.info(f"No lipid has been selected, the current lipid is mitochondrion and the slice is {slice_index}")
            return (
                program_figures.compute_heatmap_per_lipid(slice_index, 
                                                "mitochondrion",
                                                cache_flask=cache_flask,
                                                overlay=overlay,
                                                colormap_type="PuOr"),
                "Now displaying:",
            )
        else:
            # No lipid has been selected
            logging.info(f"No lipid has been selected, the current lipid is mitochondrion and the slice is {slice_index}")
            return (
                program_figures.compute_heatmap_per_lipid(slice_index, 
                                                "mitochondrion",
                                                cache_flask=cache_flask,
                                                overlay=overlay,
                                                colormap_type="PuOr"),
                "Now displaying:",
            )

    # If no trigger, the page has just been loaded, so load new figure with default parameters
    else:
        return (
            program_figures.compute_heatmap_per_lipid(slice_index, 
                                            "mitochondrion",
                                            cache_flask=cache_flask,
                                            overlay=overlay,
                                            colormap_type="PuOr"),
            "Now displaying:",
        )

@app.callback(
    Output("page-2bis-badge-program-1", "children"),
    Output("page-2bis-badge-program-2", "children"),
    Output("page-2bis-badge-program-3", "children"),
    Output("page-2bis-selected-program-1", "data"),
    Output("page-2bis-selected-program-2", "data"),
    Output("page-2bis-selected-program-3", "data"),
    Output("page-2bis-badge-program-1", "class_name"),
    Output("page-2bis-badge-program-2", "class_name"),
    Output("page-2bis-badge-program-3", "class_name"),
    Output("page-2bis-dropdown-programs", "value"),
    Input("page-2bis-dropdown-programs", "value"),
    Input("page-2bis-badge-program-1", "class_name"),
    Input("page-2bis-badge-program-2", "class_name"),
    Input("page-2bis-badge-program-3", "class_name"),
    Input("main-slider", "data"),
    Input("page-2bis-sections-mode", "value"),
    Input("page-2bis-rgb-switch", "checked"),
    State("page-2bis-selected-program-1", "data"),
    State("page-2bis-selected-program-2", "data"),
    State("page-2bis-selected-program-3", "data"),
    State("page-2bis-badge-program-1", "children"),
    State("page-2bis-badge-program-2", "children"),
    State("page-2bis-badge-program-3", "children"),
    State("main-brain", "value"),
)
def page_2bis_add_toast_selection(
    l_program_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    sections_mode,
    rgb_switch,
    program_1_index,
    program_2_index,
    program_3_index,
    header_1,
    header_2,
    header_3,
    brain_id,
):
    """This callback adds the selected lipid program to the selection."""
    logging.info("Entering function to update lipid program data")
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # Initialize with default lipid if no selection exists
    if len(id_input) == 0 or (id_input == "page-2bis-dropdown-programs" and l_program_names is None):
        default_program = "mitochondrion"
        name  = default_program
        l_program_loc = (
            program_data.get_annotations()
            .index[
                (program_data.get_annotations()["name"] == name)
                # & (program_data.get_annotations()["structure"] == structure)
                & (program_data.get_annotations()["slice"] == slice_index)
            ]
            .tolist()
        )
        
        if len(l_program_loc) == 0:
            l_program_loc = (
                program_data.get_annotations()
                .index[
                    (program_data.get_annotations()["name"] == name)
                    # & (program_data.get_annotations()["structure"] == structure)
                ]
                .tolist()
            )[:1]
        
        if len(l_program_loc) > 0:
            program_1_index = l_program_loc[0]
            header_1 = default_program
            class_name_badge_1 = "position-absolute"
            return header_1, "", "", program_1_index, -1, -1, class_name_badge_1, "d-none", "d-none", [default_program]
        else:
            return "", "", "", -1, -1, -1, "d-none", "d-none", "d-none", []

    # If RGB is turned off or sections mode is "all", keep only the first lipid
    if (id_input == "page-2bis-rgb-switch" and not rgb_switch) or (id_input == "page-2bis-sections-mode" and sections_mode == "all"):
        active_programs = []
        if header_1 and program_1_index != -1:
            active_programs.append((header_1, program_1_index))
        elif header_2 and program_2_index != -1:
            active_programs.append((header_2, program_2_index))
        elif header_3 and program_3_index != -1:
            active_programs.append((header_3, program_3_index))
            
        if active_programs:
            first_program, first_index = active_programs[0]
            return (first_program, "", "", first_index, -1, -1, 
                    "position-absolute", "d-none", "d-none", [first_program])
        return dash.no_update

    # Handle lipid deletion
    if l_program_names is not None and len(l_program_names) < len([x for x in [program_1_index, program_2_index, program_3_index] if x != -1]):
        logging.info("One or several lipids have been deleted. Reorganizing lipid badges.")
        
        # Create list of remaining lipids and their indices
        remaining_programs = []
        for program_name in l_program_names:
            # if len(program_name.split(" ")) == 2:
            #     name = program_name
            # else:   
            #     name = "_".join(lipid_name.split(" ")[::2])
            #     structure = "_".join(lipid_name.split(" ")[1::2])
            name = program_name
            print("name:", name)
                
            l_program_loc = (
                program_data.get_annotations()
                .index[
                    (program_data.get_annotations()["name"] == name)
                    # & (program_data.get_annotations()["structure"] == structure)
                    & (program_data.get_annotations()["slice"] == slice_index)
                ]
                .tolist()
            )
            print("l_program_loc:", l_program_loc)

            if len(l_program_loc) == 0:
                l_program_loc = (
                    program_data.get_annotations()
                    .index[
                        (program_data.get_annotations()["name"] == name)
                        # & (program_data.get_annotations()["structure"] == structure)
                    ]
                    .tolist()
                )[:1]
                
            if len(l_program_loc) > 0:
                remaining_programs.append((program_name, l_program_loc[0]))
        
        # Reset all slots
        header_1, header_2, header_3 = "", "", ""
        program_1_index, program_2_index, program_3_index = -1, -1, -1
        class_name_badge_1, class_name_badge_2, class_name_badge_3 = "d-none", "d-none", "d-none"
        
        # Fill slots in order with remaining lipids
        # If in all sections mode, only fill the first slot
        if sections_mode == "all" and remaining_programs:
            header_1 = remaining_programs[0][0]
            program_1_index = remaining_programs[0][1]
            class_name_badge_1 = "position-absolute"
            return (
                header_1,
                "",
                "",
                program_1_index,
                -1,
                -1,
                class_name_badge_1,
                "d-none",
                "d-none",
                [header_1]
            )
        else:
            for idx, (program_name, program_idx) in enumerate(remaining_programs):
                if idx == 0:
                    header_1 = program_name
                    program_1_index = program_idx
                    class_name_badge_1 = "position-absolute"
                elif idx == 1:
                    header_2 = program_name
                    program_2_index = program_idx
                    class_name_badge_2 = "position-absolute"
                elif idx == 2:
                    header_3 = program_name
                    program_3_index = program_idx
                    class_name_badge_3 = "position-absolute"
                
            return (
                header_1,
                header_2,
                header_3,
                program_1_index,
                program_2_index,
                program_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
                l_program_names
            )

    # Handle new lipid addition or slice change
    if (id_input == "page-2bis-dropdown-programs" and l_program_names is not None) or id_input == "main-slider":
        # If a new slice has been selected
        if id_input == "main-slider":
            # Update indices for existing lipids
            for header in [header_1, header_2, header_3]:
                # if header and len(header.split(" ")) == 2:
                #     name, structure = header.split(" ")
                # else:   
                #     name = "_".join(header.split(" ")[::2])
                #     structure = "_".join(header.split(" ")[1::2])
                name = header

                # Find lipid location
                l_program_loc_temp = (
                    program_data.get_annotations()
                    .index[
                        (program_data.get_annotations()["name"] == name)
                        # & (program_data.get_annotations()["structure"] == structure)
                    ]
                    .tolist()
                )
                
                l_program_loc = [
                    l_program_loc_temp[i]
                    for i, x in enumerate(
                        program_data.get_annotations().iloc[l_program_loc_temp]["slice"] == slice_index
                    )
                    if x
                ]
                
                program_index = l_program_loc[0] if len(l_program_loc) > 0 else -1

                if header_1 == header:
                    program_1_index = program_index
                elif header_2 == header:
                    program_2_index = program_index
                elif header_3 == header:
                    program_3_index = program_index

            # If in all sections mode, keep only first lipid
            if sections_mode == "all":
                current_programs = []
                if header_1:
                    current_programs.append(header_1)
                elif header_2:
                    current_programs.append(header_2)
                elif header_3:
                    current_programs.append(header_3)
                    
                if current_programs:
                    return (
                        current_programs[0],
                        "",
                        "",
                        program_1_index if header_1 else (program_2_index if header_2 else program_3_index),
                        -1,
                        -1,
                        "position-absolute",
                        "d-none",
                        "d-none",
                        current_programs[:1]
                    )

            return (
                header_1,
                header_2,
                header_3,
                program_1_index,
                program_2_index,
                program_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
                [h for h in [header_1, header_2, header_3] if h]
            )

        # If lipids have been added from dropdown menu
        elif id_input == "page-2bis-dropdown-programs":
            # # Get the lipid name and structure
            # if len(l_program_names[-1]) == 2:
            #     name, structure = l_program_names[-1].split(" ")
            # else:   
            #     name = "_".join(l_program_names[-1].split(" ")[::2])
            #     structure = "_".join(l_program_names[-1].split(" ")[1::2])
            name = l_program_names[-1]

            # Find lipid location
            l_program_loc = (
                program_data.get_annotations()
                .index[
                    (program_data.get_annotations()["name"] == name)
                    # & (program_data.get_annotations()["structure"] == structure)
                    & (program_data.get_annotations()["slice"] == slice_index)
                ]
                .tolist()
            )
            
            if len(l_program_loc) < 1:
                l_program_loc = (
                    program_data.get_annotations()
                    .index[
                        (program_data.get_annotations()["name"] == name)
                        # & (program_data.get_annotations()["structure"] == structure)
                    ]
                    .tolist()
                )[:1]

            if len(l_program_loc) > 0:
                program_index = l_program_loc[0]
                program_string = l_program_names[-1]

                # If in all sections mode, only allow one lipid
                if sections_mode == "all":
                    header_1 = program_string
                    program_1_index = program_index
                    class_name_badge_1 = "position-absolute"
                    return (
                        header_1,
                        "",
                        "",
                        program_1_index,
                        -1,
                        -1,
                        class_name_badge_1,
                        "d-none",
                        "d-none",
                        [header_1]
                    )

                # If lipid already exists, update its index
                if header_1 == program_string:
                    program_1_index = program_index
                elif header_2 == program_string:
                    program_2_index = program_index
                elif header_3 == program_string:
                    program_3_index = program_index
                # If it's a new lipid, fill the first available slot
                else:
                    if class_name_badge_1 == "d-none":
                        header_1 = program_string
                        program_1_index = program_index
                        class_name_badge_1 = "position-absolute"
                    elif class_name_badge_2 == "d-none":
                        header_2 = program_string
                        program_2_index = program_index
                        class_name_badge_2 = "position-absolute"
                    elif class_name_badge_3 == "d-none":
                        header_3 = program_string
                        program_3_index = program_index
                        class_name_badge_3 = "position-absolute"
                    else:
                        logging.warning("More than 3 lipid programs have been selected")
                        return dash.no_update

                return (
                    header_1,
                    header_2,
                    header_3,
                    program_1_index,
                    program_2_index,
                    program_3_index,
                    class_name_badge_1,
                    class_name_badge_2,
                    class_name_badge_3,
                    l_program_names
                )

    return dash.no_update

# # TODO: This callback must be completely rewritten to be able to download the data
# @app.callback(
#     Output("page-2bis-download-data", "data"),
#     Input("page-2bis-download-data-button", "n_clicks"),
#     State("page-2bis-selected-program-1", "data"),
#     State("page-2bis-selected-program-2", "data"),
#     State("page-2bis-selected-program-3", "data"),
#     State("main-slider", "data"),
#     State("page-2bis-badge-input", "children"),
#     prevent_initial_call=True,
# )
# def page_2bis_download(
#     n_clicks,
#     program_1_index,
#     program_2_index,
#     program_3_index,
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
#             x for x in [program_1_index, program_2_index, program_3_index] if x is not None and x != -1
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
#                     x, y = program_figures.compute_spectrum_high_res(
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
    Output("page-2bis-rgb-switch", "checked"),
    Input("page-2bis-selected-program-1", "data"),
    Input("page-2bis-selected-program-2", "data"),
    Input("page-2bis-selected-program-3", "data"),
    Input("page-2bis-sections-mode", "value"),
    State("page-2bis-rgb-switch", "checked"),
)
def page_2bis_auto_toggle_rgb(program_1_index, program_2_index, program_3_index, sections_mode, current_rgb_state):
    """This callback automatically toggles the RGB switch when multiple lipid programs are selected."""
    # Force RGB off when in all sections mode
    if sections_mode == "all":
        return False
        
    active_programs = [x for x in [program_1_index, program_2_index, program_3_index] if x != -1]
    # Only turn on RGB automatically when going from 1 to multiple lipids
    # Don't turn it off when going from multiple to 1
    if len(active_programs) > 1:
        return True
    return current_rgb_state  # Keep current state otherwise

@app.callback(
    Output("page-2bis-sections-mode", "disabled"),
    Input("page-2bis-selected-program-1", "data"),
    Input("page-2bis-selected-program-2", "data"),
    Input("page-2bis-selected-program-3", "data"),
)
def page_2bis_active_sections_control(program_1_index, program_2_index, program_3_index):
    """This callback enables/disables the sections mode control based on lipid program selection."""
    # Get the current lipid selection
    active_programs = [x for x in [program_1_index, program_2_index, program_3_index] if x != -1]
    # Enable control if at least one lipid is selected
    return len(active_programs) == 0

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
    Output("page-2bis-main-slider-style", "data"),
    Output("page-2bis-graph-hover-text", "style"),
    Output("page-2bis-annotations-container", "style"),
    Input("page-2bis-sections-mode", "value"),
)
def page_2bis_toggle_elements_visibility(sections_mode):
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
    Output("page-2bis-rgb-group", "style"),
    Input("page-2bis-sections-mode", "value"),
)
def page_2bis_toggle_rgb_group_visibility(sections_mode):
    """Controls the visibility of the RGB group."""
    if sections_mode == "all":
        return {"display": "none"}
    else:
        return {"display": "flex", "alignItems": "center", "marginLeft": "15px"}