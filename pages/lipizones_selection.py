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
from app import app, figures, data, storage, cache_flask
from modules.maldi_data import GridImageShelve, SampleDataShelve, SectionDataShelve

# Initialize GridImageShelve
grid_data = GridImageShelve(shelf_filename="grid_shelve", shelf_dir="./grid_data/")

# Initialize SampleDataShelve
sample_data_shelve = SampleDataShelve(shelf_filename="sample_data_shelve", shelf_dir="./sample_data/")

# Initialize SectionDataShelve
section_data_shelve = SectionDataShelve(shelf_filename="section_data_shelve", shelf_dir="./section_data/")

# ==================================================================================================
# --- Layout
# ==================================================================================================

def compute_hybrid_image(hex_colors_to_highlight, brain_id="ReferenceAtlas"):
    def hex_to_rgb(hex_color):
        """Convert hexadecimal color to RGB values (0-1 range)"""
        hex_color = hex_color.lstrip('#')
        return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)]) / 255.0
    
    try:
        # Retrieve sample data from shelve database
        sample_data = sample_data_shelve.retrieve_sample_data(brain_id)
        color_masks = sample_data["color_masks"]
        grayscale_image = sample_data["grayscale_image"]
        rgb_image = sample_data["grid_image"][:, :, :3]  # remove transparency channel for now
    except KeyError:
        # Fallback to default files if sample not found
        logging.warning(f"Sample data for {brain_id} not found, using default files")
        def load_color_masks_pickle(filename):
            import pickle
            with open(filename, 'rb') as f:
                color_masks = pickle.load(f)
            print(f"Loaded {len(color_masks)} color masks from {filename}")
            return color_masks
        
        color_masks = load_color_masks_pickle('my_image_masks.pkl')
        grayscale_image = np.load("grayscale_image.npy")
        rgb_image = np.load("grid_image_lipizones.npy")[:, :, :3]
    
    # Apply square root transformation to enhance contrast
    grayscale_image = np.sqrt(np.sqrt(grayscale_image))
    
    rgb_colors_to_highlight = [hex_to_rgb(hex_color) for hex_color in hex_colors_to_highlight]
    
    hybrid_image = np.zeros_like(rgb_image)
    for i in range(3):
        hybrid_image[:, :, i] = grayscale_image
    combined_mask = np.zeros((rgb_image.shape[0], rgb_image.shape[1]), dtype=bool)
    for target_rgb in rgb_colors_to_highlight:
        target_tuple = tuple(target_rgb)
        
        # If the exact color exists in our image
        if target_tuple in color_masks:
            print("in")
            combined_mask |= color_masks[target_tuple]
        else:
            # Find closest color
            distances = np.array([np.sum((np.array(color) - target_rgb) ** 2) for color in color_masks.keys()])
            closest_color_idx = np.argmin(distances)
            closest_color = list(color_masks.keys())[closest_color_idx]
            
            # If close enough to our target color, add its mask
            if distances[closest_color_idx] < 0.05:  # Threshold for color similarity
                print("elsein")
                combined_mask |= color_masks[closest_color]
    
    for i in range(3):
        hybrid_image[:, :, i][combined_mask] = rgb_image[:, :, i][combined_mask]
    hybrid_image = (hybrid_image*255) + 1
    mask = np.all(hybrid_image == 1, axis=-1)
    hybrid_image[mask] = np.nan

    height, width, _ = hybrid_image.shape

    # Compute pad sizes
    pad_top = height // 2
    pad_bottom = height // 2
    pad_left = width // 3

    # Pad the image: note that no padding is added on the right.
    padded_image = np.pad(
        hybrid_image,
        pad_width=((pad_top, pad_bottom), (pad_left, 0), (0, 0)),
        mode='constant',
        constant_values=np.nan
    )

    return padded_image

lipizonenames = pd.read_csv("lipizonename2color.csv", index_col=0)
lipizonenames = lipizonenames['lipizone_names'].values
lipizonecolors = pd.read_csv("lipizonename2color.csv", index_col=0)
lipizonecolors = lipizonecolors.to_dict(orient="records")
lipizonecolors = {row["lipizone_names"]: row["lipizone_color"] for row in lipizonecolors}
annotations = pd.read_csv("./data/annotations/lipizones_annotation.csv")

# def build_tree_from_csv(csv_path):
#     df = pd.read_csv(csv_path)
#     tree = []
    
#     def add_to_tree(tree, levels, leaf_label, leaf_value):
#         if not levels:
#             tree.append({"label": leaf_label, "value": leaf_value})
#         else:
#             current_level = str(levels[0])
#             # See if this node already exists in the tree
#             node = next((item for item in tree if item["label"] == current_level), None)
#             if node is None:
#                 node = {"label": current_level, "value": current_level, "children": []}
#                 tree.append(node)
#             add_to_tree(node["children"], levels[1:], leaf_label, leaf_value)
    
#     for _, row in df.iterrows():
#         # Build the path from the level columns
#         levels = [row["level_1"], row["level_2"], row["level_3"], row["level_4"], row["subclass_name"]]
#         leaf_label = row["lipizone_names"]
#         leaf_value = row["lipizone_names"]
#         add_to_tree(tree, levels, leaf_label, leaf_value)
    
#     return tree

# # Build the hierarchical data from your CSV file
# hierarchy_data = build_tree_from_csv("./data/annotations/lipizones_hierarchy.csv")

df_hierarchy = pd.read_csv("./data/annotations/lipizones_hierarchy.csv")

