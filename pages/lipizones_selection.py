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
from app import app, figures, data, atlas, sample_data_shelve, section_data_shelve, grid_data

# ==================================================================================================
# --- Helper functions
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
            logging.info(f"Loaded {len(color_masks)} color masks from {filename}")
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

def black_aba_contours(overlay):
    black_overlay = overlay.copy()
    contour_mask = overlay[:, :, 3] > 0
    black_overlay[contour_mask] = [0, 0, 0, 200]  # RGB black with alpha=200
    
    return black_overlay

# ==================================================================================================
# --- Data
# ==================================================================================================

lipizonenames = pd.read_csv("/data/LBA_DATA/lbae/lipizonename2color.csv", index_col=0)['lipizone_names'].values
lipizonecolors = pd.read_csv("/data/LBA_DATA/lbae/lipizonename2color.csv", index_col=0).to_dict(orient="records")
lipizonecolors = {row["lipizone_names"]: row["lipizone_color"] for row in lipizonecolors}
annotations = pd.read_csv("/data/LBA_DATA/lbae/data/annotations/lipizones_annotation.csv")
annotations_historic = pd.read_csv("/data/LBA_DATA/lbae/data/annotations/lipizones_annotation_historic.csv")

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

df_hierarchy = pd.read_csv("/data/LBA_DATA/lbae/data/annotations/lipizones_hierarchy.csv")

# ==================================================================================================
# --- Layout
# ==================================================================================================

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
                    dcc.Graph(
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
                                        id="page-6-one-section-button",
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
                                    dmc.Switch(
                                        id="page-6-toggle-annotations",
                                        label="Allen Brain Atlas Annotations",
                                        checked=False,
                                        color="cyan",
                                        radius="xl",
                                        size="sm",
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
                        ],
                    ),
                    dmc.Text(
                        "",
                        id="page-6-graph-hover-text",
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
    Output("page-6-graph-hover-text", "children"),
    Input("page-6-graph-heatmap-mz-selection", "hoverData"),
    Input("main-slider", "data"),
)
def page_6_hover(hoverData, slice_index):
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
    Output("page-6-select-level-2", "data"),
    Input("page-6-select-level-1", "value"),
)
def update_level2(level1_vals):
    print("==================== update_level2 =====================")
    # print("trigger input:", dash.callback_context.triggered)
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
    print("==================== update_level3 =====================")
    # print("trigger input:", dash.callback_context.triggered)
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
    print("==================== update_level4 =====================")
    # print("trigger input:", dash.callback_context.triggered)
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
    print("==================== update_subclass =====================")
    # print("trigger input:", dash.callback_context.triggered)
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
    print("==================== update_lipizone_names =====================")
    # print("trigger input:", dash.callback_context.triggered)
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
    print("==================== auto_select_all =====================")
    # print("trigger input:", dash.callback_context.triggered)
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
    print("==================== clear_lower_levels =====================")
    # print("trigger input:", dash.callback_context.triggered)
    return None, None, None, None

@app.callback(
    Output("page-6-graph-heatmap-mz-selection", "figure"),
    
    Input("main-slider", "data"),
    Input("page-6-all-selected-lipizones", "data"),
    Input("page-6-one-section-button", "n_clicks"),
    Input("page-6-all-sections-button", "n_clicks"),
    Input("main-brain", "value"),
    Input("page-6-toggle-annotations", "checked"),
    )
