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
from scipy.ndimage import gaussian_filter
import pickle
# threadpoolctl import threadpool_limits, threadpool_info
#threadpool_limits(limits=8)
import os
os.environ['OMP_NUM_THREADS'] = '6'

# LBAE imports
from app import app, figures, data, atlas, grid_data, lipizone_data
import plotly.express as px

# ==================================================================================================
# --- Helper functions
# ==================================================================================================

from modules.figures import black_aba_contours, is_light_color

# ==================================================================================================
# --- Layout
# ==================================================================================================

def return_layout(basic_config, slice_index):
    """Return the layout for the page."""
    # Create treemap data
    df_treemap, node_colors = lipizone_data.create_treemap_data_lipizones()
    
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
                    # Main visualization
                    dcc.Graph(
                        id="page-6-graph-heatmap-mz-selection",
                        config=basic_config | {
                            "toImageButtonOptions": {
                                "format": "png",
                                "filename": "brain_lipizone_selection",
                                "scale": 2,
                            },
                            "scrollZoom": True
                        },
                        style={
                            "width": "70%",
                            "height": "95%",
                            "position": "absolute",
                            "left": "20%",
                            "top": "0",
                            "background-color": "#1d1c1f",
                        },
                        figure=figures.build_lipid_heatmap_from_image(
                            # compute_hybrid_image(['#f75400'], brain_id="ReferenceAtlas"),
                            figures.all_sections_lipizones_image(
                                hex_colors_to_highlight=None, # all lipizones
                                brain_id="ReferenceAtlas"),
                            return_base64_string=False,
                            draw=False,
                            type_image="RGB",
                            return_go_image=False,
                        )
                    ),
                    # Hover text
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
                            "display": "block",
                        },
                    ),
                    # Left panel with treemap and controls
                    html.Div(
                        style={
                            "width": "20%",
                            "height": "95%",
                            "position": "absolute",
                            "left": "0",
                            "top": "0",
                            "background-color": "#1d1c1f",
                            "display": "flex",
                            "flexDirection": "column",
                            "padding": "10px",
                        },
                        children=[
                            # Title
                            html.H4(
                                "Visualize Lipizones",
                                style={
                                    "color": "white",
                                    "marginBottom": "15px",
                                    "fontSize": "1.2em",
                                    "fontWeight": "500",
                                }
                            ),
                            # Select All button
                            dmc.Button(
                                children="Select All Lipizones",
                                id="page-6-select-all-lipizones-button",
                                variant="filled",
                                color="cyan",
                                radius="md",
                                size="sm",
                                style={
                                    "marginBottom": "5px",
                                },
                            ),
                            # Treemap visualization
                            dcc.Graph(
                                id="page-6-lipizones-treemap",
                                figure=lipizone_data.create_treemap_figure_lipizones(df_treemap, node_colors),
                                style={
                                    "height": "40%",
                                    "background-color": "#1d1c1f",
                                },
                                config={'displayModeBar': False}
                            ),
                            # Current selection text
                            html.Div(
                                id="page-6-current-selection-text",
                                style={
                                    "padding": "10px",
                                    "color": "white",
                                    "fontSize": "0.9em",
                                    "backgroundColor": "#2c2c2c",
                                    "borderRadius": "5px",
                                    "marginTop": "10px",
                                },
                                children=["Click on a node in the tree to select all lipizones under it"]
                            ),
                            # Add selection buttons group
                            html.Div(
                                style={
                                    "marginTop": "10px",
                                    "display": "flex",
                                    "flexDirection": "row",
                                    "gap": "10px",
                                    "width": "100%",  # Take full width of container
                                },
                                children=[
                                    dmc.Button(
                                        children="Add current selection",
                                        id="page-6-add-selection-button",
                                        variant="filled",
                                        color="cyan",
                                        radius="md",
                                        size="sm",
                                        style={
                                            "flex": "1",
                                            "maxWidth": "50%",  # Ensure button doesn't exceed half the container
                                        },
                                    ),
                                    dmc.Button(
                                        children="Clear selection",
                                        id="page-6-clear-selection-button",
                                        variant="outline",
                                        color="red",
                                        radius="md",
                                        size="sm",
                                        style={
                                            "flex": "1",
                                            "maxWidth": "50%",  # Ensure button doesn't exceed half the container
                                        },
                                    ),
                                ]
                            ),
                            # Selected lipizones badges
                            html.Div(
                                id="page-6-selected-lipizones-badges",
                                style={
                                    "height": "30%",
                                    "overflowY": "auto",
                                    "padding": "10px",
                                    "marginTop": "10px",
                                    "backgroundColor": "#2c2c2c",
                                    "borderRadius": "5px",
                                },
                                children=[
                                    html.H6("Selected Lipizones", style={"color": "white", "marginBottom": "10px"}),
                                ]
                            ),
                        ],
                    ),
                    # Controls for section mode and aba annotations
                    html.Div(
                        style={
                            "left": "25%",
                            "top": "3rem",
                            "position": "fixed",
                            "z-index": 1000,
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.5rem",
                            "alignItems": "center",
                        },
                        children=[
                            # Sections mode control
                            dmc.SegmentedControl(
                                id="page-6-sections-mode",
                                value="one",
                                data=[
                                    {"value": "one", "label": "One section"},
                                    {"value": "all", "label": "All sections"},
                                ],
                                color="cyan",
                                disabled=True,
                                size="xs",
                                style={
                                    "width": "20em",
                                    "border": "1px solid rgba(255, 255, 255, 0.1)",
                                    "borderRadius": "4px",
                                }
                            ),
                            # Allen Brain Atlas switch
                            html.Div(
                                id="page-6-annotations-container",
                                style={
                                    "display": "flex",
                                    "flexDirection": "row",
                                    "alignItems": "left",
                                    "justifyContent": "left",
                                    "width": "20em",
                                },
                                children=[
                                    dmc.Switch(
                                        id="page-6-toggle-annotations",
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
                        ],
                    ),
                    # Controls at the bottom right
                    html.Div(
                        style={
                            "right": "1rem",
                            "bottom": "1rem",
                            "position": "fixed",
                            "z-index": 1000,
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.5rem",
                        },
                        children=[
                            dmc.Button(
                                children="Download data",
                                id="page-6-download-data-button",
                                variant="filled",
                                disabled=False,
                                color="cyan",
                                radius="md",
                                size="sm",
                                style={"width": "150px"},
                            ),
                            dmc.Button(
                                children="Download image",
                                id="page-6-download-image-button",
                                variant="filled",
                                disabled=False,
                                color="cyan",
                                radius="md",
                                size="sm",
                                style={"width": "150px"},
                            ),
                        ],
                    ),
                    dcc.Download(id="page-6-download-data"),
                ],
            ),
        ],
    )
    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================

