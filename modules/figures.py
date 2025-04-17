# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""This class is used to produce the figures and widgets used in the app, themselves requiring data
from the MALDI imaging, and the Allen Brain Atlas, as well as the mapping between the two."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import numpy as np
import logging
from modules.tools.misc import logmem
import plotly.graph_objects as go
import plotly.express as px
from skimage import io
from scipy.ndimage.interpolation import map_coordinates
import pandas as pd
from scipy.interpolate import griddata
from modules.tools.external_lib.clustergram import Clustergram
import copy
from plotly.subplots import make_subplots

import PyPDF2
import base64
import re
import os
from tqdm import tqdm
from scipy.ndimage import gaussian_filter
import traceback
import gc
import time

import matplotlib.colors as mcolors
from matplotlib.cm import PuRd, viridis
import matplotlib.pyplot as plt


# LBAE imports
from modules.tools.image import convert_image_to_base64
from modules.tools.atlas import project_image, slice_to_atlas_transform
from modules.tools.volume import (
    filter_voxels,
    fill_array_borders,
    fill_array_interpolation,
    fill_array_slices,
    crop_array,
)
from config import dic_colors, l_colors
from modules.tools.spectra import (
    compute_image_using_index_and_image_lookup,
    compute_index_boundaries,
    compute_avg_intensity_per_lipid,
    global_lipid_index_store,
    compute_thread_safe_function,
)
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

def get_memory_usage():
    """Get current memory usage in MB"""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        return "psutil not available"

# ==================================================================================================
# --- Class
# ==================================================================================================