def page_6_plot_graph_heatmap_mz_selection(
    slice_index,
    all_selected_lipizones,
    n_clicks_button_one_section,
    n_clicks_button_all_sections,
    brain_id,
    annotations_checked,
):
    """This callback plots the heatmap of the selected lipid(s)."""
    print(f"\n========== page_6_plot_graph_heatmap_mz_selection ==========")
    # print("trigger input:", dash.callback_context.triggered)
    logging.info("Entering function to plot heatmap or RGB depending on lipid selection")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    overlay = black_aba_contours(data.get_aba_contours(slice_index)) if annotations_checked else None

    # Handle annotations toggle separately to preserve figure state
    if id_input == "page-6-toggle-annotations":
        # Check if we have any selected lipizones
        if all_selected_lipizones and len(all_selected_lipizones.get("names", [])) > 0:
            # Get the names of all selected lipizones
            selected_lipizone_names = all_selected_lipizones.get("names", [])
            
            # Define hex_colors_to_highlight using all selected lipizones
            hex_colors_to_highlight = [lipizonecolors[name] for name in selected_lipizone_names if name in lipizonecolors]
        
            # Try to get the section data for the current slice and brain
            try:
                # Create a section key based on brain_id and slice_index
                section_data = section_data_shelve.retrieve_section_data(float(slice_index))
            
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
                    overlay=overlay,
                )
            except KeyError as e:
                # If section data not found, fall back to the hybrid image
                logging.warning(f"Section data not found: {e}. Using hybrid image instead.")
                return figures.build_lipid_heatmap_from_image(
                    compute_hybrid_image(hex_colors_to_highlight, brain_id),
                    return_base64_string=False,
                    draw=False,
                    type_image="RGB",
                    return_go_image=False,
                    overlay=overlay,
                )
    
    # If a lipid selection has been done
    if (
        id_input == "page-6-selected-lipizone-1"
        or id_input == "page-6-selected-lipizone-2"
        or id_input == "page-6-selected-lipizone-3"
        or id_input == "page-6-all-selected-lipizones"
        or id_input == "page-6-one-section-button"
        or id_input == "page-6-all-sections-button"
        or id_input == "main-brain"
        or (
            (id_input == "main-slider")
        )
    ):
        # Check if we have any selected lipizones
        if all_selected_lipizones and len(all_selected_lipizones.get("names", [])) > 0:
            # Get the names of all selected lipizones
            selected_lipizone_names = all_selected_lipizones.get("names", [])
            
            # Define hex_colors_to_highlight using all selected lipizones
            hex_colors_to_highlight = [lipizonecolors[name] for name in selected_lipizone_names if name in lipizonecolors]
    
            # Or if the current plot must be an RGB image
            if (
                id_input == "page-6-one-section-button"
                or (
                    id_input == "main-slider"
                    # and graph_input == "Current input: " + "Lipid selection RGB"
                )
            ):
                # Try to get the section data for the current slice and brain
                try:
                    # Create a section key based on brain_id and slice_index
                    section_data = section_data_shelve.retrieve_section_data(float(slice_index))
                
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
                        overlay=overlay,
                    )
                except KeyError as e:
                    # If section data not found, fall back to the hybrid image
                    logging.warning(f"Section data not found: {e}. Using hybrid image instead.")
                    return figures.build_lipid_heatmap_from_image(
                        compute_hybrid_image(hex_colors_to_highlight, brain_id),
                        return_base64_string=False,
                        draw=False,
                        type_image="RGB",
                        return_go_image=False,
                        overlay=overlay,
                    )

            # Or if the current plot must be all sections
            elif (
                id_input == "page-6-all-sections-button"
                or (
                    id_input == "main-slider"
                    # and graph_input == "Current input: " + "Lipid selection all sections"
                )
            ):
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
                        )
                    except (KeyError, Exception) as e:
                        # If that fails, fall back to the hybrid image
                        logging.warning(f"Failed to retrieve grid image: {e}. Using hybrid image instead.")
                        return figures.build_lipid_heatmap_from_image(
                            compute_hybrid_image(hex_colors_to_highlight, brain_id),
                            return_base64_string=False,
                            draw=False,
                            type_image="RGB",
                            return_go_image=False,
                        )
                else:
                    logging.info("Trying to display all sections for more than one lipid, not possible. Using first selected lipid.")
                    first_lipid = selected_lipizone_names[0] if selected_lipizone_names else "choroid plexus"
                    return figures.build_lipid_heatmap_from_image(
                        compute_hybrid_image(hex_colors_to_highlight, brain_id),
                        return_base64_string=False,
                        draw=False,
                        type_image="RGB",
                        return_go_image=False,
                    )

            # Plot RGB by default
            else:
                logging.info("Right before calling the graphing function")
                return figures.build_lipid_heatmap_from_image(
                    compute_hybrid_image(hex_colors_to_highlight, brain_id),
                    return_base64_string=False,
                    draw=False,
                    type_image="RGB",
                    return_go_image=False,
                    overlay=overlay,
                )
        elif (
            id_input == "main-slider"#  and graph_input == "Current input: "
        ):
            # Use default color for choroid plexus
            hex_colors_to_highlight = ['#f75400']  # Default color for choroid plexus
            return figures.build_lipid_heatmap_from_image(
                    compute_hybrid_image(hex_colors_to_highlight, brain_id),
                    return_base64_string=False,
                    draw=False,
                    type_image="RGB",
                    return_go_image=False,
                    overlay=overlay,
                )
        else:
            # No lipid has been selected, return image from boundaries using RGB
            hex_colors_to_highlight = ['#f75400']  # Default color for choroid plexus
            return figures.build_lipid_heatmap_from_image(
                    compute_hybrid_image(hex_colors_to_highlight, brain_id),
                    return_base64_string=False,
                    draw=False,
                    type_image="RGB",
                    return_go_image=False,
                    overlay=overlay,
                )

    # If no trigger, the page has just been loaded, so load new figure with default parameters
    else:
        return dash.no_update


