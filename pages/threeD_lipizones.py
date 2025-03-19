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

# For debugging memory usage
import psutil
import gc

# LBAE imports
from app import app, figures, data, storage, cache_flask

# ==================================================================================================
# --- Constants
# ==================================================================================================

# Path to the 3D lipizones data
LIPIZONES_3D_PATH = "/data/luca/lipidatlas/ManuscriptAnalysisRound3/3d_lipizones"

import os
import zarr
import numpy as np
import logging
from functools import lru_cache

# New constant for the Zarr store location
LIPIZONES_ZARR_PATH = "/data/luca/lipidatlas/ManuscriptAnalysisRound3/3d_lipizones.zarr"

@lru_cache(maxsize=50)
def load_lipizone_array(safe_name, downsample_factor):
    """
    Load the lipizone array from the Zarr store using the given downsample factor.
    This function is cached to avoid re-loading data that was recently requested.
    """
    try:
        store = zarr.DirectoryStore(LIPIZONES_ZARR_PATH)
        root = zarr.group(store=store)
        if safe_name not in root:
            logging.warning(f"No data found for {safe_name} in the Zarr store.")
            return None
        group = root[safe_name]
        key = f"downsampled_{downsample_factor}"
        if key in group:
            # This array is loaded lazily; slicing will read only needed chunks.
            return group[key][:]
        elif "full" in group:
            # If the precomputed downsampled version isn’t available, fall back to downsampling on the fly.
            arr = group["full"][:]
            return arr[::downsample_factor, ::downsample_factor, ::downsample_factor]
        else:
            logging.warning(f"Neither full nor downsampled array found for {safe_name}.")
            return None
    except Exception as e:
        logging.error(f"Error loading lipizone {safe_name}: {str(e)}")
        return None


# Load lipizone names from CSV
lipizonenames = pd.read_csv("lipizonename2color.csv")
lipizonenames = lipizonenames['lipizone_names'].values

# Load hierarchy data for the multiselect
df_hierarchy = pd.read_csv("./data/annotations/lipizones_hierarchy.csv")

# ==================================================================================================
# --- Layout
# ==================================================================================================

