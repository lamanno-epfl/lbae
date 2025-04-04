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
from tqdm import tqdm
from scipy.ndimage import gaussian_filter
# threadpoolctl import threadpool_limits, threadpool_info
#threadpool_limits(limits=8)
import os
os.environ['OMP_NUM_THREADS'] = '6'
import pickle

# LBAE imports
from app import app, figures, data, atlas, lipizone_sample_data, lipizone_section_data, celltype_data
import plotly.express as px

# ==================================================================================================
# --- Helper functions
# ==================================================================================================
# PROBLEM: LESS THAN HALF BRAIN IS SHOWED WHEN CHANGING THE BRAIN SLICE OR TOGGLING ANNOTATION
# fix the celltype treemap to be computed dinamically based on the slice and the celltypes available there 
# (filtering every time the df_hierarchy based on the slice index)... something like that
def compute_hybrid_image(hex_colors_to_highlight):
    def hex_to_rgb(hex_color):
        """Convert hexadecimal color to RGB values (0-1 range)"""
        hex_color = hex_color.lstrip('#')
        return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)]) / 255.0
    
    try:
        # Retrieve sample data from shelve database
        sample_data = lipizone_sample_data.retrieve_sample_data("ReferenceAtlas")
        color_masks = sample_data["color_masks"]
        grayscale_image = sample_data["grayscale_image"]
        rgb_image = sample_data["grid_image"][:, :, :3]  # remove transparency channel for now
    except KeyError:
        # Fallback to default files if sample not found
        logging.warning(f"Sample data for ReferenceAtlas not found, using default files")
        def load_color_masks_pickle(filename):
            import pickle
            with open(filename, 'rb') as f:
                color_masks = pickle.load(f)
            logging.info(f"Loaded {len(color_masks)} color masks from {filename}")
            return color_masks
        
        color_masks = load_color_masks_pickle('my_image_masks.pkl')
        grayscale_image = np.load("grayscale_image.npy")
        rgb_image = np.load("grid_image_lipizones.npy")[:, :, :3]
    
    # Apply Gaussian blur to smooth the grayscale image
    grayscale_image = gaussian_filter(grayscale_image, sigma=3)
    
    # Reduce contrast and overall intensity
    grayscale_image = np.power(grayscale_image, 2)  # Increase contrast difference
    grayscale_image = grayscale_image * 0.3  # Reduce overall intensity
    
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
            try:
                distances = np.array([np.sum((np.array(color) - target_rgb) ** 2) for color in color_masks.keys()])
                closest_color_idx = np.argmin(distances)
                closest_color = list(color_masks.keys())[closest_color_idx]
                if distances[closest_color_idx] < 0.05:
                    combined_mask |= color_masks[closest_color]
            except:
                print(f"{target_rgb} not found in color_masks_lipizones")
                continue
    
    for i in range(3):
        hybrid_image[:, :, i][combined_mask] = rgb_image[:, :, i][combined_mask]
    
    hybrid_image = (hybrid_image*255) + 1
    mask = np.all(hybrid_image == 1, axis=-1)
    hybrid_image[mask] = np.nan

    height, width, _ = hybrid_image.shape
    
    # Compute pad sizes
    pad_top = height // 2
    pad_bottom = height // 2
    pad_left = 0
    
    # Pad the image
    padded_image = np.pad(
        hybrid_image,
        pad_width=((pad_top, pad_bottom), (pad_left, 0), (0, 0)),
        mode='constant',
        constant_values=np.nan
    )

    return padded_image