def return_layout(basic_config, slice_index):
    # Precompute your level_1 options:
    level_1_options = [
        {"value": str(x), "label": str(x)}
        for x in sorted(df_hierarchy["level_1"].unique())
    ]

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
            html.Div(
                className="fixed-aspect-ratio",
                style={"background-color": "#1d1c1f"},
                children=[
                    dbc.Spinner(
                        color="info",
                        spinner_style={
                            "margin-top": "40%",
                            "width": "3rem",
                            "height": "3rem",
                        },
                        children=dcc.Graph(
                            id="page-6-graph-heatmap-mz-selection",
                            config=basic_config
                            | {
                                "toImageButtonOptions": {
                                    "format": "png",
                                    "filename": "brain_lipizone_selection",
                                    "scale": 2,
                                },
                                "scrollZoom": True
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
                            figure=figures.build_lipid_heatmap_from_image(
                                compute_hybrid_image(['#f75400'], brain_id="ReferenceAtlas"),
                                return_base64_string=False,
                                draw=False,
                                type_image="RGB",
                                return_go_image=False,
                            )
                        ),
                    ),
                    dmc.Group(
                        direction="column",
                        spacing=0,
                        style={"left": "1%", "top": "1em"},
                        class_name="position-absolute",
                        children=[
                            # Level 1 dropdown and buttons in a horizontal group
                            dmc.Group(
                                direction="row",
                                spacing="sm",
                                children=[
                                    # Level 1 dropdown
                                    dmc.MultiSelect(
                                        id="page-6-select-level-1",
                                        data=level_1_options,
                                        placeholder="Select Level 1",
                                        style={"width": "20em"},
                                    ),
                                    # Display buttons
                                    dmc.Button(
                                        children="Display one section",
                                        id="page-6-rgb-button",
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
                                        id="page-6-all-sections-button",
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
                            # Level 2 dropdown
                            dmc.MultiSelect(
                                id="page-6-select-level-2",
                                data=[],  # will be updated by callback
                                placeholder="Select Level 2",
                                style={"width": "20em", "marginTop": "0.5em"},
                            ),
                            # Level 3 dropdown
                            dmc.MultiSelect(
                                id="page-6-select-level-3",
                                data=[],
                                placeholder="Select Level 3",
                                style={"width": "20em", "marginTop": "0.5em"},
                            ),
                            # Level 4 dropdown
                            dmc.MultiSelect(
                                id="page-6-select-level-4",
                                data=[],
                                placeholder="Select Level 4",
                                style={"width": "20em", "marginTop": "0.5em"},
                            ),
                            # Subclass Select
                            dmc.MultiSelect(
                                id="page-6-select-subclass",
                                data=[],
                                placeholder="Select Subclass",
                                style={"width": "20em", "marginTop": "0.5em"},
                            ),
                            # Final MultiSelect for the lipizone_names
                            dmc.MultiSelect(
                                id="page-6-dropdown-lipizones",  # keep the same ID as before
                                data=[],  # updated by callback
                                placeholder="Select Lipizone(s)",
                                searchable=True,
                                clearable=False,
                                nothingFound="No lipizone found",
                                style={"width": "20em", "marginTop": "0.5em"},
                                value=[],  # start empty
                                maxSelectedValues=539,
                            ),
                            # Replaced colormap button with a hidden div for callback compatibility
                            html.Div(
                                id="page-6-colormap-button",
                                style={"display": "none"},
                            ),
                        ],
                    ),
                    # Hidden elements for callback compatibility
                    html.Div(
                        id="page-6-badge-input",
                        children="",
                        style={"display": "none"},
                    ),
                    html.Div(
                        id="page-6-badge-lipizone-1",
                        style={"display": "none"},
                    ),
                    html.Div(
                        id="page-6-badge-lipizone-2",
                        style={"display": "none"},
                    ),
                    html.Div(
                        id="page-6-badge-lipizone-3",
                        style={"display": "none"},
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
                                id="page-6-download-data-button",
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
                                id="page-6-download-image-button",
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
                    dcc.Download(id="page-6-download-data"),
                    # Add a store for all selected lipizones
                    dcc.Store(id="page-6-all-selected-lipizones", data={}),
                ],
            ),
        ],
    )

    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================

@app.callback(
    Output("page-6-select-level-2", "data"),
    Input("page-6-select-level-1", "value"),
)
def update_level2(level1_vals):
    # If nothing is selected, you might show all options or return an empty list
    if level1_vals:
        subset = df_hierarchy[df_hierarchy["level_1"].astype(str).isin(level1_vals)]
    else:
        subset = df_hierarchy
    opts = sorted(subset["level_2"].unique())
    return [{"value": str(x), "label": str(x)} for x in opts]


@app.callback(
    Output("page-6-select-level-3", "data"),
    [Input("page-6-select-level-1", "value"),
     Input("page-6-select-level-2", "value")],
)
def update_level3(level1_vals, level2_vals):
    subset = df_hierarchy.copy()
    if level1_vals:
        subset = subset[subset["level_1"].astype(str).isin(level1_vals)]
    if level2_vals:
        subset = subset[subset["level_2"].astype(str).isin(level2_vals)]
    opts = sorted(subset["level_3"].unique())
    return [{"value": str(x), "label": str(x)} for x in opts]


@app.callback(
    Output("page-6-select-level-4", "data"),
    [Input("page-6-select-level-1", "value"),
     Input("page-6-select-level-2", "value"),
     Input("page-6-select-level-3", "value")],
)
def update_level4(level1_vals, level2_vals, level3_vals):
    subset = df_hierarchy.copy()
    if level1_vals:
        subset = subset[subset["level_1"].astype(str).isin(level1_vals)]
    if level2_vals:
        subset = subset[subset["level_2"].astype(str).isin(level2_vals)]
    if level3_vals:
        subset = subset[subset["level_3"].astype(str).isin(level3_vals)]
    opts = sorted(subset["level_4"].unique())
    return [{"value": str(x), "label": str(x)} for x in opts]


@app.callback(
    Output("page-6-select-subclass", "data"),
    [Input("page-6-select-level-1", "value"),
     Input("page-6-select-level-2", "value"),
     Input("page-6-select-level-3", "value"),
     Input("page-6-select-level-4", "value")],
)
def update_subclass(level1_vals, level2_vals, level3_vals, level4_vals):
    filtered = df_hierarchy.copy()
    if level1_vals:
        filtered = filtered[filtered["level_1"].astype(str).isin(level1_vals)]
    if level2_vals:
        filtered = filtered[filtered["level_2"].astype(str).isin(level2_vals)]
    if level3_vals:
        filtered = filtered[filtered["level_3"].astype(str).isin(level3_vals)]
    if level4_vals:
        filtered = filtered[filtered["level_4"].astype(str).isin(level4_vals)]
    opts = sorted(filtered["subclass_name"].unique())
    return [{"value": x, "label": x} for x in opts]


@app.callback(
    Output("page-6-dropdown-lipizones", "data"),
    [Input("page-6-select-level-1", "value"),
     Input("page-6-select-level-2", "value"),
     Input("page-6-select-level-3", "value"),
     Input("page-6-select-level-4", "value"),
     Input("page-6-select-subclass", "value")],
)
def update_lipizone_names(level1_vals, level2_vals, level3_vals, level4_vals, subclass_vals):
    filtered = df_hierarchy.copy()
    if level1_vals:
        filtered = filtered[filtered["level_1"].astype(str).isin(level1_vals)]
    if level2_vals:
        filtered = filtered[filtered["level_2"].astype(str).isin(level2_vals)]
    if level3_vals:
        filtered = filtered[filtered["level_3"].astype(str).isin(level3_vals)]
    if level4_vals:
        filtered = filtered[filtered["level_4"].astype(str).isin(level4_vals)]
    if subclass_vals:
        filtered = filtered[filtered["subclass_name"].isin(subclass_vals)]
    lipizones = sorted(filtered["lipizone_names"].unique())
    return [{"value": x, "label": x} for x in lipizones]


@app.callback(
    Output("page-6-dropdown-lipizones", "value"),
    Input("page-6-dropdown-lipizones", "data"),
)
def auto_select_all(leaf_data):
    if leaf_data:
        # Return a list of all option values so that they are all selected.
        return [item["value"] for item in leaf_data]
    return []

@app.callback(
    Output("page-6-select-level-2", "value"),
    Output("page-6-select-level-3", "value"),
    Output("page-6-select-level-4", "value"),
    Output("page-6-select-subclass", "value"),
    Input("page-6-select-level-1", "value"),
    prevent_initial_call=True
)
def clear_lower_levels(_):
    return None, None, None, None

@app.callback(
    Output("page-6-graph-heatmap-mz-selection", "figure"),
    Output("page-6-badge-input", "children"),
    Input("main-slider", "data"),
    # Input("boundaries-high-resolution-mz-plot", "data"),
    # Input("boundaries-low-resolution-mz-plot", "data"),
    Input("page-6-selected-lipizone-1", "data"),
    Input("page-6-selected-lipizone-2", "data"),
    Input("page-6-selected-lipizone-3", "data"),
    Input("page-6-all-selected-lipizones", "data"),
    Input("page-6-rgb-button", "n_clicks"),
    Input("page-6-colormap-button", "n_clicks"),
    Input("page-6-all-sections-button", "n_clicks"),
    Input("main-brain", "value"),
    # Input("page-6-button-bounds", "n_clicks"),
    # State("page-6-lower-bound", "value"),
    # State("page-6-upper-bound", "value"),
    State("page-6-badge-input", "children"),
    # Input("page-6-toggle-apply-transform", "checked"),
)
def page_6_plot_graph_heatmap_mz_selection(
    slice_index,
    # bound_high_res,
    # bound_low_res,
    lipizone_1_index,
    lipizone_2_index,
    lipizone_3_index,
    all_selected_lipizones,
    n_clicks_button_rgb,
    n_clicks_button_colormap,
    n_clicks_button_all_sections,
    brain_id,
    # n_clicks_button_bounds,
    # lb,
    # hb,
    graph_input,
    # apply_transform,
):
    """This callback plots the heatmap of the selected lipid(s)."""
    print(f"\n========== page_6_plot_graph_heatmap_mz_selection ==========")
    print('indices:', lipizone_1_index, lipizone_2_index, lipizone_3_index)
    print(f"slice_index: {slice_index}")
    logging.info("Entering function to plot heatmap or RGB depending on lipid selection")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    print(f"id_input: {id_input}")    
    print("graph_input:", graph_input)
    print("brain_id:", brain_id)

    # # Case a two mz bounds values have been inputed
    # if id_input == "page-6-button-bounds" or (
    #     id_input == "main-slider" and graph_input == "Current input: " + "m/z boundaries"
    # ):
    #     if lb is not None and hb is not None:
    #         lb, hb = float(lb), float(hb)
    #         if lb >= 400 and hb <= 1600 and hb - lb > 0 and hb - lb < 10:
    #             return (
    #                 figures.compute_heatmap_per_mz(slice_index, lb, hb, cache_flask=cache_flask),
    #                 "Current input: " + "m/z boundaries",
    #             )

    #     return dash.no_update

    # If a lipid selection has been done
    if (
        id_input == "page-6-selected-lipizone-1"
        or id_input == "page-6-selected-lipizone-2"
        or id_input == "page-6-selected-lipizone-3"
        or id_input == "page-6-all-selected-lipizones"
        or id_input == "page-6-rgb-button"
        or id_input == "page-6-colormap-button"  # Now falls back to RGB option
        or id_input == "page-6-all-sections-button"
        or id_input == "main-brain"
        or (
            (id_input == "main-slider")
            and (
                graph_input == "Current input: " + "Lipid selection colormap"
                or graph_input == "Current input: " + "Lipid selection RGB"
                or graph_input == "Current input: " + "Lipid selection all sections"
            )
        )
    ):
        print("--- option 1 ---")
        # Check if we have any selected lipizones
        if all_selected_lipizones and len(all_selected_lipizones.get("names", [])) > 0:
            # Get the names of all selected lipizones
            selected_lipizone_names = all_selected_lipizones.get("names", [])
            
            # Define hex_colors_to_highlight using all selected lipizones
            hex_colors_to_highlight = [lipizonecolors[name] for name in selected_lipizone_names if name in lipizonecolors]
            
            # --- Removed heatmap branch ---
            # Previously, the following branch handled the colormap/heatmap option.
            # It has been removed so that any such request now falls to the RGB option.

            # Or if the current plot must be an RGB image
            if (
                id_input == "page-6-rgb-button"
                or (
                    id_input == "main-slider"
                    and graph_input == "Current input: " + "Lipid selection RGB"
                )
                or (
                    id_input == "page-6-toggle-apply-transform"
                    and graph_input == "Current input: " + "Lipid selection RGB"
                )
            ):
                print("--- option 1.2 ---")
                
                # Try to get the section data for the current slice and brain
                try:
                    print(slice_index)
                    # Create a section key based on brain_id and slice_index
                    section_data = section_data_shelve.retrieve_section_data(float(slice_index))
                    print(section_data["grayscale_image"].shape)

                    # Use the section data to create a hybrid image
                    grayscale_image = section_data["grayscale_image"]
                    color_masks = section_data["color_masks"]
                    grid_image = section_data["grid_image"]
                    rgb_image = grid_image[:, :, :3]  # remove transparency channel
                    
                    # Create a custom hybrid image for this specific section
                    def hex_to_rgb(hex_color):
                        """Convert hexadecimal color to RGB values (0-1 range)"""
                        hex_color = hex_color.lstrip('#')
                        return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)]) / 255.0
                    
                    # Apply square root transformation to enhance contrast
                    grayscale_image = np.sqrt(np.sqrt(grayscale_image))
                    
                    rgb_colors_to_highlight = [hex_to_rgb(hex_color) for hex_color in hex_colors_to_highlight]
                    
                    hybrid_image = np.zeros_like(rgb_image)
                    for i in range(3):
                        hybrid_image[:, :, i] = grayscale_image
                    
                    combined_mask = np.zeros((rgb_image.shape[0], rgb_image.shape[1]), dtype=bool)
                    for target_rgb in rgb_colors_to_highlight:
                        target_tuple = tuple(target_rgb)
                        
                        # If the exact color exists in our image
                        if target_tuple in color_masks:
                            combined_mask |= color_masks[target_tuple]
                        else:
                            # Find closest color
                            distances = np.array([np.sum((np.array(color) - target_rgb) ** 2) for color in color_masks.keys()])
                            closest_color_idx = np.argmin(distances)
                            closest_color = list(color_masks.keys())[closest_color_idx]
                            
                            # If close enough to our target color, add its mask
                            if distances[closest_color_idx] < 0.05:  # Threshold for color similarity
                                combined_mask |= color_masks[closest_color]
                    
                    for i in range(3):
                        hybrid_image[:, :, i][combined_mask] = rgb_image[:, :, i][combined_mask]
                    
                    hybrid_image = (hybrid_image*255) + 1
                    mask = np.all(hybrid_image == 1, axis=-1)
                    hybrid_image[mask] = np.nan
                    
                    return figures.build_lipid_heatmap_from_image(
                        hybrid_image,
                        return_base64_string=False,
                        draw=False,
                        type_image="RGB",
                        return_go_image=False,
                    ), "Current input: " + "Lipid selection RGB"
                except KeyError as e:
                    # If section data not found, fall back to the hybrid image
                    logging.warning(f"Section data not found: {e}. Using hybrid image instead.")
                    return figures.build_lipid_heatmap_from_image(
                        compute_hybrid_image(hex_colors_to_highlight, brain_id),
                        return_base64_string=False,
                        draw=False,
                        type_image="RGB",
                        return_go_image=False,
                    ), "Current input: " + "Lipid selection RGB"

            # Or if the current plot must be all sections
            elif (
                id_input == "page-6-all-sections-button"
                or (
                    id_input == "main-slider"
                    and graph_input == "Current input: " + "Lipid selection all sections"
                )
            ):
                print("--- option 1.4 ---")
                # Check that only one lipid is selected
                if len(selected_lipizone_names) == 1:
                    # Use the selected lipid
                    try:
                        # First try to get the grid image from GridImageShelve
                        image = grid_data.retrieve_grid_image(
                            lipid=selected_lipizone_names[0],
                            sample=brain_id
                        )
                        return figures.build_lipid_heatmap_from_image(
                            image,
                            return_base64_string=False,
                            draw=False,
                            type_image="RGB",
                            return_go_image=False,
                        ), ""
                    except (KeyError, Exception) as e:
                        # If that fails, fall back to the hybrid image
                        logging.warning(f"Failed to retrieve grid image: {e}. Using hybrid image instead.")
                        return figures.build_lipid_heatmap_from_image(
                            compute_hybrid_image(hex_colors_to_highlight, brain_id),
                            return_base64_string=False,
                            draw=False,
                            type_image="RGB",
                            return_go_image=False,
                        ), ""
                else:
                    print("--- option 1.4.2 ---")
                    logging.info("Trying to display all sections for more than one lipid, not possible. Using first selected lipid.")
                    first_lipid = selected_lipizone_names[0] if selected_lipizone_names else "choroid plexus"
                    return figures.build_lipid_heatmap_from_image(
                        compute_hybrid_image(hex_colors_to_highlight, brain_id),
                        return_base64_string=False,
                        draw=False,
                        type_image="RGB",
                        return_go_image=False,
                    ), ""

            # Plot RGB by default
            else:
                print("--- option 1.3 ---")
                logging.info("Right before calling the graphing function")
                return figures.build_lipid_heatmap_from_image(
                    compute_hybrid_image(hex_colors_to_highlight, brain_id),
                    return_base64_string=False,
                    draw=False,
                    type_image="RGB",
                    return_go_image=False,
                ), ""
        # For backward compatibility, check the individual lipizone indices
        elif lipizone_1_index >= 0 or lipizone_2_index >= 0 or lipizone_3_index >= 0:
            ll_lipizone_names = [
                lipizonenames[index]
                if index != -1
                else None
                for index in [lipizone_1_index, lipizone_2_index, lipizone_3_index]
            ]
            
            # Define hex_colors_to_highlight here so it's available for all branches
            hex_colors_to_highlight = [lipizonecolors[x] for x in ll_lipizone_names if x is not None]
            
            return figures.build_lipid_heatmap_from_image(
                compute_hybrid_image(hex_colors_to_highlight, brain_id),
                return_base64_string=False,
                draw=False,
                type_image="RGB",
                return_go_image=False,
            ), ""
        elif (
            id_input == "main-slider" and graph_input == "Current input: "
        ):
            print("--- option 2 ---")
            print(f"No lipid has been selected, the current lipid is choroid plexus and the slice is {slice_index}")
            # Use default color for choroid plexus
            hex_colors_to_highlight = ['#f75400']  # Default color for choroid plexus
            return figures.build_lipid_heatmap_from_image(
                    compute_hybrid_image(hex_colors_to_highlight, brain_id),
                    return_base64_string=False,
                    draw=False,
                    type_image="RGB",
                    return_go_image=False,
                ), ""
        else:
            print("--- option 3 ---")
            # No lipid has been selected, return image from boundaries using RGB
            hex_colors_to_highlight = ['#f75400']  # Default color for choroid plexus
            return figures.build_lipid_heatmap_from_image(
                    compute_hybrid_image(hex_colors_to_highlight, brain_id),
                    return_base64_string=False,
                    draw=False,
                    type_image="RGB",
                    return_go_image=False,
                ), ""
    # # Case trigger is range slider from high resolution spectrum
    # if id_input == "boundaries-high-resolution-mz-plot" or (
    #     id_input == "main-slider"
    #     and graph_input == "Current input: " + "Selection from high-res m/z graph"
    # ):
    #     if bound_high_res is not None:
    #         bound_high_res = json.loads(bound_high_res)
    #         return (
    #             figures.compute_heatmap_per_mz(
    #                 slice_index,
    #                 bound_high_res[0],
    #                 bound_high_res[1],
    #                 cache_flask=cache_flask,
    #             ),
    #             "Current input: " + "Selection from high-res m/z graph",
    #         )

    # # Case trigger is range slider from low resolution spectrum
    # if id_input == "boundaries-low-resolution-mz-plot" or (
    #     id_input == "main-slider"
    #     and graph_input == "Current input: " + "Selection from low-res m/z graph"
    # ):
    #     if bound_low_res is not None:
    #         bound_low_res = json.loads(bound_low_res)
    #         return (
    #             figures.compute_heatmap_per_mz(
    #                 slice_index,
    #                 bound_low_res[0],
    #                 bound_low_res[1],
    #                 cache_flask=cache_flask,
    #             ),
    #             "Current input: " + "Selection from low-res m/z graph",
    #         )

    # If no trigger, the page has just been loaded, so load new figure with default parameters
    else:
        return dash.no_update


