# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This module is where the app layout is created: the main container, the sidebar and the 
different pages. All the dcc.store, used to store client data across pages, are created here. It is 
also here that the URL routing is done.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import uuid
import logging
import dash_mantine_components as dmc

# LBAE modules
from app import app, data, atlas
from pages import (
    sidebar,
    home,
    lipid_selection,
    lipizones_selection,
    lipizones_vs_celltypes,
    region_analysis,
    threeD_exploration,
    lp_selection,
    id_cards,
    threeD_lipizones,
    # peak_selection,
)
from in_app_documentation.documentation import return_documentation
from config import basic_config
from modules.tools.misc import logmem

# ==================================================================================================
# --- App layout
# ==================================================================================================


def return_main_content():
    """This function compute the elements of the app that are shared across pages, including all the
    dcc.store.

    Returns:
        (html.Div): A div containing the corresponding elements.
    """
    # List of empty lipid indexes for the dropdown of page 4, assuming brain 1 is initially selected
    empty_lipid_list = [-1 for i in data.get_slice_list(indices="ReferenceAtlas")]

    # Record session id in case sessions need to be individualized
    session_id = str(uuid.uuid4())

    # Define static content
    main_content = html.Div(
        children=[
            # To handle url since multi-page app
            dcc.Location(id="url", refresh=False),
            # Record session id, useful to trigger callbacks at initialization
            dcc.Store(id="session-id", data=session_id),
            # Record the slider index
            dcc.Store(id="main-slider", data=1),
            
            # Record the lipids selected in page 2
            dcc.Store(id="page-2-selected-lipid-1", data=-1),
            dcc.Store(id="page-2-selected-lipid-2", data=-1),
            dcc.Store(id="page-2-selected-lipid-3", data=-1),
            
            # Record the lipid programs selected in page 2bis
            dcc.Store(id="page-2bis-selected-program-1", data=-1),
            dcc.Store(id="page-2bis-selected-program-2", data=-1),
            dcc.Store(id="page-2bis-selected-program-3", data=-1),

            # Record the peaks selected in peak selection page
            dcc.Store(id="page-2tris-selected-peak-1", data=-1),
            dcc.Store(id="page-2tris-selected-peak-2", data=-1),
            dcc.Store(id="page-2tris-selected-peak-3", data=-1),
            dcc.Store(id="page-2tris-last-selected-peaks", data=[]),

            # Record the lipizones selected in page 6
            dcc.Store(id="page-6-all-selected-lipizones", data={}),
            dcc.Store(id="page-6-current-treemap-selection", data=None),

            # Record the lipizones and celltypes selected in page 6bis
            dcc.Store(id="page-6bis-all-selected-lipizones", data={}),
            dcc.Store(id="page-6bis-all-selected-celltypes", data={}),
            dcc.Store(id="page-6bis-current-lipizone-treemap-selection", data=None),
            dcc.Store(id="page-6bis-current-celltype-treemap-selection", data=None),

            # Record the lipids selected in page 4
            dcc.Store(id="page-4-selected-lipid-1", data=empty_lipid_list),
            dcc.Store(id="page-4-selected-lipid-2", data=empty_lipid_list),
            dcc.Store(id="page-4-selected-lipid-3", data=empty_lipid_list),
            dcc.Store(id="page-4-last-selected-regions", data=[]),
            dcc.Store(id="page-4-selected-region-1", data=""),
            dcc.Store(id="page-4-selected-region-2", data=""),
            dcc.Store(id="page-4-selected-region-3", data=""),
            dcc.Store(id="page-4-last-selected-lipids", data=[]),
            
            # Record the lipids selected in page 3
            dcc.Store(id="page-3-selected-lipid-1", data=-1),
            dcc.Store(id="page-3-selected-lipid-2", data=-1),
            dcc.Store(id="page-3-selected-lipid-3", data=-1),
            dcc.Store(id="page-3-last-selected-lipids", data=[]),
            # Record the shapes drawn in page 3
            dcc.Store(id="dcc-store-color-mask", data=[]),
            dcc.Store(id="dcc-store-reset", data=False),
            dcc.Store(id="dcc-store-shapes-and-masks", data=[]),
            dcc.Store(id="dcc-store-shapes-and-masks-A", data=[]),
            dcc.Store(id="dcc-store-shapes-and-masks-B", data=[]),
            dcc.Store(id="dcc-store-list-idx-lipids", data=[]),
            # Record the annotated paths drawn in page 3
            dcc.Store(id="page-3-dcc-store-path-heatmap"),
            dcc.Store(id="page-3-dcc-store-basic-figure", data=True),
            # Record the computed volcano plots drawn in page 3
            # dcc.Store(id="dcc-store-list-mz-spectra", data=[]),
            dcc.Store(id="dcc-store-list-volcano-A", data=[]),
            dcc.Store(id="dcc-store-list-volcano-B", data=[]),
            # Record the lipids expressed in the region in page 3
            dcc.Store(id="page-3-dcc-store-lipids-region", data=[]),
            
            # Actual app layout
            html.Div(
                children=[
                    sidebar.layout,
                    html.Div(id="content"),
                    dmc.Center(
                        id="main-paper-slider",
                        style={
                            "position": "fixed",
                            "bottom": "2.5rem",
                            "height": "3rem",
                            "left": "7rem",
                            "right": "1rem",
                            "background-color": "rgba(0, 0, 0, 0.0)",
                        },
                        children=[
                            dmc.Text(
                                id="main-text-slider",
                                children="Rostro-caudal axis (mm): ",
                                class_name="pr-4",
                                size="sm",
                            ),
                            # Reference and Second Atlas sliders
                            dmc.Slider(
                                id="main-slider-1",
                                min=data.get_slice_list(indices="ReferenceAtlas")[0],
                                max=data.get_slice_list(indices="ReferenceAtlas")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='ReferenceAtlas').loc[data.get_AP_avg_coordinates(indices='ReferenceAtlas')['SectionID']==slice_index, 'xccf'].values[0]:.2f}" if i%3 == 0 else ""
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="ReferenceAtlas"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="ReferenceAtlas")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50",
                            ),
                            dmc.Slider(
                                id="main-slider-2",
                                min=data.get_slice_list(indices="SecondAtlas")[0],
                                max=data.get_slice_list(indices="SecondAtlas")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='SecondAtlas').loc[data.get_AP_avg_coordinates(indices='SecondAtlas')['SectionID']==slice_index, 'xccf'].values[0]:.2f}" if i%3 == 0 else ""
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="SecondAtlas"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="SecondAtlas")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            # Male brain sliders
                            dmc.Slider(
                                id="main-slider-male1",
                                min=data.get_slice_list(indices="Male1")[0],
                                max=data.get_slice_list(indices="Male1")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='Male1').loc[data.get_AP_avg_coordinates(indices='Male1')['SectionID']==slice_index, 'xccf'].values[0]:.2f}"
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="Male1"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="Male1")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            dmc.Slider(
                                id="main-slider-male2",
                                min=data.get_slice_list(indices="Male2")[0],
                                max=data.get_slice_list(indices="Male2")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='Male2').loc[data.get_AP_avg_coordinates(indices='Male2')['SectionID']==slice_index, 'xccf'].values[0]:.2f}"
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="Male2"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="Male2")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            dmc.Slider(
                                id="main-slider-male3",
                                min=data.get_slice_list(indices="Male3")[0],
                                max=data.get_slice_list(indices="Male3")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='Male3').loc[data.get_AP_avg_coordinates(indices='Male3')['SectionID']==slice_index, 'xccf'].values[0]:.2f}"
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="Male3"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="Male3")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            # Female brain sliders
                            dmc.Slider(
                                id="main-slider-female1",
                                min=data.get_slice_list(indices="Female1")[0],
                                max=data.get_slice_list(indices="Female1")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='Female1').loc[data.get_AP_avg_coordinates(indices='Female1')['SectionID']==slice_index, 'xccf'].values[0]:.2f}"
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="Female1"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="Female1")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            dmc.Slider(
                                id="main-slider-female2",
                                min=data.get_slice_list(indices="Female2")[0],
                                max=data.get_slice_list(indices="Female2")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='Female2').loc[data.get_AP_avg_coordinates(indices='Female2')['SectionID']==slice_index, 'xccf'].values[0]:.2f}"
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="Female2"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="Female2")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            dmc.Slider(
                                id="main-slider-female3",
                                min=data.get_slice_list(indices="Female3")[0],
                                max=data.get_slice_list(indices="Female3")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='Female3').loc[data.get_AP_avg_coordinates(indices='Female3')['SectionID']==slice_index, 'xccf'].values[0]:.2f}"
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="Female3"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="Female3")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            # Pregnant brain sliders
                            dmc.Slider(
                                id="main-slider-pregnant1",
                                min=data.get_slice_list(indices="Pregnant1")[0],
                                max=data.get_slice_list(indices="Pregnant1")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='Pregnant1').loc[data.get_AP_avg_coordinates(indices='Pregnant1')['SectionID']==slice_index, 'xccf'].values[0]:.2f}"
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="Pregnant1"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="Pregnant1")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            dmc.Slider(
                                id="main-slider-pregnant2",
                                min=data.get_slice_list(indices="Pregnant2")[0],
                                max=data.get_slice_list(indices="Pregnant2")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='Pregnant2').loc[data.get_AP_avg_coordinates(indices='Pregnant2')['SectionID']==slice_index, 'xccf'].values[0]:.2f}"
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="Pregnant2"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="Pregnant2")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            dmc.Slider(
                                id="main-slider-pregnant4",
                                min=data.get_slice_list(indices="Pregnant4")[0],
                                max=data.get_slice_list(indices="Pregnant4")[-1],
                                step=1,
                                marks=[
                                    {"value": slice_index,
                                     "label": f"{data.get_AP_avg_coordinates(indices='Pregnant4').loc[data.get_AP_avg_coordinates(indices='Pregnant4')['SectionID']==slice_index, 'xccf'].values[0]:.2f}"
                                    }
                                    for i, slice_index in enumerate(data.get_slice_list(
                                        indices="Pregnant4"
                                    ))
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="Pregnant4")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            dmc.Chips(
                                id="main-brain",
                                data=[
                                    {"value": "ReferenceAtlas", "label": "Brain 1"},
                                    {"value": "SecondAtlas", "label": "Brain 2"},
                                    {"value": "Male1", "label": "Male 1"},
                                    {"value": "Male2", "label": "Male 2"},
                                    {"value": "Male3", "label": "Male 3"},
                                    {"value": "Female1", "label": "Female 1"},
                                    {"value": "Female2", "label": "Female 2"},
                                    {"value": "Female3", "label": "Female 3"},
                                    {"value": "Pregnant1", "label": "Pregnant 1"},
                                    {"value": "Pregnant2", "label": "Pregnant 2"},
                                    {"value": "Pregnant4", "label": "Pregnant 3"},
                                ],
                                value="ReferenceAtlas",
                                direction="column",
                                spacing="sm",
                                align="right",
                                style={
                                    "position": "fixed",
                                    "right": "0.5rem",
                                    "top": "50%",
                                    "transform": "translateY(-50%)",
                                    "zIndex": 1000,
                                    "padding": "1rem",
                                    "borderRadius": "8px",
                                    "display": "flex",
                                    "alignItems": "flex-end",
                                },
                                color="cyan",
                            ),
                        ],
                    ),
                    # Documentation in a bottom drawer
                    dmc.Drawer(
                        children=dmc.Text("To update", size="xl", align="center"),
                        id="documentation-offcanvas",
                        # title="LBAE documentation",
                        opened=False,
                        padding="md",
                        size="85vh",
                        position="bottom",
                    ),
                    # Spinner when switching pages
                    dbc.Spinner(
                        id="main-spinner",
                        color="light",
                        children=html.Div(id="empty-content"),
                        fullscreen=True,
                        fullscreen_style={"left": "6rem", "background-color": "#1d1c1f"},
                        spinner_style={"width": "6rem", "height": "6rem"},
                        delay_hide=100,
                    ),
                ],
            ),
        ],
    )
    return main_content