def compute_image_lipizones_celltypes(
    all_selected_lipizones, 
    all_selected_celltypes, 
    slice_index,
    celltype_radius=1):  # New parameter for tunable square radius
    
    # Get the names of all selected lipizones and celltypes
    selected_lipizone_names = all_selected_lipizones.get("names", [])
    selected_celltype_names = all_selected_celltypes.get("names", [])
    
    # Define colors for both lipizones and celltypes
    hex_colors_to_highlight_lipizones = [lipizone_to_color[name] for name in selected_lipizone_names if name in lipizone_to_color]
    rgb_colors_to_highlight_celltypes = [celltype_to_color[name] for name in selected_celltype_names if name in celltype_to_color]
    
    # Get section data for both lipizones and celltypes
    section_data_lipizones = lipizone_section_data.retrieve_section_data(float(slice_index))
    section_data_celltypes = celltype_data.retrieve_section_data(int(slice_index))
    
    # Use the grayscale image from lipizones data (same for both)
    grayscale_image = section_data_lipizones["grayscale_image"]
    # grayscale_image = np.sqrt(np.sqrt(grayscale_image))
    grayscale_image = np.power(grayscale_image, float(1/6))
    
    # Apply Gaussian blur to smooth the grayscale image
    grayscale_image = gaussian_filter(grayscale_image, sigma=3)
    
    # Get color masks for both
    color_masks_lipizones = section_data_lipizones["color_masks"]
    color_masks_celltypes = section_data_celltypes["color_masks"]

    # mask the grayscale image with the color mask of the lipizones
    grayscale_image *= ~color_masks_lipizones[list(color_masks_lipizones.keys())[0]]

    # Grid image
    grid_image = section_data_lipizones["grid_image"]
    rgb_image = grid_image[:, :, :3]
    
    # Convert hex colors to RGB for lipizones
    def hex_to_rgb(hex_color):
        """Convert hexadecimal color to RGB values (0-1 range)"""
        hex_color = hex_color.lstrip('#')
        return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)]) / 255.0
    
    rgb_colors_to_highlight_lipizones = [hex_to_rgb(hex_color) for hex_color in hex_colors_to_highlight_lipizones]
    
    # Create the hybrid image with the same shape as the original
    lipizones_celltypes_image = np.zeros_like(rgb_image)
    
    # Split the image into left (lipizones) and right (celltypes) halves
    mid_point = lipizones_celltypes_image.shape[1] // 2
    
    # Process left side (lipizones)
    combined_mask_lipizones = np.zeros((rgb_image.shape[0], mid_point), dtype=bool)
    for target_rgb in tqdm(rgb_colors_to_highlight_lipizones):
        target_tuple = tuple(target_rgb)
        if target_tuple in color_masks_lipizones:
            combined_mask_lipizones |= color_masks_lipizones[target_tuple][:, :mid_point]
        else:
            try:
                distances = np.array([np.sum((np.array(color) - target_rgb) ** 2) for color in color_masks_lipizones.keys()])
                closest_color_idx = np.argmin(distances)
                closest_color = list(color_masks_lipizones.keys())[closest_color_idx]
                if distances[closest_color_idx] < 0.05:
                    combined_mask_lipizones |= color_masks_lipizones[closest_color][:, :mid_point]
            except:
                print(f"{target_rgb} not found in color_masks_lipizones")
                continue
    
    # Process right side (celltypes) with pixel enlargement
    # Initialize arrays for the right side
    celltype_colors = np.zeros((rgb_image.shape[0], lipizones_celltypes_image.shape[1] - mid_point, 3))
    celltype_mask = np.zeros((rgb_image.shape[0], lipizones_celltypes_image.shape[1] - mid_point), dtype=bool)
    
    # Process each celltype
    for target_rgb in tqdm(rgb_colors_to_highlight_celltypes):
        # Convert target_rgb to numpy array if it's a string
        target_rgb_float = np.array([float(x) for x in target_rgb.strip('()').split(',')])
        target_tuple = tuple(target_rgb_float)
        # find the corresponding name of the celltype from the celltype_to_color dictionary
        celltype_name = list(celltype_to_color.keys())[list(celltype_to_color.values()).index(target_rgb)]
        
        if celltype_name in color_masks_celltypes:
            current_mask = color_masks_celltypes[celltype_name].T[:, mid_point:]
            
            # For each center point, create a square around it
            y_coords, x_coords = np.where(current_mask)
            
            for y, x in zip(y_coords, x_coords):
                # # Get the original RGB color from the center point
                # center_color = rgb_image[y, x + mid_point]
                # Use the celltype's RGB color directly from celltype_to_color
                center_color = target_rgb_float[:3]
                
                # Define the square bounds
                y_min = max(0, y - celltype_radius)
                y_max = min(current_mask.shape[0], y + celltype_radius + 1)
                x_min = max(0, x - celltype_radius)
                x_max = min(current_mask.shape[1], x + celltype_radius + 1)
                
                # Only fill pixels that haven't been filled yet
                square_mask = np.zeros_like(celltype_mask)
                square_mask[y_min:y_max, x_min:x_max] = True
                unfilled_pixels = square_mask & ~celltype_mask
                
                if np.any(unfilled_pixels):
                    # Use broadcasting to assign the center color to all unfilled pixels in the square
                    for i in range(3):
                        celltype_colors[..., i][unfilled_pixels] = center_color[i]
                    celltype_mask[unfilled_pixels] = True
        
        # else:
        #     # Convert color mask keys to numpy arrays for comparison
        #     try:
        #         mask_rgb_str = [celltype_to_color[celltype_name] for celltype_name in color_masks_celltypes.keys()]
        #         color_keys = [np.array([float(x) for x in color.strip('()').split(',')]) 
        #         for color in mask_rgb_str]

        #         distances = np.array([np.sum((color - target_tuple) ** 2) for color in color_keys])
        #         closest_color_idx = np.argmin(distances)
        #         closest_color = list(color_masks_celltypes.keys())[closest_color_idx]
        #         if distances[closest_color_idx] < 0.05:
        #             current_mask = color_masks_celltypes[closest_color].T
        #             combined_mask_celltypes |= current_mask[:, mid_point:]
        #     except:
        #         print(f"{celltype_name} not found in color_masks_celltypes")
        #         continue
    
    # Apply grayscale background to both sides
    for i in range(3):
        lipizones_celltypes_image[:, :mid_point, i] = grayscale_image[:, :mid_point]
        lipizones_celltypes_image[:, mid_point:, i] = grayscale_image[:, mid_point:]
    
    # Apply color masks to respective sides
    for i in range(3):
        # Left side (lipizones)
        lipizones_celltypes_image[:, :mid_point, i][combined_mask_lipizones] = rgb_image[:, :mid_point, i][combined_mask_lipizones]
        # Right side (celltypes)
        lipizones_celltypes_image[:, mid_point:, i][celltype_mask] = celltype_colors[..., i][celltype_mask]
    
    # Final processing
    lipizones_celltypes_image = (lipizones_celltypes_image*255) + 1
    mask = np.all(lipizones_celltypes_image == 1, axis=-1)
    lipizones_celltypes_image[mask] = np.nan

    return lipizones_celltypes_image

def black_aba_contours(overlay):
    black_overlay = overlay.copy()
    contour_mask = overlay[:, :, 3] > 0
    black_overlay[contour_mask] = [0, 0, 0, 200]  # RGB black with alpha=200
    
    return black_overlay