# @app.callback(
#     Output("page-6-graph-low-resolution-spectrum", "figure"),
#     Input("main-slider", "data"),
#     State("page-6-selected-lipizone-1", "data"),
#     State("page-6-selected-lipizone-2", "data"),
#     State("page-6-selected-lipizone-3", "data"),
#     Input("page-6-rgb-button", "n_clicks"),
#     Input("page-6-colormap-button", "n_clicks"),
#     Input("page-6-button-bounds", "n_clicks"),
#     State("page-6-lower-bound", "value"),
#     State("page-6-upper-bound", "value"),
#     State("page-6-graph-low-resolution-spectrum", "relayoutData"),
# )
# def page_6_plot_graph_low_res_spectrum(
#     slice_index,
#     lipizone_1_index,
#     lipizone_2_index,
#     lipizone_3_index,
#     n_clicks_rgb,
#     n_clicks_colormap,
#     n_clicks_button_bounds,
#     lb,
#     hb,
#     relayoutData,
# ):
#     """This callbacks generates the graph of the low resolution spectrum when the current input
#     gets updated.""

#     # Find out which input triggered the function
#     id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

#     # If a lipid selection has been done
#     if (
#         id_input == "page-6-selected-lipizone-1"
#         or id_input == "page-6-selected-lipizone-2"
#         or id_input == "page-6-selected-lipizone-3"
#         or id_input == "page-6-rgb-button"
#         or id_input == "page-6-colormap-button"
#         or (
#             id_input == "main-slider"
#             and (
#                 graph_input == "Current input: " + "Lipid selection colormap"
#                 or graph_input == "Current input: " + "Lipid selection RGB"
#             )
#         )
#     ):
#         if lipizone_1_index >= 0 or lipizone_2_index >= 0 or lipizone_3_index >= 0:
#             # build the list of mz boundaries for each peak
#             l_lipizone_bounds = [
#                 (
#                     float(annotations.iloc[index]["min"]),
#                     float(annotations.iloc[index]["max"]),
#                 )
#                 if index != -1
#                 else None
#                 for index in [lipizone_1_index, lipizone_2_index, lipizone_3_index]
#             ]
#             return figures.compute_spectrum_low_res(slice_index, l_lipizone_bounds)