def return_validation_layout(main_content, initial_slice=12):
    """This function compute the layout of the app, including the main container, the sidebar and
    the different pages.

    Args:
        main_content (html.Div): A div containing the elements of the app that are shared across
            pages.
        initial_slice (int): Index of the slice to be displayed at launch.

    Returns:
        (html.Div): A div containing the layout of the app.
    """
    return html.Div(
        [
            main_content,
            home.layout,
            lipid_selection.return_layout(basic_config, initial_slice),
            lp_selection.return_layout(basic_config, initial_slice),
            # peak_selection.return_layout(basic_config, initial_slice),
            lipizones_selection.return_layout(basic_config, initial_slice),
            lipizones_vs_celltypes.return_layout(basic_config, initial_slice),
            id_cards.return_layout(basic_config, initial_slice),
            region_analysis.return_layout(basic_config, initial_slice),
            threeD_exploration.return_layout(basic_config, initial_slice),
            threeD_lipizones.return_layout(basic_config, initial_slice),
        ]
    )


# ==================================================================================================
# --- App callbacks
# ==================================================================================================
@app.callback(
    Output("content", "children"),
    Output("empty-content", "children"),
    Input("url", "pathname"),
    State("main-slider", "data"),
    State("main-brain", "value"),
)
def render_page_content(pathname, slice_index, brain):
    """This callback is used as a URL router."""

    # Keep track of the page in the console
    if pathname is not None:
        logging.info("Page" + pathname + " has been selected" + logmem())

    # Set the content according to the current pathname
    if pathname == "/":
        page = home.layout

    elif pathname == "/lipid-selection":
        page = lipid_selection.return_layout(basic_config, slice_index)

    elif pathname == "/lp-selection":
        page = lp_selection.return_layout(basic_config, slice_index)
    
    # elif pathname == "/peak-selection":
    #     page = peak_selection.return_layout(basic_config, slice_index)
    
    elif pathname == "/lipizones-selection":
        page = lipizones_selection.return_layout(basic_config, slice_index)

    elif pathname == "/lipizones-vs-celltypes":
        page = lipizones_vs_celltypes.return_layout(basic_config, slice_index)

    elif pathname == "/id-cards":
        page = id_cards.return_layout(basic_config, slice_index)

    elif pathname == "/region-analysis":
        page = region_analysis.return_layout(basic_config, slice_index)

    elif pathname == "/3D-exploration":
        page = threeD_exploration.return_layout(basic_config, slice_index)

    elif pathname == "/3D-lipizones":
        page = threeD_lipizones.return_layout(basic_config, slice_index)

    else:
        # If the user tries to reach a different page, return a 404 message
        page = dmc.Center(
            dmc.Alert(
                title="404: Not found",
                children=f"The pathname {pathname} was not recognised...",
                color="red",
                class_name="mt-5",
            ),
            class_name="mt-5",
        )
    return page, ""


