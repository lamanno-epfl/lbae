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
from app import app, lipizone_data

# ==================================================================================================
# --- Constants
# ==================================================================================================

# Path to the ID cards
ID_CARDS_PATH = "./data/ID_cards"

# ==================================================================================================
# --- Helper functions
# ==================================================================================================

from modules.figures import is_light_color, clean_filenamePD

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
            dcc.Store(id="lipizone-tutorial-step", data=0),
            dcc.Store(id="lipizone-tutorial-completed", storage_type="local", data=False),
            # Add tutorial button under welcome text
            html.Div(
                id="lipizone-start-tutorial-target",
                style={
                    "position": "fixed",
                    "top": "0.9em",
                    "left": "20.3em",
                    "zIndex": 2100,
                    # "width": "10rem",
                    # "height": "3rem",
                    "backgroundColor": "transparent",
                    "border": "3px solid #00bfff",
                    "borderRadius": "4px",
                    # "boxShadow": "0 0 15px rgba(0, 191, 255, 0.7)",
                    "cursor": "pointer",
                },
                children=[
                    dbc.Button(
                        "Start Tutorial",
                        id="lipizone-start-tutorial-btn",
                        color="info",
                        size="sm",
                        className="tutorial-start-btn",
                        style={
                            # "width": "100%",
                            # "height": "100%",
                            "borderRadius": "4px",
                            "backgroundColor": "transparent",
                            "border": "none",
                            # "color": "#00ffff",
                            "fontWeight": "bold",
                        }
                    )
                ]
            ),

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
                        "Lipizones ID Cards",
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
                    # Treemap visualization
                    html.Div(
                        id="lipizone-treemap-container",  # Add this ID
                        style={
                            "height": "40%",
                            "background-color": "#1d1c1f",
                        },
                        children=[
                            dcc.Graph(
                                id="id-cards-lipizones-treemap",
                                figure=lipizone_data.create_treemap_figure_lipizones(df_treemap, node_colors),
                                style={
                                    "height": "40%",
                                    "background-color": "#1d1c1f",
                                },
                                config={'displayModeBar': False}
                            ),
                        ]
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
                lipizone_indices = lipizone_data.df_hierarchy_lipizones.index[
                    lipizone_data.df_hierarchy_lipizones["lipizone_names"] == lipizone_name
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