def hex_to_rgb(hex_color):
    """Convert hexadecimal color to RGB values."""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

def rgb_to_hex(rgb):
    """Convert RGB values to hexadecimal color."""
    return f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'

def calculate_mean_color(colors, is_celltypes=False):
    """Calculate the mean color from a list of colors.
    
    Args:
        colors: List of colors (either hex strings or RGBA strings)
        is_celltypes: Boolean indicating if we're dealing with celltypes (RGBA format) or lipizones (hex format)
    """
    if not colors:
        return '#808080' if not is_celltypes else "(0.5, 0.5, 0.5, 1.0)"  # Default gray
    
    if is_celltypes:
        # For celltypes, colors are in RGBA string format
        rgb_colors = []
        for color in colors:
            if isinstance(color, str) and color.startswith('('):
                # Extract RGB values from string format "(r,g,b,a)"
                rgb_values = [float(x) for x in color.strip('()').split(',')[:3]]
                rgb_colors.append(rgb_values)
            else:
                # If somehow not in string format, convert from hex
                rgb_colors.append(hex_to_rgb(color))
    else:
        # For lipizones, colors are in hex format
        rgb_colors = [hex_to_rgb(color) for color in colors]
    
    # Calculate mean for each channel
    mean_r = sum(color[0] for color in rgb_colors) / len(rgb_colors)
    mean_g = sum(color[1] for color in rgb_colors) / len(rgb_colors)
    mean_b = sum(color[2] for color in rgb_colors) / len(rgb_colors)
    if is_celltypes:
        return rgb_to_hex([mean_r*255, mean_g*255, mean_b*255])
    else:
        return rgb_to_hex([mean_r, mean_g, mean_b])
    
def create_treemap_data(
    df_hierarchy, 
    is_celltypes=False,
    slice_index=1.0,):

    """Create data structure for treemap visualization with color information."""
    # Create a copy to avoid modifying the original
    if not is_celltypes:
        df = df_hierarchy.copy()
    else:
        # in the case of celltypes, extract only the celltypes that are available in the slice
        celltype_in_section = list(celltype_data.retrieve_section_data(int(slice_index))['color_masks'].keys())
        # Filter the DataFrame
        df = df_hierarchy_celltypes[df_hierarchy_celltypes["cell_type"].isin(celltype_in_section)]
    
    # Add a constant value column for equal-sized end nodes
    df['value'] = 1
    
    # Create a dictionary to store colors for each node
    node_colors = {}
    
    # First, assign colors to leaf nodes
    for _, row in df.iterrows():
        if is_celltypes:
            celltype = row['cell_type']
            if celltype in celltype_to_color:
                # Use only the first 10 levels for celltypes
                path = '/'.join([str(row[col]) for col in ['level_1', 'level_2', 'level_3', 'level_4', 'level_5', 
                                                          'level_6', 'level_7', 'level_8', 'level_9', 'level_10', 
                                                          'cell_type']])
                
                node_colors[path] = celltype_to_color[celltype]
        else:
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
    if is_celltypes:
        columns = ['level_1', 'level_2', 'level_3', 'level_4', 'level_5', 
                   'level_6', 'level_7', 'level_8', 'level_9', 'level_10', 
                   'cell_type']
    else:
        columns = ['level_1_name', 'level_2_name', 'level_3_name', 'level_4_name', 'subclass_name', 'lipizone_names']
    
    for i in range(len(columns)-1):  # Don't process the last level
        level_paths = set()
        # Build paths up to current level
        for _, row in df.iterrows():
            path = '/'.join([str(row[col]) for col in columns[:i+1]])
            level_paths.add(path)
        
        # Calculate mean colors for each path
        for path in level_paths:
            leaf_colors = get_leaf_colors(path + '/')
            if leaf_colors:
                node_colors[path] = calculate_mean_color(leaf_colors, is_celltypes)
    
    return df, node_colors

