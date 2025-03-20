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

# LBAE imports
from app import app, figures, data, storage, cache_flask

# ==================================================================================================
# --- Constants
# ==================================================================================================

# Path to the ID cards
ID_CARDS_PATH = "/data/luca/lipidatlas/ManuscriptAnalysisRound3/ID_cards"

# Load lipizone names from CSV
lipizonenames = pd.read_csv("/data/LBA_DATA/lbae/lipizonename2color.csv", index_col=0)
lipizonenames = lipizonenames['lipizone_names'].values

# Load hierarchy data for the multiselect
df_hierarchy = pd.read_csv("/data/LBA_DATA/lbae/data/annotations/lipizones_hierarchy.csv")

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
                        id="id-cards-select-level-1",
                        data=level_1_options,
                        placeholder="Select Level 1",
                        style={"width": "20em"},
                    ),
                    # Level 2 dropdown
                    dmc.MultiSelect(
                        id="id-cards-select-level-2",
                        data=[],  # will be updated by callback
                        placeholder="Select Level 2",
                        style={"width": "20em", "marginTop": "0.5em"},
                    ),
                    # Level 3 dropdown
                    dmc.MultiSelect(
                        id="id-cards-select-level-3",
                        data=[],
                        placeholder="Select Level 3",
                        style={"width": "20em", "marginTop": "0.5em"},
                    ),
                    # Level 4 dropdown
                    dmc.MultiSelect(
                        id="id-cards-select-level-4",
                        data=[],
                        placeholder="Select Level 4",
                        style={"width": "20em", "marginTop": "0.5em"},
                    ),
                    # Subclass Select
                    dmc.MultiSelect(
                        id="id-cards-select-subclass",
                        data=[],
                        placeholder="Select Subclass",
                        style={"width": "20em", "marginTop": "0.5em"},
                    ),
                    # Final MultiSelect for the lipizone_names
                    dmc.MultiSelect(
                        id="id-cards-dropdown-lipizones",
                        data=[],  # updated by callback
                        placeholder="Select Lipizone(s)",
                        searchable=True,
                        clearable=True,
                        nothingFound="No lipizone found",
                        style={"width": "20em", "marginTop": "0.5em"},
                        value=[],  # start empty
                        maxSelectedValues=1,  # Only allow one selection at a time
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
                        "Select a lipizone to view its ID card", 
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
    Output("id-cards-select-level-2", "data"),
    Input("id-cards-select-level-1", "value"),
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
    Output("id-cards-select-level-3", "data"),
    [Input("id-cards-select-level-1", "value"),
     Input("id-cards-select-level-2", "value")],
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
    Output("id-cards-select-level-4", "data"),
    [Input("id-cards-select-level-1", "value"),
     Input("id-cards-select-level-2", "value"),
     Input("id-cards-select-level-3", "value")],
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
    Output("id-cards-select-subclass", "data"),
    [Input("id-cards-select-level-1", "value"),
     Input("id-cards-select-level-2", "value"),
     Input("id-cards-select-level-3", "value"),
     Input("id-cards-select-level-4", "value")],
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
    Output("id-cards-dropdown-lipizones", "data"),
    [Input("id-cards-select-level-1", "value"),
     Input("id-cards-select-level-2", "value"),
     Input("id-cards-select-level-3", "value"),
     Input("id-cards-select-level-4", "value"),
     Input("id-cards-select-subclass", "value")],
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
    Output("id-cards-select-level-2", "value"),
    Output("id-cards-select-level-3", "value"),
    Output("id-cards-select-level-4", "value"),
    Output("id-cards-select-subclass", "value"),
    Input("id-cards-select-level-1", "value"),
    prevent_initial_call=True
)
def clear_lower_levels(_):
    return None, None, None, None


def clean_filenamePD(name):
    # Replace / and other problematic characters with an underscore
    return re.sub(r'[\\/:"<>|?]', '_', str(name))


@app.callback(
    Output("id-cards-pdf-viewer-container", "children"),
    Input("id-cards-dropdown-lipizones", "value"),
)
def update_pdf_viewer(selected_lipizones):
    """Update the PDF viewer based on the selected lipizone."""
    if not selected_lipizones or len(selected_lipizones) == 0:
        return html.Div(
            "Select a lipizone to view its ID card", 
            style={
                "color": "white", 
                "textAlign": "center", 
                "marginTop": "20%"
            }
        )
    
    # Get the first selected lipizone (we only allow one selection)
    lipizone_name = selected_lipizones[0]
    
    # Clean the lipizone name for the filename
    safe_lipizone_name = clean_filenamePD(lipizone_name)
    
    # Construct the PDF file path
    pdf_filename = f"lipizone_ID_card_{safe_lipizone_name}.pdf"
    pdf_path = os.path.join(ID_CARDS_PATH, pdf_filename)
    
    # Check if the file exists
    if not os.path.exists(pdf_path):
        return html.Div(
            f"ID card for '{lipizone_name}' not found", 
            style={
                "color": "white", 
                "textAlign": "center", 
                "marginTop": "20%"
            }
        )
    
    # Create iframe with PDF.js viewer
    return html.Iframe(
        src=f"/id-cards-pdf/{safe_lipizone_name}?toolbar=0&navpanes=0&scrollbar=0&statusbar=0&messages=0&preview=0",
        style={
            "width": "100%",
            "height": "100%",
            "border": "none",
            "backgroundColor": "#1d1c1f",
        }
    ) 