@app.callback(
    Output("page-6-current-treemap-selection", "data"),
    Output("page-6-current-selection-text", "children"),
    Input("page-6-lipizones-treemap", "clickData"),
)
def update_current_selection(click_data):
    """Store the current treemap selection."""
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    print("input_id", input_id)
    value = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    print("value", value)
    if not click_data:
        return None, "Click on a node in the tree to select all lipizones under it"
    
    clicked_label = click_data["points"][0]["label"] # 1_1
    current_path = click_data["points"][0]["id"] # /1/
    
    # Filter hierarchy based on the clicked node's path
    filtered = lipizone_data.df_hierarchy_lipizones.copy()
    print("filtered", filtered.shape)
    # Get the level of the clicked node
    path_columns = ['level_1_name', 'level_2_name', 'level_3_name', 'level_4_name', 'subclass_name', 'lipizone_names']
    
    # Apply filters based on the entire path up to the clicked node
    for i, value in enumerate(current_path.split("/")):
        print(i, "value", value)
        if i < len(path_columns):
            column = path_columns[i]
            filtered = filtered[filtered[column].astype(str) == str(value)]
    
    # Get all lipizones under this node
    lipizones = sorted(filtered["lipizone_names"].unique())
    print("lipizones", len(lipizones))
    if lipizones:
        return lipizones, f"Selected: {clicked_label} ({len(lipizones)} lipizones)"
    
    return None, "Click on a node in the tree to select all lipizones under it"