def create_treemap_figure(df_treemap, node_colors, is_celltypes=False):
    """Create treemap figure using plotly with custom colors."""
    if is_celltypes:
        path_columns = ['level_1', 'level_2', 'level_3', 'level_4', 'level_5', 
                        'level_6', 'level_7', 'level_8', 'level_9', 'level_10', 
                        'cell_type']
    else:
        path_columns = ['level_1_name', 'level_2_name', 'level_3_name', 'level_4_name', 'subclass_name', 'lipizone_names']
    
    fig = px.treemap(
        df_treemap,
        path=path_columns,
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

# ==================================================================================================
# --- Data
# ==================================================================================================

manual_naming_lipizones_level_1 = {
    '1' : 'White matter-rich',
    '2' : 'Gray matter-rich',
}
manual_naming_lipizones_level_2 = {
    '1_1' : 'Core white matter',
    '1_2' : 'Mixed gray and white matter, ventricles',
    '2_1' : 'Outer cortex, cerebellar molecular layer, amygdala, part of hippocampus',
    '2_2' : 'Deep cortex, part of hippocampus, striatum, cerebellar granule cells',
}
manual_naming_lipizones_level_3 = {
    '1_1_1' : 'Oligodendroglia-rich regions',
    '1_1_2' : 'Mixed white matter with neurons',
    '1_2_1' : 'Ventricular system, gray-white boundary, hypothalamus',
    '1_2_2' : 'Thalamus and midbrain',
    '2_1_1' : 'Layer 2/3 and 4, cingulate, striatum, hippocampus, subcortical plate regions',
    '2_1_2' : 'Layer 1 to border between 2/3 and 4, piriform, Purkinje cells, enthorinal, mixed',
    '2_2_1' : 'Layer 5, hippocampus and noncortical gray matter',
    '2_2_2' : 'Layers 5 and 6, hippocampus, nuclei, granular layer of the cerebellum',
}
manual_naming_lipizones_level_4 = {
    '1_1_1_1' : 'Core of fiber tracts, arbor vitae and nerves/1',
    '1_1_1_2' : 'Core of fiber tracts, arbor vitae and nerves/2',
    '1_1_2_1' : 'Bundle and boundary white matter-rich',
    '1_1_2_2' : 'Thalamus, midbrain, hindbrain white matter regions',
    '1_2_1_1' : 'Ventricular system',
    '1_2_1_2' : 'Gray-white matter boundary',
    '1_2_2_1' : 'Mostly thalamus, midbrain, hindbrain mixed types',
    '1_2_2_2' : 'Myelin-rich deep cortex, striatum, hindbrain and more',
    '2_1_1_1' : 'Layer 2/3 and 4, cingulate, striatum, hippocampus, subcortical plate regions',
    '2_1_1_2' : 'HPF, AMY, CTXSP, HY and more',
    '2_1_2_1' : 'Purkinje layer, L2/3 and boundary with L4',
    '2_1_2_2' : 'Layer 1, 2/3, piriform and enthorinal cortex, CA1',
    '2_2_1_1' : 'Layer 5, retrosplenial, hippocampus',
    '2_2_1_2' : 'Noncortical gray matter',
    '2_2_2_1' : 'Layer 5-6, nuclei, granule cells layer',
    '2_2_2_2' : 'Layer 6, mixed complex GM, granule cells layer',
}

lipizones = pd.read_csv("/data/LBA_DATA/lbae/lipizonename2color.csv", index_col=0) # HEX
lipizone_to_color = {name: color for name, color in zip(lipizones["lipizone_names"], lipizones["lipizone_color"])}
df_hierarchy_lipizones = pd.read_csv("/data/LBA_DATA/lbae/data/annotations/lipizones_hierarchy.csv")

# lipizonenames = pd.read_csv("/data/LBA_DATA/lbae/lipizonename2color.csv", index_col=0)['lipizone_names'].values
df_hierarchy_lipizones['level_1_name'] = df_hierarchy_lipizones['level_1'].astype(str).map(manual_naming_lipizones_level_1)
df_hierarchy_lipizones['level_2_name'] = df_hierarchy_lipizones['level_2'].astype(str).map(manual_naming_lipizones_level_2)
df_hierarchy_lipizones['level_3_name'] = df_hierarchy_lipizones['level_3'].astype(str).map(manual_naming_lipizones_level_3)
df_hierarchy_lipizones['level_4_name'] = df_hierarchy_lipizones['level_4'].astype(str).map(manual_naming_lipizones_level_4)

celltypes = pd.read_csv('/data/LBA_DATA/lbae/assets/hierarchy_celltypes_colors.csv')[["cell_type", "color"]]
celltype_to_color = {name: color for name, color in zip(celltypes["cell_type"], celltypes["color"])}
df_hierarchy_celltypes = pd.read_csv('/data/LBA_DATA/lbae/assets/hierarchy_celltypes_colors.csv')
# Keep hierarchy_code and reorder columns
df_hierarchy_celltypes = df_hierarchy_celltypes.iloc[:, 1:]

union_celltypes = set()
for slice_index in data.get_slice_list("ReferenceAtlas"):
    try:
        celltype_in_section = list(celltype_data.retrieve_section_data(int(slice_index))['color_masks'].keys())
        filtered_df = df_hierarchy_celltypes[df_hierarchy_celltypes["cell_type"].isin(celltype_in_section)]
        union_celltypes.update(filtered_df["cell_type"].values)
    except:
        continue

# filter the  df_hierarchy_celltypes to only keep the celltypes in union_celltypes
df_hierarchy_celltypes = df_hierarchy_celltypes[df_hierarchy_celltypes["cell_type"].isin(union_celltypes)]
df_hierarchy_celltypes = df_hierarchy_celltypes.drop(columns=['level_11', 'level_12', 'level_13', 'level_14', 'level_15', 
                                                                'level_16', 'level_17', 'level_18', 'level_19', 'level_20', 
                                                                'level_21', 'level_22', 'level_23', 'level_24', 'level_25', 
                                                                'level_26'])

# ==================================================================================================
# --- Layout
# ==================================================================================================

def return_layout(basic_config, slice_index):
    """Return the layout for the page."""
    # Create treemap data
    df_treemap_lipizones, node_colors_lipizones = create_treemap_data(df_hierarchy_lipizones)
    df_treemap_celltypes, node_colors_celltypes = create_treemap_data(
        df_hierarchy_celltypes, 
        is_celltypes=True, 
        slice_index=slice_index)

    # Get celltype pixel counts for the current slice
    section_data_celltypes = celltype_data.retrieve_section_data(int(slice_index))
    color_masks_celltypes = section_data_celltypes["color_masks"]
    celltype_pixel_counts = {
        celltype: np.sum(mask) 
        for celltype, mask in color_masks_celltypes.items()
    }
    max_pixels = max(celltype_pixel_counts.values()) if celltype_pixel_counts else 1

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
                        id="page-6bis-graph-heatmap-mz-selection",
                        config=basic_config | {
                            "toImageButtonOptions": {
                                "format": "png",
                                "filename": "brain_lipizone_selection",
                                "scale": 2,
                            },
                            "scrollZoom": True
                        },
                        style={
                            "width": "60%",  # Reduced from 80% to give more balanced space
                            "height": "95%",
                            "position": "absolute",
                            "left": "20%",  # Center it between the two side panels
                            "top": "0",
                            "background-color": "#1d1c1f",
                        },
                        figure=figures.build_lipid_heatmap_from_image(
                            compute_hybrid_image(['#f75400']),
                            return_base64_string=False,
                            draw=False,
                            type_image="RGB",
                            return_go_image=False,
                        )
                    ),
                    # Allen Brain Atlas switch (independent)
                    html.Div(
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
                                id="page-6bis-toggle-annotations",
                                checked=False,
                                color="cyan",
                                radius="xl",
                                size="sm",
                            ),
                            html.Span(
                                "Allen Brain Atlas Annotations",
                                style={
                                    "color": "white",
                                    "marginLeft": "10px",  # Changed from marginRight to marginLeft
                                    "whiteSpace": "nowrap",
                                },
                            ),
                        ],
                    ),
                    # Hover text
                    dmc.Text(
                        "",
                        id="page-6bis-graph-hover-text",
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
                    # Left panel with lipizones treemap and controls
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
                                id="page-6bis-select-all-lipizones-button",
                                variant="filled",
                                color="cyan",
                                radius="md",
                                size="sm",
                                style={
                                    "marginBottom": "5px",
                                },
                            ),
                            # Lipizones treemap visualization
                            dcc.Graph(
                                id="page-6bis-lipizones-treemap",
                                figure=create_treemap_figure(
                                    df_treemap_lipizones, 
                                    node_colors_lipizones
                                    ),
                                style={
                                    "height": "40%",
                                    "background-color": "#1d1c1f",
                                },
                                config={'displayModeBar': False}
                            ),
                            # Current selection text
                            html.Div(
                                id="page-6bis-current-lipizone-selection-text",
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
                                        id="page-6bis-add-lipizone-selection-button",
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
                                        id="page-6bis-clear-lipizone-selection-button",
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
                                id="selected-lipizones-badges",
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
                    # Right panel with celltypes treemap and controls
                    html.Div(
                        style={
                            "width": "20%",
                            "height": "95%",
                            "position": "absolute",
                            "right": "0",
                            "top": "0",
                            "background-color": "#1d1c1f",
                            "display": "flex",
                            "flexDirection": "column",
                            "padding": "10px",
                        },
                        children=[
                            # Title
                            html.H4(
                                "Visualize Cell Types",
                                style={
                                    "color": "white",
                                    "marginBottom": "15px",
                                    "fontSize": "1.2em",
                                    "fontWeight": "500",
                                    "textAlign": "right"  # Add right alignment
                                }
                            ),
                            # Select All button
                            dmc.Button(
                                children="Select All Cell Types",
                                id="page-6bis-select-all-celltypes-button",
                                variant="filled",
                                color="cyan",
                                radius="md",
                                size="sm",
                                style={
                                    "marginBottom": "5px",
                                },
                            ),
                            # Celltypes treemap visualization
                            dcc.Graph(
                                id="page-6bis-celltypes-treemap",
                                figure=create_treemap_figure(
                                    df_treemap_celltypes, 
                                    node_colors_celltypes,
                                    is_celltypes=True
                                    ),
                                style={
                                    "height": "40%",
                                    "background-color": "#1d1c1f",
                                },
                                config={'displayModeBar': False}
                            ),
                            # Current selection text
                            html.Div(
                                id="page-6bis-current-celltype-selection-text",
                                style={
                                    "padding": "10px",
                                    "color": "white",
                                    "fontSize": "0.9em",
                                    "backgroundColor": "#2c2c2c",
                                    "borderRadius": "5px",
                                    "marginTop": "10px",
                                },
                                children=["Click on a node in the tree to select all cell types under it"]
                            ),
                            # Add pixel count filter slider
                            html.Div([
                                html.Label(
                                    "Filter by minimum pixel count:",
                                    style={
                                        "color": "white",
                                        "marginTop": "10px",  # Reduced from 20px
                                        "marginBottom": "5px",  # Reduced from 10px
                                    }
                                ),
                                dcc.Slider(
                                    id="page-6bis-celltype-pixel-filter",
                                    min=0,
                                    max=max_pixels,
                                    step=int(max_pixels/100),  # 100 steps
                                    value=0,
                                    marks={
                                        '0': {'label': '0', 'style': {'color': 'white'}},
                                        str(max_pixels): {'label': str(max_pixels), 'style': {'color': 'white'}}
                                    },
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    className="slider-white"
                                ),
                            ], style={"padding": "5px"}),  # Reduced from 10px
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
                                        id="page-6bis-add-celltype-selection-button",
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
                                        id="page-6bis-clear-celltype-selection-button",
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
                            # Selected celltypes badges
                            html.Div(
                                id="selected-celltypes-badges",
                                style={
                                    "height": "30%",
                                    "overflowY": "auto",
                                    "padding": "10px",
                                    "marginTop": "10px",
                                    "backgroundColor": "#2c2c2c",
                                    "borderRadius": "5px",
                                },
                                children=[
                                    html.H6("Selected Cell Types", style={"color": "white", "marginBottom": "10px"}),
                                ]
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
                            "flexDirection": "row",  # Changed from column to row
                            "gap": "0.5rem",
                        },
                        children=[
                            dmc.Button(
                                children="Download data",
                                id="page-6bis-download-data-button",
                                variant="filled",
                                disabled=False,
                                color="cyan",
                                radius="md",
                                size="sm",
                                style={"width": "150px"},
                            ),
                            dmc.Button(
                                children="Download image",
                                id="page-6bis-download-image-button",
                                variant="filled",
                                disabled=False,
                                color="cyan",
                                radius="md",
                                size="sm",
                                style={"width": "150px"},
                            ),
                        ],
                    ),
                    dcc.Download(id="page-6bis-download-data"),
                ],
            ),
        ],
    )
    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================