#         else:
#             # Probably the page has just been loaded, so load new figure with default parameters
#             return dash.no_update

#     # Or if the plot has been updated from range or slider
#     elif id_input == "page-6-button-bounds" or (
#         id_input == "main-slider" and graph_input == "Current input: " + "m/z boundaries"
#     ):
#         lb, hb = float(lb), float(hb)
#         if lb >= 400 and hb <= 1600 and hb - lb > 0 and hb - lb < 10:
#             l_lipizone_bounds = [(lb, hb), None, None]
#             return figures.compute_spectrum_low_res(slice_index, l_lipizone_bounds)

#     elif (
#         id_input == "main-slider"
#         and graph_input == "Current input: " + "Selection from low-res m/z graph"
#     ):
#         # TODO : find a way to set relayoutdata properly
#         pass

#     return dash.no_update


# @app.callback(
#     Output("boundaries-low-resolution-mz-plot", "data"),
#     Input("page-6-graph-low-resolution-spectrum", "relayoutData"),
#     State("main-slider", "data"),
# )
# def page_6_store_boundaries_mz_from_graph_low_res_spectrum(relayoutData, slice_index):
#     """This callback stores in a dcc store the m/z boundaries of the low resolution spectrum when
#     they are updated."""

#     # If the plot has been updated from the low resolution spectrum
#     if relayoutData is not None:
#         if "xaxis.range[0]" in relayoutData:
#             return json.dumps([relayoutData["xaxis.range[0]"], relayoutData["xaxis.range[1]"]])
#         elif "xaxis.range" in relayoutData:
#             return json.dumps(relayoutData["xaxis.range"])