@app.callback(
    Output("page-6-all-selected-lipizones", "data"),

    Input("page-6-dropdown-lipizones", "value"),
    Input("main-slider", "data"),

    State("main-brain", "value"),
    State("page-6-all-selected-lipizones", "data"),
)
def page_6_add_toast_selection(
    l_lipizone_names,
    slice_index,
    brain_id,
    all_selected_lipizones,
):
    """This callback adds the selected lipid to the selection."""
    logging.info("Entering function to update lipid data")
    # annotations = pd.read_csv("/data/LBA_DATA/lbae/data/annotations/lipizones_annotation.csv")
    # print("\n================ page_6_add_toast_selection ================")
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    
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
            # Initialize all_selected_lipizones with the default lipid
            all_selected_lipizones = {
                "names": [default_lipid],
                "indices": [ l_lipizone_loc[0]]
            }
            
            return all_selected_lipizones
        else:
            # Fallback if lipid not found
            return {"names": [], "indices": []}

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

        return all_selected_lipizones
    
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

            l_lipizone_loc = [
                l_lipizone_loc_temp[i]
                for i, x in enumerate(
                    annotations_historic.iloc[l_lipizone_loc_temp]["slice"] == slice_index
                )
                if x
            ]
            
            # Record location and lipid name
            lipizone_index = l_lipizone_loc[0] if len(l_lipizone_loc) > 0 else -1
            updated_indices.append(lipizone_index)
        
        all_selected_lipizones["indices"] = updated_indices
        return all_selected_lipizones
    
    # For any other case, return no update
    return dash.no_update

# # TODO
# @app.callback(
#     Output("page-6-download-data", "data"),
#     Input("page-6-download-data-button", "n_clicks"),
#     State("page-6-selected-lipizone-1", "data"),
#     State("page-6-selected-lipizone-2", "data"),
#     State("page-6-selected-lipizone-3", "data"),
#     State("page-6-all-selected-lipizones", "data"),
#     State("main-slider", "data"),
#     State("page-6-badge-input", "children"),
#     prevent_initial_call=True,
# )
# def page_6_download(
#     n_clicks,
#     lipizone_1_index,
#     lipizone_2_index,
#     lipizone_3_index,
#     all_selected_lipizones,
#     slice_index,
#     graph_input,
# ):
#     """This callback is used to generate and download the data in proper format."""

#     # Current input is lipid selection
#     if (
#         graph_input == "Current input: " + "Lipid selection colormap"
#         or graph_input == "Current input: " + "Lipid selection RGB"
#         or graph_input == "Current input: " + "Lipizones selection"
#     ):
#         # First check if we have lipizones in the all_selected_lipizones store
#         if all_selected_lipizones and len(all_selected_lipizones.get("indices", [])) > 0:
#             l_lipids_indexes = all_selected_lipizones.get("indices", [])
            
#             # If lipids has been selected from the dropdown, filter them in the df and download them
#             if len(l_lipids_indexes) > 0:
#                 def to_excel(bytes_io):
#                     xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
#                     annotations.iloc[l_lipids_indexes].to_excel(
#                         xlsx_writer, index=False, sheet_name="Selected lipids"
#                     )
#                     for i, index in enumerate(l_lipids_indexes):
#                         name = annotations.iloc[index]["name"]

#                         # Need to clean name to use it as a sheet name
#                         name = name.replace(":", "").replace("/", "")
#                         lb = float(annotations.iloc[index]["min"]) - 10**-2
#                         hb = float(annotations.iloc[index]["max"]) + 10**-2
#                         x, y = figures.compute_spectrum_high_res(
#                             slice_index,
#                             lb,
#                             hb,
#                             plot=False,
#                             # standardization=apply_transform,
#                             cache_flask=cache_flask,
#                         )
#                         df = pd.DataFrame.from_dict({"m/z": x, "Intensity": y})
#                         df.to_excel(xlsx_writer, index=False, sheet_name=name[:31])
#                     xlsx_writer.save()

#                 return dcc.send_data_frame(to_excel, "my_lipizone_selection.xlsx")
        
#         # For backward compatibility, check the individual lipizone indices
#         l_lipids_indexes = [
#             x for x in [lipizone_1_index, lipizone_2_index, lipizone_3_index] if x is not None and x != -1
#         ]
#         # If lipids has been selected from the dropdown, filter them in the df and download them
#         if len(l_lipids_indexes) > 0:

#             def to_excel(bytes_io):
#                 xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
#                 annotations.iloc[l_lipids_indexes].to_excel(
#                     xlsx_writer, index=False, sheet_name="Selected lipids"
#                 )
#                 for i, index in enumerate(l_lipids_indexes):
#                     name = annotations.iloc[index]["name"]

#                     # Need to clean name to use it as a sheet name
#                     name = name.replace(":", "").replace("/", "")
#                     lb = float(annotations.iloc[index]["min"]) - 10**-2
#                     hb = float(annotations.iloc[index]["max"]) + 10**-2
#                     x, y = figures.compute_spectrum_high_res(
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

#             return dcc.send_data_frame(to_excel, "my_lipizone_selection.xlsx")

#     return dash.no_update


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
    Output("page-6-one-section-button", "disabled"),
    Output("page-6-all-sections-button", "disabled"),
    
    Input("page-6-all-selected-lipizones", "data"),
)
def page_6_active_download(
    all_selected_lipizones):
    """This callback is used to toggle on/off the display rgb and colormap buttons."""
    logging.info("Enabled rgb and colormap buttons")
    
    # First check if we have lipizones in the all_selected_lipizones store
    if all_selected_lipizones and len(all_selected_lipizones.get("names", [])) > 0:
        return False, False
    
    else:
        return True, True