class Figures:
    """This class is used to produce the figures and widgets used in the app. It uses the special
    attribute __slots__ for faster access to the attributes. Parameters are ignored in the docstring
    of the listed methods below to save space. Please consult the docstring of the actual methods
    in the source-code for more information:

    Attributes:
        _data (MaldiData): MaldiData object, used to manipulate the raw MALDI data.
        _storage (Storage): Used to access the shelve database.
        _atlas (Atlas): Used to manipulate the objects coming from the Allen Brain Atlas.

    Methods:
        __init__(): Initialize the Figures class.
        ------------------------------------------------------------------------------------------
        compute_image_per_lipid(): Allows to query the MALDI data to extract an image representing
            the intensity of each lipid in the requested slice.
        build_lipid_heatmap_from_image(): Converts a numpy array into a base64 string, a go.Image,
            or a Plotly Figure.
        compute_heatmap_per_lipid_selection(): Computes a heatmap of the sum of expression of the
            requested lipids in the requested slice.
        compute_rgb_array_per_lipid_selection(): Computes a numpy RGB array of expression of the
            requested lipids in the requested slice.
        compute_rgb_image_per_lipid_selection(): Similar to compute_heatmap_per_lipid_selection, but
            computes an RGB image instead of a heatmap.
        compute_spectrum_low_res(): Returns the full (low-resolution) spectrum of the requested
            slice.
        compute_spectrum_high_res(): Returns the full (high-resolution) spectrum of the requested
            slice between the two provided m/z boundaries.
        return_empty_spectrum(): Returns an empty spectrum.
        return_heatmap_lipid(): Either generate a Plotly Figure containing an empty go.Heatmap,
            or complete the figure passed as argument with a proper layout that matches the theme of
            the app.
        compute_treemaps_figure(): Generates a Plotly Figure containing a treemap of the Allen Brain
            Atlas hierarchy.
        compute_3D_root_volume(): Generate a go.Isosurface of the Allen Brain root structure,
            which will be used to enclose the display of lipid expression of other structures in the
            brain.
        get_array_of_annotations(): Returns the array of annotations from the Allen Brain Atlas,
            subsampled to decrease the size of the output.
        compute_l_array_2D(): Gets the list of expression per slice for all slices for the
            computation of the 3D brain volume.
        compute_array_coordinates_3D(): Computes the list of coordinates and expression values for
            the voxels used in the 3D representation of the brain.
        compute_3D_volume_figure(): Computes a Plotly Figure containing a go.Volume object
            representing the expression of the requested lipids in the selected regions.
        compute_clustergram_figure(): Computes a Plotly Clustergram figure, allowing to cluster and
            compare the expression of all the MAIA-transformed lipids in the dataset in the selected
            regions.
        compute_scatter_3D(): cmputes a figure representing, in a 3D scatter plot, the spots
            acquired using spatial scRNAseq experiments.
        compute_barplots_enrichment(): Computes two figures representing, in barplots, the lipid
            expression in the spots acquired using spatial scRNAseq experiments, as well as how it
            can be explained by an elastic net regression using gene expression as explaing factors.
        compute_heatmap_lipid_genes(): Computes a heatmap representing the expression of a
        given lipid in the MALDI data and the expressions of the selected genes.
        shelve_arrays_basic_figures(): Shelves in the database all the arrays of basic images
            computed in compute_figure_basic_image(), across all slices and all types of arrays.
        shelve_all_l_array_2D(): Precomputes and shelves all the arrays of lipid expression used in
            a 3D representation of the brain.
        shelve_all_arrays_annotation(): Precomputes and shelves the array of structure annotation
            used in a 3D representation of the brain.
    """

    __slots__ = ["_data", "_celltype_data", "_lipizone_data", "_atlas", "_storage"]

    # ==============================================================================================
    # --- Constructor
    # ==============================================================================================

    def __init__(
        self,
        maldi_data,
        storage,
        atlas,
        celltype_data=None,
        lipizone_data=None,
        # gene_data=None,
        # brain_id, slice_index, lipid_name,
        # scRNAseq, sample=False
    ):
        """Initialize the Figures class.

        Args:
            maldi_data (MaldiData): MaldiData object, used to manipulate the raw MALDI data.
            storage (Storage): Used to access the shelve database.
            atlas (Atlas): Used to manipulate the objects coming from the Allen Brain Atlas.
            scRNAseq (ScRNAseq): Used to manipulate the objects coming from the scRNAseq dataset.
            sample (bool, optional): If True, only a fraction of the precomputations are made (for
                debug). Default to False.
        """
        logging.info("Initializing Figures object" + logmem())

        # Attribute to easily access the maldi and allen brain atlas data
        self._data = maldi_data
        self._atlas = atlas
        self._celltype_data = celltype_data
        self._lipizone_data = lipizone_data
        # self._gene_data = gene_data
        # self._scRNAseq = scRNAseq

        # attribute to access the shelve database
        self._storage = storage

        # Check that treemaps has been computed already. If not, compute it and store it.
        if not self._storage.check_shelved_object("figures/atlas_page/3D", "treemaps"):
            self._storage.return_shelved_object(
                "figures/atlas_page/3D",
                "treemaps",
                force_update=False,
                compute_function=self.compute_treemaps_figure,
            ),

        # # Check that 3D slice figures have been computed already. If not, compute it and store it.
        # for brain in ["brain_1", "brain_2"]:
        #     if not self._storage.check_shelved_object("figures/3D_page", "slices_3D_" + brain):
        #         self._storage.return_shelved_object(
        #             "figures/3D_page",
        #             "slices_3D",
        #             force_update=False,
        #             compute_function=self.compute_figure_slices_3D,
        #             brain=brain,
        #         )

        # # Check that the 3D root volume figure has been computed already. If not, compute it and
        # # store it.
        # if self._storage.check_shelved_object("figures/scRNAseq_page", "scatter3D"):
        #     self._storage.return_shelved_object(
        #         "figures/scRNAseq_page",
        #         "scatter3D",
        #         force_update=False,
        #         compute_function=self.compute_scatter_3D,
        #     )

        # # Check that the 3D scatter plot for scRNAseq data has been computed already. If not,
        # # compute it and store it.
        # if not self._storage.check_shelved_object("figures/3D_page", "volume_root"):
        #     self._storage.return_shelved_object(
        #         "figures/3D_page",
        #         "volume_root",
        #         force_update=False,
        #         compute_function=self.compute_3D_root_volume,
        #     )

        # # Check that the base figures for lipid/genes heatmap have been computed already. If not,
        # # compute them and store them.
        # if not self._storage.check_shelved_object(
        #     "figures/scRNAseq_page", "base_heatmap_lipid_True"
        # ) or not self._storage.check_shelved_object(
        #     "figures/scRNAseq_page", "base_heatmap_lipid_False"
        # ):
        #     self._storage.return_shelved_object(
        #         "figures/scRNAseq_page",
        #         "base_heatmap_lipid",
        #         force_update=False,
        #         compute_function=self.compute_heatmap_lipid_genes,
        #         brain_1=False,
        #     ),

        #     self._storage.return_shelved_object(
        #         "figures/scRNAseq_page",
        #         "base_heatmap_lipid",
        #         force_update=False,
        #         compute_function=self.compute_heatmap_lipid_genes,
        #         brain_1=True,
        #     ),

        # # Check that all basic figures in the load_slice page are present, if not, compute them
        # if not self._storage.check_shelved_object(
        #     "figures/load_page", "arrays_basic_figures_computed"
        # ):
        #     self.shelve_arrays_basic_figures()

        # # Check that the lipid distributions for all slices, and both brains, have been computed, if
        # # not, compute them
        # if not self._storage.check_shelved_object(
        #     "figures/3D_page", "arrays_expression_True_computed"
        # ):
        #     self.shelve_all_l_array_2D(sample=sample, brain_1=True)
        # if not self._storage.check_shelved_object(
        #     "figures/3D_page", "arrays_expression_False_computed"
        # ):
        #     self.shelve_all_l_array_2D(sample=sample, brain_1=False)
        # # Check that all arrays of annotations have been computed, if not, compute them
        # if not self._storage.check_shelved_object("figures/3D_page", "arrays_annotation_computed"):
        #     self.shelve_all_arrays_annotation()

        logging.info("Figures object instantiated" + logmem())

    # ==============================================================================================
    # --- Methods used mainly in load_slice
    # ==============================================================================================

    # ==============================================================================================
    # --- Methods used mainly in lipid_selection
    # ==============================================================================================

    def compute_image_per_lipid(
        self,
        slice_index,
        RGB_format=True,
        lipid_name="",
        cache_flask=None,
    ):
        """This function allows to query the MALDI data to extract an image in the form of a Numpy
        array representing the intensity of the lipid peaking between the values lb_mz and hb_mz in
        the spectral data, for the slice slice_index.

        Args:
            slice_index (int): Index of the requested slice.
            lb_mz (float): Lower boundary for the spectral data to query.
            hb_mz (float): Higher boundary for the spectral data to query.
            RGB_format (bool, optional): If True, the values in the array are between 0 and 255,
                given that the data has been normalized beforehand. Else, between 0 and 1. This
                parameter only makes sense if the data has been normalized beforehand. Defaults to
                True.
            normalize (bool, optional): If True, and the lipid has been MAIA transformed (and is
                provided with the parameter lipid_name) and apply_transform is True, the resulting
                array is normalized according to a factor computed across all slice. If MAIA has not
                been applied to the current selection or apply_transform is False, it is normalized
                according to the 99th percentile. Else, it is not normalized. Defaults to True.
            log (bool, optional): If True, the resulting array is log-transformed. This is useful in
                case of low expression. Defaults to False.
            projected_image (bool, optional): If True, the pixels of the original acquisition get
                matched to a higher-resolution, warped space. The gaps are filled by duplicating the
                most appropriate pixels (see dosctring of Atlas.project_image() for more
                information). Defaults to True.
            apply_transform (bool, optional): If True, applies the MAIA transform (if possible) to
                the current selection, given that the parameter normalize is also True, and that
                lipid_name corresponds to an existing lipid. Defaults to False.
            lipid_name (str, optional): Name of the lipid that must be MAIA-transformed, if
                apply_transform and normalize are True. Defaults to "".
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.
        Returns:
            (np.ndarray): An image (in the form of a numpy array) representing the intensity of the
                lipid peaking between the values lb_mz and hb_mz in the spectral data, for the slice
                slice_index.
        """
        logging.info("Entering compute_image_per_lipid")
        
        image = self._data.extract_lipid_image(slice_index, lipid_name)
        
        # In case of bug, return None
        if image is None:
            return None

        # Turn to RGB format if requested
        if RGB_format:
            image *= 255

        return image

    def build_lipid_heatmap_from_image(
        self,
        image,
        return_base64_string=False,
        draw=False,
        type_image=None,
        return_go_image=False,
        overlay=None,
        colormap_type="viridis",
    ):
        """This function converts a numpy array into a base64 string, which can be returned
        directly, or itself be turned into a go.Image, which can be returned directly, or be
        turned into a Plotly Figure, which will be returned.

        Args:
            image (np.ndarray): A numpy array representing the image to be converted. Possibly with
                several channels.
            return_base64_string (bool, optional): If True, the base64 string of the image is
                returned directly, before any figure building. Defaults to False.
            draw (bool, optional): If True, the user will have the possibility to draw on the
                resulting Plotly Figure. Defaults to False.
            type_image (string, optional): The type of the image to be converted to a base64 string.
                If image_array is in 3D, type must be RGB. If 4D, type must be RGBA. Else, no
                requirement (None). Defaults to None.
            return_go_image (bool, optional): If True, the go.Image is returned directly, before
                being integrated to a Plotly Figure. Defaults to False.
            overlay (np.ndarray, optional): An array representing the overlay to be added to the
                image. Defaults to None.
            colormap_type (str, optional): The type of colormap to use. Options are "viridis" or "PuOr".
                Defaults to "viridis".
        Returns:
            Depending on the inputted arguments, may either return a base64 string, a go.Image, or
                a Plotly Figure.
        """

        logging.info("Converting image to string")
        print(image.shape)
        # Set optimize to False to gain computation time
        base64_string = convert_image_to_base64(
            image, 
            type=type_image, 
            overlay=overlay, 
            transparent_zeros=True, 
            optimize=False, 
            colormap_type=colormap_type
        )

        # Either return image directly
        if return_base64_string:
            return base64_string

        # Or compute heatmap as go image if needed
        logging.info("Converting image to go image")
        final_image = go.Image(
            visible=True,
            source=base64_string,
        )

        # Potentially return the go image directly
        if return_go_image:
            return final_image

        # Or build ploty graph
        fig = go.Figure(final_image)

        # Improve graph layout
        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            newshape=dict(
                fillcolor=dic_colors["blue"], opacity=0.7, line=dict(color="white", width=1)
            ),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            # Do not specify height for now as plotly is buggued and resets if switching pages
            # height=500,
        )
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update(layout_coloraxis_showscale=False)

        # Set how the image should be annotated
        if draw:
            fig.update_layout(dragmode="drawclosedpath")
        else:
            # Set default dragmode to pan for better touchpad navigation
            fig.update_layout(dragmode="pan")

        # Set background color to zero
        fig.layout.template = "plotly_dark"
        fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig.layout.paper_bgcolor = "rgba(0,0,0,0)"
        
        # Enable scroll zoom directly on the figure object
        # This is the most minimal change possible
        fig._config = {'scrollZoom': True}
        
        logging.info("Returning figure")

        return fig

    def compute_heatmap_per_lipid(
        self,
        slice_index,
        lipid_name,
        draw=False,
        return_base64_string=False,
        cache_flask=None,
        overlay=None,
        colormap_type="viridis",
    ):
        """This function takes two boundaries and a slice index, and returns a heatmap of the lipid
        expressed in the slice whose m/z is between the two boundaries.

        Args:
            slice_index (int): The index of the requested slice.
            lb_mz (float, optional): The lower m/z boundary. Defaults to None.
            hb_mz (float, optional): The higher m/z boundary. Defaults to None.
            draw (bool, optional): If True, the user will have the possibility to draw on the
                resulting Plotly Figure. Defaults to False.
            projected_image (bool, optional): If True, the pixels of the original acquisition get
                matched to a higher-resolution, warped space. The gaps are filled by duplicating the
                most appropriate pixels (see dosctring of Atlas.project_image() for more
                information). Defaults to True.
            return_base64_string (bool, optional): If True, the base64 string of the image is
                returned directly, before any figure building. Defaults to False.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.
        Returns:
            Depending on the value return_base64_string, may either return a base64 string, or
                a Plotly Figure.
        """

        logging.info("Starting figure computation")

        logging.info("Getting image array")

        # Compute image with given bounds
        image = self.compute_image_per_lipid(
            slice_index,
            RGB_format=False,
            lipid_name=lipid_name,
            cache_flask=cache_flask,
        )

        # Compute corresponding figure
        fig = self.build_lipid_heatmap_from_image(
            image, 
            return_base64_string=return_base64_string, 
            draw=draw, 
            overlay=overlay, 
            colormap_type=colormap_type
        )

        return fig

    def compute_rgb_array_per_lipid_selection(
        self,
        slice_index,
        ll_lipid_names=None,
        cache_flask=None,
    ):
        """This function computes a numpy RGB array (each pixel has 3 intensity values) of
        expression of the requested lipids (those whose m/z values are in ll_t_bounds) in the slice.

        Args:
            slice_index (int): The index of the requested slice.
            ll_t_bounds (list(list(tuple))): A list of lists of lipid boundaries (tuples). The first
                list is used to separate image channels. The second list is used to separate lipid.
            normalize_independently (bool, optional): If True, each lipid intensity array is
                normalized independently, regardless of other lipids or channel used. Defaults to
                True.
            projected_image (bool, optional): If True, the pixels of the original acquisition get
                matched to a higher-resolution, warped space. The gaps are filled by duplicating the
                most appropriate pixels (see dosctring of Atlas.project_image() for more
                information). Defaults to True.
            log (bool, optional): If True, the resulting array corresponds to log-transformed
                expression, for each lipid. Defaults to False.
            apply_transform (bool, optional): If True, applies the MAIA transform (if possible) to
                the current selection, given that the parameter normalize is also True, and that
                lipid_name corresponds to an existing lipid. Defaults to False.
            ll_lipid_names (list(list(int)), optional): List of list of lipid names that must be
                MAIA-transformed, if apply_transform and normalize are True. The first list is used
                to separate channels, when applicable. Defaults to None.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.

        Returns:
            (np.ndarray): A three-dimensional RGB numpy array (of uint8 dtype). The first two
                dimensions correspond to the acquisition image shape, and the third dimension
                corresponds to the channels.
        """

        # Build a list of empty images and add selected lipids for each channel
        l_images = []
        
        # Loop over channels
        for lipid_name in ll_lipid_names:
            # Compute expression image per lipid
            image_temp = self.compute_image_per_lipid(
                slice_index,
                RGB_format=True,
                lipid_name=lipid_name,
                cache_flask=cache_flask,
            ) if lipid_name is not None else np.full(self._data.image_shape, np.nan)

            l_images.append(image_temp)

        # Reoder axis to match plotly go.image requirementss
        array_image = np.moveaxis(np.array(l_images), 0, 2)
        
        return array_image

    def compute_rgb_image_per_lipid_selection(
        self,
        slice_index,
        return_image=False,
        ll_lipid_names=None,
        return_base64_string=False,
        cache_flask=None,
        overlay=None,
    ):
        """This function is very similar to compute_heatmap_per_lipid_selection, but it returns a
        RGB image instead of a heatmap.

        Args:
            slice_index (int): The index of the requested slice.
            ll_t_bounds (list(list(tuple))): A list of lists of lipid boundaries (tuples). The first
                list is used to separate image channels. The second list is used to separate lipid.
            normalize_independently (bool, optional): If True, each lipid intensity array is
                normalized independently, regardless of other lipids or channel used. Defaults to
                True.
            projected_image (bool, optional): If True, the pixels of the original acquisition get
                matched to a higher-resolution, warped space. The gaps are filled by duplicating the
                most appropriate pixels (see dosctring of Atlas.project_image() for more
                information). Defaults to True.
            log (bool, optional): If True, the resulting array corresponds to log-transformed
                expression, for each lipid. Defaults to False.
            return_image (bool, optional): If True, a go.Image is returned directly, instead of a
                Plotly Figure. Defaults to False.
            apply_transform (bool, optional): If True, applies the MAIA transform (if possible) to
                the current selection, given that the parameter normalize is also True, and that
                lipid_name corresponds to an existing lipid. Defaults to False.
            ll_lipid_names (list(list(int)), optional): List of list of lipid names that must be
                MAIA-transformed, if apply_transform and normalize are True. The first list is used
                to separate channels, when applicable. Defaults to None.
            return_base64_string (bool, optional): If True, the base64 string of the image is
                returned directly, before any figure building. Defaults to False.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.

        Returns:
            Depending on the inputted arguments, may either return a base64 string, a go.Image, or
                a Plotly Figure.
        """

        logging.info("Started RGB image computation for slice " + str(slice_index) + logmem())
        logging.info("Acquiring array_image for slice " + str(slice_index) + logmem())

        # Get RGB array for the current lipid selection
        array_image = self.compute_rgb_array_per_lipid_selection(
            slice_index,
            ll_lipid_names=ll_lipid_names,
            cache_flask=cache_flask,
        )

        logging.info("Returning fig for slice " + str(slice_index) + logmem())

        # Build the correspondig figure
        return self.build_lipid_heatmap_from_image(
            array_image,
            return_base64_string=return_base64_string,
            draw=False,
            type_image="RGB",
            return_go_image=return_image,
            overlay=overlay,
        )

    # ==============================================================================================
    # --- Methods used mainly in region_analysis
    # ==============================================================================================

    # def return_heatmap_lipid(self, fig=None):
    #     """This function is used to either generate a Plotly Figure containing an empty go.Heatmap,
    #     or complete the figure passed as argument with a proper layout that matches the theme of the
    #     app.

    #     Args:
    #         fig (Plotly Figure, optional): A Plotly Figure whose layout must be completed. If None,
    #             a new figure will be generated. Defaults to None.

    #     Returns:
    #         (Plotly Figure): A Plotly Figure containing an empty go.Heatmap, or complete the figure
    #             passed as argument with a proper layout that matches the theme of the app.
    #     """

    #     # Build empty figure if not provided
    #     if fig is None:
    #         fig = go.Figure(data=go.Heatmap(z=[[]], x=[], y=[], visible=False))

    #     # Improve figure layout
    #     fig.update_layout(
    #         margin=dict(t=25, r=0, b=10, l=0),
    #         template="plotly_dark",
    #         font_size=8,
    #     )

    #     # Transparent background
    #     fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
    #     fig.layout.paper_bgcolor = "rgba(0,0,0,0)"

    #     # Dark Template
    #     fig.layout.template = "plotly_dark"

    #     return fig

    # ==============================================================================================
    # --- Methods used mainly in lipizones-related pages
    # ==============================================================================================
    
    def all_lipizones_default_image(self, brain_id="ReferenceAtlas"):
        def hex_to_rgb(hex_color):
            """Convert hexadecimal color to RGB values (0-1 range)"""
            hex_color = hex_color.lstrip('#')
            return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)]) / 255.0
        
        # try:
        # Retrieve sample data from shelve database
        sample_data = self._lipizone_data.sample_data.retrieve_sample_data(brain_id)
        color_masks = sample_data["color_masks"]
        grayscale_image = sample_data["grayscale_image"]
        rgb_image = sample_data["grid_image"][:, :, :3]  # remove transparency channel for now
        # except KeyError:
        #     # Fallback to default files if sample not found
        #     logging.warning(f"Sample data for {brain_id} not found, using default files")
        #     def load_color_masks_pickle(filename):
        #         import pickle
        #         with open(filename, 'rb') as f:
        #             color_masks = pickle.load(f)
        #         logging.info(f"Loaded {len(color_masks)} color masks from {filename}")
        #         return color_masks
            
        #     color_masks = load_color_masks_pickle(os.path.join(self._lipizone_data.sample_data.path_data, 'color_masks.pkl'))
        #     grayscale_image = np.load(os.path.join(self._lipizone_data.sample_data.path_data, 'grayscale_image.npy'))
        #     rgb_image = np.load(os.path.join(self._lipizone_data.sample_data.path_data, 'grid_image_lipizones.npy'))[:, :, :3]
        
        # Apply square root transformation to enhance contrast
        # grayscale_image = np.sqrt(np.sqrt(grayscale_image))
        grayscale_image = np.power(grayscale_image, float(1/6))
        grayscale_image = gaussian_filter(grayscale_image, sigma=3)
        # grayscale_image = np.power(grayscale_image, 2) * 0.3
        grayscale_image *= ~color_masks[list(color_masks.keys())[0]]
        
        rgb_colors_to_highlight = [hex_to_rgb(hex_color) for hex_color in self._lipizone_data.lipizone_to_color.values()]
        
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
                # Find closest color
                distances = np.array([np.sum((np.array(color) - target_rgb) ** 2) for color in color_masks.keys()])
                closest_color_idx = np.argmin(distances)
                closest_color = list(color_masks.keys())[closest_color_idx]
                
                # If close enough to our target color, add its mask
                if distances[closest_color_idx] < 0.05:  # Threshold for color similarity
                    combined_mask |= color_masks[closest_color]
        
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

        # Pad the image: note that no padding is added on the right.
        padded_image = np.pad(
            hybrid_image,
            pad_width=((pad_top, pad_bottom), (pad_left, 0), (0, 0)),
            mode='constant',
            constant_values=np.nan
        )

        return padded_image


    def compute_image_lipizones_celltypes(
        self,
        all_selected_lipizones, 
        all_selected_celltypes, 
        slice_index,
        celltype_radius=1):  # New parameter for tunable square radius
        
        # Get the names of all selected lipizones and celltypes
        selected_lipizone_names = all_selected_lipizones.get("names", [])
        selected_celltype_names = all_selected_celltypes.get("names", [])
        
        # Define colors for both lipizones and celltypes
        hex_colors_to_highlight_lipizones = [self._lipizone_data.lipizone_to_color[name] for name in selected_lipizone_names if name in self._lipizone_data.lipizone_to_color]
        rgb_colors_to_highlight_celltypes = [self._celltype_data.celltype_to_color[name] for name in selected_celltype_names if name in self._celltype_data.celltype_to_color]
        
        # Get section data for both lipizones and celltypes
        section_data_lipizones = self._lipizone_data.section_data.retrieve_section_data(float(slice_index))
        section_data_celltypes = self._celltype_data.retrieve_section_data(int(slice_index))
        
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
            celltype_name = list(self._celltype_data.celltype_to_color.keys())[list(self._celltype_data.celltype_to_color.values()).index(target_rgb)]
            
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
        
        
        # Apply color masks to respective sides
        for i in range(3):
            # Apply grayscale background to both sides
            lipizones_celltypes_image[:, :, i] = grayscale_image
            # Left side (lipizones)
            lipizones_celltypes_image[:, :mid_point, i][combined_mask_lipizones] = rgb_image[:, :mid_point, i][combined_mask_lipizones]
            # Right side (celltypes)
            lipizones_celltypes_image[:, mid_point:, i][celltype_mask] = celltype_colors[..., i][celltype_mask]
        
        # Final processing
        lipizones_celltypes_image = (lipizones_celltypes_image*255) + 1
        mask = np.all(lipizones_celltypes_image == 1, axis=-1)
        lipizones_celltypes_image[mask] = np.nan

        return lipizones_celltypes_image

    def create_lipizone_3d_figure(self, array, color, downsample_factor=12):
        """
        Create a 3D visualization of a lipizone array
        
        Parameters:
        -----------
        array : numpy.ndarray
            3D array with the lipizone data
        color : str
            HTML color code for the lipizone
        downsample_factor : int
            Factor by which to downsample the array to reduce memory usage
            
        Returns:
        --------
        go.Volume
            The 3D volume for the lipizone
        """
        try:
            # Downsample the array to make visualization more manageable
            if downsample_factor > 1:
                array = array[::downsample_factor, ::downsample_factor, ::downsample_factor]
            
            # Create coordinate grid based on array shape
            z, y, x = np.indices(array.shape)
            
            # Replace NaN values with 0 for visualization
            array_viz = np.copy(array)
            array_viz = np.nan_to_num(array_viz)
            
            # Create the 3D volume
            lipizone3D_data = go.Volume(
                x=x.flatten(),
                y=y.flatten(),
                z=z.flatten(),
                value=array_viz.flatten(),
                isomin=0.01,  # Only show values above this threshold
                isomax=1.0,
                opacity=0.7,  # Increase opacity for better visibility
                surface_count=10,  # Reduce surface count for performance
                colorscale=[[0, 'rgba(0,0,0,0)'], [1, color]],
                caps=dict(x_show=False, y_show=False, z_show=False),
                showscale=False,  # Added this line to hide the colorbar
            )
            
            # Clean up to free memory
            del array_viz, x, y, z
            gc.collect()
            
            return lipizone3D_data
            
        except Exception as e:
            logging.error(f"Error creating 3D figure: {str(e)}")
            logging.error(traceback.format_exc())
            raise e

    def create_all_lipizones_figure(self, downsample_factor=1):
        """
        Create a 3D visualization of all lipizones together using the color array
        
        Parameters:
        -----------
        downsample_factor : int
            Factor by which to downsample the array to reduce memory usage
            
        Returns:
        --------
        go.Figure
            The 3D figure with the volume rendering
        """
        try:
            start_time = time.time()
            # logging.info("Loading all lipizones color array")
            
            # Load the color array
            color_array = np.load(self._lipizone_data.COLOR_ARRAY_PATH)
            
            # Downsample the array
            if downsample_factor > 1:
                color_array = color_array[::downsample_factor, ::downsample_factor, ::downsample_factor, :]
                # logging.info(f"Downsampled color array to shape: {color_array.shape}")
            
            # Create coordinate grid based on array shape
            z, y, x = np.indices(color_array.shape[:3])
            
            # Create a mask for voxels with non-zero values
            # Convert RGB to a single intensity value based on average brightness
            intensity = np.mean(color_array, axis=-1)
            mask = intensity > 0
            
            if not np.any(mask):
                logging.warning("No non-zero values found in the color array!")
                return go.Figure().update_layout(
                    title="No data found in color array",
                    template="plotly_dark",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
            
            # Normalize RGB values to 0-1 range if they're not already
            if color_array.max() > 1:
                color_array = color_array / 255.0
            
            # Get the coordinates and colors of non-zero voxels
            x_points = x[mask]
            y_points = y[mask]
            z_points = z[mask]
            colors = color_array[mask]
            
            
            # Create a figure with a scatter3d trace using the actual RGB colors
            fig = go.Figure()
            
            # Add a scatter3d trace for the point cloud with RGB colors
            color_strings = [f'rgb({r*255},{g*255},{b*255})' for r, g, b in colors]
            # Reduce points if there are too many (for performance)

            max_points = 400000 # Limit the number of points for performance
            if len(x_points) > max_points:
                indices = np.random.choice(len(x_points), max_points, replace=False)
                x_points = x_points[indices]
                y_points = y_points[indices]
                z_points = z_points[indices]
                color_strings = [color_strings[i] for i in indices]
            
            # Add the scatter3d trace
            fig.add_trace(go.Scatter3d(
                x=x_points, 
                y=y_points, 
                z=z_points,
                mode='markers',
                marker=dict(
                    size=downsample_factor,  # Increased size from 2 to 10 (5x larger)
                    color=color_strings,
                    opacity=1.0
                ),
                hoverinfo='none'
            ))
            
            # Improve layout
            fig.update_layout(
                margin=dict(t=0, r=0, b=0, l=0),
                scene=dict(
                    xaxis=dict(
                        showticklabels=False,
                        showgrid=False,
                        zeroline=False,
                        backgroundcolor="rgba(0,0,0,0)",
                    ),
                    yaxis=dict(
                        showticklabels=False,
                        showgrid=False,
                        zeroline=False,
                        backgroundcolor="rgba(0,0,0,0)",
                    ),
                    zaxis=dict(
                        showticklabels=False,
                        showgrid=False,
                        zeroline=False,
                        backgroundcolor="rgba(0,0,0,0)",
                    ),
                    aspectmode="data",
                ),
                template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            
            # Clean up to free memory
            del color_array, x, y, z, x_points, y_points, z_points, colors, color_strings
            gc.collect()
            
            end_time = time.time()
            logging.info(f"All lipizones figure creation completed in {end_time - start_time:.2f} seconds")
            
            return fig
            
        except Exception as e:
            logging.error(f"Error creating all lipizones figure: {str(e)}")
            logging.error(traceback.format_exc())
            raise e

    # ==============================================================================================
    # --- Methods used mainly in lipizones-related pages
    # ==============================================================================================

    def compute_image_lipids_genes(
        self,
        all_selected_lipids, 
        all_selected_genes, 
        slice_index,
        df_genes,
        rgb_mode_lipids=True,
        celltype_radius=1):

        # Get section data for both lipizones and celltypes
        section_data_lipizones = self._lipizone_data.section_data.retrieve_section_data(float(slice_index))
        grayscale_image = section_data_lipizones["grayscale_image"]
        grayscale_image = np.power(grayscale_image, float(1/6))
        grayscale_image = gaussian_filter(grayscale_image, sigma=3)

        section_data_celltypes = self._celltype_data.retrieve_section_data(int(slice_index))
        color_masks_celltypes = section_data_celltypes["color_masks"]
        df_genes_filtered = df_genes[df_genes.index.isin(section_data_celltypes["color_masks"].keys())]

        lipid_gene_image = np.zeros((grayscale_image.shape[0], grayscale_image.shape[1], 3))
        mid_point = lipid_gene_image.shape[1] // 2

        # Define the colorscales for each gene
        gene_colorscales = [
            plt.cm.Oranges, 
            plt.cm.Greens, 
            plt.cm.Blues, 
        ]

        lipid_image = self.compute_rgb_array_per_lipid_selection(
                            slice_index,
                            ll_lipid_names=all_selected_lipids,
                        ) if rgb_mode_lipids else viridis(self.compute_image_per_lipid(
                            slice_index,
                            lipid_name=all_selected_lipids[0],
                            RGB_format=False,
                            cache_flask=False,
                        ))*255

        # Create the overlay: grayscale background with lipid expression on the left side
        for i in range(3):  # For each RGB channel
            # First set the entire image to the grayscale value
            lipid_gene_image[:, :, i] = grayscale_image*255
            
            # Left side (lipid expression)
            try:
                lipid_gene_image[:, :mid_point, i] = lipid_image[:, :mid_point, i]
            except:
                lipid_gene_image[:, :mid_point, i] = np.zeros_like(lipid_gene_image[:, :mid_point, i])
        
        # Create a blank overlay for gene expression with weighted blending
        gene_overlay = np.zeros_like(lipid_gene_image[:, mid_point:, :])
        # Track how many genes are expressed in each pixel for blending
        gene_count = np.zeros((lipid_gene_image.shape[0], lipid_gene_image.shape[1] - mid_point), dtype=np.float32)
        
        # Right side (gene expression) - apply each gene with its own colorscale
        for gene_idx, gene in enumerate(all_selected_genes):
            if gene_idx >= 3:  # Only process up to 3 genes
                break
                
            # Get the appropriate colorscale for this gene
            colorscale = gene_colorscales[gene_idx]
            
            # Calculate min and max expression for this specific gene
            # This ensures each gene gets its full colorscale range
            gene_values = df_genes_filtered[gene].values
            gene_values = gene_values[~np.isnan(gene_values)]  # Remove NaN values
            if len(gene_values) > 0:
                min_val = gene_values.min()
                max_val = gene_values.max()
                # Create a normalization specific to this gene
                gene_norm = mcolors.Normalize(vmin=min_val, vmax=max_val)
            else:
                # If no valid values, skip this gene
                continue
            
            # Process each cell type for this gene
            for celltype in color_masks_celltypes.keys():
                cell_mask = color_masks_celltypes[celltype].T.copy()
                
                # Expand the mask to include neighboring pixels for better visibility
                y_coords, x_coords = np.where(cell_mask)
                for y, x in zip(y_coords, x_coords):
                    y_min = max(0, y - celltype_radius)
                    y_max = min(cell_mask.shape[0], y + celltype_radius + 1)
                    x_min = max(0, x - celltype_radius)
                    x_max = min(cell_mask.shape[1], x + celltype_radius + 1)
                    
                    cell_mask[y_min:y_max, x_min:x_max] = True
                
                # Get gene expression value for this celltype
                try:
                    genexpr_value = df_genes_filtered.loc[celltype, gene]
                except:
                    genexpr_value = 0
                
                # Apply the colorscale to this cell mask using the gene-specific normalization
                if not np.isnan(genexpr_value) and genexpr_value > min_val:
                    color_values = colorscale(gene_norm(genexpr_value))  # This gives RGB values
                    
                    # Apply each color channel separately - to the overlay
                    right_side_mask = cell_mask[:, mid_point:]
                    for i in range(3):  # RGB channels
                        # Add this gene's color to the overlay
                        gene_overlay[:, :, i][right_side_mask] += color_values[i] * 255
                    
                    # Increment gene count for these pixels
                    gene_count[right_side_mask] += 1
        
        # Apply the blended gene overlay to the right side of the image
        # Normalize by gene count to prevent oversaturation
        for i in range(3):
            # Where gene_count > 0, apply normalized gene colors
            mask = gene_count > 0
            if np.any(mask):
                normalized_overlay = np.zeros_like(gene_overlay[:, :, i])
                normalized_overlay[mask] = gene_overlay[:, :, i][mask] / gene_count[mask]
                # Apply the normalized overlay to the right side
                lipid_gene_image[:, mid_point:, i] = np.where(mask, normalized_overlay, lipid_gene_image[:, mid_point:, i])
        
        # Final processing
        binary_mask = np.where(self._data.acronyms_masks[slice_index] == 'Undefined', np.nan, 1)
        lipid_gene_image = lipid_gene_image*binary_mask[..., np.newaxis]

        return lipid_gene_image

    # ==============================================================================================
    # --- Methods used mainly in threeD_exploration
    # ==============================================================================================

    def compute_treemaps_figure(self, maxdepth=5):
        """Generate a Plotly treemap of the Allen Brain Atlas hierarchy using colors
        extracted from the Allen Brain Atlas API.

        Args:
            maxdepth (int, optional): The depth of the treemap to generate. Defaults to 5.

        Returns:
            Plotly.Figure: A Plotly Figure containing the customized treemap.
        """
        import requests
        import plotly.express as px

        # --- 1. Fetch the structure tree from the Allen Brain Atlas API ---
        url = "http://api.brain-map.org/api/v2/structure_graph_download/1.json"
        response = requests.get(url)
        data = response.json()

        # --- 2. Extract a mapping from region name to its color hex code ---
        def extract_name_to_color(node):
            """
            Recursively extract a mapping from the structure's name to its color_hex_triplet.
            """
            mapping = {}
            if 'name' in node and 'color_hex_triplet' in node:
                mapping[node['name']] = node['color_hex_triplet']
            if 'children' in node:
                for child in node['children']:
                    mapping.update(extract_name_to_color(child))
            return mapping

        name_to_color = {}
        if 'msg' in data:
            for item in data['msg']:
                name_to_color.update(extract_name_to_color(item))

        # --- 3. Build the treemap figure using your atlas nodes and parents ---
        fig = px.treemap(
            names=self._atlas.l_nodes,
            parents=self._atlas.l_parents,
            maxdepth=maxdepth
        )

        # --- 4. Create a list of colors for each node using the extracted mapping ---
        # If a node name is not found in the mapping, use a default color "#1d3d5c"
        colors = ['#' + name_to_color.get(name, "1d3d5c") for name in self._atlas.l_nodes]
        fig.data[0].marker.colors = colors

        # --- 5. Update layout for aesthetics ---
        fig.update_layout(
            uniformtext=dict(minsize=15),
            margin=dict(t=30, r=0, b=10, l=0),
        )
        fig.layout.template = "plotly_dark"
        fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig.layout.paper_bgcolor = "rgba(0,0,0,0)"

        return fig

    '''
    def compute_3D_root_volume(self, decrease_dimensionality_factor=7, differentiate_borders=False):
        """This function is used to generate a go.Isosurface of the Allen Brain root structure,
        which will be used to enclose the display of lipid expression of other structures in the
        brain.

        Args:
            decrease_dimensionality_factor (int, optional): Decrease the dimensionnality of the
                brain to display, to get a lighter output. Defaults to 7.

        Returns:
            (go.Isosurface): A semi-transparent go.Isosurface of the Allen Brain root structure.
        """

        # Get array of annotations, which associate coordinate to id
        array_annotation_root = np.array(self._atlas.bg_atlas.annotation, dtype=np.int32)

        # Subsample array of annotation the same way array_atlas was subsampled
        array_annotation_root = array_annotation_root[
            ::decrease_dimensionality_factor,
            ::decrease_dimensionality_factor,
            ::decrease_dimensionality_factor,
        ]


        # Bug correction for the last slice
        #array_annotation_root = np.concatenate(
        #    (
        #        array_annotation_root,
        #        np.zeros((1, array_annotation_root.shape[1], array_annotation_root.shape[2])),
        #    )
        #)

        # Get the volume array
        array_atlas_borders_root = fill_array_borders(
            array_annotation_root,
            differentiate_borders=differentiate_borders,
            color_near_borders=False,
            keep_structure_id=None,
        )

        print(array_atlas_borders_root.shape)
        
        # Compute the 3D grid
        X_root, Y_root, Z_root = np.mgrid[
            0 : array_atlas_borders_root.shape[0]
            / 1000
            * 25
            * decrease_dimensionality_factor : array_atlas_borders_root.shape[0]
            * 1j,
            0 : array_atlas_borders_root.shape[1]
            / 1000
            * 25
            * decrease_dimensionality_factor : array_atlas_borders_root.shape[1]
            * 1j,
            0 : array_atlas_borders_root.shape[2]
            / 1000
            * 25
            * decrease_dimensionality_factor : array_atlas_borders_root.shape[2]
            * 1j,
        ]

        # Compute the plot
        brain_root_data = go.Isosurface(
            x=X_root.flatten(),
            y=Y_root.flatten(),
            z=Z_root.flatten(),
            value=array_atlas_borders_root.flatten(),
            isomin=-0.21,
            isomax=2.55,
            opacity=0.1,  # max opacity
            surface_count=2,
            colorscale="Blues",  # colorscale,
            flatshading=True,
            showscale=False,
        )

        return brain_root_data
    '''

    def compute_3D_root_volume(self, decrease_dimensionality_factor=7, differentiate_borders=False):
        """This function is used to generate a go.Volume (changed from Isosurface) of the Allen Brain root structure,
        which will be used to enclose the display of lipid expression of other structures in the brain.

        Args:
            decrease_dimensionality_factor (int, optional): Decrease the dimensionality of the
                brain to display, to get a lighter output. Defaults to 7.
        Returns:
            (go.Volume): A semi-transparent go.Volume of the Allen Brain root structure.
        """
        # Get array of annotations, which associate coordinate to id
        array_annotation_root = np.array(self._atlas.bg_atlas.annotation, dtype=np.int32)

        # Subsample array of annotation
        array_annotation_root = array_annotation_root[
            ::decrease_dimensionality_factor,
            ::decrease_dimensionality_factor,
            ::decrease_dimensionality_factor,
        ]

        # Get the volume array
        array_atlas_borders_root = fill_array_borders(
            array_annotation_root,
            differentiate_borders=differentiate_borders,
            color_near_borders=False,
            keep_structure_id=None,
        )
        # print(array_atlas_borders_root.shape)

        # IMPORTANT CHANGE: Use np.indices instead of np.mgrid to match the lipid visualization
        # Create coordinate grid based on array shape
        z_root, y_root, x_root = np.indices(array_atlas_borders_root.shape)

        # Compute the plot, now using go.Volume instead of go.Isosurface
        brain_root_data = go.Volume(
            x=x_root.flatten(),
            y=y_root.flatten(),
            z=z_root.flatten(),
            value=array_atlas_borders_root.flatten(),
            isomin=-0.21,
            isomax=2.55,
            opacity=0.1,
            surface_count=2,
            colorscale="Greys",
            caps=dict(x_show=False, y_show=False, z_show=False),
        )
        return brain_root_data

    def get_array_of_annotations(self, decrease_dimensionality_factor):
        """This function returns the array of annotations from the Allen Brain Atlas, subsampled to
        decrease the size of the output.
        Args:
            decrease_dimensionality_factor (int): An integer used for subsampling the array. The
                higher, the higher the subsampling.

        Returns:
            (np.ndarray): A 3D array of annotation, in which structures are annotated with specific
                identifiers.
        """
        # Get subsampled array of annotations
        array_annotation = np.array(
            self._atlas.bg_atlas.annotation[
                ::decrease_dimensionality_factor,
                ::decrease_dimensionality_factor,
                ::decrease_dimensionality_factor,
            ],
            dtype=np.int32,
        )

        # Bug correction for the last slice
        # array_annotation = np.concatenate(
        #     (
        #         array_annotation,
        #         np.zeros((1, array_annotation.shape[1], array_annotation.shape[2])),
        #     )
        # )

        return array_annotation

    def compute_3D_volume_figure(
        self,
        lipid_name,
        annotation_path=None,
        set_id_regions=None,
        downsample_factor=1,
        opacity=0.4,
        surface_count=15,  # Reduced from 40 to 15
        colorscale="Inferno",
    ):
        """
        Render a 3D volume visualization of lipid data with optional region filtering and grayscale root data.
        Uses optimized rendering settings for better performance.

        Parameters:
        -----------
        lipid_name : str
            Name of the lipid file to load
        annotation_path : str, optional
            Path to the annotation file with region labels
        set_id_regions : list, optional
            List of region IDs to include in the visualization
        downsample_factor : int, default=1
            Factor by which to downsample the data (higher = less detailed but faster)
        opacity : float, default=0.1
            Base opacity for the volume rendering
        surface_count : int, default=15
            Number of isosurfaces to display
        colorscale : str, default='Inferno'
            Colorscale for the visualization

        Returns:
        --------
        fig : plotly.graph_objects.Figure
            The 3D volume figure
        """
        # Load lipid data
        lipid_path = f"./data/3d_interpolated_native/{lipid_name}interpolation_log.npy"
        np3d = np.load(lipid_path)

        # print(downsample_factor)

        # CRITICAL: Use the same downsampling factor for both datasets
        # Get root data with the same downsampling factor
        root_data = self.compute_3D_root_volume(
            decrease_dimensionality_factor=downsample_factor * 4
        )
        
        # Get annotations with the same downsampling factor
        annotations = self.get_array_of_annotations(
            decrease_dimensionality_factor=downsample_factor * 4
        )
        # Downsample lipid data for better performance
        sub_np3d = np3d[::downsample_factor, ::downsample_factor, ::downsample_factor]
        
        # Apply region filtering if regions are provided
        if set_id_regions is not None:
            # Create mask for selected regions
            mask = np.zeros_like(annotations, dtype=bool)
            for region_id in set_id_regions:
                mask = np.logical_or(mask, annotations == region_id)

            # Apply mask to lipid data
            sub_np3d_clean = sub_np3d.copy()
            sub_np3d_clean[~mask] = np.nan
        else:
            # If no filtering, use the downsampled data as is
            sub_np3d_clean = sub_np3d

        # print(sub_np3d_clean.shape)

        # Create coordinate grid for lipid data
        z, y, x = np.indices(sub_np3d_clean.shape)

        # Define custom opacity scale for better visualization (from old implementation)
        # This makes background transparent while highlighting important features
        opacityscale = [
            [0.0, 0.0],      # Fully transparent for background/low values
            [0.3, 0.2],      # Increase from 0.05 to 0.2
            [0.7, 0.5],      # Increase from 0.2 to 0.5
            [1.0, 0.8]       # Increase from 0.5 to 0.8
        ]

        # Set up volume plot with lipid data
        lipid_volume = go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=sub_np3d_clean.flatten(),
            isomin=np.nanmin(sub_np3d_clean) if not np.isnan(sub_np3d_clean).all() else 0,
            isomax=np.nanmax(sub_np3d_clean) if not np.isnan(sub_np3d_clean).all() else 1,
            # Replace flat opacity with custom opacity scale
            opacityscale=opacityscale,
            surface_count=surface_count,  # Reduced from 40 to 15
            colorscale=colorscale,
            caps=dict(x_show=False, y_show=False, z_show=False),
        )

        # Create figure with both lipid and root data, root data first for proper layering
        fig = go.Figure(data=[root_data, lipid_volume])

        # Improve layout
        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            scene=dict(
                xaxis=dict(
                    showticklabels=True,
                    showgrid=True,
                    zeroline=False,
                    backgroundcolor="rgba(0,0,0,0)",
                    showline=False,
                    tickmode="auto",
                    nticks=5,  # Infrequent ticks
                    gridcolor="rgba(255,255,255,0.1)",  # Light grid
                ),
                yaxis=dict(
                    showticklabels=True,
                    showgrid=True,
                    zeroline=False,
                    backgroundcolor="rgba(0,0,0,0)",
                    showline=False,
                    tickmode="auto",
                    nticks=5,  # Infrequent ticks
                    gridcolor="rgba(255,255,255,0.1)",  # Light grid
                ),
                zaxis=dict(
                    showticklabels=True,
                    showgrid=True,
                    zeroline=False,
                    backgroundcolor="rgba(0,0,0,0)",
                    showline=False,
                    tickmode="auto",
                    nticks=5,  # Infrequent ticks
                    gridcolor="rgba(255,255,255,0.1)",  # Light grid
                ),
                aspectmode="data",
            ),
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        return fig
        
    # # ==============================================================================================
    # # --- Methods used in scRNAseq page
    # # ==============================================================================================

    # def compute_heatmap_lipid_genes(
    #     self,
    #     lipid=None,
    #     l_genes=None,
    #     initial_frame=5,
    #     brain_1=False,
    #     set_progress=None,
    # ):
    #     """This functions computes a heatmap representing, on the left side, the expression of a
    #     given lipid in the (low-resolution, interpolated) MALDI data, and the right side, the
    #     expressions of the selected genes (in l_genes) in the scRNAseq experiments from the
    #     molecular atlas data.

    #     Args:
    #         lipid (str): The name of the lipid to be displayed. If None, the most expressed lipid
    #             will be displayed. Defaults to None.
    #         l_genes (list): The list of gene names to be displayed. If None, the three most
    #             expressed genes will be displayed. Defaults to None.
    #         initial_frame   (int, optional): The frame on which the slider is initialized.
    #         brain_1 (bool, optional): If True, the heatmap will be computed with the data coming
    #             from the first brain. Else, from the 2nd brain. Defaults to False.
    #         set_progress: Used as part of the Plotly long callbacks, to indicate the progress of the
    #             computation in the corresponding progress bar.

    #     Returns:
    #         (Plotly.Figure): A Plotly Figure containing a go.Heatmap object representing the
    #             expression of the selected lipid and genes.
    #     """

    #     logging.info("Starting computing heatmap for scRNAseq experiments" + logmem())

    #     if set_progress is not None:
    #         set_progress((5, "Loading data"))

    #     if brain_1:
    #         x = self._scRNAseq.l_name_lipids_brain_1
    #         y = self._scRNAseq.array_coef_brain_1
    #         name_genes = self._scRNAseq.l_genes_brain_1
    #         name_lipids = self._scRNAseq.l_name_lipids_brain_1
    #         array_lipids = self._scRNAseq.array_exp_lipids_brain_1
    #         array_genes = self._scRNAseq.array_exp_genes_brain_1
    #     else:
    #         x = self._scRNAseq.l_name_lipids_brain_2
    #         y = self._scRNAseq.array_coef_brain_2
    #         name_genes = self._scRNAseq.l_genes_brain_2
    #         name_lipids = self._scRNAseq.l_name_lipids_brain_2
    #         array_lipids = self._scRNAseq.array_exp_lipids_brain_2
    #         array_genes = self._scRNAseq.array_exp_genes_brain_2

    #     # Get the most expressed lipid and genes if not provided
    #     if lipid is None and l_genes is None:
    #         expression = np.mean(array_lipids, axis=0)
    #         index_sorted = np.argsort(expression)[::-1]
    #         expression = expression[index_sorted]
    #         lipids = np.array(x)[index_sorted]
    #         y_sorted = y[index_sorted, :]
    #         index_sorted = np.argsort(y_sorted[0, :])[::-1]
    #         y_sorted = y_sorted[:, index_sorted]
    #         genes = np.array(name_genes)[index_sorted]
    #         lipid = lipids[0]
    #         l_genes = genes[:3]

    #     # Get coordinates
    #     x = self._scRNAseq.xmol
    #     y = -self._scRNAseq.ymol
    #     z = self._scRNAseq.zmol

    #     # Get idx lipid and genes
    #     if lipid is not None:
    #         idx_lipid = list(name_lipids).index(lipid)
    #     else:
    #         idx_lipid = None

    #     l_idx_genes_with_None = [
    #         list(name_genes).index(gene) if gene is not None else None for gene in l_genes
    #     ]
    #     l_idx_genes = [idx_gene for idx_gene in l_idx_genes_with_None if idx_gene is not None]

    #     # Build grids on which the data will be interpolated
    #     x_domain = np.arange(np.min(x), np.max(x), 0.5)
    #     y_domain = np.arange(np.min(y), np.max(y), 0.1)
    #     z_domain = np.arange(np.min(z), np.max(z), 0.1)
    #     x_grid, y_grid, z_grid = np.meshgrid(x_domain, y_domain, z_domain, indexing="ij")

    #     if set_progress is not None:
    #         set_progress((15, "Preparing interpolation"))

    #     # Build data from interpolation since sampling is irregular
    #     if idx_lipid is not None:
    #         grid_lipid = griddata(
    #             np.vstack((x, y, z)).T,
    #             array_lipids[:, idx_lipid],
    #             (x_grid, y_grid, z_grid),
    #             method="linear",
    #         )
    #     else:
    #         grid_lipid = None

    #     if len(l_idx_genes) == 1:
    #         grid_genes = griddata(
    #             np.vstack((x, y, z)).T,
    #             array_genes[:, l_idx_genes[0]],
    #             (x_grid, y_grid, z_grid),
    #             method="linear",
    #         )
    #     elif len(l_idx_genes) > 1:
    #         grid_genes = np.moveaxis(
    #             np.stack(
    #                 [
    #                     griddata(
    #                         np.vstack((x, y, z)).T,
    #                         array_genes[:, idx_genes],
    #                         (x_grid, y_grid, z_grid),
    #                         method="linear",
    #                     )
    #                     if idx_genes is not None
    #                     else np.zeros_like(x_grid)
    #                     for idx_genes in l_idx_genes_with_None
    #                 ]
    #             ),
    #             0,
    #             -1,
    #         )
    #     else:
    #         grid_genes = None

    #     if set_progress is not None:
    #         set_progress((75, "Finished interpolation... Building figure"))
    #     fig = make_subplots(1, 2)

    #     # Build Figure, with several frames as it will be slidable
    #     if grid_lipid is not None:
    #         for i in range(0, grid_lipid.shape[0], 1):
    #             fig.add_heatmap(
    #                 z=grid_lipid[i, :, :],
    #                 row=1,
    #                 col=1,
    #                 colorscale="Viridis",
    #                 visible=True if i == initial_frame else False,
    #                 showscale=False,
    #             )
    #     if grid_genes is not None:
    #         if len(grid_genes.shape) == 3:
    #             for i in range(0, grid_genes.shape[0], 1):
    #                 fig.add_heatmap(
    #                     z=grid_genes[i, :, :],
    #                     row=1,
    #                     col=2,
    #                     colorscale="Viridis",
    #                     visible=True if i == initial_frame else False,
    #                     showscale=False,
    #                 )
    #         elif len(grid_genes.shape) == 4:
    #             for i in range(0, grid_genes.shape[0], 1):
    #                 fig.add_image(
    #                     z=grid_genes[i, :, :, :],
    #                     row=1,
    #                     col=2,
    #                     visible=True if i == initial_frame else False,
    #                 )
    #     if grid_genes is not None or grid_lipid is not None:
    #         steps = []
    #         for i in range(grid_lipid.shape[0]):
    #             step = dict(
    #                 method="restyle",
    #                 args=["visible", [False] * len(fig.data)],
    #                 label=str(i),
    #             )
    #             if grid_lipid is not None and grid_genes is not None:
    #                 step["args"][1][i] = True
    #                 step["args"][1][i + grid_lipid.shape[0]] = True
    #             elif grid_lipid is not None or grid_genes is not None:
    #                 step["args"][1][i] = True
    #             steps.append(step)

    #         sliders = [
    #             dict(
    #                 active=initial_frame,
    #                 steps=steps,
    #                 pad={"b": 5, "t": 10},
    #                 len=0.9,
    #                 x=0.05,
    #                 y=0.0,
    #                 currentvalue={
    #                     "visible": False,
    #                 },
    #             )
    #         ]

    #         # Layout
    #         fig.update_layout(
    #             title_text="Comparison between lipid and gene expression",
    #             title_x=0.5,
    #             title_y=0.98,
    #             margin=dict(t=20, r=20, b=20, l=20),
    #             template="plotly_dark",
    #             sliders=sliders,
    #         )

    #         # No display of tick labels as they're wrong anyway
    #         fig.update_layout(
    #             scene=dict(
    #                 xaxis=dict(showticklabels=False),
    #                 yaxis=dict(showticklabels=False),
    #             ),
    #             paper_bgcolor="rgba(0,0,0,0.)",
    #             plot_bgcolor="rgba(0,0,0,0.)",
    #             yaxis_scaleanchor="x",
    #         )

    #         # Reverse y axis if Image has been used
    #         if grid_genes is not None:
    #             if len(grid_genes.shape) == 4:
    #                 fig.update_yaxes(autorange=True, row=1, col=2)

    #         # Remove tick labels
    #         fig.update_xaxes(showticklabels=False)  # Hide x axis ticks
    #         fig.update_yaxes(showticklabels=False)  # Hide y axis ticks

    #         if set_progress is not None:
    #             set_progress((90, "Returning figure"))
    #         return fig

    # ==============================================================================================
    # --- Methods used for shelving results
    # ==============================================================================================

    # def shelve_arrays_basic_figures(self, force_update=False):
    #     """This function shelves in the database all the arrays of basic images computed in
    #     self.compute_figure_basic_image(), across all slices and all types of arrays. This forces
    #     the precomputations of these arrays, and allows to access them faster. Once everything has
    #     been shelved, a boolean value is stored in the shelve database, to indicate that the arrays
    #     do not need to be recomputed at next app startup.

    #     Args:
    #         force_update (bool, optional): If True, the function will not overwrite existing files.
    #             Defaults to False.
    #     """
    #     for idx_slice in range(self._data.get_slice_number()):
    #         for type_figure in ["original_data", "warped_data", "projection_corrected", "atlas"]:
    #             for display_annotations in [True, False]:
    #                 # Force no annotation for the original data
    #                 self._storage.return_shelved_object(
    #                     "figures/load_page",
    #                     "figure_basic_image",
    #                     force_update=force_update,
    #                     compute_function=self.compute_figure_basic_image,
    #                     type_figure=type_figure,
    #                     index_image=idx_slice,
    #                     plot_atlas_contours=display_annotations
    #                     if type_figure != "original_data"
    #                     else False,
    #                 )

    #     self._storage.dump_shelved_object(
    #         "figures/load_page", "arrays_basic_figures_computed", True
    #     )

    # def shelve_all_l_array_2D(self, force_update=False, sample=False, brain_1=True):
    #     """This functions precomputes and shelves all the arrays of lipid expression used in a 3D
    #     representation of the brain (through self.compute_3D_volume_figure()). Once everything has
    #     been shelved, a boolean value is stored in the shelve database, to indicate that the arrays
    #     do not need to be recomputed at next app startup.

    #     Args:
    #         force_update (bool, optional): If True, the function will not overwrite existing files.
    #             Defaults to False.
    #         sample (bool, optional): If True, only a fraction of the precomputations are made (for
    #             debug). Default to False.
    #         brain_1 (bool, optional): If True, the data is precomputed for the brain 1. Else for
    #             the brain 2. Defaults to True.
    #     """

    #     # Count number of lipids processed for sampling
    #     n_processed = 0
    #     if sample:
    #         logging.warning("Only a sample of the lipid arrays will be computed!")

    #     # Simulate a click on all lipid names
    #     df_annotations_MAIA = self._data.get_annotations_MAIA_transformed_lipids(brain_1=brain_1)
    #     for name in sorted(df_annotations_MAIA.name.unique()):
    #         structures = df_annotations_MAIA[df_annotations_MAIA["name"] == name].structure.unique()
    #         for structure in sorted(structures):
    #             cations = df_annotations_MAIA[
    #                 (df_annotations_MAIA["name"] == name)
    #                 & (df_annotations_MAIA["structure"] == structure)
    #             ].cation.unique()
    #             for cation in sorted(cations):
    #                 l_selected_lipids = []
    #                 for slice_index in self._data.get_slice_list(
    #                     indices="brain_1" if brain_1 else "brain_2"
    #                 ):
    #                     # Find lipid location
    #                     l_lipid_loc = (
    #                         self._data.get_annotations()
    #                         .index[
    #                             (self._data.get_annotations()["name"] == name)
    #                             & (self._data.get_annotations()["structure"] == structure)
    #                             & (self._data.get_annotations()["slice"] == slice_index)
    #                             & (self._data.get_annotations()["cation"] == cation)
    #                         ]
    #                         .tolist()
    #                     )

    #                     # If several lipids correspond to the selection, we have a problem...
    #                     if len(l_lipid_loc) > 1:
    #                         logging.warning("More than one lipid corresponds to the selection")
    #                         l_lipid_loc = [l_lipid_loc[-1]]
    #                     # If no lipid correspond to the selection, set to -1
    #                     if len(l_lipid_loc) == 0:
    #                         l_lipid_loc = [-1]

    #                     # add lipid index for each slice
    #                     l_selected_lipids.append(l_lipid_loc[0])

    #                 # Get final lipid name
    #                 lipid_string = name + " " + structure + " " + cation

    #                 # If lipid is present in at least one slice
    #                 if np.sum(l_selected_lipids) > -len(
    #                     self._data.get_slice_list(indices="brain_1" if brain_1 else "brain_2")
    #                 ):
    #                     # Build the list of mz boundaries for each peak and each index
    #                     lll_lipid_bounds = [
    #                         [
    #                             [
    #                                 (
    #                                     float(self._data.get_annotations().iloc[index]["min"]),
    #                                     float(self._data.get_annotations().iloc[index]["max"]),
    #                                 )
    #                             ]
    #                             if index != -1
    #                             else None
    #                             for index in [lipid_1_index, -1, -1]
    #                         ]
    #                         for lipid_1_index in l_selected_lipids
    #                     ]

    #                     # Compute 3D figures, selection is limited to one lipid
    #                     name_lipid = lipid_string

    #                     self._storage.return_shelved_object(
    #                         "figures/3D_page",
    #                         "arrays_expression_" + str(brain_1) + "_" + name_lipid + "__",
    #                         force_update=force_update,
    #                         compute_function=self.compute_l_array_2D,
    #                         ignore_arguments_naming=True,
    #                         ll_t_bounds=lll_lipid_bounds,
    #                         brain_1=brain_1,
    #                         cache_flask=None,  # No cache needed since launched at startup
    #                     )

    #                     n_processed += 1
    #                     if n_processed >= 10 and sample:
    #                         return None

    #     # Variable to signal everything has been computed
    #     self._storage.dump_shelved_object(
    #         "figures/3D_page", "arrays_expression_" + str(brain_1) + "_computed", True
    #     )

    def shelve_all_arrays_annotation(self):
        """This functions precomputes and shelves the array of structure annotation used in a
        3D representation of the brain (through self.compute_3D_volume_figure()), at different
        resolutions. Once everything has been shelved, a boolean value is stored in the shelve
        database, to indicate that the arrays do not need to be recomputed at next app startup.
        """
        for decrease_dimensionality_factor in range(2, 13):
            self._storage.return_shelved_object(
                "figures/3D_page",
                "arrays_annotation",
                force_update=False,
                compute_function=self.get_array_of_annotations,
                decrease_dimensionality_factor=decrease_dimensionality_factor,
            )

        # Variable to signal everything has been computed
        self._storage.dump_shelved_object("figures/3D_page", "arrays_annotation_computed", True)

    def compute_heatmap_grid_per_lipid(
        self,
        lipid_name,
        draw=False,
        return_base64_string=False,
        cache_flask=None,
    ):
        """This function creates a grid of heatmaps showing the lipid expression across all slices.

        Args:
            lipid_name (str): Name of the lipid to display
            draw (bool, optional): If True, enables drawing on the figure. Defaults to False.
            return_base64_string (bool, optional): If True, returns base64 string. Defaults to False.
            cache_flask (flask_caching.Cache, optional): Flask cache. Defaults to None.

        Returns:
            go.Figure: A Plotly figure containing a grid of heatmaps for all slices
        """
        logging.info("Starting grid figure computation")

        # Get total number of slices from MaldiData
        n_slices = self._data.get_slice_number()

        # Calculate grid dimensions, convert to Python int to avoid numpy integer issues
        n_cols = 12
        n_rows = int(
            (n_slices + n_cols - 1) // n_cols
        )  # Ceiling division with explicit int conversion

        # Create subplots
        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            horizontal_spacing=0.01,
            vertical_spacing=0.01,
        )

        # Add heatmaps for each slice
        valid_count = 0
        max_height = 0
        max_width = 0

        # First pass to determine maximum dimensions for aspect ratio consistency
        for slice_index in range(1, n_slices + 1):
            try:
                image = self._data.extract_lipid_image(float(slice_index), lipid_name)
                if image is not None and image.size > 0:
                    max_height = max(max_height, image.shape[0])
                    max_width = max(max_width, image.shape[1])
            except:
                continue

        # Calculate cell size to maintain aspect ratio
        aspect_ratio = max_height / max_width if max_width > 0 else 1
        cell_width = 100
        cell_height = int(cell_width * aspect_ratio)

        # Second pass to add the traces
        for slice_index in range(1, n_slices + 1):
            try:
                # Calculate row and column position (1-based indexing for subplot)
                row = (valid_count // n_cols) + 1
                col = (valid_count % n_cols) + 1

                # Get lipid image directly from MaldiData
                image = self._data.extract_lipid_image(float(slice_index), lipid_name)

                # Skip if image is None or empty
                if image is None or image.size == 0:
                    continue

                # Flip the image vertically
                image = np.flip(image.T, np.flipud(image), axis=0)

                # Add heatmap to subplot
                fig.add_trace(
                    go.Heatmap(
                        z=image,
                        showscale=False,
                        colorscale="viridis",
                        hoverinfo="none",  # Disable hover to simplify
                    ),
                    row=row,
                    col=col,
                )

                # Add a simple text annotation for slice number
                fig.add_annotation(
                    text=f"{slice_index}",
                    x=0.5,
                    y=0.9,
                    xref=f"x{valid_count+1}",
                    yref=f"y{valid_count+1}",
                    showarrow=False,
                    font=dict(color="white", size=10),
                )

                valid_count += 1

            except Exception as e:
                logging.warning(f"Error processing slice {slice_index}: {str(e)}")
                continue

        # Update layout
        fig.update_layout(
            height=cell_height * n_rows + 100,
            width=cell_width * n_cols + 100,
            showlegend=False,
            margin=dict(t=30, r=10, b=10, l=10),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",  # Darker background
            plot_bgcolor="rgba(0,0,0,0)",  # Darker background
            clickmode="event+select",  # Enable click events
        )

        # Remove all axes, grids and ticks
        fig.update_xaxes(
            visible=False,
            showgrid=False,
            zeroline=False,
            constrain="domain",  # Maintain aspect ratio
            scaleanchor="y",  # Keep x and y scales linked
        )

        fig.update_yaxes(
            visible=False,
            showgrid=False,
            zeroline=False,
            constrain="domain",  # Maintain aspect ratio
            scaleanchor="x",  # Keep x and y scales linked
        )

        # Add a callback for handling double-click events
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    buttons=[
                        dict(
                            label="Reset View",
                            method="relayout",
                            args=[{"xaxis.autorange": True, "yaxis.autorange": True}],
                        )
                    ],
                    x=0.05,
                    y=0.05,
                    xanchor="left",
                    yanchor="bottom",
                )
            ]
        )

        # Add JavaScript for double-click zooming functionality
        fig.update_layout(
            annotations=[
                dict(
                    x=0,
                    y=0,
                    xref="paper",
                    yref="paper",
                    text="Double-click on a plot to zoom in",
                    showarrow=False,
                    font=dict(size=10, color="white"),
                    opacity=0.7,
                    align="left",
                )
            ]
        )

        # Add custom JavaScript for double-click zooming
        fig.update_layout(
            newshape=dict(line_color="yellow"),  # Just to add a hook for the JavaScript
        )

        # Add setup for callback via JavaScript with plotly_doubleclick event
        fig._config = {"responsive": True}

        return fig

    def export_grid_to_plotly(
        self,
        grid_image,
        output_file="brain_sections.html",
        width=None,
        height=None,
    ):
        """
        Export a grid image to an interactive Plotly HTML file.

        Parameters:
        -----------
        grid_image : numpy.ndarray
            RGBA image array of the section grid with shape (dim1, dim2, 4) where 4 = RGB + transparency
        output_file : str
            Output HTML file path
        width : int, optional
            Custom width for the plot (defaults to image width)
        height : int, optional
            Custom height for the plot (defaults to image height)

        Returns:
        --------
        fig : plotly.graph_objects.Figure
            The generated Plotly figure
        config : dict
            Configuration for the Plotly figure
        """
        # Get dimensions from the image if not specified
        if width is None:
            width = grid_image.shape[1]
        if height is None:
            height = grid_image.shape[0]

        # Check if we need to process the image for Plotly
        if grid_image.dtype != np.uint8:
            # Convert floats (0-1) to uint8 (0-255)
            grid_image_uint8 = (grid_image * 255).astype(np.uint8)
        else:
            grid_image_uint8 = grid_image

        # Ensure we have the right shape for plotly
        if grid_image_uint8.shape[2] == 4:  # RGBA
            # Plotly doesn't handle alpha channel properly in imshow
            # Create an RGB version of the image with white background
            rgb_image = (
                np.ones((grid_image_uint8.shape[0], grid_image_uint8.shape[1], 3), dtype=np.uint8)
                * 255
            )

            # Blend alpha channel
            alpha = grid_image_uint8[:, :, 3].astype(float) / 255
            for c in range(3):  # RGB channels
                rgb_image[:, :, c] = (
                    grid_image_uint8[:, :, c] * alpha + rgb_image[:, :, c] * (1 - alpha)
                ).astype(np.uint8)
        else:
            # If it's already RGB, just use it
            rgb_image = grid_image_uint8

        # Create figure using Plotly Express
        fig = px.imshow(rgb_image, binary_string=True, binary_backend="auto")

        # Update layout with improved settings and dark theme
        fig.update_layout(
            width=width,
            height=height,
            margin=dict(l=0, r=0, b=0, t=30),
            dragmode="pan",  # Set default drag mode to pan instead of zoom
            paper_bgcolor="black",  # Set paper background to black ######### if not it does not even display the fkn all sections at all how come lol
            plot_bgcolor="black",  hovermode=False, # Set plot background to black
        )

        # Update axes to remove tick labels and grid
        fig.update_xaxes(
            showticklabels=False,
            showgrid=False,  # Remove grid lines
            zeroline=False,  # Remove zero line
            showline=False,  # Remove axis line
            constrain="domain",  fixedrange=False,# Constrains axes to the domain to prevent artificial borders
        )

        fig.update_yaxes(
            showticklabels=False,
            showgrid=False,  # Remove grid lines
            zeroline=False,  # Remove zero line
            showline=False,  # Remove axis line
            scaleanchor="x",  # Forces y-axis to scale with x-axis to maintain aspect ratio
            constrain="domain",  fixedrange=False,# Constrains axes to the domain to prevent artificial borders
        )

        # Configure for interactive viewing with minimal UI
        config = {
            "responsive": True,
            "scrollZoom": True,  # Enable scroll to zoom
            "displayModeBar": False,  # Hide the mode bar completely
            "doubleClick": "reset",  # Double click to reset the view
        }

        # Return both the figure and the config
        return fig, config

    def compute_heatmap_lipid_genes(
        self,
        lipid=None,
        l_genes=None,
        initial_frame=5,
        brain_1=False,
        set_progress=None,
    ):
        """This functions computes a heatmap representing, on the left side, the expression of a
        given lipid in the (low-resolution, interpolated) MALDI data, and the right side, the
        expressions of the selected genes (in l_genes) in the scRNAseq experiments from the
        molecular atlas data.

        Args:
            lipid (str): The name of the lipid to be displayed. If None, the most expressed lipid
                will be displayed. Defaults to None.
            l_genes (list): The list of gene names to be displayed. If None, the three most
                expressed genes will be displayed. Defaults to None.
            initial_frame   (int, optional): The frame on which the slider is initialized.
            brain_1 (bool, optional): If True, the heatmap will be computed with the data coming
                from the first brain. Else, from the 2nd brain. Defaults to False.
            set_progress: Used as part of the Plotly long callbacks, to indicate the progress of the
                computation in the corresponding progress bar.

        Returns:
            (Plotly.Figure): A Plotly Figure containing a go.Heatmap object representing the
                expression of the selected lipid and genes.
        """

        logging.info("Starting computing heatmap for scRNAseq experiments" + logmem())

        if set_progress is not None:
            set_progress((5, "Loading data"))

        if brain_1:
            x = self._scRNAseq.l_name_lipids_brain_1
            y = self._scRNAseq.array_coef_brain_1
            name_genes = self._scRNAseq.l_genes_brain_1
            name_lipids = self._scRNAseq.l_name_lipids_brain_1
            array_lipids = self._scRNAseq.array_exp_lipids_brain_1
            array_genes = self._scRNAseq.array_exp_genes_brain_1
        else:
            x = self._scRNAseq.l_name_lipids_brain_2
            y = self._scRNAseq.array_coef_brain_2
            name_genes = self._scRNAseq.l_genes_brain_2
            name_lipids = self._scRNAseq.l_name_lipids_brain_2
            array_lipids = self._scRNAseq.array_exp_lipids_brain_2
            array_genes = self._scRNAseq.array_exp_genes_brain_2

        # Get the most expressed lipid and genes if not provided
        if lipid is None and l_genes is None:
            expression = np.mean(array_lipids, axis=0)
            index_sorted = np.argsort(expression)[::-1]
            expression = expression[index_sorted]
            lipids = np.array(x)[index_sorted]
            y_sorted = y[index_sorted, :]
            index_sorted = np.argsort(y_sorted[0, :])[::-1]
            y_sorted = y_sorted[:, index_sorted]
            genes = np.array(name_genes)[index_sorted]
            lipid = lipids[0]
            l_genes = genes[:3]

        # Get coordinates
        x = self._scRNAseq.xmol
        y = -self._scRNAseq.ymol
        z = self._scRNAseq.zmol

        # Get idx lipid and genes
        if lipid is not None:
            idx_lipid = list(name_lipids).index(lipid)
        else:
            idx_lipid = None

        l_idx_genes_with_None = [
            list(name_genes).index(gene) if gene is not None else None for gene in l_genes
        ]
        l_idx_genes = [idx_gene for idx_gene in l_idx_genes_with_None if idx_gene is not None]

        # Build grids on which the data will be interpolated
        x_domain = np.arange(np.min(x), np.max(x), 0.5)
        y_domain = np.arange(np.min(y), np.max(y), 0.1)
        z_domain = np.arange(np.min(z), np.max(z), 0.1)
        x_grid, y_grid, z_grid = np.meshgrid(x_domain, y_domain, z_domain, indexing="ij")

        if set_progress is not None:
            set_progress((15, "Preparing interpolation"))

        # Build data from interpolation since sampling is irregular
        if idx_lipid is not None:
            grid_lipid = griddata(
                np.vstack((x, y, z)).T,
                array_lipids[:, idx_lipid],
                (x_grid, y_grid, z_grid),
                method="linear",
            )
        else:
            grid_lipid = None

        if len(l_idx_genes) == 1:
            grid_genes = griddata(
                np.vstack((x, y, z)).T,
                array_genes[:, l_idx_genes[0]],
                (x_grid, y_grid, z_grid),
                method="linear",
            )
        elif len(l_idx_genes) > 1:
            grid_genes = np.moveaxis(
                np.stack(
                    [
                        griddata(
                            np.vstack((x, y, z)).T,
                            array_genes[:, idx_genes],
                            (x_grid, y_grid, z_grid),
                            method="linear",
                        )
                        if idx_genes is not None
                        else np.zeros_like(x_grid)
                        for idx_genes in l_idx_genes_with_None
                    ]
                ),
                0,
                -1,
            )
        else:
            grid_genes = None

        if set_progress is not None:
            set_progress((75, "Finished interpolation... Building figure"))
        fig = make_subplots(1, 2)

        # Build Figure, with several frames as it will be slidable
        if grid_lipid is not None:
            for i in range(0, grid_lipid.shape[0], 1):
                fig.add_heatmap(
                    z=grid_lipid[i, :, :],
                    row=1,
                    col=1,
                    colorscale="Viridis",
                    visible=True if i == initial_frame else False,
                    showscale=False,
                )
        if grid_genes is not None:
            if len(grid_genes.shape) == 3:
                for i in range(0, grid_genes.shape[0], 1):
                    fig.add_heatmap(
                        z=grid_genes[i, :, :],
                        row=1,
                        col=2,
                        colorscale="Viridis",
                        visible=True if i == initial_frame else False,
                        showscale=False,
                    )
            elif len(grid_genes.shape) == 4:
                for i in range(0, grid_genes.shape[0], 1):
                    fig.add_image(
                        z=grid_genes[i, :, :, :],
                        row=1,
                        col=2,
                        visible=True if i == initial_frame else False,
                    )
        if grid_genes is not None or grid_lipid is not None:
            steps = []
            for i in range(grid_lipid.shape[0]):
                step = dict(
                    method="restyle",
                    args=["visible", [False] * len(fig.data)],
                    label=str(i),
                )
                if grid_lipid is not None and grid_genes is not None:
                    step["args"][1][i] = True
                    step["args"][1][i + grid_lipid.shape[0]] = True
                elif grid_lipid is not None or grid_genes is not None:
                    step["args"][1][i] = True
                steps.append(step)

            sliders = [
                dict(
                    active=initial_frame,
                    steps=steps,
                    pad={"b": 5, "t": 10},
                    len=0.9,
                    x=0.05,
                    y=0.0,
                    currentvalue={
                        "visible": False,
                    },
                )
            ]

            # Layout
            fig.update_layout(
                title_text="Comparison between lipid and gene expression",
                title_x=0.5,
                title_y=0.98,
                margin=dict(t=20, r=20, b=20, l=20),
                template="plotly_dark",
                sliders=sliders,
            )

            # No display of tick labels as they're wrong anyway
            fig.update_layout(
                scene=dict(
                    xaxis=dict(showticklabels=False),
                    yaxis=dict(showticklabels=False),
                ),
                paper_bgcolor="rgba(0,0,0,0.)",
                plot_bgcolor="rgba(0,0,0,0.)",
                yaxis_scaleanchor="x",
            )

            # Reverse y axis if Image has been used
            if grid_genes is not None:
                if len(grid_genes.shape) == 4:
                    fig.update_yaxes(autorange=True, row=1, col=2)

            # Remove tick labels
            fig.update_xaxes(showticklabels=False)  # Hide x axis ticks
            fig.update_yaxes(showticklabels=False)  # Hide y axis ticks

            if set_progress is not None:
                set_progress((90, "Returning figure"))
            return fig