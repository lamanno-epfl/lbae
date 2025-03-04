"""This file contains the page used to explore 3D numpy arrays in an interactive viewer."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

import dash_bootstrap_components as dbc
from dash import dcc, html, clientside_callback
import logging
import dash_draggable
from dash.dependencies import Input, Output, State
import numpy as np
import dash
import dash_mantine_components as dmc
import plotly.graph_objects as go
import copy

# LBAE imports
from app import app, data, figures, storage, atlas, cache_flask

# ==================================================================================================
# --- Helper Functions
# ==================================================================================================


def process_3d_array(array_data, pad_width=30, crop_size=128):
    """Process 3D array for visualization with padding and cropping."""
    # Print initial data stats
    logging.info(f"Initial data stats - min: {np.nanmin(array_data)}, max: {np.nanmax(array_data)}")
    logging.info(f"Initial shape: {array_data.shape}")

    # Replace NaN values with zeros
    data_clean = np.nan_to_num(array_data, nan=0.0)

    # Take log of data after adding a small constant to avoid log(0)
    data_clean = np.log1p(data_clean)

    # Print stats after log transform
    logging.info(f"After log transform - min: {np.min(data_clean)}, max: {np.max(data_clean)}")

    # Normalize the data to [0,1] range before padding
    data_min = np.min(data_clean)
    data_max = np.max(data_clean)
    if data_max > data_min:
        data_normalized = (data_clean - data_min) / (data_max - data_min)
    else:
        data_normalized = np.zeros_like(data_clean)

    # Print stats after normalization
    logging.info(
        f"After normalization - min: {np.min(data_normalized)}, max: {np.max(data_normalized)}"
    )

    # Pad the data with zeros
    data = np.pad(
        data_normalized,
        pad_width=((pad_width, pad_width), (pad_width, pad_width), (pad_width, pad_width)),
        mode="constant",
        constant_values=0,
    )

    # Crop the central square
    center = np.array(data.shape) // 2
    start = center - crop_size // 2
    end = center + crop_size // 2
    data_cropped = data[start[0] : end[0], start[1] : end[1], start[2] : end[2]]

    # Print final stats
    logging.info(f"Final shape: {data_cropped.shape}")
    logging.info(f"Final data stats - min: {np.min(data_cropped)}, max: {np.max(data_cropped)}")
    logging.info(f"Number of non-zero values: {np.sum(data_cropped > 0)}")

    return data_cropped


def create_3d_figure(array_data, colorscale="inferno", opacity=0.9, threshold=0.1):
    """Create a 3D figure from numpy array."""
    # Create the 3D volume
    fig = go.Figure(
        data=go.Volume(
            x=np.arange(array_data.shape[0]),
            y=np.arange(array_data.shape[1]),
            z=np.arange(array_data.shape[2]),
            value=array_data,
            opacity=opacity,
            colorscale=colorscale,
            surface_count=20,
            caps=dict(x_show=False, y_show=False, z_show=False),
            isomin=threshold,  # Use threshold parameter
            isomax=1.0,
            showscale=True,  # Show colorbar
            reversescale=True,  # Reverse the colorscale
            opacityscale=[[0, 0], [threshold, opacity], [1, opacity]],  # Custom opacity scale
        )
    )

    # Update the layout for better visualization
    fig.update_layout(
        scene=dict(
            xaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False),
            zaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False),
            bgcolor="rgb(33, 33, 33)",
            camera=dict(
                up=dict(x=0, y=0, z=1),
                center=dict(x=0, y=0, z=0),
                eye=dict(x=2.5, y=2.5, z=1.5),  # Adjusted camera position
            ),
            aspectmode="data",  # Use the actual data aspect ratio
        ),
        paper_bgcolor="rgb(33, 33, 33)",
        margin=dict(l=0, r=0, t=0, b=0),
    )

    return fig


# ==================================================================================================
# --- Layout
# ==================================================================================================


def return_layout(basic_config, slice_index):
    """Return the layout for the 3D numpy array visualization page."""
    try:
        # Load and process the test data
        test_data = np.load("./data/3d_test_data.npy")
        logging.info("Successfully loaded data")

        processed_data = process_3d_array(test_data)
        logging.info("Successfully processed data")

        # Create initial figure with more visible settings
        initial_figure = create_3d_figure(
            processed_data,
            colorscale="hot",
            opacity=0.3,  # Lower initial opacity
            threshold=0.05,  # Lower initial threshold
        )

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
                # Main content grid
                dash_draggable.ResponsiveGridLayout(
                    id="numpy-3d-draggable",
                    clearSavedLayout=True,
                    isDraggable=False,
                    isResizable=False,
                    containerPadding=[0, 0],
                    breakpoints={
                        "xxl": 1600,
                        "lg": 1200,
                        "md": 996,
                        "sm": 768,
                        "xs": 480,
                        "xxs": 0,
                    },
                    gridCols={
                        "xxl": 12,
                        "lg": 12,
                        "md": 10,
                        "sm": 6,
                        "xs": 4,
                        "xxs": 2,
                    },
                    style={"background-color": "#1d1c1f"},
                    layouts={
                        "xxl": [
                            {"i": "numpy-3d-controls", "x": 0, "y": 0, "w": 3, "h": 20},
                            {"i": "numpy-3d-viewer", "x": 3, "y": 0, "w": 9, "h": 20},
                        ],
                        "lg": [
                            {"i": "numpy-3d-controls", "x": 0, "y": 0, "w": 3, "h": 20},
                            {"i": "numpy-3d-viewer", "x": 3, "y": 0, "w": 9, "h": 20},
                        ],
                        "md": [
                            {"i": "numpy-3d-controls", "x": 0, "y": 0, "w": 3, "h": 20},
                            {"i": "numpy-3d-viewer", "x": 3, "y": 0, "w": 7, "h": 20},
                        ],
                        "sm": [
                            {"i": "numpy-3d-controls", "x": 0, "y": 0, "w": 2, "h": 20},
                            {"i": "numpy-3d-viewer", "x": 2, "y": 0, "w": 4, "h": 20},
                        ],
                        "xs": [
                            {"i": "numpy-3d-controls", "x": 0, "y": 0, "w": 4, "h": 10},
                            {"i": "numpy-3d-viewer", "x": 0, "y": 10, "w": 4, "h": 15},
                        ],
                        "xxs": [
                            {"i": "numpy-3d-controls", "x": 0, "y": 0, "w": 2, "h": 10},
                            {"i": "numpy-3d-viewer", "x": 0, "y": 10, "w": 2, "h": 15},
                        ],
                    },
                    children=[
                        # Controls panel
                        dbc.Card(
                            id="numpy-3d-controls",
                            style={
                                "width": "100%",
                                "height": "100%",
                                "background-color": "#1d1c1f",
                            },
                            children=[
                                dbc.CardBody(
                                    children=[
                                        dmc.Text(
                                            "Visualization Controls", size="xl", align="center"
                                        ),
                                        html.Hr(),
                                        # Opacity control
                                        dmc.Text("Opacity", size="sm"),
                                        dcc.Slider(
                                            id="opacity-slider",
                                            min=0,
                                            max=1,
                                            step=0.05,
                                            value=0.3,  # Lower default opacity
                                            marks={i / 10: str(i / 10) for i in range(0, 11, 2)},
                                        ),
                                        html.Br(),
                                        # Threshold control
                                        dmc.Text("Threshold", size="sm"),
                                        dcc.Slider(
                                            id="threshold-slider",
                                            min=0,
                                            max=0.3,  # Lower max threshold
                                            step=0.01,
                                            value=0.05,  # Lower default threshold
                                            marks={i / 10: str(i / 10) for i in range(0, 4, 1)},
                                        ),
                                        html.Br(),
                                        # Colormap selection
                                        dmc.Text("Colormap", size="sm"),
                                        dcc.Dropdown(
                                            id="colormap-dropdown",
                                            options=[
                                                {"label": "Hot", "value": "hot"},
                                                {"label": "Jet", "value": "jet"},
                                                {"label": "Viridis", "value": "viridis"},
                                                {"label": "Plasma", "value": "plasma"},
                                                {"label": "Inferno", "value": "inferno"},
                                                {"label": "Magma", "value": "magma"},
                                            ],
                                            value="hot",
                                        ),
                                        html.Br(),
                                        # Camera controls
                                        dmc.Text("Camera Position", size="sm"),
                                        dcc.Slider(
                                            id="camera-zoom-slider",
                                            min=0.5,
                                            max=5,
                                            step=0.1,
                                            value=2.5,  # Increased default zoom
                                            marks={i / 2: str(i / 2) for i in range(1, 11, 2)},
                                        ),
                                    ]
                                )
                            ],
                        ),
                        # 3D viewer panel
                        dbc.Card(
                            id="numpy-3d-viewer",
                            style={
                                "width": "100%",
                                "height": "100%",
                                "background-color": "#1d1c1f",
                            },
                            children=[
                                dbc.CardBody(
                                    children=[
                                        dcc.Graph(
                                            id="numpy-3d-graph",
                                            figure=initial_figure,
                                            config=basic_config
                                            | {
                                                "scrollZoom": True,
                                                "modeBarButtonsToAdd": ["resetCameraDefault3d"],
                                            },
                                        )
                                    ]
                                )
                            ],
                        ),
                    ],
                )
            ],
        )
        return page
    except Exception as e:
        logging.error(f"Error in return_layout: {e}")
        return html.Div(f"Error loading data: {str(e)}")


# ==================================================================================================
# --- Callbacks
# ==================================================================================================


@app.callback(
    Output("numpy-3d-graph", "figure"),
    [
        Input("opacity-slider", "value"),
        Input("colormap-dropdown", "value"),
        Input("camera-zoom-slider", "value"),
        Input("threshold-slider", "value"),
    ],
)
def update_figure(opacity, colormap, zoom, threshold):
    """Update the 3D figure based on control values."""
    try:
        # Load and process data
        test_data = np.load("./data/3d_test_data.npy")
        processed_data = process_3d_array(test_data)

        # Create figure with new parameters
        fig = create_3d_figure(
            processed_data, colorscale=colormap, opacity=opacity, threshold=threshold
        )

        # Update camera position
        fig.update_layout(
            scene_camera=dict(
                up=dict(x=0, y=0, z=1), center=dict(x=0, y=0, z=0), eye=dict(x=zoom, y=zoom, z=zoom)
            )
        )

        return fig
    except Exception as e:
        logging.error(f"Error in update_figure: {e}")
        raise