@app.callback(
    Output("page-6bis-celltypes-treemap", "figure"),
    Input("main-slider", "data"),
    prevent_initial_call=True
)
def update_celltype_treemap(slice_index):
    """Update the celltype treemap when the slice changes."""
    print("\n======== update_celltype_treemap =========")
    # Create new treemap data for celltypes with the current slice
    df_treemap_celltypes, node_colors_celltypes = create_treemap_data(
        df_hierarchy_celltypes, 
        is_celltypes=True,
        slice_index=slice_index
    )
    print("slice_index: ", slice_index)
    print("shape of df_treemap_celltypes: ", df_treemap_celltypes.shape)
    print("len of node_colors_celltypes: ", len(node_colors_celltypes))
    # Create and return the new figure
    return create_treemap_figure(
        df_treemap_celltypes, 
        node_colors_celltypes,
        is_celltypes=True
    )

@app.callback(
    Output("page-6bis-current-lipizone-treemap-selection", "data"),
    Output("page-6bis-current-lipizone-selection-text", "children"),
    Input("page-6bis-lipizones-treemap", "clickData"),
    prevent_initial_call=True
)
def update_current_lipizone_selection(click_data):
    """Store the current treemap selection for lipizones."""
    print("\n======== update_current_lipizone_selection =========")    
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    
    if not click_data:
        return None, "Click on a node in the tree to select all lipizones under it"
    
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
    
    return None, "Click on a node in the tree to select all lipizones under it"

