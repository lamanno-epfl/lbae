# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to view lipizone ID cards as PDFs."""

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
import pickle
import plotly.express as px
import PyPDF2
import io
import base64
from flask import send_file

# LBAE imports
from app import app

# ==================================================================================================
# --- Constants
# ==================================================================================================

# Path to the ID cards
ID_CARDS_PATH = "./data/ID_cards"
df_hierarchy_lipizones = pd.read_csv("./data/lipizone_data/lipizones_hierarchy.csv")
lipizone_to_color = pickle.load(open("./data/lipizone_data/lipizone_to_color.pkl", "rb"))

# ==================================================================================================
# --- Helper functions
# ==================================================================================================

def is_light_color(hex_color):
    """Determine if a color is light or dark based on its RGB values."""
    # Convert hex to RGB
    rgb = hex_to_rgb(hex_color)
    # Calculate luminance using the formula: L = 0.299*R + 0.587*G + 0.114*B
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return luminance > 0.5

def hex_to_rgb(hex_color):
    """Convert hexadecimal color to RGB values."""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

def rgb_to_hex(rgb):
    """Convert RGB values to hexadecimal color."""
    return f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'

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
    return re.sub(r'[\\/:"<>|?]', '_', str(name))

def merge_pdfs(pdf_paths):
    """Merge multiple PDFs into a single PDF."""
    try:
        merger = PyPDF2.PdfMerger()
        
        # Keep track of successfully merged PDFs
        merged_count = 0
        for pdf_path in pdf_paths:
            try:
                with open(pdf_path, 'rb') as pdf_file:
                    merger.append(pdf_file)
                    merged_count += 1
            except Exception as e:
                logging.error(f"Error adding PDF {pdf_path}: {str(e)}")
                continue
        
        if merged_count == 0:
            raise Exception("No PDFs were successfully merged")
        
        # Create a BytesIO object to store the merged PDF
        output = io.BytesIO()
        merger.write(output)
        
        # Important: Get the value before closing
        pdf_content = output.getvalue()
        
        # Clean up resources
        merger.close()
        output.close()
        
        # Convert to base64
        encoded_pdf = base64.b64encode(pdf_content).decode('utf-8')
        
        return encoded_pdf
    except Exception as e:
        logging.error(f"Error in merge_pdfs: {str(e)}")
        raise

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
                        "Select Lipizones for ID Cards",
                        style={
                            "color": "white",
                            "marginBottom": "15px",
                            "fontSize": "1.2em",
                            "fontWeight": "500",
                        }
                    ),
                    # Treemap visualization
                    dcc.Graph(
                        id="id-cards-lipizones-treemap",
                        figure=create_treemap_figure(df_treemap, node_colors),
                        style={
                            "height": "40%",
                            "background-color": "#1d1c1f",
                        },
                        config={'displayModeBar': False}
                    ),
                    # Current selection text
                    html.Div(
                        id="id-cards-current-selection-text",
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
                        id="id-cards-selected-lipizones-badges",
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
                                id="id-cards-add-selection-button",
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
                                id="id-cards-clear-selection-button",
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
                ],
            ),
            
            # PDF viewer container
            html.Div(
                id="id-cards-pdf-viewer-container",
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
                        "Select lipizones to view their ID cards", 
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
    Output("id-cards-current-treemap-selection", "data"),
    Output("id-cards-current-selection-text", "children"),
    Input("id-cards-lipizones-treemap", "clickData"),
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
    Output("id-cards-all-selected-lipizones", "data"),
    Input("id-cards-add-selection-button", "n_clicks"),
    Input("id-cards-clear-selection-button", "n_clicks"),
    State("id-cards-current-treemap-selection", "data"),
    State("id-cards-all-selected-lipizones", "data"),
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
    if triggered_id == "id-cards-clear-selection-button":
        return {"names": [], "indices": []}
    
    # Handle add button
    elif triggered_id == "id-cards-add-selection-button":
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
        print("all_selected_lipizones", all_selected_lipizones)
        return all_selected_lipizones
    
    return dash.no_update

@app.callback(
    Output("id-cards-selected-lipizones-badges", "children"),
    Input("id-cards-all-selected-lipizones", "data"),
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
    Output("id-cards-pdf-viewer-container", "children"),
    Input("id-cards-all-selected-lipizones", "data"),
)
def update_pdf_viewer(all_selected_lipizones):
    """Update the PDF viewer based on the selected lipizones."""
    if not all_selected_lipizones or not all_selected_lipizones.get("names") or len(all_selected_lipizones["names"]) == 0:
        return html.Div(
            "Select lipizones to view their ID cards", 
            style={
                "color": "white", 
                "textAlign": "center", 
                "marginTop": "20%"
            }
        )
    
    # Get all selected lipizones and clean their names
    safe_lipizone_names = [clean_filenamePD(name) for name in all_selected_lipizones["names"]]
    
    # Join the filenames with commas for the URL
    filenames_param = ','.join(safe_lipizone_names)
    
    # Create iframe with PDF viewer
    return html.Iframe(
        src=f"/merged-id-cards-pdf/{filenames_param}?toolbar=1&navpanes=1&scrollbar=1&statusbar=1",
        style={
            "width": "100%",
            "height": "100%",
            "border": "none",
            "backgroundColor": "#1d1c1f",
        }
    )

# Add route for serving merged PDFs
@app.server.route('/merged-id-cards-pdf/<path:filenames>')
def serve_merged_pdf(filenames):
    try:
        # Split filenames and construct full paths
        pdf_paths = []
        for filename in filenames.split(','):
            pdf_path = os.path.join(ID_CARDS_PATH, f"lipizone_ID_card_{filename}.pdf")
            if os.path.exists(pdf_path):
                pdf_paths.append(pdf_path)
        
        if not pdf_paths:
            return "No PDFs found", 404
        
        # If only one PDF, serve it directly
        if len(pdf_paths) == 1:
            return send_file(pdf_paths[0])
        
        # Merge PDFs
        merger = PyPDF2.PdfMerger()
        for pdf_path in pdf_paths:
            merger.append(pdf_path)
        
        # Write to BytesIO
        output = io.BytesIO()
        merger.write(output)
        merger.close()
        
        # Prepare for sending
        output.seek(0)
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=False,
            download_name='merged_id_cards.pdf'
        )
    except Exception as e:
        logging.error(f"Error serving merged PDF: {e}")
        return str(e), 500 