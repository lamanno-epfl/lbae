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
from app import app, figures, data, storage, cache_flask

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

# New constant for the Zarr store location
LIPIZONES_ZARR_PATH = "./data/lipizone_data/3d_lipizones_all.zarr"

# New constant for the color array file
COLOR_ARRAY_PATH = "./data/lipizone_data/color_array_fullres.npy"

# @lru_cache(maxsize=50)
# def load_lipizone_array(
#     safe_name, 
#     downsample_factor
#     ):
#     """
#     Load the lipizone array from the Zarr store using the given downsample factor.
#     This function is cached to avoid re-loading data that was recently requested.
#     """
#     try:
#         store = zarr.DirectoryStore(LIPIZONES_ZARR_PATH)
#         root = zarr.group(store=store)
#         if safe_name not in root:
#             logging.warning(f"No data found for {safe_name} in the Zarr store.")
#             return None
#         group = root[safe_name]
#         key = f"downsampled_{downsample_factor}"
#         if key in group:
#             # This array is loaded lazily; slicing will read only needed chunks.
#             return group[key][:]
#         elif "full" in group:
#             # If the precomputed downsampled version isn't available, fall back to downsampling on the fly.
#             arr = group["full"][:]
#             return arr[::downsample_factor, ::downsample_factor, ::downsample_factor]
#         else:
#             logging.warning(f"Neither full nor downsampled array found for {safe_name}.")
#             return None
#     except Exception as e:
#         logging.error(f"Error loading lipizone {safe_name}: {str(e)}")
#         return None

# Load hierarchy data
df_hierarchy_lipizones = pd.read_csv("./data/lipizone_data/lipizones_hierarchy.csv")
lipizone_to_color = pickle.load(open("./data/lipizone_data/lipizone_to_color.pkl", "rb"))

# ==================================================================================================
# --- Helper functions
# ==================================================================================================

def hex_to_rgb(hex_color):
    """Convert hexadecimal color to RGB values."""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

def rgb_to_hex(rgb):
    """Convert RGB values to hexadecimal color."""
    return f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'

def is_light_color(hex_color):
    """Determine if a color is light or dark based on its RGB values."""
    # Convert hex to RGB
    rgb = hex_to_rgb(hex_color)
    # Calculate luminance using the formula: L = 0.299*R + 0.587*G + 0.114*B
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return luminance > 0.5

def calculate_mean_color(hex_colors):
    """Calculate the mean color from a list of hex colors."""
    if not hex_colors:
        return '#808080'  # Default gray if no colors
    
    # Convert hex to RGB
    rgb_colors = [hex_to_rgb(color) for color in hex_colors]
    
    # Calculate mean for each channel
    mean_r = sum(color[0] for color in rgb_colors) / len(rgb_colors)
    mean_g = sum(color[1] for color in rgb_colors) / len(rgb_colors)
    mean_b = sum(color[2] for color in rgb_colors) / len(rgb_colors)
    
    return rgb_to_hex([mean_r, mean_g, mean_b])

def create_treemap_data(df_hierarchy):
    """Create data structure for treemap visualization with color information."""
    # Create a copy to avoid modifying the original
    df = df_hierarchy.copy()
    
    # Add a constant value column for equal-sized end nodes
    df['value'] = 1
    
    # Create a dictionary to store colors for each node
    node_colors = {}
    
    # First, assign colors to leaf nodes (lipizones)
    for _, row in df.iterrows():
        lipizone = row['lipizone_names']
        if lipizone in lipizone_to_color:
            path = '/'.join([str(row[col]) for col in ['level_1_name', 'level_2_name', 'level_3_name', 'level_4_name', 'subclass_name', 'lipizone_names']])
            node_colors[path] = lipizone_to_color[lipizone]
    
    # Function to get all leaf colors under a node
    def get_leaf_colors(path_prefix):
        colors = []
        for full_path, color in node_colors.items():
            if full_path.startswith(path_prefix):
                colors.append(color)
        return colors
    
    # Calculate colors for each level, from bottom to top
    columns = ['level_1_name', 'level_2_name', 'level_3_name', 'level_4_name', 'subclass_name', 'lipizone_names']
    for i in range(len(columns)-1):  # Don't process the last level (lipizones)
        level_paths = set()
        # Build paths up to current level
        for _, row in df.iterrows():
            path = '/'.join([str(row[col]) for col in columns[:i+1]])
            level_paths.add(path)
        
        # Calculate mean colors for each path
        for path in level_paths:
            leaf_colors = get_leaf_colors(path + '/')
            if leaf_colors:
                node_colors[path] = calculate_mean_color(leaf_colors)
    
    return df, node_colors