@app.callback(
    Output("page-6bis-current-celltype-treemap-selection", "data"),
    Output("page-6bis-current-celltype-selection-text", "children"),
    Input("page-6bis-celltypes-treemap", "clickData"),
    Input("main-slider", "data"),
    prevent_initial_call=True
)
def update_current_celltype_selection(click_data, slice_index):
    """Store the current treemap selection for celltypes."""
    print("\n======== update_current_celltype_selection =========")
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    
    if not click_data:
        return None, "Click on a node in the tree to select all cell types under it"
    
    clicked_label = click_data["points"][0]["label"]
    current_path = click_data["points"][0]["id"]
    
    celltype_in_section = list(celltype_data.retrieve_section_data(int(slice_index))['color_masks'].keys())
    # Filter the DataFrame
    filtered = df_hierarchy_celltypes[df_hierarchy_celltypes["cell_type"].isin(celltype_in_section)]
    
    # Get the level of the clicked node
    path_columns = ['level_1', 'level_2', 'level_3', 'level_4', 'level_5', 
                    'level_6', 'level_7', 'level_8', 'level_9', 'level_10', 
                    'cell_type']
    
    # Apply filters based on the entire path up to the clicked node
    for i, value in enumerate(current_path.split("/")):
        if i < len(path_columns):
            column = path_columns[i]
            filtered = filtered[filtered[column].astype(str) == str(value)]
    
    # Get all cell types under this node that are present in the current slice
    celltypes = sorted(filtered["cell_type"].unique())
    
    if celltypes:
        return celltypes, f"Selected: {clicked_label} ({len(celltypes)} cell types)"
    
    return None, "Click on a node in the tree to select all cell types under it"