@app.callback(
    Output("page-6-all-selected-lipizones", "data"),
    Input("page-6-select-all-lipizones-button", "n_clicks"),
    Input("page-6-add-selection-button", "n_clicks"),
    Input("page-6-clear-selection-button", "n_clicks"),
    State("page-6-current-treemap-selection", "data"),
    State("page-6-all-selected-lipizones", "data"),
    prevent_initial_call=True
)
def handle_selection_changes(
    select_all_clicks,
    add_clicks,
    clear_clicks,
    current_selection,
    all_selected_lipizones,
):
    """Handle all selection changes."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    # Get which button was clicked
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Handle select all button
    if triggered_id == "page-6-select-all-lipizones-button":
        all_lipizones = {"names": [], "indices": []}
        for lipizone_name in lipizone_data.df_hierarchy_lipizones["lipizone_names"].unique():
            lipizone_indices = lipizone_data.df_hierarchy_lipizones.index[
                lipizone_data.df_hierarchy_lipizones["lipizone_names"] == lipizone_name
            ].tolist()
            if lipizone_indices:
                all_lipizones["names"].append(lipizone_name)
                all_lipizones["indices"].extend(lipizone_indices[:1])
        return all_lipizones
    
    # Handle clear button
    elif triggered_id == "page-6-clear-selection-button":
        return {"names": [], "indices": []}
    
    # Handle add button
    elif triggered_id == "page-6-add-selection-button":
        if not current_selection:
            return all_selected_lipizones or {"names": [], "indices": []}
        
        # Initialize all_selected_lipizones if it's empty
        all_selected_lipizones = all_selected_lipizones or {"names": [], "indices": []}
        
        # Add each lipizone that isn't already selected
        for lipizone_name in current_selection:
            if lipizone_name not in all_selected_lipizones["names"]:
                # Find the indices for this lipizone
                lipizone_indices = lipizone_data.df_hierarchy_lipizones.index[
                    lipizone_data.df_hierarchy_lipizones["lipizone_names"] == lipizone_name
                ].tolist()
                
                if lipizone_indices:
                    all_selected_lipizones["names"].append(lipizone_name)
                    all_selected_lipizones["indices"].extend(lipizone_indices[:1])
        
        return all_selected_lipizones
    
    return dash.no_update

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
            x = hoverData["points"][0]["x"]
            y = hoverData["points"][0]["y"]
            try:
                return atlas.dic_acronym_name[acronym_mask[y, x]]
            except:
                return "Undefined"
    return dash.no_update

@app.callback(
    Output("page-6-graph-hover-text", "style"),
    Input("page-6-sections-mode", "value"),
)
def hide_hover_text(sections_mode):
    """This callback hides the hover text when in all-sections mode."""
    base_style = {
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
    }
    
    if sections_mode == "all":
        return {**base_style, "display": "none"}
    return {**base_style, "display": "block"}

@app.callback(
    Output("page-6-sections-mode", "disabled"),
    Input("page-6-all-selected-lipizones", "data"),
)
def page_6_active_sections_control(all_selected_lipizones):
    """This callback enables/disables the sections mode control based on lipizone selection."""
    # Enable control if at least one lipizone is selected
    if all_selected_lipizones and len(all_selected_lipizones.get("names", [])) > 0:
        return False
    return True

@app.callback(
    Output("page-6-graph-heatmap-mz-selection", "figure"),
    Input("main-slider", "data"),
    Input("page-6-all-selected-lipizones", "data"),
    Input("page-6-sections-mode", "value"),
    Input("main-brain", "value"),
    Input("page-6-toggle-annotations", "checked"),
)
def page_6_plot_graph_heatmap_mz_selection(
    slice_index,
    all_selected_lipizones,
    sections_mode,
    brain_id,
    annotations_checked,
):
    """This callback plots the heatmap of the selected lipid(s)."""
    logging.info("Entering function to plot heatmap or RGB depending on lipid selection")
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    
    overlay = black_aba_contours(data.get_aba_contours(slice_index)) if annotations_checked else None

    # Get the names of all selected lipizones
    selected_lipizone_names = all_selected_lipizones.get("names", [])
    
    # Define hex_colors_to_highlight using all selected lipizones
    hex_colors_to_highlight = [lipizone_data.lipizone_to_color[name] for name in selected_lipizone_names if name in lipizone_data.lipizone_to_color]
    
    # Handle annotations toggle separately to preserve figure state
    # the annotations can only be displayed if one section is selected
    if id_input == "page-6-toggle-annotations":
        # Check if we have any selected lipizones
        
        # Try to get the section data for the current slice and brain
        try:
            hybrid_image = figures.one_section_lipizones_image(
                slice_index,
                hex_colors_to_highlight=hex_colors_to_highlight,
            )
            
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
            logging.warning(f"Section data not found: {e}. Displaying all lipizones.")
            return figures.build_lipid_heatmap_from_image(
                # compute_hybrid_image(hex_colors_to_highlight, brain_id),
                figures.one_section_lipizones_image(
                    slice_index,
                    hex_colors_to_highlight=None, # all lipizones
                ),
                return_base64_string=False,
                draw=False,
                type_image="RGB",
                return_go_image=False,
                overlay=overlay,
            )
    
    # If a lipid selection has been done
    if (
        id_input == "page-6-all-selected-lipizones"
        or id_input == "page-6-sections-mode"
        or id_input == "main-brain"
        or id_input == "main-slider"
    ):
        
        if sections_mode == "one":
            # Try to get the section data for the current slice and brain
            hybrid_image = figures.one_section_lipizones_image(
                slice_index=slice_index,
                hex_colors_to_highlight=hex_colors_to_highlight,
            )
            
            return figures.build_lipid_heatmap_from_image(
                hybrid_image,
                return_base64_string=False,
                draw=False,
                type_image="RGB",
                return_go_image=False,
                overlay=overlay,
            )

        # Or if the current plot must be all sections
        elif sections_mode == "all":
            return figures.build_lipid_heatmap_from_image(
                figures.all_sections_lipizones_image(
                    hex_colors_to_highlight=hex_colors_to_highlight,
                    brain_id=brain_id),
                return_base64_string=False,
                draw=False,
                type_image="RGB",
                return_go_image=False,
            )
        else:
            # it should never happen
            logging.info("Section mode is neither 'one-section' nor 'all-sections'. Displaying default all lipizones and all sections")
            return figures.build_lipid_heatmap_from_image(
                # compute_hybrid_image(hex_colors_to_highlight, brain_id),
                figures.all_sections_lipizones_image(
                    hex_colors_to_highlight=None, # all lipizones
                    brain_id=brain_id),
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

# Add callback to update badges
@app.callback(
    Output("page-6-selected-lipizones-badges", "children"),
    Input("page-6-all-selected-lipizones", "data"),
)
def update_selected_lipizones_badges(all_selected_lipizones):
    """Update the badges showing selected lipizones with their corresponding colors."""
    children = [html.H6("Selected Lipizones", style={"color": "white", "marginBottom": "10px"})]
    
    if all_selected_lipizones and "names" in all_selected_lipizones:
        for name in all_selected_lipizones["names"]:
            # Get the color for this lipizone, default to cyan if not found
            lipizone_color = lipizone_data.lipizone_to_color.get(name, "#00FFFF")

            # Determine if the background color is light or dark
            is_light = is_light_color(lipizone_color)
            text_color = "black" if is_light else "white"
            
            # Create a style that uses the lipizone's color
            badge_style = {
                "margin": "2px",
                "backgroundColor": lipizone_color,
                "color": text_color,  # Use black text for better contrast
                "border": "none",
            }
            
            children.append(
                dmc.Badge(
                    name,
                    variant="filled",
                    size="sm",
                    style=badge_style,
                )
            )
    
    return children

@app.callback(
    Output("page-6-toggle-annotations", "disabled"),
    Input("page-6-sections-mode", "value"),
)
def page_6_toggle_annotations_visibility(sections_mode):
    """This callback enables/disables the annotations toggle based on sections mode."""
    # Only enable annotations toggle when in "one" section mode
    return sections_mode != "one"