#         # If the range is re-initialized, need to explicitely pass the first
#         # and last values of the spectrum to the figure
#         elif "xaxis.autorange" in relayoutData:
#             return json.dumps(
#                 [
#                     data.get_array_avg_spectrum_downsampled(slice_index)[0, 0].astype("float"),
#                     data.get_array_avg_spectrum_downsampled(slice_index)[0, -1].astype("float"),
#                 ]
#             )

#     # When the app is launched, or when the plot is displayed and autoresized,
#     # no boundaries are passed not to update the heatmap for nothing
#     return dash.no_update


# @app.callback(
#     Output("page-6-graph-high-resolution-spectrum", "figure"),
#     Input("main-slider", "data"),
#     Input("boundaries-low-resolution-mz-plot", "data"),
#     Input("page-6-selected-lipizone-1", "data"),
#     Input("page-6-selected-lipizone-2", "data"),
#     Input("page-6-selected-lipizone-3", "data"),
#     Input("page-6-rgb-button", "n_clicks"),
#     Input("page-6-colormap-button", "n_clicks"),
#     Input("page-6-button-bounds", "n_clicks"),
#     State("page-6-lower-bound", "value"),
#     State("page-6-upper-bound", "value"),
#     State("page-6-badge-input", "children"),
#     Input("page-6-toggle-apply-transform", "checked"),
# )
# def page_6_plot_graph_high_res_spectrum(
#     slice_index,
#     bound_high_res,
#     lipizone_1_index,
#     lipizone_2_index,
#     lipizone_3_index,
#     n_clicks_rgb,
#     n_clicks_colormap,
#     n_clicks_button_bounds,
#     lb,
#     hb,
#     graph_input,
#     apply_transform,
# ):
#     """This callback generates the graph of the high resolution spectrum when the current input has
#     a small enough m/z range."""

#     # Find out which input triggered the function
#     id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