@app.callback(
    Output("page-6bis-all-selected-lipizones", "data"),
    Input("page-6bis-select-all-lipizones-button", "n_clicks"),
    Input("page-6bis-add-lipizone-selection-button", "n_clicks"),
    Input("page-6bis-clear-lipizone-selection-button", "n_clicks"),
    State("page-6bis-current-lipizone-treemap-selection", "data"),
    State("page-6bis-all-selected-lipizones", "data"),
    prevent_initial_call=True
)
def handle_lipizone_selection_changes(
    select_all_clicks, 
    add_clicks, 
    clear_clicks, 
    current_selection, 
    all_selected_lipizones):
    """Handle all lipizone selection changes."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    # Get which button was clicked
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Handle select all button
    if triggered_id == "page-6bis-select-all-lipizones-button":
        all_lipizones = {"names": [], "indices": []}
        for lipizone_name in df_hierarchy_lipizones["lipizone_names"].unique():
            lipizone_indices = lipizones.index[
                lipizones["lipizone_names"] == lipizone_name
            ].tolist()
            if lipizone_indices:
                all_lipizones["names"].append(lipizone_name)
                all_lipizones["indices"].extend(lipizone_indices[:1])
        return all_lipizones
    
    # Handle clear button
    elif triggered_id == "page-6bis-clear-lipizone-selection-button":
        return {"names": [], "indices": []}
    
    # Handle add button
    elif triggered_id == "page-6bis-add-lipizone-selection-button":
        if not current_selection:
            return all_selected_lipizones or {"names": [], "indices": []}
        
        # Initialize all_selected_lipizones if it's empty
        all_selected_lipizones = all_selected_lipizones or {"names": [], "indices": []}
        
        # Add each lipizone that isn't already selected
        for lipizone_name in current_selection:
            if lipizone_name not in all_selected_lipizones["names"]:
                # Find the indices for this lipizone
                lipizone_indices = lipizones.index[
                    lipizones["lipizone_names"] == lipizone_name
                ].tolist()
                
                if lipizone_indices:
                    all_selected_lipizones["names"].append(lipizone_name)
                    all_selected_lipizones["indices"].extend(lipizone_indices[:1])
        
        return all_selected_lipizones
    
    return dash.no_update

@app.callback(
    Output("page-6bis-all-selected-celltypes", "data"),
    Output("page-6bis-celltype-pixel-filter", "max"),
    Output("page-6bis-celltype-pixel-filter", "step"),
    Output("page-6bis-celltype-pixel-filter", "marks"),
    Output("page-6bis-celltype-pixel-filter", "value"),
    Input("page-6bis-select-all-celltypes-button", "n_clicks"),
    Input("page-6bis-add-celltype-selection-button", "n_clicks"),
    Input("page-6bis-clear-celltype-selection-button", "n_clicks"),
    Input("main-slider", "data"),
    Input("page-6bis-celltype-pixel-filter", "value"),
    State("page-6bis-current-celltype-treemap-selection", "data"),
    State("page-6bis-all-selected-celltypes", "data"),
    prevent_initial_call=True
)
def handle_celltype_selection_changes(
    select_all_clicks, 
    add_clicks, 
    clear_clicks, 
    slice_index,
    min_pixels,
    current_selection, 
    all_selected_celltypes):
    """Handle all celltype selection changes."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Get which input triggered the callback
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Get the available celltypes and their masks in the current slice
    section_data = celltype_data.retrieve_section_data(int(slice_index))
    color_masks = section_data["color_masks"]
    
    # Calculate pixel counts for each celltype
    celltype_pixel_counts = {
        celltype: np.sum(mask) 
        for celltype, mask in color_masks.items()
    }
    
    # Calculate max pixels for this slice
    max_pixels = max(celltype_pixel_counts.values()) if celltype_pixel_counts else 1
    step = max(1, int(max_pixels/100))  # 100 steps
    marks = {
        '0': {'label': '0', 'style': {'color': 'white'}},
        str(max_pixels): {'label': str(max_pixels), 'style': {'color': 'white'}}
    }
    
    # Filter celltypes based on pixel count
    available_celltypes = [
        celltype 
        for celltype, count in celltype_pixel_counts.items() 
        if count >= min_pixels
    ]
    
    # If slice changed, reset slider to 0 and show all celltypes
    if triggered_id == "main-slider":
        # Filter the DataFrame
        filtered_df = df_hierarchy_celltypes[df_hierarchy_celltypes["cell_type"].isin(available_celltypes)]
        
        # Create the all_celltypes dictionary with only celltypes from the current slice
        all_celltypes = {"names": [], "indices": []}
        for celltype_name in filtered_df["cell_type"].unique():
            celltype_indices = celltypes.index[
                celltypes["cell_type"] == celltype_name
            ].tolist()
            if celltype_indices:
                all_celltypes["names"].append(celltype_name)
                all_celltypes["indices"].extend(celltype_indices[:1])
        return all_celltypes, max_pixels, step, marks, 0
    
    # If slider value changed, filter current selection
    elif triggered_id == "page-6bis-celltype-pixel-filter":
        # Filter the DataFrame
        filtered_df = df_hierarchy_celltypes[df_hierarchy_celltypes["cell_type"].isin(available_celltypes)]
        
        # Create the all_celltypes dictionary with only celltypes that meet the pixel threshold
        all_celltypes = {"names": [], "indices": []}
        for celltype_name in filtered_df["cell_type"].unique():
            celltype_indices = celltypes.index[
                celltypes["cell_type"] == celltype_name
            ].tolist()
            if celltype_indices:
                all_celltypes["names"].append(celltype_name)
                all_celltypes["indices"].extend(celltype_indices[:1])
        return all_celltypes, max_pixels, step, marks, min_pixels
    
    # Handle select all button
    elif triggered_id == "page-6bis-select-all-celltypes-button":
        # Filter the DataFrame
        filtered_df = df_hierarchy_celltypes[df_hierarchy_celltypes["cell_type"].isin(available_celltypes)]
        
        # Create the all_celltypes dictionary with only celltypes that meet the pixel threshold
        all_celltypes = {"names": [], "indices": []}
        for celltype_name in filtered_df["cell_type"].unique():
            celltype_indices = celltypes.index[
                celltypes["cell_type"] == celltype_name
            ].tolist()
            if celltype_indices:
                all_celltypes["names"].append(celltype_name)
                all_celltypes["indices"].extend(celltype_indices[:1])
        return all_celltypes, max_pixels, step, marks, min_pixels
    
    # Handle clear button
    elif triggered_id == "page-6bis-clear-celltype-selection-button":
        return {"names": [], "indices": []}, max_pixels, step, marks, min_pixels
    
    # Handle add button
    elif triggered_id == "page-6bis-add-celltype-selection-button":
        if not current_selection:
            return all_selected_celltypes or {"names": [], "indices": []}, max_pixels, step, marks, min_pixels
        
        # Initialize all_selected_celltypes if it's empty
        all_selected_celltypes = all_selected_celltypes or {"names": [], "indices": []}
        
        # Add each celltype that isn't already selected and meets the pixel threshold
        for celltype_name in current_selection:
            if celltype_name not in all_selected_celltypes["names"] and celltype_name in available_celltypes:
                # Find the indices for this celltype
                celltype_indices = celltypes.index[
                    celltypes["cell_type"] == celltype_name
                ].tolist()
                
                if celltype_indices:
                    all_selected_celltypes["names"].append(celltype_name)
                    all_selected_celltypes["indices"].extend(celltype_indices[:1])
        
        return all_selected_celltypes, max_pixels, step, marks, min_pixels
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    Output("page-6bis-graph-hover-text", "children"),
    Input("page-6bis-graph-heatmap-mz-selection", "hoverData"),
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
    Output("page-6bis-graph-heatmap-mz-selection", "figure"),
    Input("main-slider", "data"),
    Input("page-6bis-all-selected-lipizones", "data"),
    Input("page-6bis-all-selected-celltypes", "data"),
    Input("page-6bis-toggle-annotations", "checked"),
    prevent_initial_call=True
)
def page_6_plot_graph_heatmap_mz_selection(
    slice_index,
    all_selected_lipizones,
    all_selected_celltypes,
    annotations_checked,
):
    """This callback plots the heatmap of the selected lipid(s)."""
    print("\n======== page_6_plot_graph_heatmap_mz_selection =========")
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    # Get which input triggered the callback
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    input_id = ctx.triggered[0]["prop_id"].split(".")[1]

    # Handle annotations overlay
    overlay = black_aba_contours(data.get_aba_contours(slice_index)) if annotations_checked else None
    
    # If annotations toggle was triggered, preserve current selections
    if triggered_id == "page-6bis-toggle-annotations":
        lipizones_celltypes_image = compute_image_lipizones_celltypes(
                    all_selected_lipizones, 
                    all_selected_celltypes, 
                    slice_index)
        
        fig = figures.build_lipid_heatmap_from_image(
            lipizones_celltypes_image,
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )
        
        return fig
    
    # Handle other triggers (slider, selections, brain change)
    if (
        (all_selected_lipizones and len(all_selected_lipizones.get("names", [])) > 0)
        or (all_selected_celltypes and len(all_selected_celltypes.get("names", [])) > 0)
    ):
        lipizones_celltypes_image = compute_image_lipizones_celltypes(
            all_selected_lipizones, 
            all_selected_celltypes, 
            slice_index)
            
        fig = figures.build_lipid_heatmap_from_image(
            lipizones_celltypes_image,
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )

        return fig

    else:
        # No selections, use default color for choroid plexus
        hex_colors_to_highlight = ['#f75400']
        fig = figures.build_lipid_heatmap_from_image(
            compute_hybrid_image(hex_colors_to_highlight),
            return_base64_string=False,
            draw=False,
            type_image="RGB",
            return_go_image=False,
            overlay=overlay,
        )
        
        return fig