@app.callback(
    Output("documentation-offcanvas", "opened"),
    [
        Input("sidebar-documentation", "n_clicks"),
    ],
    [State("documentation-offcanvas", "opened")],
)
def toggle_collapse(n1, is_open):
    """This callback triggers the modal windows that toggles the documentation when clicking on the
    corresponding button."""
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output("main-paper-slider", "class_name"), Input("url", "pathname"), prevent_initial_call=False
)
def hide_slider(pathname):
    """This callback is used to hide the slider div when the user is on a page that does not need it.
    """

    # Pages in which the slider is displayed
    l_path_with_slider = [
        "/lipid-selection",
        "/lp-selection",
        "/peak-selection",
        "/lipizones-selection",
        "/region-analysis",
        "/3D-exploration",
        "/3D-lipizones",
        "/lipizones-vs-celltypes",
    ]

    # Set the content according to the current pathname
    if pathname in l_path_with_slider:
        return ""

    else:
        return "d-none"


@app.callback(
    Output("main-slider-1", "style"),
    Output("main-slider-2", "style"),
    Output("main-text-slider", "style"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def hide_slider_but_leave_brain(pathname):
    """This callback is used to hide the slider but leave brain chips when needed."""

    # Pages in which the slider is displayed
    l_path_without_slider_but_with_brain = [
        "/3D-exploration",
        "/3D-lipizones",
    ]

    # Set the content according to the current pathname
    if pathname in l_path_without_slider_but_with_brain:
        return {"visibility": "hidden"}, {"visibility": "hidden"}, {"visibility": "hidden"}

    else:
        return {}, {}, {}


@app.callback(
    [Output(f"main-slider-{slider_id}", "class_name") for slider_id in [
        "1", "2", "male1", "male2", "male3", "female1", "female2", "female3", 
        "pregnant1", "pregnant2", "pregnant4"
    ]],
    [Output(f"main-slider-{slider_id}", "value") for slider_id in [
        "1", "2", "male1", "male2", "male3", "female1", "female2", "female3",
        "pregnant1", "pregnant2", "pregnant4"
    ]],
    Input("main-brain", "value"),
    [State(f"main-slider-{slider_id}", "value") for slider_id in [
        "1", "2", "male1", "male2", "male3", "female1", "female2", "female3",
        "pregnant1", "pregnant2", "pregnant4"
    ]],
    prevent_initial_call=False,
)
def update_slider_visibility(brain, *values):
    """This callback is used to update the slider visibility based on the selected brain."""
    # Base class for visible slider
    visible_class = "mt-2 mr-5 ml-2 mb-1 w-50"
    # Base class for hidden slider
    hidden_class = "mt-2 mr-5 ml-2 mb-1 w-50 d-none"
    
    # Initialize all sliders as hidden
    classes = [hidden_class] * 11
    # Keep all values as is
    new_values = list(values)
    
    # Map brain names to slider indices
    brain_to_index = {
        "ReferenceAtlas": 0, "SecondAtlas": 1,
        "Male1": 2, "Male2": 3, "Male3": 4,
        "Female1": 5, "Female2": 6, "Female3": 7,
        "Pregnant1": 8, "Pregnant2": 9, "Pregnant4": 10
    }
    
    # Show only the selected brain's slider 
    if brain in brain_to_index:
        classes[brain_to_index[brain]] = visible_class
    
    return classes + new_values

app.clientside_callback(
    """
    function(value_1, value_2, value_male1, value_male2, value_male3, 
             value_female1, value_female2, value_female3,
             value_pregnant1, value_pregnant2, value_pregnant4, brain){
        const values = {
            'ReferenceAtlas': value_1,
            'SecondAtlas': value_2,
            'Male1': value_male1,
            'Male2': value_male2,
            'Male3': value_male3,
            'Female1': value_female1,
            'Female2': value_female2,
            'Female3': value_female3,
            'Pregnant1': value_pregnant1,
            'Pregnant2': value_pregnant2,
            'Pregnant4': value_pregnant4
        };
        return values[brain] || value_1;
    }
    """,
    Output("main-slider", "data"),
    [Input(f"main-slider-{slider_id}", "value") for slider_id in [
        "1", "2", "male1", "male2", "male3", "female1", "female2", "female3",
        "pregnant1", "pregnant2", "pregnant4"
    ]],
    State("main-brain", "value"),
)
"""This clientside callback is used to update the slider indices with the selected brain."""

@app.callback(
    Output("main-brain", "style"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def hide_brain_chips(pathname):
    """This callback is used to hide the brain selection chips when they are not needed."""
    if pathname == "/lipizones-vs-celltypes":
        return {"display": "none"}
    else:
        return {
            "position": "fixed",
            "right": "0.5rem",
            "top": "50%",
            "transform": "translateY(-50%)",
            "zIndex": 1000,
            "padding": "1rem",
            "borderRadius": "8px",
            "display": "flex",
            "alignItems": "flex-end",
        }