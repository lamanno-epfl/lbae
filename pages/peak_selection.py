# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to select and visualize peaks according to pre-existing 
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
import os
os.environ['OMP_NUM_THREADS'] = '6'

# LBAE imports
from app import app, peak_figures, peak_data, cache_flask, atlas, grid_data

# ==================================================================================================
# --- Layout
# ==================================================================================================

def return_layout(basic_config, slice_index):
    page = (
        html.Div(
            style={
                "position": "absolute",
                "top": "0px",
                "right": "0px",
                "bottom": "0px",
                "left": "6rem",
                "background-color": "#1d1c1f",
                "overflow": "hidden",  # Prevent any scrolling
            },
            children=[
                # Add a store component to hold the slider style
                dcc.Store(id="page-2tris-main-slider-style", data={"display": "block"}),
                dcc.Store(id="peak-tutorial-step", data=0),
                dcc.Store(id="peak-tutorial-completed", storage_type="local", data=False),

                # Add tutorial button under welcome text
                html.Div(
                    id="peak-start-tutorial-target",
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
                            id="peak-start-tutorial-btn",
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
                    className="fixed-aspect-ratio",
                    style={
                        "background-color": "#1d1c1f",
                        "position": "absolute",
                        "top": "0",
                        "left": "0",
                        "right": "0",
                        "bottom": "0",
                        "overflow": "hidden",
                    },
                    children=[
                        dcc.Graph(
                            id="page-2tris-graph-heatmap-mz-selection",
                            config=basic_config
                            | {
                                "toImageButtonOptions": {
                                    "format": "png",
                                    "filename": "brain_peak_selection",
                                    "scale": 2,
                                },"scrollZoom": True
                            }
                            | {"staticPlot": False},
                            style={
                                "height": "100%",
                                "width": "100%",
                                "position": "absolute",
                                "left": 0,
                                "top": 0,
                                "bottom": 0,
                                "right": 0,
                                "background-color": "#1d1c1f",
                            },
                            figure=peak_figures.compute_heatmap_per_lipid(
                                slice_index,
                                '1000.169719',
                                cache_flask=cache_flask,
                            ),
                        ),
                        # Allen Brain Atlas switch (independent)
                        html.Div(
                            id="page-2tris-annotations-container",
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
                                    id="page-2tris-toggle-annotations",
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
                        # Title
                        html.H4(
                            "Visualize Peaks",
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
                        # Peak selection controls group
                        dmc.Group(
                            direction="column",
                            spacing=0,
                            style={
                                "left": "1%",
                                "top": "3.5em",
                                "position": "absolute",
                            },
                            children=[
                                dmc.Text("Choose up to 3 peaks", size="lg"),
                                dmc.Group(
                                    spacing="xs",
                                    align="center",
                                    children=[
                                        dmc.MultiSelect(
                                            id="page-2tris-dropdown-peaks",
                                            data=peak_data.return_peak_options(),
                                            value=['1000.169719'],
                                            searchable=True,
                                            nothingFound="No peak found",
                                            radius="md",
                                            # size="xs",
                                            placeholder="Choose up to 3 peaks",
                                            clearable=False,
                                            maxSelectedValues=3,
                                            transitionDuration=150,
                                            transition="pop-top-left",
                                            transitionTimingFunction="ease",
                                            style={
                                                "width": "20em",
                                            },
                                        ),
                                        html.Div(
                                            id="page-2tris-rgb-group",
                                            style={
                                                "display": "flex", 
                                                "alignItems": "center", 
                                                "marginLeft": "15px"
                                            },
                                            children=[
                                                dmc.Switch(
                                                    id="page-2tris-rgb-switch",
                                                    checked=False,
                                                    color="cyan",
                                                    radius="xl",
                                                    size="sm",
                                                ),
                                                html.Span(
                                                    "Display as RGB",
                                                    style={
                                                        "color": "white",
                                                        "marginLeft": "8px",
                                                        "fontWeight": "500",
                                                        "fontSize": "14px",
                                                    },
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        # TODO: uncomment this when all sections view are computed and stored correctly
                        # # Sections mode control
                        # dmc.SegmentedControl(
                        #     id="page-2tris-sections-mode",
                        #     value="one",
                        #     data=[
                        #         {"value": "one", "label": "One section"},
                        #         {"value": "all", "label": "All sections"},
                        #     ],
                        #     color="cyan",
                        #     disabled=True,
                        #     size="xs",
                        #     style={
                        #         "position": "absolute",
                        #         "left": "1%",
                        #         "top": "9em",
                        #         "width": "20em",
                        #         "border": "1px solid rgba(255, 255, 255, 0.1)",
                        #         "borderRadius": "4px",
                        #     }
                        # ),
                        # Show spectrum button
                        dmc.Button(
                            children="Show section mass spectrum",
                            id="page-2tris-show-spectrum-button",
                            variant="filled",
                            color="cyan",
                            radius="md",
                            size="md",
                            disabled=False,
                            compact=False,
                            loading=False,
                            style={
                                "position": "absolute",
                                "left": "1%",
                                "top": "12em",
                                "width": "20em",
                            },
                        ),
                        dmc.Text(
                            id="page-2tris-badge-input",
                            children="Now displaying:",
                            class_name="position-absolute",
                            style={"right": "1%", "top": "1em"},
                        ),
                        # Group for badge 1 and its annotation
                        dmc.Group(
                            id="page-2tris-badge-group-1",
                            class_name="d-none",
                            style={
                                "position": "absolute",
                                "right": "1%", 
                                "top": "4em",
                                "justifyContent": "flex-end",
                                "alignItems": "center",
                                "width": "auto",
                            },
                            children=[
                                dmc.Text(
                                    id="page-2tris-annotation-peak-1",
                                    children="",
                                    style={
                                        "font-style": "italic", 
                                        "font-size": "0.85rem", 
                                        "text-align": "right",
                                        "marginRight": "10px",
                                    },
                                ),
                                dmc.Badge(
                                    id="page-2tris-badge-peak-1",
                                    children="name-peak-1",
                                    color="red",
                                    variant="filled",
                                ),
                            ],
                        ),
                        # Group for badge 2 and its annotation
                        dmc.Group(
                            id="page-2tris-badge-group-2",
                            class_name="d-none",
                            style={
                                "position": "absolute",
                                "right": "1%", 
                                "top": "6em",
                                "justifyContent": "flex-end",
                                "alignItems": "center",
                                "width": "auto",
                            },
                            children=[
                                dmc.Text(
                                    id="page-2tris-annotation-peak-2",
                                    children="",
                                    style={
                                        "font-style": "italic", 
                                        "font-size": "0.85rem", 
                                        "text-align": "right",
                                        "marginRight": "10px",
                                    },
                                ),
                                dmc.Badge(
                                    id="page-2tris-badge-peak-2",
                                    children="name-peak-2",
                                    color="teal",
                                    variant="filled",
                                ),
                            ],
                        ),
                        # Group for badge 3 and its annotation
                        dmc.Group(
                            id="page-2tris-badge-group-3",
                            class_name="d-none",
                            style={
                                "position": "absolute",
                                "right": "1%", 
                                "top": "8em",
                                "justifyContent": "flex-end",
                                "alignItems": "center",
                                "width": "auto",
                            },
                            children=[
                                dmc.Text(
                                    id="page-2tris-annotation-peak-3",
                                    children="",
                                    style={
                                        "font-style": "italic", 
                                        "font-size": "0.85rem", 
                                        "text-align": "right",
                                        "marginRight": "10px",
                                    },
                                ),
                                dmc.Badge(
                                    id="page-2tris-badge-peak-3",
                                    children="name-peak-3",
                                    color="blue",
                                    variant="filled",
                                ),
                            ],
                        ),

                        dmc.Text(
                            "",
                            id="page-2tris-graph-hover-text",
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
                                    id="page-2tris-download-data-button",
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
                                    id="page-2tris-download-image-button",
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
                        dcc.Download(id="page-2tris-download-data"),
                    ],
                ),

                # Tutorial Popovers with adjusted positions
                dbc.Popover(
                    [
                        dbc.PopoverHeader(
                            "M/Z Peaks Exploration",
                            style={"fontWeight": "bold"}
                        ),
                        dbc.PopoverBody(
                            [
                                html.P(
                                    "Welcome to M/Z Peaks Exploration! This page lets you visualize the spatial distribution of detected m/z peaks across brain sections. As with the Lipid page, you can overlay anatomical structures from the Allen Brain Atlas to guide your interpretation of spatial patterns.",
                                    style={"color": "#333", "marginBottom": "15px"}
                                ),
                                dbc.Button("Next", id="peak-tutorial-next-1", color="primary", size="sm", className="float-end")
                            ]
                        ),
                    ],
                    id="peak-tutorial-popover-1",
                    target="peak-start-tutorial-target",
                    placement="right",
                    is_open=False,
                    style={
                        "zIndex": 9999,
                        "border": "2px solid #00bfff",
                        "boxShadow": "0 0 15px 2px #00bfff"
                    }
                ),
                # --- Peak Selection ---
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Choose Up to 3 M/Z Peaks", style={"fontWeight": "bold"}),
                        dbc.PopoverBody(
                            [
                                html.P(
                                    "You can select up to three m/z peaks to display. Peaks are organized for easy browsing, and you can freely combine them to explore co-expression patterns across the brain.",
                                    style={"color": "#333", "marginBottom": "15px"}
                                ),
                                dbc.Button("Next", id="peak-tutorial-next-2", color="primary", size="sm", className="float-end")
                            ]
                        ),
                    ],
                    id="peak-tutorial-popover-2",
                    target="page-2tris-dropdown-peaks",  # dropdown menu
                    placement="bottom",
                    is_open=False,
                    style={
                        "zIndex": 9999,
                        "border": "2px solid #00bfff",
                        "boxShadow": "0 0 15px 2px #00bfff"
                    },
                ),
                # --- Spectrum Viewer ---
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Inspect the Full M/Z Spectrum", style={"fontWeight": "bold"}),
                        dbc.PopoverBody(
                            [
                                html.P(
                                    "Open the spectrum viewer to see the full m/z intensity profile for the currently selected brain slice. This allows you to inspect the spectral signal, locate specific peaks, and then display them spatially for further analysis.",
                                    style={"color": "#333", "marginBottom": "15px"}
                                ),
                                dbc.Button("Next", id="peak-tutorial-next-3", color="primary", size="sm", className="float-end")
                            ]
                        ),
                    ],
                    id="peak-tutorial-popover-3",
                    target="page-2tris-show-spectrum-button",  # spectrum viewer button
                    placement="bottom",
                    is_open=False,
                    style={
                        "zIndex": 9999,
                        "border": "2px solid #00bfff",
                        "boxShadow": "0 0 15px 2px #00bfff"
                    },
                ),
                # --- RGB Mode ---
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Color Map Options", style={"fontWeight": "bold"}),
                        dbc.PopoverBody(
                            [
                                html.P(
                                    "When one peak is selected, you can choose to display it using either the viridis colormap or the red channel of the RGB space. If two or three peaks are selected, the visualization automatically switches to RGB mode, where each peak is mapped to a different channel: red for the first, green for the second, and blue for the third.",
                                    style={"color": "#333", "marginBottom": "15px"}
                                ),
                                dbc.Button("Next", id="peak-tutorial-next-4", color="primary", size="sm", className="float-end")
                            ]
                        ),
                    ],
                    id="peak-tutorial-popover-4",
                    target="page-2tris-rgb-switch",  # rgb switch
                    placement="bottom",
                    is_open=False,
                    style={
                        "zIndex": 9999,
                        "border": "2px solid #00bfff",
                        "boxShadow": "0 0 15px 2px #00bfff"
                    },
                ),
                # # TODO: uncomment and add tutorial for one vs all sections when all sections view are computed and stored correctly
                # # --- One vs All Sections ---
                # dbc.Popover(
                #     [
                #         dbc.PopoverHeader("View All Slices at Once", style={"fontWeight": "bold"}),
                #         dbc.PopoverBody(
                #             [
                #                 html.P(
                #                     "You can switch to a view that shows all brain sections at once. In this mode, only the first selected peak will be displayed to keep the view clean and interpretable.",
                #                     style={"color": "#333", "marginBottom": "15px"}
                #                 ),
                #                 dbc.Button("Next", id="peak-tutorial-next-4", color="primary", size="sm", className="float-end")
                #             ]
                #         ),
                #     ],
                #     id="peak-tutorial-popover-4",
                #     target="page-2tris-sections-mode",  # sections mode switch
                #     placement="bottom",
                #     is_open=False,
                #     style={
                #         "zIndex": 9999,
                #         "border": "2px solid #00bfff",
                #         "boxShadow": "0 0 15px 2px #00bfff"
                #     },
                # ),
                # --- Annotations ---
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Overlay Anatomical Contours", style={"fontWeight": "bold"}),
                        dbc.PopoverBody(
                            [
                                html.P(
                                    "You can enable the Allen Brain Atlas annotations to overlay anatomical labels directly on the slices. This helps you navigate the brain and interpret lipid signals in their biological context.",
                                    style={"color": "#333", "marginBottom": "15px"}
                                ),
                                dbc.Button("Next", id="peak-tutorial-next-5", color="primary", size="sm", className="float-end") # TODO: change this to 5 when the tutorial for all sections is updated
                            ]
                        ),
                    ],
                    id="peak-tutorial-popover-5", # TODO: change this to 5 when the tutorial for all sections is updated
                    target="page-2tris-toggle-annotations",  # annotations switch
                    placement="bottom",
                    is_open=False,
                    style={
                        "zIndex": 9999,
                        "border": "2px solid #00bfff",
                        "boxShadow": "0 0 15px 2px #00bfff"
                    },
                ),
                # --- Brain Slider ---
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Navigate Along Brain Anterior-Posterior Axis", style={"fontWeight": "bold"}),
                        dbc.PopoverBody(
                            [
                                html.P(
                                    "In the single-section view, you can navigate through the brain by selecting different slices along the rostro-caudal (front-to-back) axis. This allows detailed inspection of lipid signals at specific anatomical levels.",
                                    style={"color": "#333", "marginBottom": "15px"}
                                ),
                                dbc.Button("Next", id="peak-tutorial-next-6", color="primary", size="sm", className="float-end") # TODO: change this to 6 when the tutorial for all sections is updated
                            ]
                        ),
                    ],
                    id="peak-tutorial-popover-6", # TODO: change this to 6 when the tutorial for all sections is updated
                    target="main-paper-slider",  # slider
                    placement="top",
                    is_open=False,
                    style={
                        "zIndex": 9999,
                        "border": "2px solid #00bfff",
                        "boxShadow": "0 0 15px 2px #00bfff"
                    },
                ),
                # --- Brain Chips ---
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Choose Experimental Condition", style={"fontWeight": "bold"}),
                        dbc.PopoverBody(
                            [
                                html.P(
                                    "You can choose which mouse brain to view. Brain1 is the reference brain used for the atlas, but you can also explore Brain2, control male and female brains, and pregnant brains to see how lipid distributions differ across biological conditions.",
                                    style={"color": "#333", "marginBottom": "15px"}
                                ),
                                dbc.Button("Finish", id="peak-tutorial-finish", color="success", size="sm", className="float-end")
                            ]
                        ),
                    ],
                    id="peak-tutorial-popover-7", # TODO: change this to 7 when the tutorial for all sections is updated
                    target="main-brain",  # brain switch
                    placement="left",
                    is_open=False,
                    style={
                        "zIndex": 9999,
                        "border": "2px solid #00bfff",
                        "boxShadow": "0 0 15px 2px #00bfff"
                    },
                ),

            ],
        ),
        html.Div(
            children=[
                dbc.Offcanvas(
                    id="page-2tris-drawer-spectrum",
                    backdrop=True,
                    placement="bottom",
                    close_button=False,
                    style={
                        "position": "fixed",
                        "left": "6rem",
                        "width": "calc(100% - 6rem)",
                        "height": "88%",
                        "bottom": 0,
                        "background-color": "#1d1c1f",
                        "boxShadow": "0 -2px 16px rgba(0,0,0,0.5)",
                        "zIndex": 2000,
                        "padding": 0,
                    },
                    children=[
                        html.Div(
                            className="loading-wrapper",
                            style={
                                "position": "relative",
                                "height": "100%",
                                "width": "100%",
                                "padding": 0,
                                "margin": 0,
                                "background": "#1d1c1f",
                            },
                            children=[
                                dmc.Button(
                                    children="Hide spectrum",
                                    id="page-2tris-close-spectrum-button",
                                    variant="filled",
                                    disabled=False,
                                    color="red",
                                    radius="md",
                                    size="md",
                                    compact=False,
                                    loading=False,
                                    style={
                                        "position": "absolute",
                                        "top": "10px",
                                        "right": "10px",
                                        "zIndex": 1000,
                                    },
                                ),
                                html.Div(
                                    style={"height": "100%", "width": "100%"},
                                    children=[
                                        dbc.Spinner(
                                            color="dark",
                                            children=[
                                                html.Div(
                                                    style={"height": "100%", "width": "100%", "padding": 0, "margin": 0},
                                                    children=[
                                                        dcc.Graph(
                                                            id="page-2tris-graph-spectrum",
                                                            style={
                                                                "height": "100%",
                                                                "width": "100%",
                                                                "margin": 0,
                                                                "padding": 0,
                                                                "display": "block",
                                                                "position": "absolute",
                                                                "top": 0,
                                                                "left": 0,
                                                            },
                                                            responsive=True,
                                                            config=basic_config
                                                            | {
                                                                "toImageButtonOptions": {
                                                                    "format": "png",
                                                                    "filename": "section_mass_spectrum",
                                                                    "scale": 2,
                                                                }
                                                            },
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    )

    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================

@app.callback(
    Output("page-2tris-graph-hover-text", "children"),
    Input("page-2tris-graph-heatmap-mz-selection", "hoverData"),
    Input("main-slider", "data"),
)
def page_peak_hover(hoverData, slice_index):
    """This callback is used to update the text displayed when hovering over the slice image."""
    acronym_mask = peak_data.acronyms_masks[slice_index]
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            x = hoverData["points"][0]["x"] # --> from 0 to 456
            y = hoverData["points"][0]["y"] # --> from 0 to 320
            try:
                return atlas.dic_acronym_name[acronym_mask[y, x]]
            except:
                return "Undefined"

    return dash.no_update

@app.callback(
    Output("page-2tris-graph-heatmap-mz-selection", "figure"),
    Output("page-2tris-badge-input", "children"),

    Input("main-slider", "data"),
    Input("page-2tris-selected-peak-1", "data"),
    Input("page-2tris-selected-peak-2", "data"),
    Input("page-2tris-selected-peak-3", "data"),
    Input("page-2tris-rgb-switch", "checked"),
    # Input("page-2tris-sections-mode", "value"), # TODO: uncomment this when all sections view are computed and stored correctly
    Input("main-brain", "value"),
    Input("page-2tris-toggle-annotations", "checked"),

    State("page-2tris-badge-input", "children"),
)
def page_peak_plot_graph_heatmap_mz_selection(
    slice_index,
    peak_1_index,
    peak_2_index,
    peak_3_index,
    rgb_mode,
    # sections_mode, # TODO: uncomment this when all sections view are computed and stored correctly
    brain_id,
    annotations_checked,
    graph_input,
):
    """This callback plots the heatmap of the selected Peak(s)."""
    print(f"\n========== page_peak_plot_graph_heatmap_mz_selection ==========")
    logging.info("Entering function to plot heatmap or RGB depending on Peak selection")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    
    overlay = peak_data.get_aba_contours(slice_index) if annotations_checked else None
    
    # Handle annotations toggle separately to preserve figure state
    if id_input == "page-2tris-toggle-annotations":
        if peak_1_index >= 0 or peak_2_index >= 0 or peak_3_index >= 0:
            ll_peak_names = [
                peak_data.get_annotations().iloc[index]["name"].astype(str)
                if index != -1
                else None
                for index in [peak_1_index, peak_2_index, peak_3_index]
            ]
            
            # TODO: when all sections view are computed and stored correctly, uncomment this
            # # If all sections view is requested, only use first peak
            # if sections_mode == "all":
            #     active_peaks = [name for name in ll_peak_names if name is not None]
            #     first_peak = active_peaks[0] if active_peaks else "1000.169719"
            #     image = grid_data.retrieve_grid_image(
            #         lipid=first_peak,
            #         sample=brain_id
            #     )
            #     return(peak_figures.build_lipid_heatmap_from_image(
            #                 image, 
            #                 return_base64_string=False,
            #                 overlay=overlay),
            #             "Now displaying:")
            
            if rgb_mode: # and sections_mode != "all": # TODO: uncomment this when all sections view are computed and stored correctly
                return (
                    peak_figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_peak_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    ),
                    "Now displaying:",
                )
            else:
                # Check that only one peak is selected for colormap mode
                active_peaks = [name for name in ll_peak_names if name is not None]
                if len(active_peaks) == 1:
                    image = peak_figures.compute_image_per_lipid(
                        slice_index,
                        RGB_format=False,
                        lipid_name=active_peaks[0],
                        cache_flask=cache_flask,
                    )
                    return (
                        peak_figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False,
                            overlay=overlay,
                        ),
                        "Now displaying:",
                    )
                else:
                    # If multiple peaks and not in RGB mode, force RGB mode (except in all sections mode)
                    # if sections_mode != "all":
                    return (
                        peak_figures.compute_rgb_image_per_lipid_selection(
                            slice_index,
                            ll_lipid_names=ll_peak_names,
                            cache_flask=cache_flask,
                            overlay=overlay,
                        ),
                        "Now displaying:",
                    )
                    # else:
                    #     TODO: when all sections view are computed and stored correctly, uncomment this
                    #     # In all sections mode, use only first peak
                    #     first_peak = active_peaks[0] if active_peaks else "1000.169719"
                    #     image = grid_data.retrieve_grid_image(
                    #         lipid=first_peak,
                    #         sample=brain_id
                    #     )
                    #     return(peak_figures.build_lipid_heatmap_from_image(
                                # image, 
                                # return_base64_string=False,
                                # overlay=overlay),
                                # "Now displaying:")

        return dash.no_update

    # If a peak selection has been done
    if (
        id_input == "page-2tris-selected-peak-1"
        or id_input == "page-2tris-selected-peak-2"
        or id_input == "page-2tris-selected-peak-3"
        or id_input == "page-2tris-rgb-switch"
        # or id_input == "page-2tris-sections-mode" # TODO: uncomment this when all sections view are computed and stored correctly
        or id_input == "main-brain"
        or id_input == "main-slider"
    ):
        if peak_1_index >= 0 or peak_2_index >= 0 or peak_3_index >= 0:
            ll_peak_names = [
                peak_data.get_annotations().iloc[index]["name"].astype(str)
                if index != -1
                else None
                for index in [peak_1_index, peak_2_index, peak_3_index]
            ]

            # TODO: when all sections view are computed and stored correctly, uncomment this
            # # If all sections view is requested
            # if sections_mode == "all":
            #     TODO:
                
            #     return(peak_figures.build_lipid_heatmap_from_image(
            #                 image, 
            #                 return_base64_string=False,
            #                 overlay=overlay),
            #             "Now displaying:")
            
            # Handle normal display mode (RGB or colormap)
            # else:
            active_peaks = [name for name in ll_peak_names if name is not None]
            if rgb_mode:
                return (
                    peak_figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_peak_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    ),
                    "Now displaying:",
                )
            else:
                # If not in RGB mode, use first peak only
                first_peak = active_peaks[0] if active_peaks else "1000.169719"
                image = peak_figures.compute_image_per_lipid(
                    slice_index,
                    RGB_format=False,
                    lipid_name=first_peak,
                    cache_flask=cache_flask,
                )
                return (
                    peak_figures.build_lipid_heatmap_from_image(
                        image, 
                        return_base64_string=False,
                        overlay=overlay,
                    ),
                    "Now displaying:",
                )
        elif (
            id_input == "main-slider" and graph_input == "Now displaying:"
        ):
            logging.info(f"No peak has been selected, the current peak is 1000.169719 and the slice is {slice_index}")
            return (
                peak_figures.compute_heatmap_per_lipid(slice_index, 
                                                '1000.169719',
                                                cache_flask=cache_flask,
                                                overlay=overlay),
                "Now displaying:",
            )
        else:
            # No peak has been selected
            logging.info(f"No peak has been selected, the current peak is 1000.169719 and the slice is {slice_index}")
            return (
                peak_figures.compute_heatmap_per_lipid(slice_index, 
                                                '1000.169719',
                                                cache_flask=cache_flask,
                                                overlay=overlay),
                "Now displaying:",
            )

    # If no trigger, the page has just been loaded, so load new figure with default parameters
    else:
        return (
            peak_figures.compute_heatmap_per_lipid(slice_index, 
                                            '1000.169719',
                                            cache_flask=cache_flask,
                                            overlay=overlay),
            "Now displaying:",
        )


@app.callback(
    Output("page-2tris-badge-peak-1", "children"),
    Output("page-2tris-badge-peak-2", "children"),
    Output("page-2tris-badge-peak-3", "children"),
    Output("page-2tris-selected-peak-1", "data"),
    Output("page-2tris-selected-peak-2", "data"),
    Output("page-2tris-selected-peak-3", "data"),
    Output("page-2tris-badge-group-1", "class_name"),
    Output("page-2tris-badge-group-2", "class_name"),
    Output("page-2tris-badge-group-3", "class_name"),
    Output("page-2tris-dropdown-peaks", "value"),
    Output("page-2tris-annotation-peak-1", "children"),
    Output("page-2tris-annotation-peak-2", "children"),
    Output("page-2tris-annotation-peak-3", "children"),
    Input("page-2tris-dropdown-peaks", "value"),
    Input("page-2tris-badge-group-1", "class_name"),
    Input("page-2tris-badge-group-2", "class_name"),
    Input("page-2tris-badge-group-3", "class_name"),
    Input("main-slider", "data"),
    # Input("page-2tris-sections-mode", "value"), # TODO: uncomment this when all sections view are computed and stored correctly
    Input("page-2tris-rgb-switch", "checked"),
    State("page-2tris-selected-peak-1", "data"),
    State("page-2tris-selected-peak-2", "data"),
    State("page-2tris-selected-peak-3", "data"),
    State("page-2tris-badge-peak-1", "children"),
    State("page-2tris-badge-peak-2", "children"),
    State("page-2tris-badge-peak-3", "children"),
    State("main-brain", "value"),
)
def page_peak_add_toast_selection(
    l_peak_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    # sections_mode,
    rgb_switch,
    peak_1_index,
    peak_2_index,
    peak_3_index,
    header_1,
    header_2,
    header_3,
    brain_id,
):
    """This callback adds the selected peak to the selection."""
    logging.info("Entering function to update peak data")
    print("\n================ page_peak_add_toast_selection ================")
    
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    
    # Initialize annotation variables
    annotation_1 = ""
    annotation_2 = ""
    annotation_3 = ""
    
    # Initialize with default peak if no selection exists
    if len(id_input) == 0 or (id_input == "page-2tris-dropdown-peaks" and l_peak_names is None):
        default_peak = '1000.169719'
        name = default_peak
        l_peak_loc = (
            peak_data.get_annotations()
            .index[
                (peak_data.get_annotations()["name"] == name)
                & (peak_data.get_annotations()["slice"] == slice_index)
            ]
            .tolist()
        )
        
        if len(l_peak_loc) == 0:
            l_peak_loc = (
                peak_data.get_annotations()
                .index[
                    (peak_data.get_annotations()["name"] == name)
                ]
                .tolist()
            )[:1]
        
        if len(l_peak_loc) > 0:
            peak_1_index = l_peak_loc[0]
            header_1 = default_peak
            class_name_badge_1 = "position-absolute"
            
            # Get annotation for the default peak
            annotation_value = peak_data.get_annotations().iloc[peak_1_index]["annotation"]
            annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
            
            return (header_1, "", "", peak_1_index, -1, -1, class_name_badge_1, "d-none", "d-none", 
                    [default_peak], annotation_1, "", "")
        else:
            return ("", "", "", -1, -1, -1, "d-none", "d-none", "d-none", 
                    [], "", "", "")

    # If RGB is turned off or sections mode is "all", keep only the first peak
    if (id_input == "page-2tris-rgb-switch" and not rgb_switch): 
        # TODO: uncomment this when all sections view are computed and stored correctly
        # or (id_input == "page-2tris-sections-mode" and sections_mode == "all"):
        active_peaks = []
        if header_1 and peak_1_index != -1:
            active_peaks.append((header_1, peak_1_index))
        elif header_2 and peak_2_index != -1:
            active_peaks.append((header_2, peak_2_index))
        elif header_3 and peak_3_index != -1:
            active_peaks.append((header_3, peak_3_index))
            
        if active_peaks:
            first_peak, first_index = active_peaks[0]
            
            # Get annotation for the selected peak
            annotation_value = peak_data.get_annotations().iloc[first_index]["annotation"]
            annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
            
            return (first_peak, "", "", first_index, -1, -1, 
                    "position-absolute", "d-none", "d-none", [first_peak],
                    annotation_1, "", "")
        return dash.no_update

    # Handle peak deletion
    if l_peak_names is not None and len(l_peak_names) < len([x for x in [peak_1_index, peak_2_index, peak_3_index] if x != -1]):
        logging.info("One or several peaks have been deleted. Cleaning peak badges now.")
        
        # Create list of remaining peaks and their indices
        remaining_peaks = []
        for peak_name in l_peak_names:
            name = peak_name
            l_peak_loc = (
                peak_data.get_annotations()
                .index[
                    (peak_data.get_annotations()["name"].astype(str) == str(name))
                    & (peak_data.get_annotations()["slice"] == slice_index)
                ]
                .tolist()
            )
            
            if len(l_peak_loc) == 0:
                l_peak_loc = (
                    peak_data.get_annotations()
                    .index[
                        (peak_data.get_annotations()["name"].astype(str) == str(name))
                    ]
                    .tolist()
                )[:1]
                
            if len(l_peak_loc) > 0:
                remaining_peaks.append((peak_name, l_peak_loc[0]))
        
        # Reset all slots
        header_1, header_2, header_3 = "", "", ""
        peak_1_index, peak_2_index, peak_3_index = -1, -1, -1
        class_name_badge_1, class_name_badge_2, class_name_badge_3 = "d-none", "d-none", "d-none"
        annotation_1, annotation_2, annotation_3 = "", "", ""
        
        # TODO: uncomment this when all sections view are computed and stored correctly
        # # Fill slots in order with remaining peaks
        # # If in all sections mode, only fill the first slot
        # if sections_mode == "all" and remaining_peaks:
        #     header_1 = remaining_peaks[0][0]
        #     peak_1_index = remaining_peaks[0][1]
        #     class_name_badge_1 = "position-absolute"
            
        #     # Get annotation for peak 1
        #     annotation_value = peak_data.get_annotations().iloc[peak_1_index]["annotation"]
        #     annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
            
        #     return (
        #         header_1,
        #         "",
        #         "",
        #         peak_1_index,
        #         -1,
        #         -1,
        #         class_name_badge_1,
        #         "d-none",
        #         "d-none",
        #         [header_1],
        #         annotation_1,
        #         "",
        #         ""
        #     )
        # else:
        for idx, (peak_name, peak_idx) in enumerate(remaining_peaks):
            if idx == 0:
                header_1 = peak_name
                peak_1_index = peak_idx
                class_name_badge_1 = "position-absolute"
                
                # Get annotation for peak 1
                annotation_value = peak_data.get_annotations().iloc[peak_1_index]["annotation"]
                annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                
            elif idx == 1:
                header_2 = peak_name
                peak_2_index = peak_idx
                class_name_badge_2 = "position-absolute"
                
                # Get annotation for peak 2
                annotation_value = peak_data.get_annotations().iloc[peak_2_index]["annotation"]
                annotation_2 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                
            elif idx == 2:
                header_3 = peak_name
                peak_3_index = peak_idx
                class_name_badge_3 = "position-absolute"
                
                # Get annotation for peak 3
                annotation_value = peak_data.get_annotations().iloc[peak_3_index]["annotation"]
                annotation_3 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
            
        return (
            header_1,
            header_2,
            header_3,
            peak_1_index,
            peak_2_index,
            peak_3_index,
            class_name_badge_1,
            class_name_badge_2,
            class_name_badge_3,
            l_peak_names,
            annotation_1,
            annotation_2,
            annotation_3
        )

    # Handle new peak addition or slice change
    if (id_input == "page-2tris-dropdown-peaks" and l_peak_names is not None) or id_input == "main-slider":
        # If a new slice has been selected
        if id_input == "main-slider":
            # Update indices for existing peaks
            for header in [header_1, header_2, header_3]:
                if not header:
                    continue
                    
                name = header
                # Find peak location
                l_peak_loc_temp = (
                    peak_data.get_annotations()
                    .index[
                        (peak_data.get_annotations()["name"].astype(str) == str(name))
                    ]
                    .tolist()
                )
                
                l_peak_loc = [
                    l_peak_loc_temp[i]
                    for i, x in enumerate(
                        peak_data.get_annotations().iloc[l_peak_loc_temp]["slice"] == slice_index
                    )
                    if x
                ]
                
                peak_index = l_peak_loc[0] if len(l_peak_loc) > 0 else -1

                if header_1 == header:
                    peak_1_index = peak_index
                elif header_2 == header:
                    peak_2_index = peak_index
                elif header_3 == header:
                    peak_3_index = peak_index

            # Update annotations for all peaks
            if peak_1_index != -1:
                annotation_value = peak_data.get_annotations().iloc[peak_1_index]["annotation"]
                annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
            else:
                annotation_1 = ""
                
            if peak_2_index != -1:
                annotation_value = peak_data.get_annotations().iloc[peak_2_index]["annotation"]
                annotation_2 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
            else:
                annotation_2 = ""
                
            if peak_3_index != -1:
                annotation_value = peak_data.get_annotations().iloc[peak_3_index]["annotation"]
                annotation_3 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
            else:
                annotation_3 = ""

            # If in all sections mode, keep only first peak
            # TODO: uncomment this when all sections view are computed and stored correctly
            # if sections_mode == "all":
                # current_peaks = []
                # if header_1 and peak_1_index != -1:
                #     current_peaks.append(header_1)
                #     annotation_value = peak_data.get_annotations().iloc[peak_1_index]["annotation"]
                #     annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                # elif header_2 and peak_2_index != -1:
                #     current_peaks.append(header_2)
                #     annotation_value = peak_data.get_annotations().iloc[peak_2_index]["annotation"]
                #     annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                # elif header_3 and peak_3_index != -1:
                #     current_peaks.append(header_3)
                #     annotation_value = peak_data.get_annotations().iloc[peak_3_index]["annotation"]
                #     annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    
                # if current_peaks:
                #     return (
                #         current_peaks[0],
                #         "",
                #         "",
                #         peak_1_index if header_1 else (peak_2_index if header_2 else peak_3_index),
                #         -1,
                #         -1,
                #         "position-absolute",
                #         "d-none",
                #         "d-none",
                #         current_peaks[:1],
                #         annotation_1,
                #         "",
                #         ""
                #     )

            return (
                header_1,
                header_2,
                header_3,
                peak_1_index,
                peak_2_index,
                peak_3_index,
                "position-absolute" if peak_1_index != -1 else "d-none",
                "position-absolute" if peak_2_index != -1 else "d-none",
                "position-absolute" if peak_3_index != -1 else "d-none",
                [h for h in [header_1, header_2, header_3] if h],
                annotation_1,
                annotation_2,
                annotation_3
            )

        # If peaks have been added from dropdown menu
        elif id_input == "page-2tris-dropdown-peaks":
            # Get the peak name
            name = l_peak_names[-1]

            # Find peak location
            l_peak_loc = (
                peak_data.get_annotations()
                .index[
                    (peak_data.get_annotations()["name"].astype(str) == str(name))
                    & (peak_data.get_annotations()["slice"] == slice_index)
                ]
                .tolist()
            )
            
            if len(l_peak_loc) < 1:
                l_peak_loc = (
                    peak_data.get_annotations()
                    .index[
                        (peak_data.get_annotations()["name"].astype(str) == str(name))
                    ]
                    .tolist()
                )[:1]

            if len(l_peak_loc) > 0:
                peak_index = l_peak_loc[0]
                peak_string = l_peak_names[-1]

                # TODO: when all sections view are computed and stored correctly, uncomment this
                # # If in all sections mode, only allow one peak
                # if sections_mode == "all":
                #     header_1 = peak_string
                #     peak_1_index = peak_index
                #     class_name_badge_1 = "position-absolute"
                    
                #     # Get annotation for the peak
                #     annotation_value = peak_data.get_annotations().iloc[peak_1_index]["annotation"]
                #     annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    
                #     return (
                #         header_1,
                #         "",
                #         "",
                #         peak_1_index,
                #         -1,
                #         -1,
                #         class_name_badge_1,
                #         "d-none",
                #         "d-none",
                #         [header_1],
                #         annotation_1,
                #         "",
                #         ""
                #     )

                # If peak already exists, update its index
                if header_1 == peak_string:
                    peak_1_index = peak_index
                    
                    # Update annotation
                    annotation_value = peak_data.get_annotations().iloc[peak_1_index]["annotation"]
                    annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    
                elif header_2 == peak_string:
                    peak_2_index = peak_index
                    
                    # Update annotation
                    annotation_value = peak_data.get_annotations().iloc[peak_2_index]["annotation"]
                    annotation_2 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    
                elif header_3 == peak_string:
                    peak_3_index = peak_index
                    
                    # Update annotation
                    annotation_value = peak_data.get_annotations().iloc[peak_3_index]["annotation"]
                    annotation_3 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    
                # If it's a new peak, fill the first available slot
                else:
                    if class_name_badge_1 == "d-none":
                        header_1 = peak_string
                        peak_1_index = peak_index
                        class_name_badge_1 = "position-absolute"
                        
                        # Add annotation for peak 1
                        annotation_value = peak_data.get_annotations().iloc[peak_1_index]["annotation"]
                        annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        
                        # Make sure existing annotations remain visible
                        if peak_2_index != -1:
                            annotation_value = peak_data.get_annotations().iloc[peak_2_index]["annotation"]
                            annotation_2 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        if peak_3_index != -1:
                            annotation_value = peak_data.get_annotations().iloc[peak_3_index]["annotation"]
                            annotation_3 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        
                    elif class_name_badge_2 == "d-none":
                        header_2 = peak_string
                        peak_2_index = peak_index
                        class_name_badge_2 = "position-absolute"
                        
                        # Add annotation for peak 2
                        annotation_value = peak_data.get_annotations().iloc[peak_2_index]["annotation"]
                        annotation_2 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        
                        # Make sure existing annotations remain visible
                        if peak_1_index != -1:
                            annotation_value = peak_data.get_annotations().iloc[peak_1_index]["annotation"]
                            annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        if peak_3_index != -1:
                            annotation_value = peak_data.get_annotations().iloc[peak_3_index]["annotation"]
                            annotation_3 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        
                    elif class_name_badge_3 == "d-none":
                        header_3 = peak_string
                        peak_3_index = peak_index
                        class_name_badge_3 = "position-absolute"
                        
                        # Add annotation for peak 3
                        annotation_value = peak_data.get_annotations().iloc[peak_3_index]["annotation"]
                        annotation_3 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        
                        # Make sure existing annotations remain visible
                        if peak_1_index != -1:
                            annotation_value = peak_data.get_annotations().iloc[peak_1_index]["annotation"]
                            annotation_1 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        if peak_2_index != -1:
                            annotation_value = peak_data.get_annotations().iloc[peak_2_index]["annotation"]
                            annotation_2 = "No matched molecule" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        
                    else:
                        logging.warning("More than 3 peaks have been selected")
                        return dash.no_update

                return (
                    header_1,
                    header_2,
                    header_3,
                    peak_1_index,
                    peak_2_index,
                    peak_3_index,
                    "position-absolute" if peak_1_index != -1 else "d-none",
                    "position-absolute" if peak_2_index != -1 else "d-none",
                    "position-absolute" if peak_3_index != -1 else "d-none",
                    l_peak_names,
                    annotation_1,
                    annotation_2,
                    annotation_3
                )

    return dash.no_update


clientside_callback(
    """
    function(n_clicks){
        if(n_clicks > 0){
            domtoimage.toBlob(document.getElementById('page-2tris-graph-heatmap-mz-selection'))
                .then(function (blob) {
                    window.saveAs(blob, 'peak_selection_plot.png');
                });
        }
        return null;
    }
    """,
    Output("page-2tris-download-image-button", "n_clicks"),
    Input("page-2tris-download-image-button", "n_clicks"),
)
"""This clientside callback is used to download the current heatmap."""


@app.callback(
    Output("page-2tris-drawer-spectrum", "is_open"),
    Input("page-2tris-show-spectrum-button", "n_clicks"),
    Input("page-2tris-close-spectrum-button", "n_clicks"),
    [State("page-2tris-drawer-spectrum", "is_open")],
)
def toggle_spectrum_drawer(n1, n2, is_open):
    """This callback is used to toggle the mass spectrum drawer."""
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("page-2tris-graph-spectrum", "figure"),
    Input("main-slider", "data"),
    Input("page-2tris-drawer-spectrum", "is_open"),
)
def plot_section_mass_spectrum(slice_index, is_open):
    """This callback plots the mass spectrum for the current section."""
    import plotly.graph_objects as go
    import pandas as pd
    import os
    
    if not is_open:
        # If the drawer is closed, don't update
        return dash.no_update
        
    # Check if mzsectionaverages.csv exists, if not create a placeholder
    df = pd.read_csv(os.path.join(peak_data.path_data, "mzsectionaverages.csv"), index_col=0)
    df.index = df.index.astype(int)
    
    # Get the spectrum data for the current slice
    spectrum_data = df.loc[int(slice_index)]
    
    # Create the x and y values for the plot
    x_values = [float(col) for col in df.columns]
    y_values = spectrum_data.values
    
    # Define figure data
    data = go.Scattergl(
        x=x_values,
        y=y_values,
        visible=True,
        line_color="#00bfff",
        fill="tozeroy",
        )
    
    # Define figure layout
    layout = go.Layout(
        margin=dict(t=0, r=0, b=0, l=0),
        showlegend=False,
        xaxis=dict(rangeslider={"visible": False}, title="m/z"),
        yaxis=dict(fixedrange=False, title="Intensity"),
        template="plotly_dark",
        autosize=True,
        title={
            "text": "Mass Spectrum",
            "y": 0.99,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(
                size=18,
            ),
        },
        paper_bgcolor="#1d1c1f",
        plot_bgcolor="#1d1c1f",
        height=None,
        width=None,
    )

    # Build figure
    fig = go.Figure(data=data, layout=layout)
    
    return fig

@app.callback(
    Output("page-2tris-rgb-switch", "checked"),
    Input("page-2tris-selected-peak-1", "data"),
    Input("page-2tris-selected-peak-2", "data"),
    Input("page-2tris-selected-peak-3", "data"),
    # Input("page-2tris-sections-mode", "value"), # TODO: uncomment this when all sections view are computed and stored correctly
    State("page-2tris-rgb-switch", "checked"),
)
def page_peak_auto_toggle_rgb(
    peak_1_index, 
    peak_2_index, 
    peak_3_index, 
    # sections_mode, 
    current_rgb_state):
    """This callback automatically toggles the RGB switch when multiple peaks are selected."""

    # TODO: uncomment this when all sections view are computed and stored correctly
    # # Force RGB off when in all sections mode
    # if sections_mode == "all":
    #     return False
        
    active_peaks = [x for x in [peak_1_index, peak_2_index, peak_3_index] if x != -1]
    # Only turn on RGB automatically when going from 1 to multiple peaks
    # Don't turn it off when going from multiple to 1
    if len(active_peaks) > 1:
        return True
    return current_rgb_state  # Keep current state otherwise

# TODO: uncomment this when all sections view are computed and stored correctly
# @app.callback(
#     # Output("page-2tris-sections-mode", "disabled"),
#     Input("page-2tris-selected-peak-1", "data"),
#     Input("page-2tris-selected-peak-2", "data"),
#     Input("page-2tris-selected-peak-3", "data"),
# )
# def page_peak_active_sections_control(peak_1_index, peak_2_index, peak_3_index):
#     """This callback enables/disables the sections mode control based on peak selection."""
#     # Get the current peak selection
#     active_peaks = [x for x in [peak_1_index, peak_2_index, peak_3_index] if x != -1]
#     # Enable control if at least one peak is selected
#     return len(active_peaks) == 0

# TODO: uncomment this when all sections view are computed and stored correctly
# @app.callback(
#     Output("page-2tris-main-slider-style", "data"),
#     Output("page-2tris-graph-hover-text", "style"),
#     Output("page-2tris-annotations-container", "style"),
#     # Input("page-2tris-sections-mode", "value"),
# )
# def page_peak_toggle_elements_visibility(sections_mode):
#     """This callback toggles the visibility of elements based on sections mode."""
#     if sections_mode == "all":
#         # Hide elements
#         return {"display": "none"}, {"display": "none"}, {"display": "none"}
#     else:
#         # Show elements
#         return (
#             {"display": "block"}, 
#             {
#                 "width": "auto",
#                 "position": "absolute",
#                 "left": "50%",
#                 "transform": "translateX(-50%)",
#                 "top": "1em",
#                 "fontSize": "1.5em",
#                 "textAlign": "center",
#                 "zIndex": 1000,
#                 "backgroundColor": "rgba(0, 0, 0, 0.7)",
#                 "padding": "0.5em 2em",
#                 "borderRadius": "8px",
#                 "minWidth": "200px",
#             },
#             {
#                 "position": "absolute",
#                 "left": "50%",
#                 "transform": "translateX(-50%)",
#                 "top": "0.5em",
#                 "z-index": 1000,
#                 "display": "flex",
#                 "flexDirection": "row",
#                 "alignItems": "center",
#                 "justifyContent": "center",
#                 "padding": "0.5em 2em",
#             }
#         )

# TODO: uncomment this when all sections view are computed and stored correctly
# # Add a separate callback just for the RGB group visibility
# @app.callback(
#     Output("page-2tris-rgb-group", "style"),
#     Input("page-2tris-sections-mode", "value"),
# )
# def page_peak_toggle_rgb_group_visibility(sections_mode):
#     """Controls the visibility of the RGB group."""
#     if sections_mode == "all":
#         return {"display": "none"}
#     else:
#         return {"display": "flex", "alignItems": "center", "marginLeft": "15px"}

# @app.callback(
#     Output("page-2tris-hide-store", "data"),
#     Input("page-2tris-sections-mode", "value"),
#     State("url", "pathname"),
#     prevent_initial_call=True,
# )
# def compute_page2tris_hide(peak_sections_mode, pathname):
#     if pathname == "/peak-selection":
#         return "d-none" if (peak_sections_mode == "all") else ""
#     return ""

# Use clientside callback for tutorial step updates
app.clientside_callback(
    """
    function(start, next1, next2, next3, next4, next5, next6, finish) { 
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered.length) {
            return window.dash_clientside.no_update;
        }
        const trigger_id = ctx.triggered[0].prop_id.split('.')[0];
        if (trigger_id === 'peak-start-tutorial-btn' && start) {
            return 1;
        } else if (trigger_id === 'peak-tutorial-next-1' && next1) {
            return 2;
        } else if (trigger_id === 'peak-tutorial-next-2' && next2) {
            return 3;
        } else if (trigger_id === 'peak-tutorial-next-3' && next3) {
            return 4;
        } else if (trigger_id === 'peak-tutorial-next-4' && next4) {
            return 5;
        } else if (trigger_id === 'peak-tutorial-next-5' && next5) {
            return 6;
        } else if (trigger_id === 'peak-tutorial-next-6' && next6) {
            return 7;
        } else if (trigger_id === 'peak-tutorial-finish' && finish) {
            return 0;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("peak-tutorial-step", "data"),
    [Input("peak-start-tutorial-btn", "n_clicks"),
     Input("peak-tutorial-next-1", "n_clicks"),
     Input("peak-tutorial-next-2", "n_clicks"),
     Input("peak-tutorial-next-3", "n_clicks"),
     Input("peak-tutorial-next-4", "n_clicks"),
     Input("peak-tutorial-next-5", "n_clicks"),
     Input("peak-tutorial-next-6", "n_clicks"),
     Input("peak-tutorial-finish", "n_clicks")],
    prevent_initial_call=True,
)

# Use clientside callback for popover visibility
app.clientside_callback(
    """
    function(step) {
        if (step === undefined || step === null) {
            return [false, false, false, false, false, false, false];
        }
        return [
            step === 1,
            step === 2,
            step === 3,
            step === 4,
            step === 5,
            step === 6,
            step === 7,
        ];
    }
    """,
    [Output(f"peak-tutorial-popover-{i}", "is_open") for i in range(1, 7)], # TODO: change this to 8 when the tutorial for all sections is updated
    Input("peak-tutorial-step", "data"),
    prevent_initial_call=True,
)

# Use clientside callback for tutorial completion
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            return true;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("peak-tutorial-completed", "data"),
    Input("peak-tutorial-finish", "n_clicks"),
    prevent_initial_call=True,
)