# Add callback to update badges
@app.callback(
    Output("selected-lipizones-badges", "children"),
    Input("page-6bis-all-selected-lipizones", "data"),
)
def update_selected_lipizones_badges(all_selected_lipizones):
    """Update the badges showing selected lipizones with their corresponding colors."""
    # Get the count of selected lipizones
    count = len(all_selected_lipizones.get("names", [])) if all_selected_lipizones else 0
    
    children = [
        html.H6(
            f"Selected Lipizones ({count})", 
            style={"color": "white", "marginBottom": "10px"}
        )
    ]
    
    if all_selected_lipizones and "names" in all_selected_lipizones:
        for name in all_selected_lipizones["names"]:
            # Get the color for this lipizone, default to cyan if not found
            lipizone_color = lipizone_to_color.get(name, "#00FFFF")
            
            # Create a style that uses the lipizone's color
            badge_style = {
                "margin": "2px",
                "backgroundColor": lipizone_color,
                "color": "black",  # Use black text for better contrast
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
    Output("selected-celltypes-badges", "children"),
    Input("page-6bis-all-selected-celltypes", "data"),
)
def update_selected_celltypes_badges(all_selected_celltypes):
    """Update the badges showing selected celltypes with their corresponding colors."""
    # Get the count of selected celltypes
    count = len(all_selected_celltypes.get("names", [])) if all_selected_celltypes else 0
    
    children = [
        html.H6(
            f"Selected Cell Types ({count})", 
            style={"color": "white", "marginBottom": "10px"}
        )
    ]
    
    if all_selected_celltypes and "names" in all_selected_celltypes:
        for name in all_selected_celltypes["names"]:
            # Get the color for this celltype, default to cyan if not found
            celltype_color = celltype_to_color.get(name, "#00FFFF")
            
            # Convert RGB tuple string to CSS color
            if isinstance(celltype_color, str) and celltype_color.startswith('('):
                # Parse the RGB values from the string tuple
                rgb_values = [float(x) for x in celltype_color.strip('()').split(',')]
                # Convert from 0-1 range to 0-255 range and format as CSS rgb()
                css_color = f"rgb({int(rgb_values[0] * 255)}, {int(rgb_values[1] * 255)}, {int(rgb_values[2] * 255)})"
            else:
                # If it's already a hex color or other format, use as is
                css_color = celltype_color
            
            # Create a style that uses the celltype's color
            badge_style = {
                "margin": "2px",
                "backgroundColor": css_color,
                "color": "black",  # Use black text for better contrast
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