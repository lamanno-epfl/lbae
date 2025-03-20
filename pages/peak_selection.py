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

# LBAE imports
from app import app, peak_figures, peak_data, cache_flask

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
            },
            children=[
                html.Div(
                    className="fixed-aspect-ratio",
                    style={
                        "background-color": "#1d1c1f",
                    },
                    children=[
                        dbc.Spinner(
                            color="info",
                            spinner_style={
                                "margin-top": "40%",
                                "width": "3rem",
                                "height": "3rem",
                            },
                            children=dcc.Graph(
                                id="page-peak-graph-heatmap-mz-selection",
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
                                    "width": "95%",
                                    "height": "95%",
                                    "position": "absolute",
                                    "left": "0",
                                    "top": "0",
                                    "background-color": "#1d1c1f",
                                },
                                figure=peak_figures.compute_heatmap_per_lipid(
                                    slice_index,
                                    '1000.169719',
                                    cache_flask=cache_flask,
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
                                dmc.Text("Choose up to 3 peaks", size="lg"),
                                dmc.Group(
                                    spacing="xs",
                                    align="flex-start",
                                    children=[
                                        dmc.MultiSelect(
                                            id="page-peak-dropdown-lps",
                                            data=peak_data.return_peak_options(),
                                            value=['1000.169719'],
                                            searchable=True,
                                            nothingFound="No peak found",
                                            radius="md",
                                            size="xs",
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
                                        dmc.Button(
                                            children="Display as RGB",
                                            id="page-peak-rgb-button",
                                            variant="filled",
                                            color="cyan",
                                            radius="md",
                                            size="xs",
                                            disabled=True,
                                            compact=False,
                                            loading=False,
                                        ),
                                        dmc.Button(
                                            children="Display as colormap",
                                            id="page-peak-colormap-button",
                                            variant="filled",
                                            color="cyan",
                                            radius="md",
                                            size="xs",
                                            disabled=True,
                                            compact=False,
                                            loading=False,
                                        ),
                                        dmc.Button(
                                            children="Show section mass spectrum",
                                            id="page-peak-show-spectrum-button",
                                            variant="filled",
                                            color="cyan",
                                            radius="md",
                                            size="xs",
                                            disabled=False,
                                            compact=False,
                                            loading=False,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        dmc.Text(
                            id="page-peak-badge-input",
                            children="Current input: ",  #  + "m/z boundaries",
                            class_name="position-absolute",
                            style={"right": "1%", "top": "1em"},
                        ),
                        dmc.Badge(
                            id="page-peak-badge-lp-1",
                            children="name-lp-1",
                            color="red",
                            variant="filled",
                            class_name="d-none",
                            style={"right": "1%", "top": "4em"},
                        ),
                        dmc.Text(
                            id="page-peak-annotation-lp-1",
                            children="",
                            class_name="d-none",
                            style={"right": "calc(1% + 120px)", "top": "3.7em", "font-style": "italic", "font-size": "0.85rem", "line-height": "1.8", "text-align": "right"},
                        ),
                        dmc.Badge(
                            id="page-peak-badge-lp-2",
                            children="name-lp-2",
                            color="teal",
                            variant="filled",
                            class_name="d-none",
                            style={"right": "1%", "top": "6em"},
                        ),
                        dmc.Text(
                            id="page-peak-annotation-lp-2",
                            children="",
                            class_name="d-none",
                            style={"right": "calc(1% + 120px)", "top": "5.7em", "font-style": "italic", "font-size": "0.85rem", "line-height": "1.8", "text-align": "right"},
                        ),
                        dmc.Badge(
                            id="page-peak-badge-lp-3",
                            children="name-lp-3",
                            color="blue",
                            variant="filled",
                            class_name="d-none",
                            style={"right": "1%", "top": "8em"},
                        ),
                        dmc.Text(
                            id="page-peak-annotation-lp-3",
                            children="",
                            class_name="d-none",
                            style={"right": "calc(1% + 120px)", "top": "7.7em", "font-style": "italic", "font-size": "0.85rem", "line-height": "1.8", "text-align": "right"},
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
                                    id="page-peak-download-data-button",
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
                                    id="page-peak-download-image-button",
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
                        dcc.Download(id="page-peak-download-data"),
                    ],
                ),
            ],
        ),
        html.Div(
            children=[
                dbc.Offcanvas(
                    id="page-peak-drawer-spectrum",
                    backdrop=True,
                    placement="end",
                    style={"width": "30%"},
                    children=[
                        html.Div(
                            className="loading-wrapper",
                            style={"margin-top": "5%"},
                            children=[
                                dbc.Spinner(
                                    color="dark",
                                    children=[
                                        html.Div(
                                            children=[
                                                dmc.Button(
                                                    children="Hide spectrum",
                                                    id="page-peak-close-spectrum-button",
                                                    variant="filled",
                                                    disabled=False,
                                                    color="red",
                                                    radius="md",
                                                    size="xs",
                                                    compact=False,
                                                    loading=False,
                                                ),
                                                dcc.Graph(
                                                    id="page-peak-graph-spectrum",
                                                    style={
                                                        "height": 280,
                                                        "width": "100%",
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
    Output("page-peak-graph-heatmap-mz-selection", "figure"),
    Output("page-peak-badge-input", "children"),
    Input("main-slider", "data"),
    Input("page-peak-selected-lp-1", "data"),
    Input("page-peak-selected-lp-2", "data"),
    Input("page-peak-selected-lp-3", "data"),
    Input("page-peak-rgb-button", "n_clicks"),
    Input("page-peak-colormap-button", "n_clicks"),
    State("page-peak-badge-input", "children"),
)
def page_peak_plot_graph_heatmap_mz_selection(
    slice_index,
    lp_1_index,
    lp_2_index,
    lp_3_index,
    n_clicks_button_rgb,
    n_clicks_button_colormap,
    graph_input,
):
    """This callback plots the heatmap of the selected LP(s)."""
    print(f"\n========== page_peak_plot_graph_heatmap_mz_selection ==========")
    print('indices:', lp_1_index, lp_2_index, lp_3_index)
    print(f"slice_index: {slice_index}")
    logging.info("Entering function to plot heatmap or RGB depending on LP selection")

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    print(f"id_input: {id_input}")    
    print("graph_input:", graph_input)

    if (
        id_input == "page-peak-selected-lp-1"
        or id_input == "page-peak-selected-lp-2"
        or id_input == "page-peak-selected-lp-3"
        or id_input == "page-peak-rgb-button"
        or id_input == "page-peak-colormap-button"
        or (
            (id_input == "main-slider")
            and (
                graph_input == "Current input: " + "LP selection colormap"
                or graph_input == "Current input: " + "LP selection RGB"
            )
        )
    ):
        print("--- option 1 ---")
        if lp_1_index >= 0 or lp_2_index >= 0 or lp_3_index >= 0:
            ll_lp_names = [
                peak_data.get_annotations().iloc[index]["name"]
                if index != -1
                else None
                for index in [lp_1_index, lp_2_index, lp_3_index]
            ]
            print("ll_lp_names:", ll_lp_names)

            if (
                id_input == "page-peak-colormap-button"
                or (
                    id_input == "main-slider"
                    and graph_input == "Current input: " + "LP selection colormap"
                )
            ):
                print("--- option 1.1 ---")
                if ll_lp_names.count(None) == len(ll_lp_names) - 1 and None in ll_lp_names:
                    nonull_ll_lp_names = [x for x in ll_lp_names if x is not None][0]
                    image = peak_figures.compute_image_per_lipid(
                        slice_index,
                        RGB_format=False,
                        lipid_name=nonull_ll_lp_names,
                        cache_flask=cache_flask,
                    )
                    print("--- option 1.1.1 ---")
                    return (
                        peak_figures.build_lipid_heatmap_from_image(
                            image, 
                            return_base64_string=False)
                    ,
                    "Current input: " + "LP selection colormap",
                )
                else:
                    print("--- option 1.1.2 ---")
                    logging.info("Trying to plot a heatmap for more than one LP, not possible. Return the rgb plot instead")
                    return (
                        peak_figures.compute_rgb_image_per_lipid_selection(
                            slice_index,
                            ll_lipid_names=ll_lp_names,
                            cache_flask=cache_flask,
                        ),
                        "Current input: " + "LP selection RGB",
                    )

            elif (
                id_input == "page-peak-rgb-button"
                or (
                    id_input == "main-slider"
                    and graph_input == "Current input: " + "LP selection RGB"
                )
                or (
                    id_input == "page-peak-toggle-apply-transform"
                    and graph_input == "Current input: " + "LP selection RGB"
                )
            ):
                print("--- option 1.2 ---")
                return (
                    peak_figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lp_names,
                        cache_flask=cache_flask,
                    ),
                    "Current input: " + "LP selection RGB",
                )

            else:
                print("--- option 1.3 ---")
                logging.info("Right before calling the graphing function")
                print("########################################################")
                print(graph_input)
                print(f"ll_lp_names: {ll_lp_names}")
                print(f"slice_index: {slice_index}")
                return (
                    peak_figures.compute_rgb_image_per_lipid_selection(
                        slice_index,
                        ll_lipid_names=ll_lp_names,
                        cache_flask=cache_flask,
                    ),
                    "Current input: " + "LP selection RGB",
                )
        elif (
            id_input == "main-slider" and graph_input == "Current input: "
        ):
            print("--- option 2 ---")
            print(f"No LP has been selected, the current LP is '1000.169719' and the slice is {slice_index}")
            return (
                peak_figures.compute_heatmap_per_lipid(slice_index, 
                                                '1000.169719',
                                                cache_flask=cache_flask),
                "Current input: " + '1000.169719',
            )
        else:
            print("--- option 3 ---")
            return (
                peak_figures.compute_heatmap_per_lipid(slice_index, 
                                                '1000.169719',
                                                cache_flask=cache_flask),
                "Current input: " + '1000.169719',
            )
    else:
        return dash.no_update


@app.callback(
    Output("page-peak-badge-lp-1", "children"),
    Output("page-peak-badge-lp-2", "children"),
    Output("page-peak-badge-lp-3", "children"),
    Output("page-peak-selected-lp-1", "data"),
    Output("page-peak-selected-lp-2", "data"),
    Output("page-peak-selected-lp-3", "data"),
    Output("page-peak-badge-lp-1", "class_name"),
    Output("page-peak-badge-lp-2", "class_name"),
    Output("page-peak-badge-lp-3", "class_name"),
    Output("page-peak-annotation-lp-1", "children"),
    Output("page-peak-annotation-lp-1", "class_name"),
    Output("page-peak-annotation-lp-2", "children"),
    Output("page-peak-annotation-lp-2", "class_name"),
    Output("page-peak-annotation-lp-3", "children"),
    Output("page-peak-annotation-lp-3", "class_name"),
    Input("page-peak-dropdown-lps", "value"),
    Input("page-peak-badge-lp-1", "class_name"),
    Input("page-peak-badge-lp-2", "class_name"),
    Input("page-peak-badge-lp-3", "class_name"),
    Input("main-slider", "data"),
    State("page-peak-selected-lp-1", "data"),
    State("page-peak-selected-lp-2", "data"),
    State("page-peak-selected-lp-3", "data"),
    State("page-peak-badge-lp-1", "children"),
    State("page-peak-badge-lp-2", "children"),
    State("page-peak-badge-lp-3", "children"),
)
def page_peak_add_toast_selection(
    l_lp_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    lp_1_index,
    lp_2_index,
    lp_3_index,
    header_1,
    header_2,
    header_3,
):
    """This callback adds the selected LP to the selection."""
    logging.info("Entering function to update LP data")
    print("\n================ page_peak_add_toast_selection ================")
    
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    print(f"id_input: {id_input}")
    print(f"value_input: {value_input}")
    
    # Initialize annotation variables
    annotation_1 = ""
    annotation_2 = ""
    annotation_3 = ""
    class_name_annotation_1 = "d-none"
    class_name_annotation_2 = "d-none"
    class_name_annotation_3 = "d-none"
    
    if len(id_input) == 0 or (id_input == "page-peak-dropdown-lps" and l_lp_names is None):
        # Initialize with '1000.169719' as the default peak
        default_lp = '1000.169719'
        name = default_lp
        l_lp_loc = (
            peak_data.get_annotations()
            .index[
                (peak_data.get_annotations()["name"] == name)
                & (peak_data.get_annotations()["slice"] == slice_index)
            ]
            .tolist()
        )
        print(f"l_lp_loc: {l_lp_loc}")
        
        if len(l_lp_loc) == 0:
            l_lp_loc = (
                peak_data.get_annotations()
                .index[
                    (peak_data.get_annotations()["name"] == name)
                ]
                .tolist()
            )[:1]
        print(f"l_lp_loc: {l_lp_loc}")

        if len(l_lp_loc) > 0:
            lp_1_index = l_lp_loc[0]
            header_1 = default_lp
            class_name_badge_1 = "position-absolute"
            
            # Get annotation for the default peak
            annotation_value = peak_data.get_annotations().iloc[lp_1_index]["annotation"]
            annotation_1 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
            class_name_annotation_1 = "position-absolute"
            
            return (header_1, "", "", lp_1_index, -1, -1, class_name_badge_1, "d-none", "d-none", 
                    annotation_1, class_name_annotation_1, "", "d-none", "", "d-none")
        else:
            return ("", "", "", -1, -1, -1, "d-none", "d-none", "d-none", 
                    "", "d-none", "", "d-none", "", "d-none")

    if l_lp_names is not None:
        if len(l_lp_names) < len(
            [x for x in [lp_1_index, lp_2_index, lp_3_index] if x != -1]
        ):
            logging.info("One or several LPs have been deleter. Cleaning LP badges now.")
            for idx_header, header in enumerate([header_1, header_2, header_3]):
                found = False
                for lp_name in l_lp_names:
                    if lp_name == header:
                        found = True
                if not found:
                    if idx_header == 0:
                        header_1 = ""
                        lp_1_index = -1
                        class_name_badge_1 = "d-none"
                        class_name_annotation_1 = "d-none"
                    if idx_header == 1:
                        header_2 = ""
                        lp_2_index = -1
                        class_name_badge_2 = "d-none"
                        class_name_annotation_2 = "d-none"
                    if idx_header == 2:
                        header_3 = ""
                        lp_3_index = -1
                        class_name_badge_3 = "d-none"
                        class_name_annotation_3 = "d-none"

            # Prepare annotations for remaining peaks
            if lp_1_index != -1:
                annotation_value = peak_data.get_annotations().iloc[lp_1_index]["annotation"]
                annotation_1 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                class_name_annotation_1 = "position-absolute"
            if lp_2_index != -1:
                annotation_value = peak_data.get_annotations().iloc[lp_2_index]["annotation"]
                annotation_2 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                class_name_annotation_2 = "position-absolute"
            if lp_3_index != -1:
                annotation_value = peak_data.get_annotations().iloc[lp_3_index]["annotation"]
                annotation_3 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                class_name_annotation_3 = "position-absolute"

            return (
                header_1,
                header_2,
                header_3,
                lp_1_index,
                lp_2_index,
                lp_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
                annotation_1,
                class_name_annotation_1,
                annotation_2,
                class_name_annotation_2,
                annotation_3,
                class_name_annotation_3,
            )

    if (
        id_input == "page-peak-dropdown-lps" and l_lp_names is not None
    ) or id_input == "main-slider":

        if id_input == "main-slider":
            print(f"header_1: {header_1}")
            print(f"header_2: {header_2}")
            print(f"header_3: {header_3}")
            for header in [header_1, header_2, header_3]:
                name = header
                l_lp_loc_temp = (
                    peak_data.get_annotations()
                    .index[
                        (peak_data.get_annotations()["name"].astype(str) == str(name))
                    ]
                    .tolist()
                )
                print(f"l_lp_loc_temp: {l_lp_loc_temp}")
                l_lp_loc = [
                    l_lp_loc_temp[i]
                    for i, x in enumerate(
                        peak_data.get_annotations().iloc[l_lp_loc_temp]["slice"] == slice_index
                    )
                    if x
                ]
                print(f"l_lp_loc: {l_lp_loc}")
                lp_index = l_lp_loc[0] if len(l_lp_loc) > 0 else -1

                if header_1 == header:
                    lp_1_index = lp_index
                elif header_2 == header:
                    lp_2_index = lp_index
                elif header_3 == header:
                    lp_3_index = lp_index

            # Update annotations for all peaks
            if lp_1_index != -1:
                annotation_value = peak_data.get_annotations().iloc[lp_1_index]["annotation"]
                annotation_1 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                class_name_annotation_1 = "position-absolute"
            if lp_2_index != -1:
                annotation_value = peak_data.get_annotations().iloc[lp_2_index]["annotation"]
                annotation_2 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                class_name_annotation_2 = "position-absolute"
            if lp_3_index != -1:
                annotation_value = peak_data.get_annotations().iloc[lp_3_index]["annotation"]
                annotation_3 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                class_name_annotation_3 = "position-absolute"

            logging.info("Returning updated LP data")
            return (
                header_1,
                header_2,
                header_3,
                lp_1_index,
                lp_2_index,
                lp_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
                annotation_1,
                class_name_annotation_1,
                annotation_2,
                class_name_annotation_2,
                annotation_3,
                class_name_annotation_3,
            )

        elif id_input == "page-peak-dropdown-lps":
            print(f"l_lp_names: {l_lp_names}")
            print(f"l_lp_names[-1]: {l_lp_names[-1]}")
            name = l_lp_names[-1]
            print(f"name: {name}")

            print("########################################################")

            print(peak_data.get_annotations())

            print(f"slice_index: {slice_index}")


            l_lp_loc = (
                peak_data.get_annotations()
                .index[
                    (peak_data.get_annotations()["name"].astype(str) == str(name))
                    & (peak_data.get_annotations()["slice"].astype(int) == int(slice_index))
                ]
                .tolist()
            )

            print(f"l_lp_loc: {l_lp_loc}")

            if len(l_lp_loc) > 1:
                logging.warning("More than one LP corresponds to the selection")
                l_lp_loc = [l_lp_loc[-1]]

            if len(l_lp_loc) < 1:
                logging.warning("No LP annotation exist. Taking another slice annotation")
                l_lp_loc = (
                    peak_data.get_annotations()
                    .index[
                        (peak_data.get_annotations()["name"] == name)
                    ]
                    .tolist()
                )[:1]

            lp_index = l_lp_loc[0]
            lp_string = l_lp_names[-1]

            change_made = False

            if header_1 == lp_string:
                lp_1_index = lp_index
                change_made = True
            elif header_2 == lp_string:
                lp_2_index = lp_index
                change_made = True
            elif header_3 == lp_string:
                lp_3_index = lp_index
                change_made = True

            if lp_string not in [header_1, header_2, header_2]:
                if class_name_badge_1 == "d-none":
                    header_1 = lp_string
                    lp_1_index = lp_index
                    class_name_badge_1 = "position-absolute"
                    
                    # Add annotation for peak 1
                    annotation_value = peak_data.get_annotations().iloc[lp_1_index]["annotation"]
                    annotation_1 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    class_name_annotation_1 = "position-absolute"
                    
                    # Make sure existing annotations remain visible
                    if lp_2_index != -1:
                        annotation_value = peak_data.get_annotations().iloc[lp_2_index]["annotation"]
                        annotation_2 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        class_name_annotation_2 = "position-absolute"
                    if lp_3_index != -1:
                        annotation_value = peak_data.get_annotations().iloc[lp_3_index]["annotation"]
                        annotation_3 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        class_name_annotation_3 = "position-absolute"
                    
                elif class_name_badge_2 == "d-none":
                    header_2 = lp_string
                    lp_2_index = lp_index
                    class_name_badge_2 = "position-absolute"
                    
                    # Add annotation for peak 2
                    annotation_value = peak_data.get_annotations().iloc[lp_2_index]["annotation"]
                    annotation_2 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    class_name_annotation_2 = "position-absolute"
                    
                    # Make sure existing annotations remain visible
                    if lp_1_index != -1:
                        annotation_value = peak_data.get_annotations().iloc[lp_1_index]["annotation"]
                        annotation_1 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        class_name_annotation_1 = "position-absolute"
                    if lp_3_index != -1:
                        annotation_value = peak_data.get_annotations().iloc[lp_3_index]["annotation"]
                        annotation_3 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        class_name_annotation_3 = "position-absolute"
                    
                elif class_name_badge_3 == "d-none":
                    header_3 = lp_string
                    lp_3_index = lp_index
                    class_name_badge_3 = "position-absolute"
                    
                    # Add annotation for peak 3
                    annotation_value = peak_data.get_annotations().iloc[lp_3_index]["annotation"]
                    annotation_3 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    class_name_annotation_3 = "position-absolute"
                    
                    # Make sure existing annotations remain visible
                    if lp_1_index != -1:
                        annotation_value = peak_data.get_annotations().iloc[lp_1_index]["annotation"]
                        annotation_1 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        class_name_annotation_1 = "position-absolute"
                    if lp_2_index != -1:
                        annotation_value = peak_data.get_annotations().iloc[lp_2_index]["annotation"]
                        annotation_2 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                        class_name_annotation_2 = "position-absolute"
                    
                else:
                    logging.warning("More than 3 LPs have been selected")
                    return dash.no_update
                change_made = True
            else:
                # Update annotations for all visible peaks
                if lp_1_index != -1:
                    annotation_value = peak_data.get_annotations().iloc[lp_1_index]["annotation"]
                    annotation_1 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    class_name_annotation_1 = "position-absolute"
                if lp_2_index != -1:
                    annotation_value = peak_data.get_annotations().iloc[lp_2_index]["annotation"]
                    annotation_2 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    class_name_annotation_2 = "position-absolute"
                if lp_3_index != -1:
                    annotation_value = peak_data.get_annotations().iloc[lp_3_index]["annotation"]
                    annotation_3 = "No match" if annotation_value == "_db" else "Predicted molecule: " + annotation_value
                    class_name_annotation_3 = "position-absolute"

            if change_made:
                logging.info(
                    "Changes have been made to the LP selection or indexation,"
                    + " propagating callback."
                )
                return (
                    header_1,
                    header_2,
                    header_3,
                    lp_1_index,
                    lp_2_index,
                    lp_3_index,
                    class_name_badge_1,
                    class_name_badge_2,
                    class_name_badge_3,
                    annotation_1,
                    class_name_annotation_1,
                    annotation_2,
                    class_name_annotation_2,
                    annotation_3,
                    class_name_annotation_3,
                )
            else:
                return dash.no_update

    return dash.no_update


clientside_callback(
    """
    function(n_clicks){
        if(n_clicks > 0){
            domtoimage.toBlob(document.getElementById('page-peak-graph-heatmap-mz-selection'))
                .then(function (blob) {
                    window.saveAs(blob, 'peak_selection_plot.png');
                });
        }
        return null;
    }
    """,
    Output("page-peak-download-image-button", "n_clicks"),
    Input("page-peak-download-image-button", "n_clicks"),
)
"""This clientside callback is used to download the current heatmap."""


@app.callback(
    Output("page-peak-rgb-button", "disabled"),
    Output("page-peak-colormap-button", "disabled"),
    Input("page-peak-selected-lp-1", "data"),
    Input("page-peak-selected-lp-2", "data"),
    Input("page-peak-selected-lp-3", "data"),
)
def page_peak_active_download(lp_1_index, lp_2_index, lp_3_index):
    logging.info("Enabled rgb and colormap buttons")
    print(f"lp_1_index: {lp_1_index}")
    print(f"lp_2_index: {lp_2_index}")
    print(f"lp_3_index: {lp_3_index}")
    l_lps_indexes = [
        x for x in [lp_1_index, lp_2_index, lp_3_index] if x is not None and x != -1
    ]

    if len(l_lps_indexes) > 0:
        return False, False
    else:
        return True, True


@app.callback(
    Output("page-peak-drawer-spectrum", "is_open"),
    Input("page-peak-show-spectrum-button", "n_clicks"),
    Input("page-peak-close-spectrum-button", "n_clicks"),
    [State("page-peak-drawer-spectrum", "is_open")],
)
def toggle_spectrum_drawer(n1, n2, is_open):
    """This callback is used to toggle the mass spectrum drawer."""
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output("page-peak-graph-spectrum", "figure"),
    Input("main-slider", "data"),
    Input("page-peak-drawer-spectrum", "is_open"),
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
    df = pd.read_csv('mzsectionaverages.csv', index_col=0)
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
        margin=dict(t=50, r=0, b=10, l=0),
        showlegend=False,
        xaxis=dict(rangeslider={"visible": False}, title="m/z"),
        yaxis=dict(fixedrange=False, title="Intensity"),
        template="plotly_dark",
        autosize=True,
        title={
            "text": f"Mass spectrum for section {slice_index}",
            "y": 0.92,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(
                size=14,
            ),
        },
        paper_bgcolor="rgba(0,0,0,0.3)",
        plot_bgcolor="rgba(0,0,0,0.3)",
    )

    # Build figure
    fig = go.Figure(data=data, layout=layout)
    
    return fig