# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to explore the lipid data from either pre-existing annotated 
structures or human-selected in the app.

Updates:
- Added toggle switch for Allen Brain Atlas annotations overlay
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html, clientside_callback
from dash.dependencies import Input, Output, State
import dash
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import logging
import dash_draggable
from numba import njit
import dash_mantine_components as dmc
import pickle
from skimage.draw import polygon
from statsmodels.stats.multitest import multipletests
from scipy.stats import mannwhitneyu, ttest_ind
# LBAE imports
from app import app, figures, data, atlas, cache_flask
import config
from modules.tools.image import convert_image_to_base64
from config import l_colors

# ==================================================================================================
# --- Helper functions
# ==================================================================================================

def global_store(
    slice_index, 
    l_shapes_and_masks,
):
    """This function computes and returns the lipids' expression for the selected regions.

    Args:
        slice_index (int): Index of the selected slice.
        l_shapes_and_masks (list): A list of either user-draw regions, or pre-existing masks coming
            from annotations (both custom objects).
        l_mask_name (list(str)): If masks are present in l_shapes_and_masks, this list contains the
            corresponding names of the masks.
        relayoutData (_type_): If user-draw regions are present in l_shapes_and_masks, this list
            contains the corresponding relayout data, which itself contains the path used to define
            the drawn shapes.
    Returns:
        (list(np.ndarray)): A list of numpy arrays, each corresponding to the lipidomic data of a
            user-draw region, or pre-existing mask.
    """

    # Empty variables before computing the lipidomic data
    idx_mask = -1
    idx_path = -1
    l_expressions = []

    # Loop over all user-draw regions and pre-existing masks
    print("l_shapes_and_masks = ", l_shapes_and_masks)
    for shape in l_shapes_and_masks:
        grah_scattergl_data = None
        # Compute lipid expressions from mask
        if shape[0] == "mask":
            mask_name = shape[1]
            print("mask_name = ", mask_name)
            
            id_name = atlas.dic_name_acronym[mask_name]
            if id_name in atlas.dic_existing_masks[slice_index]:
                descendants = atlas.bg_atlas.get_structure_descendants(id_name)
                acronym_mask = data.acronyms_masks[slice_index]
                mask2D = np.isin(acronym_mask, descendants + [id_name])
                indices = np.where(mask2D)
                y_indices = indices[0]
                z_indices = indices[1]
                grah_scattergl_data = data.get_pixels_from_indices(slice_index, z_indices, y_indices)
                # grah_scattergl_data = pixels.iloc[:, :173].values
                
            else:
                logging.warning("Bug, the selected mask does't exist")
                return dash.no_update

        elif shape[0] == "shape":
            idx_path += 1

            if "path" in shape[2]:
                parsed_path = shape[2]["path"][1:-1].replace("L", ",").split(",")
                path = [round(float(x)) for x in parsed_path]

                if len(path) > 0:
                    path.append(path[0])  # to close the path
                logging.info("Computing path finished")
                
                # Convert list of vertices to a NumPy array for convenience
                vertices = np.array([(path[i], path[i+1]) for i in range(0, len(path)-1, 2)])
                x_coords = vertices[:, 0]
                y_coords = vertices[:, 1]

                # Get the rows and columns for pixels inside the polygon
                y_indices, z_indices = polygon(y_coords, x_coords)
                
                # Combine into a list of (x, y) pixel coordinates
                grah_scattergl_data = data.get_pixels_from_indices(slice_index, z_indices, y_indices)
                # grah_scattergl_data = pixels.iloc[:, :173].values

            else:
                logging.warning("Bug, the selected path is empty")
                return None
        else:
            logging.warning("Bug, the selected shape is not a mask or a path")
            return None
            
        if grah_scattergl_data is not None:
            l_expressions.append(grah_scattergl_data)
        
    return l_expressions

def differential_lipids(l_A, l_B):
    results = []
    # l_A and l_B are lists of numpy arrays, same amount of columns, different amount of rows
    # create 2 dataframes that stack the arrays
    A_df = pd.DataFrame(np.vstack(l_A), columns=data.get_available_lipids(1.0))
    B_df = pd.DataFrame(np.vstack(l_B), columns=data.get_available_lipids(11))
    meanA = A_df.mean(axis=0)
    meanB = B_df.mean(axis=0)
    log2fold_change = np.log2(meanB / (meanA + 1e-7)) # if meanA > 0 and meanB > 0 else np.nan
    
    for i, lip in enumerate(data.get_available_lipids(1.0)):
       
        # Wilcoxon test or t-test
        # try:
        _, p_value = mannwhitneyu(A_df[lip], B_df[lip], alternative='two-sided')
        # _, p_value = ttest_ind(A_df[lip], B_df[lip])
        # except ValueError:
        #     p_value = np.nan
    
        results.append({'lipid': lip, 'log2fold_change': log2fold_change.iloc[i], 'p_value': p_value})

    results_df = pd.DataFrame(results)

    # correct for multiple testing
    reject, pvals_corrected, _, _ = multipletests(results_df['p_value'].values, alpha=0.05, method='fdr_bh')
    results_df['p_value_corrected'] = pvals_corrected
    
    return results_df


# ==================================================================================================
# --- Layout
# ==================================================================================================

