# Copyright (c) 2024. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to visualize lipizones in 3D space."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html
import logging
import dash
import pandas as pd
from dash.dependencies import Input, Output, State
import dash_mantine_components as dmc
import numpy as np
import os
import re
import plotly.graph_objects as go
import traceback  # For detailed error logging
import time  # For performance tracking
import pickle
import plotly.express as px

# For debugging memory usage
import psutil
import gc
from tqdm import tqdm

# LBAE imports
from app import app, figures, lipizone_data

# ==================================================================================================
# --- Constants
# ==================================================================================================

# Path to the 3D lipizones data
# LIPIZONES_3D_PATH = "/data/luca/lipidatlas/ManuscriptAnalysisRound3/3d_lipizones"

import os
import zarr
import numpy as np
import logging
# from functools import lru_cache
from app import figures, lipizone_data

# ==================================================================================================
# --- Helper functions
# ==================================================================================================

from modules.figures import is_light_color, clean_filenamePD

def get_background_brain(downsample_factor=12):
    """
    Get the background brain visualization
    
    Parameters:
    -----------
    downsample_factor : int
        Factor by which to downsample the brain atlas
        
    Returns:
    --------
    go.Volume
        The 3D volume for the background brain
    """
    
    try:
        # Get atlas data from figures module
        brain_root_data = figures.compute_3D_root_volume(
            decrease_dimensionality_factor=downsample_factor
        )
        # Add showscale=False to the returned volume
        if hasattr(brain_root_data, 'showscale'):
            brain_root_data.showscale = False
        return brain_root_data
    except Exception as e:
        return None

# ==================================================================================================
# --- Layout
# ==================================================================================================

def return_layout(basic_config, slice_index):
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
            # Left panel for selection controls
            html.Div(
                style={
                    "position": "absolute", 
                    "left": "1%", 
                    "top": "1em", 
                    "width": "22em",
                    "zIndex": 100,
                    "backgroundColor": "#1d1c1f",
                    "display": "flex",
                    "flexDirection": "column",
                    "padding": "10px",
                },
                children=[
                    # Title
                    html.H4(
                        "Select Lipizones for 3D Visualization",
                        style={
                            "color": "white",
                            "marginBottom": "15px",
                            "fontSize": "1.2em",
                            "fontWeight": "500",
                        }
                    ),
                    # Treemap visualization
                    dcc.Graph(
                        id="3d-lipizones-treemap",
                        figure=lipizone_data.create_treemap_figure_lipizones(df_treemap, node_colors),
                        style={
                            "height": "40%",
                            "background-color": "#1d1c1f",
                        },
                        config={'displayModeBar': False}
                    ),
                    # Current selection text
                    html.Div(
                        id="3d-lipizones-current-selection-text",
                        style={
                            "padding": "10px",
                            "color": "white",
                            "fontSize": "0.9em",
                            "backgroundColor": "#2c2c2c",
                            "borderRadius": "5px",
                            "marginTop": "10px",
                        },
                        children=["Click on a node in the tree to select lipizones"]
                    ),
                    # Selected lipizones badges
                    html.Div(
                        id="3d-lipizones-selected-lipizones-badges",
                        style={
                            "padding": "10px",
                            "marginTop": "10px",
                            "backgroundColor": "#2c2c2c",
                            "borderRadius": "5px",
                            "maxHeight": "200px",
                            "overflowY": "auto",
                        },
                        children=[
                            html.H6("Selected Lipizones", style={"color": "white", "marginBottom": "10px"}),
                        ]
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
                                id="3d-lipizones-add-selection-button",
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
                                id="3d-lipizones-clear-selection-button",
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
                    # Button to view all lipizones together
                    dmc.Button(
                        "View All Lipizones",
                        id="view-all-lipizones-btn",
                        color="blue",
                        style={"width": "100%", "marginTop": "1.5em"},
                    ),
                ],
            ),
            
            # 3D visualization container
            html.Div(
                id="3d-lipizones-visualization-container",
                style={
                    "width": "calc(100% - 22em)",  # Leave space for the left panel
                    "height": "100%",
                    "position": "absolute",
                    "top": "0",
                    "right": "0",
                    "backgroundColor": "#1d1c1f",
                },
                children=[
                    html.Div(
                        "Select lipizones to view their 3D distribution", 
                        style={
                            "color": "white", 
                            "textAlign": "center", 
                            "marginTop": "20%"
                        }
                    )
                ]
            ),
        ],
    )
    
    return page