def create_treemap_figure(df_treemap, node_colors):
    """Create treemap figure using plotly with custom colors."""
    fig = px.treemap(
        df_treemap,
        path=[
            'level_1_name',
            'level_2_name',
            'level_3_name',
            'level_4_name',
            'subclass_name',
            'lipizone_names'
        ],
        values='value'
    )
    
    # Update traces with custom colors
    def get_node_color(node_path):
        # Convert node path to string format matching our dictionary
        path_str = '/'.join(str(x) for x in node_path if x)
        return node_colors.get(path_str, '#808080')
    
    # Apply colors to each node based on its path
    colors = [get_node_color(node_path.split('/')) for node_path in fig.data[0].ids]
    
    fig.update_traces(
        marker=dict(colors=colors),
        hovertemplate='%{label}<extra></extra>',  # Only show the label
        textposition='middle center',
        root_color="rgba(0,0,0,0)",  # Make root node transparent
    )
    
    # Update layout for better visibility
    fig.update_layout(
        margin=dict(t=0, l=0, r=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
    )
    
    return fig

def clean_filenamePD(name):
    # Replace / and other problematic characters with an underscore
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
        # Downsample the array to make visualization more manageable
        if downsample_factor > 1:
            array = array[::downsample_factor, ::downsample_factor, ::downsample_factor]
        
        # Create coordinate grid based on array shape
        z, y, x = np.indices(array.shape)
        
        # Replace NaN values with 0 for visualization
        array_viz = np.copy(array)
        array_viz = np.nan_to_num(array_viz)
        
        # Create the 3D volume
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
            showscale=False,  # Added this line to hide the colorbar
        )
        
        # Clean up to free memory
        del array_viz, x, y, z
        gc.collect()
        
        return lipizone_data
        
    except Exception as e:
        logging.error(f"Error creating 3D figure: {str(e)}")
        logging.error(traceback.format_exc())
        raise e

def create_all_lipizones_figure(downsample_factor=1):
    """
    Create a 3D visualization of all lipizones together using the color array
    
    Parameters:
    -----------
    downsample_factor : int
        Factor by which to downsample the array to reduce memory usage
        
    Returns:
    --------
    go.Figure
        The 3D figure with the volume rendering
    """
    try:
        start_time = time.time()
        # logging.info("Loading all lipizones color array")
        
        # Load the color array
        color_array = np.load(COLOR_ARRAY_PATH)
        
        # Downsample the array
        if downsample_factor > 1:
            color_array = color_array[::downsample_factor, ::downsample_factor, ::downsample_factor, :]
            # logging.info(f"Downsampled color array to shape: {color_array.shape}")
        
        # Create coordinate grid based on array shape
        z, y, x = np.indices(color_array.shape[:3])
        
        # Create a mask for voxels with non-zero values
        # Convert RGB to a single intensity value based on average brightness
        intensity = np.mean(color_array, axis=-1)
        mask = intensity > 0
        
        if not np.any(mask):
            logging.warning("No non-zero values found in the color array!")
            return go.Figure().update_layout(
                title="No data found in color array",
                template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
        
        # Normalize RGB values to 0-1 range if they're not already
        if color_array.max() > 1:
            color_array = color_array / 255.0
        
        # Get the coordinates and colors of non-zero voxels
        x_points = x[mask]
        y_points = y[mask]
        z_points = z[mask]
        colors = color_array[mask]
        
        
        # Create a figure with a scatter3d trace using the actual RGB colors
        fig = go.Figure()
        
        # Add a scatter3d trace for the point cloud with RGB colors
        color_strings = [f'rgb({r*255},{g*255},{b*255})' for r, g, b in colors]
        # Reduce points if there are too many (for performance)

        max_points = 400000 # Limit the number of points for performance
        if len(x_points) > max_points:
            indices = np.random.choice(len(x_points), max_points, replace=False)
            x_points = x_points[indices]
            y_points = y_points[indices]
            z_points = z_points[indices]
            color_strings = [color_strings[i] for i in indices]
        
        # Add the scatter3d trace
        fig.add_trace(go.Scatter3d(
            x=x_points, 
            y=y_points, 
            z=z_points,
            mode='markers',
            marker=dict(
                size=downsample_factor,  # Increased size from 2 to 10 (5x larger)
                color=color_strings,
                opacity=1.0
            ),
            hoverinfo='none'
        ))
        
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
        
        # Clean up to free memory
        del color_array, x, y, z, x_points, y_points, z_points, colors, color_strings
        gc.collect()
        
        end_time = time.time()
        logging.info(f"All lipizones figure creation completed in {end_time - start_time:.2f} seconds")
        
        return fig
        
    except Exception as e:
        logging.error(f"Error creating all lipizones figure: {str(e)}")
        logging.error(traceback.format_exc())
        raise e

# ==================================================================================================
# --- Layout
# ==================================================================================================

def return_layout(basic_config, slice_index):
    # Create treemap data
    df_treemap, node_colors = create_treemap_data(df_hierarchy_lipizones)
    
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
                        figure=create_treemap_figure(df_treemap, node_colors),
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
    filtered = df_hierarchy_lipizones.copy()
    
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
                lipizone_indices = df_hierarchy_lipizones.index[
                    df_hierarchy_lipizones["lipizone_names"] == lipizone_name
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
            lipizone_color = lipizone_to_color.get(name, "#00FFFF")
            
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
                fig = create_all_lipizones_figure(downsample_factor=1)
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
        
        store = zarr.DirectoryStore(LIPIZONES_ZARR_PATH)
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
            color = lipizone_to_color.get(lipizone_name, "#1f77b4")  # default blue
            
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