def return_layout(basic_config, slice_index):
    # Precompute level_1 options for the dropdown
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
            # Left panel for selection controls
            dmc.Group(
                direction="column",
                spacing=0,
                style={
                    "position": "absolute", 
                    "left": "1%", 
                    "top": "1em", 
                    "width": "22em",
                    "zIndex": 100
                },
                children=[
                    # Level 1 dropdown
                    dmc.MultiSelect(
                        id="3d-lipizones-select-level-1",
                        data=level_1_options,
                        placeholder="Select Level 1",
                        style={"width": "20em"},
                    ),
                    # Level 2 dropdown
                    dmc.MultiSelect(
                        id="3d-lipizones-select-level-2",
                        data=[],  # will be updated by callback
                        placeholder="Select Level 2",
                        style={"width": "20em", "marginTop": "0.5em"},
                    ),
                    # Level 3 dropdown
                    dmc.MultiSelect(
                        id="3d-lipizones-select-level-3",
                        data=[],
                        placeholder="Select Level 3",
                        style={"width": "20em", "marginTop": "0.5em"},
                    ),
                    # Level 4 dropdown
                    dmc.MultiSelect(
                        id="3d-lipizones-select-level-4",
                        data=[],
                        placeholder="Select Level 4",
                        style={"width": "20em", "marginTop": "0.5em"},
                    ),
                    # Subclass Select
                    dmc.MultiSelect(
                        id="3d-lipizones-select-subclass",
                        data=[],
                        placeholder="Select Subclass",
                        style={"width": "20em", "marginTop": "0.5em"},
                    ),
                    # Final MultiSelect for the lipizone_names
                    dmc.MultiSelect(
                        id="3d-lipizones-dropdown-lipizones",
                        data=[],  # updated by callback
                        placeholder="Select Lipizone(s)",
                        searchable=True,
                        clearable=False,   # note: as in lipizones_selection.py
                        nothingFound="No lipizone found",
                        style={"width": "20em", "marginTop": "0.5em"},
                        value=[],          # starts empty
                        maxSelectedValues=100,  ########################
                    ),
                    # Selected lipizones list display
                    html.Div(
                        id="3d-lipizones-selected-list",
                        style={"width": "20em", "marginTop": "1em", "color": "white"}
                    )
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
    Output("3d-lipizones-select-level-2", "data"),
    Input("3d-lipizones-select-level-1", "value"),
)
def update_level2(level1_vals):
    if level1_vals:
        subset = df_hierarchy[df_hierarchy["level_1"].astype(str).isin(level1_vals)]
    else:
        subset = df_hierarchy
    opts = sorted(subset["level_2"].unique())
    return [{"value": str(x), "label": str(x)} for x in opts]

@app.callback(
    Output("3d-lipizones-select-level-3", "data"),
    [Input("3d-lipizones-select-level-1", "value"),
     Input("3d-lipizones-select-level-2", "value")],
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
    Output("3d-lipizones-select-level-4", "data"),
    [Input("3d-lipizones-select-level-1", "value"),
     Input("3d-lipizones-select-level-2", "value"),
     Input("3d-lipizones-select-level-3", "value")],
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
    Output("3d-lipizones-select-subclass", "data"),
    [Input("3d-lipizones-select-level-1", "value"),
     Input("3d-lipizones-select-level-2", "value"),
     Input("3d-lipizones-select-level-3", "value"),
     Input("3d-lipizones-select-level-4", "value")],
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
    Output("3d-lipizones-dropdown-lipizones", "data"),
    [Input("3d-lipizones-select-level-1", "value"),
     Input("3d-lipizones-select-level-2", "value"),
     Input("3d-lipizones-select-level-3", "value"),
     Input("3d-lipizones-select-level-4", "value"),
     Input("3d-lipizones-select-subclass", "value")],
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

def clean_filenamePD(name):
    # Replace / and other problematic characters with an underscore
    logging.info(f"Cleaning filename: {name}")
    return re.sub(r'[^\w\s-]', '_', name)

def get_memory_usage():
    """Get current memory usage in MB"""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        return "psutil not available"

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
    logging.info("Creating background brain visualization")
    
    try:
        # Get atlas data from figures module
        brain_root_data = figures.compute_3D_root_volume(
            decrease_dimensionality_factor=downsample_factor
        )
        logging.info("Successfully created background brain")
        return brain_root_data
    except Exception as e:
        logging.error(f"Error creating background brain: {str(e)}")
        logging.error(traceback.format_exc())
        return None

def create_lipizone_3d_figure(array, color, downsample_factor=12):
    """
    Create a 3D visualization of a lipizone array
    
    Parameters:
    -----------
    array : numpy.ndarray
        3D array with the lipizone data
    color : str
        HTML color code for the lipizone
    downsample_factor : int
        Factor by which to downsample the array to reduce memory usage
        
    Returns:
    --------
    go.Volume
        The 3D volume for the lipizone
    """
    try:
        start_time = time.time()
        # Log original array shape and memory usage
        original_shape = array.shape
        mem = get_memory_usage()
        logging.info(f"Original array shape: {original_shape}, Current memory usage: {mem} MB")
        
        # Downsample the array to make visualization more manageable
        if downsample_factor > 1:
            array = array[::downsample_factor, ::downsample_factor, ::downsample_factor]
            logging.info(f"Downsampled array to shape: {array.shape}")
        
        # Create coordinate grid based on array shape
        logging.info("Creating coordinate grid")
        z, y, x = np.indices(array.shape)
        
        # Replace NaN values with 0 for visualization
        logging.info("Processing array values")
        array_viz = np.copy(array)
        array_viz = np.nan_to_num(array_viz)
        
        # Check for non-zero values to confirm data is present
        non_zero_count = np.count_nonzero(array_viz)
        logging.info(f"Array has {non_zero_count} non-zero values")
        if non_zero_count == 0:
            logging.warning("Array contains only zeros or NaNs!")
        
        # Create the 3D volume
        logging.info(f"Creating 3D volume with color: {color}")
        lipizone_data = go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=array_viz.flatten(),
            isomin=0.01,  # Only show values above this threshold
            isomax=1.0,
            opacity=0.7,  # Increase opacity for better visibility
            surface_count=10,  # Reduce surface count for performance
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, color]],
            caps=dict(x_show=False, y_show=False, z_show=False),
        )
        
        # Clean up to free memory
        del array_viz, x, y, z
        gc.collect()
        
        end_time = time.time()
        logging.info(f"3D figure creation completed in {end_time - start_time:.2f} seconds")
        
        return lipizone_data
        
    except Exception as e:
        logging.error(f"Error creating 3D figure: {str(e)}")
        logging.error(traceback.format_exc())
        raise e