# ==================================================================================================
# --- Callbacks
# ==================================================================================================

@app.callback(
    Output("3d-lipizones-current-treemap-selection", "data"),
    Output("3d-lipizones-current-selection-text", "children"),
    Input("3d-lipizones-treemap", "clickData"),
)
def update_current_selection(click_data):
    """Store the current treemap selection."""
    if not click_data:
        return None, "Click on a node in the tree to select lipizones"
    
    clicked_label = click_data["points"][0]["label"]
    current_path = click_data["points"][0]["id"]
    
    # Filter hierarchy based on the clicked node's path
    filtered = lipizone_data.df_hierarchy_lipizones.copy()
    
    # Get the level of the clicked node
    path_columns = ['level_1_name', 'level_2_name', 'level_3_name', 'level_4_name', 'subclass_name', 'lipizone_names']
    
    # Apply filters based on the entire path up to the clicked node
    for i, value in enumerate(current_path.split("/")):
        if i < len(path_columns):
            column = path_columns[i]
            filtered = filtered[filtered[column].astype(str) == str(value)]
    
    # Get all lipizones under this node
    lipizones = sorted(filtered["lipizone_names"].unique())
    
    if lipizones:
        return lipizones, f"Selected: {clicked_label} ({len(lipizones)} lipizones)"
    
    return None, "Click on a node in the tree to select lipizones"