#     # If a lipid selection has been done
#     if (
#         id_input == "page-6-selected-lipizone-1"
#         or id_input == "page-6-selected-lipizone-2"
#         or id_input == "page-6-selected-lipizone-3"
#         or id_input == "page-6-rgb-button"
#         or id_input == "page-6-colormap-button"
#         or id_input == "page-6-last-selected-lipids"
#         or (
#             id_input == "main-slider"
#             and (
#                 graph_input == "Current input: " + "Lipid selection colormap"
#                 or graph_input == "Current input: " + "Lipid selection RGB"
#             )
#         )
#     ):
#         # If at least one lipid index has been recorded
#         if lipizone_1_index >= 0 or lipizone_2_index >= 0 or lipizone_3_index >= 0:
#             # Build the list of mz boundaries for each peak
#             l_indexes = [lipizone_1_index, lipizone_2_index, lipizone_3_index]
#             l_lipizone_bounds = [
#                 (
#                     float(annotations.iloc[index]["min"]),
#                     float(annotations.iloc[index]["max"]),
#                 )
#                 if index != -1
#                 else None
#                 for index in l_indexes
#             ]
#             if lipizone_3_index >= 0:
#                 current_lipizone_index = 2
#             elif lipizone_2_index >= 0:
#                 current_lipizone_index = 1
#             else:
#                 current_lipizone_index = 0
#             return figures.compute_spectrum_high_res(
#                 slice_index,
#                 l_lipizone_bounds[current_lipizone_index][0] - 10**-2,
#                 l_lipizone_bounds[current_lipizone_index][1] + 10**-2,
#                 annotations=l_lipizone_bounds,
#                 force_xlim=True,
#                 standardization=apply_transform,
#                 cache_flask=cache_flask,
#             )

#     # If the user has selected a new m/z range
#     elif id_input == "page-6-button-bounds" or (
#         id_input == "main-slider" and graph_input == "Current input: " + "m/z boundaries"
#     ):
#         lb, hb = float(lb), float(hb)
#         if lb >= 400 and hb <= 1600 and hb - lb > 0 and hb - lb < 10:
#             # l_lipizone_bounds = [(lb, hb), None, None]
#             return figures.compute_spectrum_high_res(
#                 slice_index,
#                 lb - 10**-2,
#                 hb + 10**-2,
#                 force_xlim=True,  # annotations=l_lipizone_bounds,
#                 standardization=apply_transform,
#                 cache_flask=cache_flask,
#             )

#     # If the figure is created at app launch or after load button is cliked, or with an empty lipid
#     # selection, don't plot anything
#     elif "page-6-selected-lipid" in id_input:
#         return dash.no_update

#     # Otherwise, if new boundaries have been selected on the low-resolution spectrum
#     elif id_input == "boundaries-low-resolution-mz-plot" and bound_high_res is not None:
#         bound_high_res = json.loads(bound_high_res)

#         # Case the zoom is high enough
#         if bound_high_res[1] - bound_high_res[0] <= 3:
#             return figures.compute_spectrum_high_res(
#                 slice_index,
#                 bound_high_res[0],
#                 bound_high_res[1],
#                 standardization=apply_transform,
#                 cache_flask=cache_flask,
#             )
#         # Otherwise just return default (empty) graph
#         else:
#             return dash.no_update

#     # The page has just been loaded, no spectrum is displayed
#     return dash.no_update


# @app.callback(
#     Output("boundaries-high-resolution-mz-plot", "data"),
#     Input("page-6-graph-high-resolution-spectrum", "relayoutData"),
#     Input("boundaries-low-resolution-mz-plot", "data"),
# )
# def page_6_store_boundaries_mz_from_graph_high_res_spectrum(relayoutData, bound_low_res):
#     """This callback records the m/z boundaries of the high resolution spectrum in a dcc store."""

#     # Primarily update high-res boundaries with high-res range slider
#     if relayoutData is not None:
#         if "xaxis.range[0]" in relayoutData:
#             return json.dumps([relayoutData["xaxis.range[0]"], relayoutData["xaxis.range[1]"]])
#         elif "xaxis.range" in relayoutData:
#             return json.dumps(relayoutData["xaxis.range"])

#         # If the range is re-initialized, need to explicitely pass the low-res value of the slider
#         elif "xaxis.autorange" in relayoutData:
#             if bound_low_res is not None:
#                 bound_low_res = json.loads(bound_low_res)
#                 if bound_low_res[1] - bound_low_res[0] <= 3:
#                     return json.dumps(bound_low_res)

#     # But also needs to be updated when low-res slider is changed and is zoomed enough
#     elif bound_low_res is not None:
#         bound_low_res = json.loads(bound_low_res)
#         if bound_low_res[1] - bound_low_res[0] <= 3:
#             return json.dumps(bound_low_res)

#     # Page has just been loaded, do nothing
#     else:
#         return dash.no_update