# Layout of the page
def return_layout(basic_config, slice_index=1):
    page = html.Div(
        style={
            "position": "absolute",
            "top": "0px",
            "right": "0px",
            "bottom": "0px",
            "left": "6rem",
            "background-color": "#1d1c1f",
            "overflow": "hidden",
        },
        children=[
            html.Div(
                className="fixed-aspect-ratio",
                style={
                    "background-color": "#1d1c1f",
                    "minHeight": "100vh",
                    "position": "relative",
                },
                children=[
                    dmc.Group(
                        children=dcc.Graph(
                            id="page-3-graph-heatmap-mz-selection",
                            config=basic_config
                            | {
                                "toImageButtonOptions": {
                                    "format": "png",
                                    "filename": "annotated_brain_slice",
                                    "scale": 2,
                                }
                            },
                            style={
                                "width": "77%",
                                "height": "100%",
                                "position": "absolute",
                                "left": "19em",
                                "top": "0",
                                "background-color": "#1d1c1f",
                            },
                            figure = figures.compute_rgb_image_per_lipid_selection(
                                        slice_index,
                                        ll_lipid_names=["SM 34:1;O2", None, None],
                                        cache_flask=cache_flask,
                                    ).update_layout(
                                        dragmode="drawclosedpath",
                                        newshape=dict(
                                            fillcolor=l_colors[0],
                                            opacity=0.7,
                                            line=dict(color="white", width=1),
                                        ),
                                        autosize=True,
                                    ),
                        ),
                    ),
                    dmc.Group(
                        direction="column",
                        spacing=0,
                        style={
                            "left": "1%",
                            "top": "1em",
                        },
                        class_name="position-absolute",
                        children=[
                            dmc.Text("Choose up to 3 lipids", size="lg"),
                            dmc.Group(
                                spacing="xs",
                                align="flex-start",
                                children=[
                                    dmc.MultiSelect(
                                        id="page-3-dropdown-lipids",
                                        data=data.return_lipid_options(),
                                        value=['SM 34:1;O2'],
                                        searchable=True,
                                        nothingFound="No lipid found",
                                        radius="md",
                                        size="xs",
                                        placeholder="Choose up to 3 lipids",
                                        clearable=False,
                                        maxSelectedValues=3,
                                        transitionDuration=150,
                                        transition="pop-top-left",
                                        transitionTimingFunction="ease",
                                        style={
                                            "width": "20em",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                    dmc.Text(
                        id="page-3-badge-input",
                        children="Colors: NA",
                        class_name="position-absolute",
                        style={"left": "1%", "top": "7em"},
                    ),
                    dmc.Badge(
                        id="page-3-badge-lipid-1",
                        children="name-lipid-1",
                        color="red",
                        variant="filled",
                        class_name="d-none",
                        style={"left": "1%", "top": "13em"},
                    ),
                    dmc.Badge(
                        id="page-3-badge-lipid-2",
                        children="name-lipid-2",
                        color="teal",
                        variant="filled",
                        class_name="d-none",
                        style={"left": "1%", "top": "15em"},
                    ),
                    dmc.Badge(
                        id="page-3-badge-lipid-3",
                        children="name-lipid-3",
                        color="blue",
                        variant="filled",
                        class_name="d-none",
                        style={"left": "1%", "top": "17em"},
                    ),
                    # First divider - IMMEDIATELY after badges
                    dmc.Divider(
                        style={
                            "width": "20em",
                            "left": "1%",
                            "top": "14em",  # EXACTLY where the last badge ends
                            "borderTopWidth": "2px",
                            "borderColor": "white",
                        },
                        class_name="position-absolute",
                    ),
                    # Switch - right after divider
                    dmc.Switch(
                        id="page-3-toggle-annotations",
                        label="Allen Brain Atlas Annotations",
                        checked=False,
                        color="cyan",
                        radius="xl",
                        size="sm",
                        style={
                            "left": "1%", 
                            "top": "15em"},
                        class_name="position-absolute",
                    ),
                    ## Brain regions dropdown - right after switch
                    dmc.Group(
                        direction="column",
                        spacing=0,
                        style={
                            "left": "1%",
                            "top": "17em",
                        },
                        class_name="position-absolute",
                        children=[
                            dmc.Text("Select brain regions", size="lg"),
                            dmc.Group(
                                spacing="xs",
                                align="flex-start",
                                children=[
                                    dmc.MultiSelect(
                                        id="page-3-dropdown-brain-regions",
                                        data=[
                                            {
                                                "label": atlas.dic_acronym_name[node],
                                                "value": atlas.dic_acronym_name[node],
                                            }
                                            for node in atlas.dic_existing_masks[slice_index]
                                        ],
                                        searchable=True,
                                        nothingFound="No structure found",
                                        radius="md",
                                        size="xs",
                                        placeholder="Select a brain region",
                                        clearable=False,
                                        maxSelectedValues=10,
                                        transitionDuration=150,
                                        transition="pop-top-left",
                                        transitionTimingFunction="ease",
                                        style={
                                            "width": "20em",
                                            "maxHeight": "6em",  # This sets the fixed height (23em - 17em = 6em)
                                            "overflowY": "auto"  # This enables vertical scrolling
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                    dmc.Text(
                        "... And draw a region on the brain",
                        size="lg",
                        color="cyan",
                        weight=500,
                        style={
                            "left": "1%",
                            "top": "23em",
                            "position": "absolute",
                        },
                    ),
                    # Second divider
                    dmc.Divider(
                        style={
                            "width": "20em",
                            "left": "1%",
                            "top": "28em",
                            "borderTopWidth": "2px",
                            "borderColor": "white",
                        },
                        class_name="position-absolute",
                    ),
                    # Group assignment section
                    dmc.Group(
                        direction="column",
                        spacing=0,
                        style={
                            "left": "1%",
                            "top": "29em",
                        },
                        class_name="position-absolute",
                        children=[
                            dmc.Text("Assign regions to groups:", size="lg"),
                            dmc.MultiSelect(
                                id="page-3-group-a-selector",
                                data=[],
                                placeholder="Select regions for Group A",
                                style={"width": "20em", "margin-top": "10px"},
                            ),
                            dmc.MultiSelect(
                                id="page-3-group-b-selector",
                                data=[],
                                placeholder="Select regions for Group B",
                                style={"width": "20em", "margin-top": "10px"},
                            ),
                        ],
                    ),
                    # Reset button at the bottom
                    dmc.Button(
                        children="Reset all regions",
                        id="page-3-reset-button",
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
                            "bottom": "3em",
                            "zIndex": 1000
                        },
                        class_name="position-absolute",
                    ),
                    dmc.Button(
                        children="Compute differential analysis",
                        id="page-3-button-compute-volcano",
                        variant="filled",
                        color="cyan",
                        radius="md",
                        size="xs",
                        disabled=True,
                        compact=False,
                        loading=False,
                        style={
                            "right": "1%",
                            "top": "3em",
                        },
                        class_name="position-absolute",
                    ),

                    dmc.Text(
                        "",
                        id="page-3-graph-hover-text",
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
                ],
            ),
            html.Div(
                children=[
                    dbc.Offcanvas(
                        id="page-4-drawer-region-selection",
                        backdrop=False,
                        placement="end",
                        style={
                            "width": "calc(100% - 6rem)",
                            "height": "100vh",  # Use viewport height
                            "background-color": "#1d1c1f",
                            "padding": "0",
                            "overflow": "hidden",  # Prevent scrolling
                        },
                        children=[
                            dbc.Card(
                                id="page-3-card-volcano",
                                style={
                                    "width": "100%",
                                    "height": "100%",
                                    "margin": "0",
                                    "background-color": "#1d1c1f",
                                },
                                children=[
                                    # Header with title and close button side by side
                                    dbc.CardHeader(
                                        className="d-flex justify-content-between align-items-center",
                                        style={
                                            "background-color": "#1d1c1f",
                                            "color": "white",
                                            "border": "none",
                                            "padding": "1rem",
                                        },
                                        children=[
                                            html.H3(
                                                "Differential analysis for current selection",
                                                style={
                                                    "margin": "0",
                                                    "color": "white",
                                                    "fontSize": "1.8rem",
                                                }
                                            ),
                                            dmc.Button(
                                                children="Close panel",
                                                id="page-4-close-drawer-region-selection",
                                                variant="filled",
                                                color="red",
                                                radius="md",
                                                size="md",
                                            ),
                                        ]
                                    ),
                                    # Body with fixed height and no scroll
                                    dbc.CardBody(
                                        className="loading-wrapper p-0",
                                        style={
                                            "background-color": "#1d1c1f",
                                        },
                                        children=[
                                            html.Div(
                                                style={
                                                    "height": "100%",
                                                    "width": "100%",
                                                    "position": "relative",
                                                    "overflow": "hidden",  # Prevent scrolling
                                                },
                                                children=[
                                                    # dbc.Spinner(
                                                    #     color="cyan",
                                                    #     type="grow",
                                                    dcc.Loading(
                                                        id="loading-volcano",
                                                        type="default",
                                                        children=[
                                                            # # Alerts
                                                            # html.Div(
                                                            #     className="px-5",
                                                            #     children=[
                                                            #         html.Div(
                                                            #             id="page-3-alert",
                                                            #             className="text-center my-5",
                                                            #             style={"display": "none"},
                                                            #             children=html.Strong(
                                                            #                 children="Please draw at least one region on the heatmap and click on 'compute differential analysis'.",
                                                            #                 style={"color": "#df5034"},
                                                            #             ),
                                                            #         ),
                                                            #         html.Div(
                                                            #             id="page-3-alert-2",
                                                            #             className="text-center my-2",
                                                            #             style={"display": "none"},
                                                            #             children=html.Strong(
                                                            #                 children="Too many regions selected, please reset the annotations.",
                                                            #                 style={"color": "#df5034"},
                                                            #             ),
                                                            #         ),
                                                            #     ],
                                                            # ),
                                                            # # Graph
                                                            # dcc.Graph(
                                                            #     id="page-3-graph-volcano",
                                                            #     style={
                                                            #         "height": "calc(100% - 2rem)",
                                                            #         "display": "none",
                                                            #     },
                                                            #     config=basic_config | {
                                                            #         "toImageButtonOptions": {
                                                            #             "format": "png",
                                                            #             "filename": "volcano_from_custom_region",
                                                            #             "scale": 2,
                                                            #         }
                                                            #     },
                                                            dcc.Graph(
                                                                id="page-3-graph-volcano",
                                                                style={
                                                                    "height": "calc(100vh - 8rem)",
                                                                    "width": "100%",
                                                                }
                                                            )
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className="px-5",
                                                        children=[
                                                            html.Div(
                                                                id="page-3-alert",
                                                                className="text-center my-5",
                                                                style={"display": "none"},
                                                                children=html.Strong(
                                                                    children="Please draw at least one region on the heatmap and click on 'compute differential analysis'.",
                                                                    style={"color": "#df5034"},
                                                                ),
                                                            ),
                                                            html.Div(
                                                                id="page-3-alert-2",
                                                                className="text-center my-2",
                                                                style={"display": "none"},
                                                                children=html.Strong(
                                                                    children="Too many regions selected, please reset the annotations.",
                                                                    style={"color": "#df5034"},
                                                                ),
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            dcc.Download(id="page-3-download-data"),
                        ],
                    ),
                ],
            )
        ],
    )

    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================


@app.callback(
    Output("page-3-graph-hover-text", "children"),
    Input("page-3-graph-heatmap-mz-selection", "hoverData"),
    Input("main-slider", "data"),
)
def page_3_hover(hoverData, slice_index):
    """This callback is used to update the text displayed when hovering over the slice image."""
    acronym_mask = data.acronyms_masks[slice_index]
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            x = hoverData["points"][0]["x"] # --> from 0 to 456
            y = hoverData["points"][0]["y"] # --> from 0 to 320
            # z = arr_z[y, x]
            try:
                return atlas.dic_acronym_name[acronym_mask[y, x]]
            except:
                return "Undefined"

    return dash.no_update


@app.callback(
    Output("page-3-graph-heatmap-mz-selection", "relayoutData"),
    Input("page-3-reset-button", "n_clicks"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def page_3_reset_layout(cliked_reset, url):
    """This callback is used to reset the layout of the heatmap when navigating to this page."""
    # print("\n============ page_3_reset_layout =============")
    return {}


@app.callback(
    Output("page-3-graph-heatmap-mz-selection", "figure"),
    Output("page-3-badge-input", "children"),
    Output("dcc-store-color-mask", "data"),
    Output("dcc-store-reset", "data"),
    Output("dcc-store-shapes-and-masks", "data"),

    Input("page-3-graph-heatmap-mz-selection", "relayoutData"),
    Input("main-slider", "data"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-dropdown-brain-regions", "value"),
    Input("url", "pathname"),
    Input("page-3-selected-lipid-1", "data"),
    Input("page-3-selected-lipid-2", "data"),
    Input("page-3-selected-lipid-3", "data"),
    Input("page-3-toggle-annotations", "checked"),
    
    State("dcc-store-color-mask", "data"),
    State("dcc-store-reset", "data"),
    State("dcc-store-shapes-and-masks", "data"),
    State("page-3-badge-input", "children"),
    prevent_initial_call=True,
)
def page_3_plot_heatmap(
    relayoutData,
    slice_index,
    cliked_reset,
    l_mask_name,
    url,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    annotations_checked,
    l_color_mask,
    reset,
    l_shapes_and_masks,
    graph_input,
):
    """This callback plots the heatmap of the selected lipid(s)."""
    # print("\n============ page_3_plot_heatmap =============")
    logging.info("Entering page_3_plot_heatmap")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    
    # Define overlay based on annotations toggle
    overlay = data.get_aba_contours(slice_index) if annotations_checked else None

    # If a lipid selection has been done
    if (
        id_input == "page-3-selected-lipid-1"
        or id_input == "page-3-selected-lipid-2"
        or id_input == "page-3-selected-lipid-3"
        or id_input == "page-3-colormap-button"
        or (
            (id_input == "main-slider")
            and graph_input == "Colors: "
        )
    ):
        if lipid_1_index >= 0 or lipid_2_index >= 0 or lipid_3_index >= 0:
            ll_lipid_names = [
                ' '.join([
                    data.get_annotations().iloc[index]["name"].split('_')[i] + ' ' 
                    + data.get_annotations().iloc[index]["structure"].split('_')[i] 
                    for i in range(len(data.get_annotations().iloc[index]["name"].split('_')))
                    ])
                if index != -1
                else None
                for index in [lipid_1_index, lipid_2_index, lipid_3_index]
            ]
            
            # Or if the current plot must be an RGB image
            if (
                id_input == "main-slider"
                and graph_input == "Colors: "
            ):
                fig = figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lipid_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    )
                fig.update_layout(
                    dragmode="drawclosedpath",
                    newshape=dict(
                        fillcolor=l_colors[0],
                        opacity=0.7,
                        line=dict(color="white", width=1),
                    ),
                    autosize=True,
                )
                return fig, "Colors: ", [], True, [],

            # Plot RBG By default
            else:
                logging.info("Right before calling the graphing function")
                fig = figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lipid_names,
                        cache_flask=cache_flask,
                        overlay=overlay,
                    )
                fig.update_layout(
                    dragmode="drawclosedpath",
                    newshape=dict(
                        fillcolor=l_colors[0],
                        opacity=0.7,
                        line=dict(color="white", width=1),
                    ),
                    autosize=True,
                )
                return fig, "Colors: ", [], True, []
        
        elif (
            id_input == "main-slider" and graph_input == "Colors: "
        ):
            fig = figures.compute_rgb_image_per_lipid_selection(
                    slice_index,
                    ll_lipid_names=["SM 34:1;O2", None, None],
                    cache_flask=cache_flask,
                    overlay=overlay,
                )
            fig.update_layout(
                dragmode="drawclosedpath",
                newshape=dict(
                    fillcolor=l_colors[0],
                    opacity=0.7,
                    line=dict(color="white", width=1),
                ),
                autosize=True,
            )
            return fig, "Colors: " + "SM 34:1;O2", [], True, []

        else:
            # No lipid has been selected
            fig = figures.compute_rgb_image_per_lipid_selection(
                    slice_index,
                    ll_lipid_names=["SM 34:1;O2", None, None],
                    cache_flask=cache_flask,
                    overlay=overlay,
                )
            fig.update_layout(
                dragmode="drawclosedpath",
                newshape=dict(
                    fillcolor=l_colors[0],
                    opacity=0.7,
                    line=dict(color="white", width=1),
                ),
                autosize=True,
            )
            return fig, "Colors: " + "SM 34:1;O2", [], True, []
    
    # ------------------------------------------------------------------------------------------------
    # If a new slice is loaded or the page just got loaded
    # do nothing because of automatic relayout of the heatmap which is automatically triggered when
    # the page is loaded
    if lipid_1_index >= 0 or lipid_2_index >= 0 or lipid_3_index >= 0:
        ll_lipid_names = [
            ' '.join([
                data.get_annotations().iloc[index]["name"].split('_')[i] + ' ' 
                + data.get_annotations().iloc[index]["structure"].split('_')[i] 
                for i in range(len(data.get_annotations().iloc[index]["name"].split('_')))
                ])
            if index != -1
            else None
            for index in [lipid_1_index, lipid_2_index, lipid_3_index]
        ]
    else:
        ll_lipid_names = ["SM 34:1;O2", None, None]
    
    # Drawing or selecting a brain region
    if (
        len(id_input) == 0
        or id_input == "page-3-reset-button"
        or id_input == "url"
    ):
        fig = figures.compute_rgb_image_per_lipid_selection(
                slice_index,
                ll_lipid_names=ll_lipid_names, # ["SM 34:1;O2", None, None],
                cache_flask=cache_flask,
                overlay=overlay,
            )
        fig.update_layout(
            dragmode="drawclosedpath",
            newshape=dict(
                fillcolor=l_colors[0],
                opacity=0.7,
                line=dict(color="white", width=1),
            ),
            autosize=True,
        )
        return fig, "Colors: ", [], True, []

    # Fix bug with automatic relayout
    if value_input == "relayoutData" and relayoutData == {"autosize": True}:
        return dash.no_update

    # Handle annotations toggle separately to preserve shapes
    if id_input == "page-3-toggle-annotations":
        fig = figures.compute_rgb_image_per_lipid_selection(
            slice_index,
            ll_lipid_names=ll_lipid_names,
            cache_flask=cache_flask,
            overlay=overlay,
        )
        
        # Preserve existing shapes and layout settings
        if relayoutData and "shapes" in relayoutData:
            fig.update_layout(shapes=relayoutData["shapes"])
        
        # Preserve existing color masks
        if l_shapes_and_masks:
            for shape_or_mask in l_shapes_and_masks:
                if shape_or_mask[0] == "mask":
                    mask_name = shape_or_mask[1]
                    base64_string = shape_or_mask[2]
                    fig.add_trace(
                        go.Image(visible=True, source=base64_string, hoverinfo="skip")
                    )
        
        fig.update_layout(
            dragmode="drawclosedpath",
            newshape=dict(
                fillcolor=l_colors[len(l_shapes_and_masks) % 7] if l_shapes_and_masks else l_colors[0],
                opacity=0.7,
                line=dict(color="white", width=1),
            ),
            autosize=True,
        )
        return fig, graph_input, l_color_mask, False, l_shapes_and_masks

    # Fix other bug with automatic dropdown selection
    if (
        id_input == "page-3-dropdown-brain-regions"
        and relayoutData is None
        and cliked_reset is None
        and (l_mask_name is None or len(l_mask_name) == 0)
    ):
        fig = figures.compute_rgb_image_per_lipid_selection(
                slice_index,
                ll_lipid_names=ll_lipid_names, # ["SM 34:1;O2", None, None],
                cache_flask=cache_flask,
                overlay=overlay,
            )
        fig.update_layout(
            dragmode="drawclosedpath",
            newshape=dict(
                fillcolor=l_colors[0],
                opacity=0.7,
                line=dict(color="white", width=1),
            ),
            autosize=True,
        )
        return fig, "Colors: ", [], True, []

    # If the user selected a new mask or drew on the plot
    if id_input == "page-3-graph-heatmap-mz-selection" or id_input == "page-3-dropdown-brain-regions":
        # Check that a mask has actually been selected
        if l_mask_name is not None or relayoutData is not None:
            # Rebuild figure
            fig = figures.compute_rgb_image_per_lipid_selection(
                slice_index,
                ll_lipid_names=ll_lipid_names, # ["SM 34:1;O2", None, None],
                cache_flask=cache_flask,
                overlay=overlay,
            )
            color_idx = None
            col_next = None
            if l_mask_name is not None:
                # If a mask has been selected
                if len(l_mask_name) > 0:
                    for idx_mask, mask_name in enumerate(l_mask_name):
                        id_name = atlas.dic_name_acronym[mask_name]
                        if id_name in atlas.dic_existing_masks[slice_index]:
                            descendants = atlas.bg_atlas.get_structure_descendants(id_name)

                            acronym_mask = data.acronyms_masks[slice_index]
                            mask2D = np.isin(acronym_mask, descendants + [id_name])
                        else:
                            logging.warning("The mask " + str(mask_name) + " couldn't be found")

                        if idx_mask < len(l_color_mask):
                            color_rgb = l_color_mask[idx_mask]
                        else:
                            color_idx = len(l_color_mask)
                            if relayoutData is not None:
                                if "shapes" in relayoutData:
                                    color_idx += len(relayoutData["shapes"])
                            color = config.l_colors[color_idx % 7][1:]
                            color_rgb = [int(color[i : i + 2], 16) for i in (0, 2, 4)] + [255]
                            l_color_mask.append(color_rgb)

                        l_images = [
                            mask2D * color
                            # normalized_projected_mask * color
                            for c, color in zip(["r", "g", "b", "a"], color_rgb)
                        ]
                        
                        # Reoder axis to match plotly go.image requirements
                        array_image = np.moveaxis(np.array(l_images, dtype=np.uint8), 0, 2)

                        # Convert image to string to save space (new image as each mask must have a
                        # different color)
                        base64_string = convert_image_to_base64(
                            array_image, optimize=True, format="webp", type="RGBA"
                        )
                        fig.add_trace(
                            go.Image(visible=True, source=base64_string, hoverinfo="skip")
                        )
                        fig.update_layout(
                            dragmode="drawclosedpath",
                        )

                        if id_input == "page-3-dropdown-brain-regions" and color_idx is not None:
                            # Save in l_shapes_and_masks
                            l_shapes_and_masks.append(["mask", mask_name, base64_string, color_idx])

            # If a region has been drawn by the user
            if relayoutData is not None:
                if "shapes" in relayoutData:
                    if len(relayoutData["shapes"]) > 0:
                        if not reset or value_input == "relayoutData":
                            if "path" in relayoutData["shapes"][-1]:
                                fig["layout"]["shapes"] = relayoutData["shapes"]  #
                                col_next = config.l_colors[
                                    (len(relayoutData["shapes"]) + len(l_color_mask)) % 7
                                ]

                                # compute color and save in l_shapes_and_masks
                                if id_input == "page-3-graph-heatmap-mz-selection":
                                    color_idx_for_registration = len(l_color_mask)
                                    if relayoutData is not None:
                                        if "shapes" in relayoutData:
                                            color_idx_for_registration += len(
                                                relayoutData["shapes"]
                                            )
                                    l_shapes_and_masks.append(
                                        [
                                            "shape",
                                            f"Shape {color_idx_for_registration - 1}",
                                            relayoutData["shapes"][-1],
                                            color_idx_for_registration - 1,
                                        ]
                                    )
            # Update col_next
            if color_idx is not None and col_next is None:
                col_next = config.l_colors[(color_idx + 1) % 7]
            elif col_next is None:
                col_next = config.l_colors[0]
            fig.update_layout(
                dragmode="drawclosedpath",
                newshape=dict(
                    fillcolor=col_next,
                    opacity=0.7,
                    line=dict(color="white", width=1),
                ),
            )

            # Update drag mode
            if relayoutData is not None:
                if "shapes" in relayoutData:
                    if len(relayoutData["shapes"]) + len(l_color_mask) > 10:
                        fig.update_layout(dragmode=False)
            if len(l_color_mask) > 10:
                fig.update_layout(dragmode=False)

            # Return figure and corresponding data
            return fig, "Colors: ", l_color_mask, False, l_shapes_and_masks

    # either graph is already here
    return dash.no_update

@app.callback(
    Output("page-3-badge-lipid-1", "children"),
    Output("page-3-badge-lipid-2", "children"),
    Output("page-3-badge-lipid-3", "children"),
    Output("page-3-selected-lipid-1", "data"),
    Output("page-3-selected-lipid-2", "data"),
    Output("page-3-selected-lipid-3", "data"),
    Output("page-3-badge-lipid-1", "class_name"),
    Output("page-3-badge-lipid-2", "class_name"),
    Output("page-3-badge-lipid-3", "class_name"),

    Input("page-3-dropdown-lipids", "value"),
    Input("page-3-badge-lipid-1", "class_name"),
    Input("page-3-badge-lipid-2", "class_name"),
    Input("page-3-badge-lipid-3", "class_name"),
    Input("main-slider", "data"),

    State("page-3-selected-lipid-1", "data"),
    State("page-3-selected-lipid-2", "data"),
    State("page-3-selected-lipid-3", "data"),
    State("page-3-badge-lipid-1", "children"),
    State("page-3-badge-lipid-2", "children"),
    State("page-3-badge-lipid-3", "children"),
)
def page_3_add_toast_selection(
    l_lipid_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    header_1,
    header_2,
    header_3,
):
    """This callback adds the selected lipid to the selection."""
    logging.info("Entering function to update lipid data")
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    # if page-3-dropdown-lipids is called while there's no lipid name defined, it means the page
    # just got loaded
    if len(id_input) == 0 or (id_input == "page-3-dropdown-lipids" and l_lipid_names is None):
        # Initialize with SM 34:1;O2 as the default lipid
        default_lipid = "SM 34:1;O2"
        # Find lipid location for the default lipid
        name, structure = default_lipid.split(" ")
        l_lipid_loc = (
            data.get_annotations()
            .index[
                (data.get_annotations()["name"] == name)
                & (data.get_annotations()["structure"] == structure)
                & (data.get_annotations()["slice"] == slice_index)
            ]
            .tolist()
        )
        
        # If no match for current slice, try to find it in any slice
        if len(l_lipid_loc) == 0:
            l_lipid_loc = (
                data.get_annotations()
                .index[
                    (data.get_annotations()["name"] == name)
                    & (data.get_annotations()["structure"] == structure)
                ]
                .tolist()
            )[:1]
        
        # Set default lipid if found
        if len(l_lipid_loc) > 0:
            lipid_1_index = l_lipid_loc[0]
            header_1 = default_lipid
            class_name_badge_1 = "position-absolute"
            return header_1, "", "", lipid_1_index, -1, -1, class_name_badge_1, "d-none", "d-none"
        else:
            # Fallback if lipid not found
            return "", "", "", -1, -1, -1, "d-none", "d-none", "d-none", # None

    # If one or several lipids have been deleted
    if l_lipid_names is not None:
        if len(l_lipid_names) < len(
            [x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x != -1]
        ):
            logging.info("One or several lipids have been deleter. Cleaning lipid badges now.")
            for idx_header, header in enumerate([header_1, header_2, header_3]):
                found = False
                for lipid_name in l_lipid_names:
                    if lipid_name == header:
                        found = True
                if not found:
                    if idx_header == 0:
                        header_1 = ""
                        lipid_1_index = -1
                        class_name_badge_1 = "d-none"
                    if idx_header == 1:
                        header_2 = ""
                        lipid_2_index = -1
                        class_name_badge_2 = "d-none"
                    if idx_header == 2:
                        header_3 = ""
                        lipid_3_index = -1
                        class_name_badge_3 = "d-none"

            return (
                header_1,
                header_2,
                header_3,
                lipid_1_index,
                lipid_2_index,
                lipid_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
            )

    # Otherwise, update selection or add lipid
    if (
        id_input == "page-3-dropdown-lipids" and l_lipid_names is not None
    ) or id_input == "main-slider":
        # If a new slice has been selected
        if id_input == "main-slider":
            for header in [header_1, header_2, header_3]:
                # if len(header) > 1:
                if len(header.split(" ")) == 2:
                    name, structure = header.split(" ")
                else:   
                    name = "_".join(header.split(" ")[::2])
                    structure = "_".join(header.split(" ")[1::2])
                # Find lipid location
                l_lipid_loc_temp = (
                    data.get_annotations()
                    .index[
                        (data.get_annotations()["name"] == name)
                        & (data.get_annotations()["structure"] == structure)
                    ]
                    .tolist()
                )
                l_lipid_loc = [
                    l_lipid_loc_temp[i]
                    for i, x in enumerate(
                        data.get_annotations().iloc[l_lipid_loc_temp]["slice"] == slice_index
                    )
                    if x
                ]
                # Record location and lipid name
                lipid_index = l_lipid_loc[0] if len(l_lipid_loc) > 0 else -1

                # If lipid has already been selected before, replace the index
                if header_1 == header:
                    lipid_1_index = lipid_index
                elif header_2 == header:
                    lipid_2_index = lipid_index
                elif header_3 == header:
                    lipid_3_index = lipid_index

            logging.info("Returning updated lipid data")
            return (
                header_1,
                header_2,
                header_3,
                lipid_1_index,
                lipid_2_index,
                lipid_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
                # None,
            )

        # If lipids have been added from dropdown menu
        elif id_input == "page-3-dropdown-lipids":
            if len(l_lipid_names[-1]) == 2:
                name, structure = l_lipid_names[-1].split(" ")
            else:   
                name = "_".join(l_lipid_names[-1].split(" ")[::2])
                structure = "_".join(l_lipid_names[-1].split(" ")[1::2])
            # Find lipid location
            l_lipid_loc = (
                data.get_annotations()
                .index[
                    (data.get_annotations()["name"] == name)
                    & (data.get_annotations()["structure"] == structure)
                    & (data.get_annotations()["slice"] == slice_index)
                ]
                .tolist()
            )
            
            # If several lipids correspond to the selection, we have a problem...
            if len(l_lipid_loc) > 1:
                logging.warning("More than one lipid corresponds to the selection")
                l_lipid_loc = [l_lipid_loc[-1]]

            if len(l_lipid_loc) < 1:
                logging.warning("No lipid annotation exist. Taking another slice annotation")
                l_lipid_loc = (
                    data.get_annotations()
                    .index[
                        (data.get_annotations()["name"] == name)
                        & (data.get_annotations()["structure"] == structure)
                    ]
                    .tolist()
                )[:1]
                # return dash.no_update

            # Record location and lipid name
            lipid_index = l_lipid_loc[0]
            lipid_string = l_lipid_names[-1]

            change_made = False

            # If lipid has already been selected before, replace the index
            if header_1 == lipid_string:
                lipid_1_index = lipid_index
                change_made = True
            elif header_2 == lipid_string:
                lipid_2_index = lipid_index
                change_made = True
            elif header_3 == lipid_string:
                lipid_3_index = lipid_index
                change_made = True

            # If it's a new lipid selection, fill the first available header
            if lipid_string not in [header_1, header_2, header_2]:
                # Check first slot available
                if class_name_badge_1 == "d-none":
                    header_1 = lipid_string
                    lipid_1_index = lipid_index
                    class_name_badge_1 = "position-absolute"
                elif class_name_badge_2 == "d-none":
                    header_2 = lipid_string
                    lipid_2_index = lipid_index
                    class_name_badge_2 = "position-absolute"
                elif class_name_badge_3 == "d-none":
                    header_3 = lipid_string
                    lipid_3_index = lipid_index
                    class_name_badge_3 = "position-absolute"
                else:
                    logging.warning("More than 3 lipids have been selected")
                    return dash.no_update
                change_made = True

            if change_made:
                logging.info(
                    "Changes have been made to the lipid selection or indexation,"
                    + " propagating callback."
                )
                return (
                    header_1,
                    header_2,
                    header_3,
                    lipid_1_index,
                    lipid_2_index,
                    lipid_3_index,
                    class_name_badge_1,
                    class_name_badge_2,
                    class_name_badge_3,
                    # None,
                )
            else:
                return dash.no_update

    return dash.no_update

@app.callback(
    Output("page-3-dropdown-brain-regions", "data"),
    Input("main-slider", "data"),
)
def page_3_update_dropdown_option(slice_index):
    """This callback updates the dropdown options for the brain regions."""

    if slice_index is not None:
        return [
            {"label": atlas.dic_acronym_name[node], "value": atlas.dic_acronym_name[node]}
            for node in atlas.dic_existing_masks[slice_index]
        ]
    else:
        return dash.no_update

@app.callback(
    Output("page-3-dropdown-brain-regions", "disabled"),
    Input("page-3-dropdown-brain-regions", "value"),
    Input("page-3-reset-button", "n_clicks"),
    prevent_initial_call=True,
)
def page_3_disable_dropdown(l_selection, clicked_reset): 
    """This callback disables the dropdown options for the brain regions if more than five regions
    have already been selected."""

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-3-reset-button":
        return False

    if l_selection is not None:
        if len(l_selection) > 0 and len(l_selection) < 11:  # Changed from 4 to 5
            return False
        elif len(l_selection) >= 11:  # Changed from 4 to 5
            return True
    return dash.no_update


@app.callback(
    Output("page-3-dropdown-brain-regions", "value"),
    Input("page-3-reset-button", "n_clicks"),
    Input("main-slider", "data"),
    prevent_initial_call=True,
)
def page_3_empty_dropdown(clicked_reset, slice_index): # 
    """This callback empties the dropdown options for the brain regions when clicking reset or
    changing slice."""
    return []


@app.callback(
    Output("page-3-button-compute-volcano", "disabled"),
    Input("page-3-graph-heatmap-mz-selection", "relayoutData"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-dropdown-brain-regions", "value"),
    prevent_initial_call=True,
)
def page_3_button_compute_volcano(relayoutData, clicked_reset, mask):
    """This callback disables the button to compute volcano plot if no region has been selected or
    drawn."""
    # print("\n============ page_3_button_compute_volcano =============")
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    
    # In case of reset, disable button
    if id_input == "page-3-reset-button":
        return True

    # If at least one mask, activate button
    if mask is not None:
        if mask != []:
            return False

    # If at least one drawn shape, activate button
    if relayoutData is not None:
        if "shapes" in relayoutData:
            if len(relayoutData["shapes"]) > 0:
                return False

    return True

@app.callback(
    Output("page-3-graph-volcano", "style"),
    Output("page-3-alert-2", "style"),
    # Output("page-3-graph-heatmap-per-lipid", "style"),

    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-button-compute-volcano", "n_clicks"),
    State("page-3-dropdown-brain-regions", "value"),
    State("page-3-graph-heatmap-mz-selection", "relayoutData"),
    prevent_initial_call=True,
)
def page_3_display_volcano(clicked_reset, clicked_compute, mask, relayoutData):
    """This callback displays the volcano plot when clicking on the compute volcano button
    (and hide the corresponding alert)."""
    # print("\n============ page_3_display_volcano =============")
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # If reset button has been clicked, hide all plot
    if id_input == "page-3-reset-button":
        return {"display": "none"}, {"display": "none"} # , {"display": "none"}

    # If the button to compute volcano has been clicked, display the plots
    elif id_input == "page-3-button-compute-volcano":
        logging.info("Compute volcano button has been clicked")

        # If at least one mask, display the plots
        if mask is not None:
            if mask != []:
                logging.info("One or several masks have been selected, displaying graphs")
                return (
                    {"height": "calc(100vh - 8rem)", "display": "block"}, # HEIGHT_PLOTS*5},
                    {"display": "none"},
                    # {
                    #     "height": 2 * HEIGHT_PLOTS,
                    #     "background-color": "#1d1c1f",
                    # },
                )

        # If at least one drawn region, display the plots
        if relayoutData is not None:
            if "shapes" in relayoutData:
                if len(relayoutData["shapes"]) > 0:
                    logging.info("One or several shapes have been selected, displaying graphs")
                    return (
                        {"height": "calc(100vh - 8rem)", "display": "block"}, # HEIGHT_PLOTS*5},
                        {"display": "none"},
                    )

    return dash.no_update

@app.callback(
    Output("dcc-store-list-volcano-A", "data"),
    Output("dcc-store-list-volcano-B", "data"),
    
    Input("page-3-button-compute-volcano", "n_clicks"),
    Input("page-3-dcc-store-path-heatmap", "data"),
    Input("page-3-reset-button", "n_clicks"),
    Input("url", "pathname"),
    Input("main-slider", "data"),
    State("page-3-dropdown-brain-regions", "value"),
    # State("dcc-store-shapes-and-masks", "data"),
    State("dcc-store-shapes-and-masks-A", "data"),
    State("dcc-store-shapes-and-masks-B", "data"),
    State("page-3-graph-heatmap-mz-selection", "relayoutData"),
    State("session-id", "data"),
    prevent_initial_call=True,
)
def page_3_record_volcano(
    clicked_compute,
    l_paths,
    cliked_reset,
    url,
    slice_index,
    l_mask_name,
    # l_shapes_and_masks,
    l_shapes_and_masks_A,
    l_shapes_and_masks_B,
    relayoutData,
    session_id,
):
    """This callback is used to compute and record the lipids' expression of the selected
    region(s)."""
    # print("\n============ page_3_record_volcano =============")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    
    # If a new slice is loaded or the page just got loaded, do nothing because
    # of automatic relayout of the heatmap which is automatically triggered when the page is loaded
    if len(id_input) == 0 or (value_input == "relayoutData" and relayoutData == {"autosize": True}):
        return dash.no_update

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button": # or id_input == "url":
        return [], []

    # If the user clicked on the button after drawing a region and/or selecting a structure
    elif id_input == "page-3-button-compute-volcano" and len(l_shapes_and_masks_A) > 0 and len(l_shapes_and_masks_B) > 0:
        logging.info("Starting to compute volcano plot")

        l_expressions_A = global_store(
            slice_index, l_shapes_and_masks_A
        )
        l_expressions_B = global_store(
            slice_index, l_shapes_and_masks_B
        )
        print(len(l_expressions_A))
        print(len(l_expressions_B))

        if l_expressions_A is not None and l_expressions_B is not None:
            if l_expressions_A != [] and l_expressions_B != []:
                logging.info("Volcano plot computed, returning it now")
                # Return a dummy variable to indicate that the volcano plot has been computed and
                # trigger the callback
                return l_expressions_A, l_expressions_B # "A ok", "B ok"
        logging.warning("A bug appeared during volcano plot computation")

    return [], []


@app.callback(
    Output("page-3-graph-volcano", "figure"),

    Input("page-3-reset-button", "n_clicks"),
    Input("dcc-store-list-volcano-A", "data"),
    Input("dcc-store-list-volcano-B", "data"),
    Input("main-slider", "data"),
    
    State("page-3-dropdown-brain-regions", "value"),
    State("dcc-store-shapes-and-masks-A", "data"),
    State("dcc-store-shapes-and-masks-B", "data"),
    State("page-3-graph-heatmap-mz-selection", "relayoutData"),
    prevent_initial_call=True,
)
def page_3_plot_volcano(
    cliked_reset,
    l_expressions_A,
    l_expressions_B,
    slice_index,
    l_mask_name,
    l_shapes_and_masks_A,
    l_shapes_and_masks_B,
    relayoutData,
):
    """This callback is used to plot the volcano plot of the selected region(s)."""
    # print("\n============ page_3_plot_volcano =============")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # If a new slice is loaded or the page just got loaded, do nothing
    if len(id_input) == 0:
        return dash.no_update

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button" or l_expressions_A is None or l_expressions_A == [] or l_expressions_B is None or l_expressions_B == []:
        return go.Figure().update_layout(template="plotly_dark") # figures.return_empty_spectrum()

    # Do nothing if l_expressions is None or []
    elif id_input == "dcc-store-list-volcano-A" or id_input == "dcc-store-list-volcano-B":
        if len(l_expressions_A) > 0 or l_expressions_A == "ok" or len(l_expressions_B) > 0 or l_expressions_B == "ok":
            logging.info("Starting volcano plotting now")
            # l_expressions_A = global_store(
            #     slice_index, l_shapes_and_masks_A
            # )
            # l_expressions_B = global_store(
            #     slice_index, l_shapes_and_masks_B
            # )
            
            # Compute differential lipids
            difflips = differential_lipids(l_expressions_A, l_expressions_B)

            colors = pd.read_hdf("./data/annotations/lipidclasscolors.h5ad", key="table")
            colors.loc['PA'] = {'count': 0, 'classcolors': '#D3D3D3'}
            colors.loc['LPA'] = {'count': 0, 'classcolors': '#D3D3D3'}

            fc_cutoff = 0.2
            pvalue_cutoff = 0.01

            min_pval = np.min(difflips[difflips['p_value_corrected'] > 0]['p_value_corrected'])
            difflips['p_value_corrected'] = np.clip(difflips['p_value_corrected'], min_pval, 1)
            difflips['minus_log10_p'] = -np.log10(difflips['p_value_corrected'])

            # Compute the actual fold change from log2 fold change
            difflips['fold_change'] = 2 ** difflips['log2fold_change']

            # Extract the lipid family (assuming it is the first word in the lipid name)
            difflips['lipid_family'] = difflips['lipid'].apply(lambda x: x.split(' ')[0])

            # Compute marker size: smaller for non-significant points, larger for significant points
            difflips['marker_size'] = np.where(
                (difflips['log2fold_change'] > -fc_cutoff) & (difflips['log2fold_change'] < fc_cutoff),
                3,   # smaller size for non-significant points
                10   # larger size for significant points
            )

            # Custom color mapping based on lipid family
            lipid_to_color = colors['classcolors'].to_dict()
            custom_color_map = {family: color for family, color in lipid_to_color.items()}

            # Create figure
            fig = go.Figure()

            # Add scatter plot for each lipid family
            for family in difflips['lipid_family'].unique():
                mask = difflips['lipid_family'] == family
                fig.add_trace(
                    go.Scatter(
                        x=difflips[mask]['log2fold_change'],
                        y=difflips[mask]['minus_log10_p'],
                        mode='markers',
                        name=family,
                        marker=dict(
                            size=difflips[mask]['marker_size'],
                            color=custom_color_map[family],
                            line=dict(width=0)
                        ),
                        customdata=np.column_stack((
                            difflips[mask]['lipid'],
                            difflips[mask]['p_value_corrected'],
                            difflips[mask]['fold_change']
                        )),
                        hovertemplate='Lipid: %{customdata[0]}'
                        # hovertemplate='Lipid: %{customdata[0]}<br>p-value: %{customdata[1]:.2e}<br>Fold Change: %{customdata[2]:.3f}<extra></extra>'
                    )
                )

            # Add vertical lines for fold change cutoffs
            fig.add_vline(x=-fc_cutoff, line_dash="dash", line_color="grey", line_width=1)
            fig.add_vline(x=fc_cutoff, line_dash="dash", line_color="grey", line_width=1)

            # Add horizontal line for significance threshold
            sig_y = -np.log10(pvalue_cutoff)
            fig.add_hline(y=sig_y, line_dash="dash", line_color="grey", line_width=1)

            # range_x_axis = [min(difflips['log2fold_change']) - 0.1, max(difflips['log2fold_change']) + 0.1]
            # range_y_axis = [0, max(difflips['minus_log10_p']) + 50]

            # Update layout
            fig.update_layout(
                showlegend=True,
                legend_title_text='Lipid Family',
                xaxis_title='Log₂(Fold Change), where Fold Change = <sup>Mean Intensity in Group B</sup> / <sub>Mean Intensity in Group A</sub>',
                yaxis_title='-Log₁₀(p-Value)',
                xaxis=dict(
                    # range=range_x_axis,
                    showspikes=True,
                    spikemode='toaxis',
                    spikesnap='cursor',
                    spikethickness=1,
                    spikedash='dot'
                ),
                yaxis=dict(
                    # range=range_y_axis,
                    showspikes=True,
                    spikemode='toaxis',
                    spikesnap='cursor',
                    spikethickness=1,
                    spikedash='dot'
                ),
                hovermode='closest',
                template="plotly_dark",
                margin=dict(l=50, r=50, t=30, b=70, pad=5),  # Reduce margins
                autosize=True,  # Allow the plot to resize with container
            )

            fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
            fig.layout.paper_bgcolor = "rgba(0,0,0,0)"

            logging.info("Volcano plotted. Returning it now")

            # Return dummy variable for ll_idx_labels to confirm that it has been computed
            # # save the figure in the working directory
            # fig.write_html("volcano.html")
            return fig

    return dash.no_update

@app.callback(
    Output("page-4-drawer-region-selection", "is_open"),
    Input("page-3-button-compute-volcano", "n_clicks"),
    Input("page-4-close-drawer-region-selection", "n_clicks"),
    State("page-4-drawer-region-selection", "is_open"),
)
def toggle_offcanvas(n1, n2, is_open): #  
    """This callback is used to open the drawer containing the lipid expression analysis of the
    selected region."""
    if n1 or n2: #  
        return not is_open
    return is_open

@app.callback(
    Output("page-3-group-a-selector", "data"),
    Output("page-3-group-b-selector", "data"),
    Output("page-3-group-a-selector", "value"),
    Output("page-3-group-b-selector", "value"),

    Input("dcc-store-shapes-and-masks", "data"),
    Input("page-3-group-a-selector", "value"),
    Input("page-3-group-b-selector", "value"),
    State("page-3-group-a-selector", "data"),
    State("page-3-group-b-selector", "data"),
)
def update_group_selectors(
    l_shapes_and_masks,
    group_a_selected,
    group_b_selected,
    current_a_data,
    current_b_data,
):
    # print("\n============ update_group_selectors =============")
    # Find which input triggered the callback
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # When no shapes have been drawn or selected yet, reset everything
    if not l_shapes_and_masks:
        return [], [], None, None
    
    # Generate base options
    options = []
    for i, shape in enumerate(l_shapes_and_masks):
        label = shape[1]
        # if shape[0] == "mask":
        #     label = f"Mask: {shape[1]}"
        # else:
        #     label = f"Shape {i+1}"
        options.append({"label": label, "value": i})
    
    # If triggered by selection change, update available options
    if trigger_id in ["page-3-group-a-selector", "page-3-group-b-selector"]:
        group_a_selected = group_a_selected or []
        group_b_selected = group_b_selected or []
        
        # Filter options for each group
        options_a = [opt for opt in options if opt["value"] not in group_b_selected]
        options_b = [opt for opt in options if opt["value"] not in group_a_selected]
        
        return options_a, options_b, group_a_selected, group_b_selected
    
    # Initial load or shapes/masks update
    return options, options, group_a_selected, group_b_selected

@app.callback(
    Output("dcc-store-shapes-and-masks-A", "data"),
    Output("dcc-store-shapes-and-masks-B", "data"),
    
    Input("page-3-group-a-selector", "value"),
    Input("page-3-group-b-selector", "value"),
    State("dcc-store-shapes-and-masks", "data"),
)
def partition_shapes(
    group_a_values,
    group_b_values,
    l_shapes_and_masks,
):
    # print("\n============ partition_shapes =============")
    trigger_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    if l_shapes_and_masks is None:
        return dash.no_update, dash.no_update

    # Convert selections to sets for easier processing
    group_a_values = set(group_a_values or [])
    group_b_values = set(group_b_values or [])
    
    # No need to handle conflicts since they're prevented by the selector options
    shapes_group_A = [l_shapes_and_masks[i] for i in sorted(list(group_a_values))]
    shapes_group_B = [l_shapes_and_masks[i] for i in sorted(list(group_b_values))]
    
    # Add unassigned shapes to Group A
    assigned = group_a_values.union(group_b_values)
    for i in range(len(l_shapes_and_masks)):
        if i not in assigned:
            shapes_group_A.append(l_shapes_and_masks[i])
    
    return shapes_group_A, shapes_group_B

# clientside_callback(
#     """
#     function(n_clicks){
#         if(n_clicks > 0){
#             domtoimage.toBlob(document.getElementById('page-3-graph-heatmap-per-lipid'))
#                 .then(function (blob) {
#                     window.saveAs(blob, 'heatmap_comparison.png');
#                 }
#             );
#         }
#     }
#     """,
#     Output("page-3-download-heatmap-button", "n_clicks"),
#     Input("page-3-download-heatmap-button", "n_clicks"),
# )
# """This clientside callback allows to download the main heatmap as a png file."""

# clientside_callback(
#     """
#     function(n_clicks){
#         if(n_clicks > 0){
#             domtoimage.toBlob(document.getElementById('page-3-div-graph-lipid-comparison'))
#                 .then(function (blob) {
#                     window.saveAs(blob, 'plot_region_selection.png');
#                 }
#             );
#         }
#     }
#     """,
#     Output("page-3-download-plot-button", "n_clicks"),
#     Input("page-3-download-plot-button", "n_clicks"),
# )
# """This clientside callback allows to download the heatmap used to show differential lipid 
# expression in the selected regions as a png file."""