@app.callback(
    Output("3d-lipizones-all-selected-lipizones", "data"),
    Input("3d-lipizones-add-selection-button", "n_clicks"),
    Input("3d-lipizones-clear-selection-button", "n_clicks"),
    State("3d-lipizones-current-treemap-selection", "data"),
    State("3d-lipizones-all-selected-lipizones", "data"),
    prevent_initial_call=True
)
def handle_selection_changes(
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
    
    # Handle clear button
    if triggered_id == "3d-lipizones-clear-selection-button":
        return {"names": [], "indices": []}
    
    # Handle add button
    elif triggered_id == "3d-lipizones-add-selection-button":
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
    Output("3d-lipizones-selected-lipizones-badges", "children"),
    Input("3d-lipizones-all-selected-lipizones", "data"),
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
            
            # Create a style that uses the lipizone's color and appropriate text color
            badge_style = {
                "margin": "2px",
                "backgroundColor": lipizone_color,
                "color": text_color,  # Use black or white text based on background
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
    Output("all-lipizones-view-state", "data"),
    Input("view-all-lipizones-btn", "n_clicks"),
    Input("3d-lipizones-add-selection-button", "n_clicks"),
    Input("3d-lipizones-clear-selection-button", "n_clicks"),
    State("all-lipizones-view-state", "data"),
    prevent_initial_call=True,
)
def update_all_lipizones_view_state(view_all_clicks, add_selection_clicks, clear_selection_clicks, current_state):
    """Update the all-lipizones-view-state based on button clicks"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    # Get which button was clicked
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if triggered_id == "view-all-lipizones-btn":
        return True
    elif triggered_id in ["3d-lipizones-add-selection-button", "3d-lipizones-clear-selection-button"]:
        return False
    
    return current_state

@app.callback(
    Output("3d-lipizones-visualization-container", "children"),
    [Input("3d-lipizones-all-selected-lipizones", "data"),
     Input("all-lipizones-view-state", "data")],
    prevent_initial_call=True,
)
def update_3d_visualization(
        all_selected_lipizones, 
        view_all_lipizones
        ):
    print("\n============= update_3d_visualization =============")
    start_time = time.time()
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    print(f"Callback triggered by {trigger_id} with view_all_lipizones={view_all_lipizones}")
    print("all_selected_lipizones", all_selected_lipizones)
    print("view_all_lipizones", view_all_lipizones)
    
    logging.info(f"Callback triggered by {trigger_id} with view_all_lipizones={view_all_lipizones}")
    
    try:
        # If the "View All Lipizones" button was clicked
        if view_all_lipizones:
            print("\n------------- view_all_lipizones -------------")
            logging.info("Displaying all lipizones view")
            try:
                # Create figure with all lipizones
                fig = figures.create_all_lipizones_figure(downsample_factor=1)
                # save fig to file
                fig.write_html("all_lipizones.html")
                
                return dcc.Graph(
                    figure=fig,
                    style={"height": "100%", "width": "100%"},
                    config={
                        "displayModeBar": True,
                        "displaylogo": False,
                        "scrollZoom": True
                    }
                )
            except Exception as e:
                logging.error(f"Error rendering all lipizones: {str(e)}")
                logging.error(traceback.format_exc())
                return html.Div(
                    f"Error loading all lipizones visualization: {str(e)}", 
                    style={"color": "white", "textAlign": "center", "marginTop": "20%"}
                )
        
        # Otherwise, handle individual lipizone selection
        if not all_selected_lipizones or not all_selected_lipizones.get("names") or len(all_selected_lipizones["names"]) == 0:
            return html.Div(
                "Select lipizones to view their 3D distribution. Consider that this might take seconds to minutes to load.", 
                style={
                    "color": "white", 
                    "textAlign": "center", 
                    "marginTop": "20%"
                }
            )
        
        # Adaptive downsampling based on number of lipizones
        num_lipizones = len(all_selected_lipizones["names"])
        if num_lipizones <= 1:
            downsample_factor = 1
        elif num_lipizones <= 5:
            downsample_factor = 2
        elif num_lipizones <= 20:
            downsample_factor = 4
        elif num_lipizones <= 100:
            downsample_factor = 8
        else:
            downsample_factor = 16
        
        logging.info(f"Using adaptive downsample factor {downsample_factor} for {num_lipizones} lipizones")
        
        # Get background brain visualization
        background_brain = get_background_brain(downsample_factor)
        
        # Process each selected lipizone
        data_list = []
        if background_brain is not None:
            data_list.append(background_brain)
        
        store = zarr.DirectoryStore(lipizone_data.LIPIZONES_ZARR_PATH)
        root = zarr.group(store=store)
        all_lipizones = root['all_lipizones'] # this is the array of lipizone ids (528, 320, 456)
        
        for i, lipizone_name in tqdm(enumerate(all_selected_lipizones["names"]), total=len(all_selected_lipizones["names"]), desc="Processing lipizones"):
            lipizone_index = all_selected_lipizones["indices"][i]
            # Get the lipizone name and clean it
            safe_name = clean_filenamePD(lipizone_name)
            
            mask = all_lipizones[:] == lipizone_index
            # array *= mask.astype(int) --> range in [0, lipizone_index]
            array = mask.astype(float) # range in [0, 1.0]
            
            if array is None:
                logging.warning(f"No valid data loaded for {lipizone_name} (safe name: {safe_name}).")
                continue
            
            # Get the color for this lipizone
            color = lipizone_data.lipizone_to_color.get(lipizone_name, "#1f77b4")  # default blue
            
            # Create the 3D visualization
            try:
                lipizone_volume = figures.create_lipizone_3d_figure(array, color, downsample_factor)
                data_list.append(lipizone_volume)
                
            except Exception as e:
                logging.error(f"Error creating 3D visualization for {lipizone_name}: {str(e)}")
                continue
        
        # If no valid lipizones were processed
        if len(data_list) == 0 or (len(data_list) == 1 and background_brain is not None):
            return html.Div(
                "No valid lipizone data found for the selected lipizones.",
                style={"color": "white", "textAlign": "center", "marginTop": "20%"}
            )
        
        # Create the combined figure
        fig = go.Figure(data=data_list)
        
        # Improve layout
        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            scene=dict(
                xaxis=dict(
                    showticklabels=False,
                    showgrid=False,
                    zeroline=False,
                    backgroundcolor="rgba(0,0,0,0)",
                ),
                yaxis=dict(
                    showticklabels=False,
                    showgrid=False,
                    zeroline=False,
                    backgroundcolor="rgba(0,0,0,0)",
                ),
                zaxis=dict(
                    showticklabels=False,
                    showgrid=False,
                    zeroline=False,
                    backgroundcolor="rgba(0,0,0,0)",
                ),
                aspectmode="data",
            ),
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        
        end_time = time.time()
        logging.info(f"Total callback execution time: {end_time - start_time:.2f} seconds")
        
        return dcc.Graph(
            figure=fig,
            style={"height": "100%", "width": "100%"},
            config={
                "displayModeBar": True,
                "displaylogo": False,
                "scrollZoom": True
            }
        )
            
    except Exception as e:
        logging.error(f"Unexpected error in callback: {str(e)}")
        logging.error(traceback.format_exc())
        return html.Div(
            f"An error occurred: {str(e)}", 
            style={"color": "white", "textAlign": "center", "marginTop": "20%"}
        ) 