@app.callback(
    Output("page-6-badge-lipizone-1", "children"),
    Output("page-6-badge-lipizone-2", "children"),
    Output("page-6-badge-lipizone-3", "children"),
    Output("page-6-selected-lipizone-1", "data"),
    Output("page-6-selected-lipizone-2", "data"),
    Output("page-6-selected-lipizone-3", "data"),
    Output("page-6-badge-lipizone-1", "class_name"),
    Output("page-6-badge-lipizone-2", "class_name"),
    Output("page-6-badge-lipizone-3", "class_name"),
    Output("page-6-all-selected-lipizones", "data"),
    Input("page-6-dropdown-lipizones", "value"),
    Input("page-6-badge-lipizone-1", "class_name"),
    Input("page-6-badge-lipizone-2", "class_name"),
    Input("page-6-badge-lipizone-3", "class_name"),
    Input("main-slider", "data"),
    State("page-6-selected-lipizone-1", "data"),
    State("page-6-selected-lipizone-2", "data"),
    State("page-6-selected-lipizone-3", "data"),
    State("page-6-badge-lipizone-1", "children"),
    State("page-6-badge-lipizone-2", "children"),
    State("page-6-badge-lipizone-3", "children"),
    State("main-brain", "value"),
    State("page-6-all-selected-lipizones", "data"),
)
def page_6_add_toast_selection(
    l_lipizone_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    lipizone_1_index,
    lipizone_2_index,
    lipizone_3_index,
    header_1,
    header_2,
    header_3,
    brain_id,
    all_selected_lipizones,
):
    """This callback adds the selected lipid to the selection."""
    logging.info("Entering function to update lipid data")
    annotations = pd.read_csv("./data/annotations/lipizones_annotation.csv")
    print("\n================ page_6_add_toast_selection ================")
    print(f"l_lipizone_names: {l_lipizone_names}")
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    print(f"id_input: {id_input}")
    print(f"value_input: {value_input}")
    
    # Initialize all_selected_lipizones if it's empty
    if not all_selected_lipizones:
        all_selected_lipizones = {"names": [], "indices": []}
    
    # if page-6-dropdown-lipizones is called while there's no lipid name defined, it means the page
    # just got loaded
    if len(id_input) == 0 or (id_input == "page-6-dropdown-lipizones" and l_lipizone_names is None):
        # Initialize with choroid plexus as the default lipid
        default_lipid = "choroid plexus"
        # Find lipid location for the default lipid
        l_lipizone_loc = (
            annotations
            .index[
                (annotations["name"] == default_lipid)
                #& (annotations["slice"] == slice_index)
            ]
            .tolist()
        )
        
        # If no match for current slice, try to find it in any slice
        if len(l_lipizone_loc) == 0:
            l_lipizone_loc = (
                annotations
                .index[
                    annotations["name"] == default_lipid
                ]
                .tolist()
            )[:1]
        
        # Set default lipid if found
        if len(l_lipizone_loc) > 0:
            lipizone_1_index = l_lipizone_loc[0]
            header_1 = default_lipid
            class_name_badge_1 = "position-absolute"
            
            # Initialize all_selected_lipizones with the default lipid
            all_selected_lipizones = {
                "names": [default_lipid],
                "indices": [lipizone_1_index]
            }
            
            return header_1, "", "", lipizone_1_index, -1, -1, class_name_badge_1, "d-none", "d-none", all_selected_lipizones
        else:
            # Fallback if lipid not found
            return "", "", "", -1, -1, -1, "d-none", "d-none", "d-none", {"names": [], "indices": []}

    # If dropdown selection has changed
    if id_input == "page-6-dropdown-lipizones" and l_lipizone_names is not None:
        # Update all_selected_lipizones with the new selection
        all_selected_lipizones = {"names": [], "indices": []}
        
        for lipizone_name in l_lipizone_names:
            # Find lipid location
            l_lipizone_loc = (
                annotations
                .index[
                    (annotations["name"] == lipizone_name)
                ]
                .tolist()
            )
            
            # If several lipids correspond to the selection, take the last one
            if len(l_lipizone_loc) > 1:
                logging.warning("More than one lipid corresponds to the selection")
                l_lipizone_loc = [l_lipizone_loc[-1]]
            
            # If no lipid found, try to find it in any slice
            if len(l_lipizone_loc) < 1:
                logging.warning("No lipid annotation exist. Taking another slice annotation")
                l_lipizone_loc = (
                    annotations
                    .index[
                        (annotations["name"] == lipizone_name)
                    ]
                    .tolist()
                )[:1]
            
            # Add to all_selected_lipizones if found
            if len(l_lipizone_loc) > 0:
                all_selected_lipizones["names"].append(lipizone_name)
                all_selected_lipizones["indices"].append(l_lipizone_loc[0])
        
        # For backward compatibility, update the first 3 badges
        # This keeps the existing UI elements working while we transition to the new approach
        header_1, header_2, header_3 = "", "", ""
        lipizone_1_index, lipizone_2_index, lipizone_3_index = -1, -1, -1
        class_name_badge_1, class_name_badge_2, class_name_badge_3 = "d-none", "d-none", "d-none"
        
        # Fill the first 3 badges with the first 3 selected lipizones
        for i, (name, index) in enumerate(zip(all_selected_lipizones["names"][:3], all_selected_lipizones["indices"][:3])):
            if i == 0:
                header_1 = name
                lipizone_1_index = index
                class_name_badge_1 = "position-absolute"
            elif i == 1:
                header_2 = name
                lipizone_2_index = index
                class_name_badge_2 = "position-absolute"
            elif i == 2:
                header_3 = name
                lipizone_3_index = index
                class_name_badge_3 = "position-absolute"
        
        return (
            header_1,
            header_2,
            header_3,
            lipizone_1_index,
            lipizone_2_index,
            lipizone_3_index,
            class_name_badge_1,
            class_name_badge_2,
            class_name_badge_3,
            all_selected_lipizones,
        )
    
    # If a new slice has been selected
    if id_input == "main-slider":
        # Update indices for all selected lipizones for the new slice
        updated_indices = []
        for name in all_selected_lipizones["names"]:
            # Find lipid location for the new slice
            l_lipizone_loc_temp = (
                annotations
                .index[
                    (annotations["name"] == name)
                ]
                .tolist()
            )
            
            #########################################################
            annotations = pd.read_csv("./data/annotations/lipizones_annotation_historic.csv")

            l_lipizone_loc = [
                l_lipizone_loc_temp[i]
                for i, x in enumerate(
                    annotations.iloc[l_lipizone_loc_temp]["slice"] == slice_index
                )
                if x
            ]
            
            # Record location and lipid name
            lipizone_index = l_lipizone_loc[0] if len(l_lipizone_loc) > 0 else -1
            updated_indices.append(lipizone_index)
        
        all_selected_lipizones["indices"] = updated_indices
        
        # For backward compatibility, update the first 3 badges
        header_1, header_2, header_3 = "", "", ""
        lipizone_1_index, lipizone_2_index, lipizone_3_index = -1, -1, -1
        class_name_badge_1, class_name_badge_2, class_name_badge_3 = "d-none", "d-none", "d-none"
        
        # Fill the first 3 badges with the first 3 selected lipizones
        for i, (name, index) in enumerate(zip(all_selected_lipizones["names"][:3], all_selected_lipizones["indices"][:3])):
            if i == 0:
                header_1 = name
                lipizone_1_index = index
                class_name_badge_1 = "position-absolute"
            elif i == 1:
                header_2 = name
                lipizone_2_index = index
                class_name_badge_2 = "position-absolute"
            elif i == 2:
                header_3 = name
                lipizone_3_index = index
                class_name_badge_3 = "position-absolute"
        
        return (
            header_1,
            header_2,
            header_3,
            lipizone_1_index,
            lipizone_2_index,
            lipizone_3_index,
            class_name_badge_1,
            class_name_badge_2,
            class_name_badge_3,
            all_selected_lipizones,
        )
    
    # For any other case, return no update
    return dash.no_update


# @app.callback(
#     Output("page-6-graph-high-resolution-spectrum", "style"),
#     Input("page-6-graph-high-resolution-spectrum", "figure"),
# )
# def page_6_display_high_res_mz_plot(figure):
#     """This callback is used to turn visible the high-resolution m/z plot."""
#     if figure is not None:
#         if figure["data"][0]["x"] != [[]]:
#             return {"height": 280}

#     return {"display": "none"}