@app.callback(
    Output("3d-lipizones-selected-list", "children"),
    Input("3d-lipizones-dropdown-lipizones", "value"),
)
def update_selected_lipizones_list(selected_lipizones):
    if not selected_lipizones or len(selected_lipizones) == 0:
        return "No lipizones selected"
    
    lipizones_list = [html.Div(f"Selected lipizones:", style={"fontWeight": "bold"})]
    
    for i, lipizone in enumerate(selected_lipizones):
        try:
            # Get color for the lipizone
            lipizone_colors = pd.read_csv("lipizonename2color.csv")
            if lipizone in lipizone_colors['lipizone_names'].values:
                color = lipizone_colors[lipizone_colors['lipizone_names'] == lipizone]['lipizone_color'].iloc[0]
            else:
                color = "#1f77b4"  # default blue
                
            lipizones_list.append(
                html.Div([
                    html.Span("■ ", style={"color": color}),
                    html.Span(lipizone)
                ])
            )
        except Exception as e:
            logging.error(f"Error displaying lipizone {lipizone}: {str(e)}")
            lipizones_list.append(html.Div(lipizone))
    
    return lipizones_list

@app.callback(
    Output("3d-lipizones-visualization-container", "children"),
    Input("3d-lipizones-dropdown-lipizones", "value"),
    prevent_initial_call=True,
)
def update_3d_visualization(selected_lipizones):
    start_time = time.time()
    logging.info(f"Callback triggered with selected lipizones: {selected_lipizones}")
    
    try:
        if not selected_lipizones or len(selected_lipizones) == 0:
            return html.Div(
                "Select lipizones to view their 3D distribution. Consider that this might take seconds to minutes to load.", 
                style={
                    "color": "white", 
                    "textAlign": "center", 
                    "marginTop": "20%"
                }
            )
        
        # Fixed downsample factor to 2
        downsample_factor = 4
        logging.info(f"Using fixed downsample factor: {downsample_factor}")
        
        # Get background brain visualization
        background_brain = get_background_brain(downsample_factor)
        
        # Process each selected lipizone
        data_list = []
        if background_brain is not None:
            data_list.append(background_brain)
        
        for lipizone_name in selected_lipizones:
            # Get the lipizone name and clean it
            safe_name = clean_filenamePD(lipizone_name)
            # Use the downsample factor that matches your precomputed arrays (e.g., 4)
            array = load_lipizone_array(safe_name, 1) #######################################
            if array is None:
                logging.warning(f"No valid data loaded for {lipizone_name} (safe name: {safe_name}).")
                continue
            
            # Get the color for this lipizone from the CSV
            try:
                lipizone_colors = pd.read_csv("lipizonename2color.csv")
                
                # Check if the lipizone name exists in the dataframe
                if lipizone_name not in lipizone_colors['lipizone_names'].values:
                    color = "#1f77b4"  # default blue
                else:
                    color = lipizone_colors[lipizone_colors['lipizone_names'] == lipizone_name]['lipizone_color'].iloc[0]
                    
            except Exception as e:
                logging.error(f"Error getting lipizone color: {str(e)}")
                color = "#1f77b4"  # default blue
            
            # Create the 3D visualization
            try:
                lipizone_volume = create_lipizone_3d_figure(array, color, downsample_factor)
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