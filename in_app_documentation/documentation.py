# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""This file is used to build the in-app documentation and the readme file."""

# ==================================================================================================
# --- Imports
# ==================================================================================================
import dash_mantine_components as dmc
import os
from dash import dcc
import re

# ==================================================================================================
# --- Functions
# ==================================================================================================
def merge_md(write_doc=False):
    """This function merges the separate files (one per section) from the documentation folder into
    a final markdown document. It is not written in the most optimal way but it works and has no
    requirement for performance.

    Args:
        write_doc (bool, optional): It True, the markdown document is saved as a new file. Defaults
            to False.

    Returns:
        (str): A string representing the documentation of the app written in markdown.
    """
    order_final_md = [
        "_overview", 
        "_explore", 
        "_data", 
        "_usage",
        "_about", 
        ]
    final_md = "# Lipid Brain Atlas Explorer documentation \n\n"
    # final_md = ""
    for filename in order_final_md:
        for file in os.listdir(os.path.join(os.getcwd(), "in_app_documentation")):
            if file.endswith(".md") and filename in file:
                with open(os.path.join(os.getcwd(), "in_app_documentation", file), "r") as f:
                    final_md += f.read() + "\n"
                break
    if write_doc:
        with open(os.path.join(os.getcwd(), "in_app_documentation", "documentation.md"), "w") as f:
            f.write(final_md)

    return final_md


def load_md():
    """This function is used to load the markdown documentation in a string variable from the
    corresponding file.

    Returns:
        (str): A string representing the documentation of the app written in markdown.
    """
    with open(os.path.join(os.getcwd(), "in_app_documentation", "documentation.md"), "r") as f:
        md = f.read()
    return md


def preprocess_md(md):
    # Replace <img src="readme/xxx.png" ...> with ![](assets/xxx.png)
    md = re.sub(
        r'<img\s+src="readme/([^\"]+)"[^>]*>',
        r'![](assets/\1)',
        md
    )
    # Remove <p align="center"> and </p>
    md = re.sub(r'<p align="center">', '', md)
    md = re.sub(r'</p>', '', md)
    return md


def convert_md(md, app):
    """This function is used to convert the markdown documentation in a list of dash components.

    Args:
        md (str): A string representing the documentation of the app written in markdown.
        app (dash.Dash): The dash app, used to fetch the asset folder URL.

    Returns:
        (list): A list of dash components representing the documentation.
    """
    # Find all markdown image links
    pattern = r'!\[([^\]]*)\]\((assets/[^)]+)\)'
    parts = []
    last_end = 0
    for match in re.finditer(pattern, md):
        # Add text before the image
        if match.start() > last_end:
            parts.append(dcc.Markdown(md[last_end:match.start()]))
        # Add the image as a Dash component
        alt_text, img_path = match.groups()
        parts.append(
            dmc.Image(
                src=app.get_asset_url(img_path.replace('assets/', '')),
                alt=alt_text,
                class_name="mx-auto my-5",
                fit="contain",
            )
        )
        last_end = match.end()
    # Add any remaining text after the last image
    if last_end < len(md):
        parts.append(dcc.Markdown(md[last_end:]))
    # Space at the end for clarity
    parts += [dmc.Space(h=80)]
    return parts


def return_documentation(app, write_doc=False):
    """This function is used to return the documentation of the app as a dash component.

    Args:
        app (dash.Dash): The dash app, used to fetch the asset folder URL.
        write_doc (bool, optional): It True, the markdown document is saved as a new file. Defaults
            to False.
    Returns:
        (dmc.Center): A Dash Mantine Component representing the documentation in a nice centered and
            scrollable page.
    """
    layout = dmc.Center(
        class_name="mx-auto",
        style={"width": "60%"},
        children=dmc.ScrollArea(
            type="scroll",
            style={"height": "90vh"},
            children=convert_md(merge_md(write_doc), app),
        ),
    )

    return layout