# @app.callback(
#     Output("page-6-alert", "style"),
#     Input("page-6-graph-high-resolution-spectrum", "figure"),
# )
# def page_6_display_alert(figure):
#     """This callback is used to turn visible the alert regarding the high-res m/z plot."""
#     if figure is not None:
#         if figure["data"][0]["x"] != [[]]:
#             return {"display": "none"}
#     return {}


@app.callback(
    Output("page-6-download-data", "data"),
    Input("page-6-download-data-button", "n_clicks"),
    State("page-6-selected-lipizone-1", "data"),
    State("page-6-selected-lipizone-2", "data"),
    State("page-6-selected-lipizone-3", "data"),
    State("page-6-all-selected-lipizones", "data"),
    State("main-slider", "data"),
    State("page-6-toggle-apply-transform", "checked"),
    State("page-6-badge-input", "children"),
    State("boundaries-low-resolution-mz-plot", "data"),
    State("page-6-lower-bound", "value"),
    State("page-6-upper-bound", "value"),
    prevent_initial_call=True,
)
def page_6_download(
    n_clicks,
    lipizone_1_index,
    lipizone_2_index,
    lipizone_3_index,
    all_selected_lipizones,
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
        or graph_input == "Current input: " + "Lipizones selection"
    ):
        # First check if we have lipizones in the all_selected_lipizones store
        if all_selected_lipizones and len(all_selected_lipizones.get("indices", [])) > 0:
            l_lipids_indexes = all_selected_lipizones.get("indices", [])
            
            # If lipids has been selected from the dropdown, filter them in the df and download them
            if len(l_lipids_indexes) > 0:
                def to_excel(bytes_io):
                    xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                    annotations.iloc[l_lipids_indexes].to_excel(
                        xlsx_writer, index=False, sheet_name="Selected lipids"
                    )
                    for i, index in enumerate(l_lipids_indexes):
                        name = annotations.iloc[index]["name"]

                        # Need to clean name to use it as a sheet name
                        name = name.replace(":", "").replace("/", "")
                        lb = float(annotations.iloc[index]["min"]) - 10**-2
                        hb = float(annotations.iloc[index]["max"]) + 10**-2
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

                return dcc.send_data_frame(to_excel, "my_lipizone_selection.xlsx")
        
        # For backward compatibility, check the individual lipizone indices
        l_lipids_indexes = [
            x for x in [lipizone_1_index, lipizone_2_index, lipizone_3_index] if x is not None and x != -1
        ]
        # If lipids has been selected from the dropdown, filter them in the df and download them
        if len(l_lipids_indexes) > 0:

            def to_excel(bytes_io):
                xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                annotations.iloc[l_lipids_indexes].to_excel(
                    xlsx_writer, index=False, sheet_name="Selected lipids"
                )
                for i, index in enumerate(l_lipids_indexes):
                    name = annotations.iloc[index]["name"]

                    # Need to clean name to use it as a sheet name
                    name = name.replace(":", "").replace("/", "")
                    lb = float(annotations.iloc[index]["min"]) - 10**-2
                    hb = float(annotations.iloc[index]["max"]) + 10**-2
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

            return dcc.send_data_frame(to_excel, "my_lipizone_selection.xlsx")

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


clientside_callback(
    """
    function(n_clicks){
        if(n_clicks > 0){
            domtoimage.toBlob(document.getElementById('page-6-graph-heatmap-mz-selection'))
                .then(function (blob) {
                    window.saveAs(blob, 'lipizone_selection_plot.png');
                }
            );
        }
    }
    """,
    Output("page-6-download-image-button", "n_clicks"),
    Input("page-6-download-image-button", "n_clicks"),
)
"""This clientside callback is used to download the current heatmap."""


@app.callback(
    Output("page-6-rgb-button", "disabled"),
    Output("page-6-all-sections-button", "disabled"),
    Input("page-6-selected-lipizone-1", "data"),
    Input("page-6-selected-lipizone-2", "data"),
    Input("page-6-selected-lipizone-3", "data"),
    Input("page-6-all-selected-lipizones", "data"),
)
def page_6_active_download(lipizone_1_index, lipizone_2_index, lipizone_3_index, all_selected_lipizones):
    # print("lipizone_1_index", lipizone_1_index)
    # print("lipizone_2_index", lipizone_2_index)
    # print("lipizone_3_index", lipizone_3_index)
    """This callback is used to toggle on/off the display rgb and colormap buttons."""
    # logging.info("Enabled rgb and colormap buttons")
    
    # First check if we have lipizones in the all_selected_lipizones store
    if all_selected_lipizones and len(all_selected_lipizones.get("names", [])) > 0:
        return False, False
    
    # For backward compatibility, check the individual lipizone indices
    # Get the current lipid selection
    l_lipids_indexes = [
        x for x in [lipizone_1_index, lipizone_2_index, lipizone_3_index] if x is not None and x != -1
    ]
    # If lipids has been selected from the dropdown, activate button
    if len(l_lipids_indexes) > 0:
        return False, False
    else:
        return True, True

# @app.callback(
#     Output("page-6-button-bounds", "disabled"),
#     Input("page-6-lower-bound", "value"),
#     Input("page-6-upper-bound", "value"),
# )
# def page_6_button_window(lb, hb):
#     """This callaback is used to toggle on/off the display heatmap from bounds button."""

#     # Check that the user has inputted something
#     if lb is not None and hb is not None:
#         lb, hb = float(lb), float(hb)
#         if lb >= 400 and hb <= 1600 and hb - lb > 0 and hb - lb < 10:
#             return False
#     return True


# @app.callback(
#     Output("page-6-drawer-low-res-spectra", "is_open"),
#     Input("page-6-show-low-res-spectrum-button", "n_clicks"),
#     Input("page-6-close-low-res-spectrum-button", "n_clicks"),
#     [State("page-6-drawer-low-res-spectra", "is_open")],
# )
# def toggle_offcanvas(n1, n2, is_open):
#     """This callback is used to toggle the low-res spectra drawer."""
#     if n1 or n2:
#         return not is_open
#     return is_open


# @app.callback(
#     Output("page-6-drawer-high-res-spectra", "is_open"),
#     Input("page-6-show-high-res-spectrum-button", "n_clicks"),
#     Input("page-6-close-high-res-spectrum-button", "n_clicks"),
#     [State("page-6-drawer-high-res-spectra", "is_open")],
# )
# def toggle_offcanvas_high_res(n1, n2, is_open):
#     """This callback is used to toggle the high-res spectra drawer."""
#     if n1 or n2:
#         return not is_open
#     return is_open

