import os
import shelve
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from time import time
from typing import Dict, List, Optional, Tuple
# from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
import numpy as np
from scipy.ndimage import generic_filter
from collections import Counter
import pickle
from tqdm import tqdm
import plotly.express as px

from modules.figures import calculate_mean_color

# Make sure to import or define these functions:
# from your_module import create_section_grid, normalize_grid_with_percentiles


class LipizoneSampleData:
    """
    A class to store and retrieve processed sample data (grid image,
    grayscale image, and color masks) using a shelve database.
    """
    def __init__(
        self, 
        path_data: str = "./data/lipizone_data/",
    ):
        """
        Initializes the shelve database.
        
        Parameters:
            shelf_filename (str): Base filename for the shelve database.
            path_data (str): Directory in which to store the shelve files.
        """
        self.path_data = path_data
        self.filename = "lipizone_sample_data_shelve"
        # Create the directory if it does not exist
        if not os.path.exists(self.path_data):
            os.makedirs(self.path_data)
        self.shelf_path = os.path.join(self.path_data, self.filename)
    
    def store_sample_data(
        self, 
        sample, 
        grid_image, 
        grayscale_image, 
        color_masks):
        """
        Stores the processed data for a given sample.
        
        Parameters:
            sample (str): The sample identifier.
            grid_image (np.ndarray): The full grid image (3D).
            rgb_image (np.ndarray): The RGB portion of the grid image.
            grayscale_image (np.ndarray): The grayscale image.
            color_masks (dict): The precomputed color masks.
        """
        data = {
            "grid_image": grid_image,
            "grayscale_image": grayscale_image, 
            "color_masks": color_masks,
        }
        with shelve.open(self.shelf_path) as db:
            db[sample] = data
        print(f"Stored data for sample: {sample}")
    
    def retrieve_sample_data(self, sample):
        """
        Retrieves the processed data for a given sample.
        
        Parameters:
            sample (str): The sample identifier.
        
        Returns:
            dict: A dictionary containing 'grid_image', 'rgb_image', 
                  'grayscale_image', and 'color_masks'.
        
        Raises:
            KeyError: If the sample is not found in the database.
        """
        with shelve.open(self.shelf_path) as db:
            if sample in db:
                return db[sample]
            else:
                raise KeyError(f"Data for sample '{sample}' not found.")


class LipizoneSectionData:
    """
    A class to store and retrieve processed section data (grid image, RGB image,
    grayscale image, and color masks) using a shelve database.
    """
    def __init__(
        self, 
        path_data: str = "./data/lipizone_data/"
    ):
        """
        Initializes the shelve database.
        
        Parameters:
            shelf_filename (str): Base filename for the shelve database.
            path_data (str): Directory in which to store the shelve files.
        """
        self.path_data = path_data
        self.filename = "lipizone_section_data_shelve"
        
        # Create the directory if it does not exist
        if not os.path.exists(self.path_data):
            os.makedirs(self.path_data)
        self.shelf_path = os.path.join(self.path_data, self.filename)
    
    def store_section_data(
        self, 
        section, 
        grid_image, 
        grayscale_image, 
        color_masks):
        """
        Stores the processed data for a given section.
        
        Parameters:
            section (str or int): The section identifier.
            grid_image (np.ndarray): The grid image (3D).
            rgb_image (np.ndarray): The RGB portion of the grid image.
            grayscale_image (np.ndarray): The grayscale image.
            color_masks (dict): The precomputed color masks.
        """
        data = {
            "grid_image": grid_image,           # (320, 456, 4)
            "grayscale_image": grayscale_image, # (320, 456)
            "color_masks": color_masks,         # dict
        }
        # Use the section name (or id) as the key (converted to string)
        key = str(section)
        with shelve.open(self.shelf_path) as db:
            db[key] = data
        print(f"Stored data for section: {key}")
    
    def retrieve_section_data(self, section):
        """
        Retrieves the processed data for a given section.
        
        Parameters:
            section (str or int): The section identifier.
        
        Returns:
            dict: A dictionary containing 'grid_image', 'rgb_image', 
                  'grayscale_image', and 'color_masks'.
        
        Raises:
            KeyError: If the section is not found in the database.
        """
        key = str(section)
        with shelve.open(self.shelf_path) as db:
            if key in db:
                return db[key]
            else:
                raise KeyError(f"Data for section '{key}' not found.")

class LipizoneData:
    """
    A class to store and retrieve processed lipizone data (grid image, RGB image,
    grayscale image, and color masks) using a shelve database.
    """
    def __init__(self, path_data: str = "./data/lipizone_data/"):
        
        self.path_data = path_data
        self.section_data = LipizoneSectionData(path_data=path_data)
        self.sample_data = LipizoneSampleData(path_data=path_data)

        # manual_naming_lipizones_level_1 = {
        #     '1' : 'White matter-rich',
        #     '2' : 'Gray matter-rich',
        # }
        # manual_naming_lipizones_level_2 = {
        #     '1_1' : 'Core white matter',
        #     '1_2' : 'Mixed gray and white matter, ventricles',
        #     '2_1' : 'Outer cortex, cerebellar molecular layer, amygdala, part of hippocampus',
        #     '2_2' : 'Deep cortex, part of hippocampus, striatum, cerebellar granule cells',
        # }
        # manual_naming_lipizones_level_3 = {
        #     '1_1_1' : 'Oligodendroglia-rich regions',
        #     '1_1_2' : 'Mixed white matter with neurons',
        #     '1_2_1' : 'Ventricular system, gray-white boundary, hypothalamus',
        #     '1_2_2' : 'Thalamus and midbrain',
        #     '2_1_1' : 'Layer 2/3 and 4, cingulate, striatum, hippocampus, subcortical plate regions',
        #     '2_1_2' : 'Layer 1 to border between 2/3 and 4, piriform, Purkinje cells, enthorinal, mixed',
        #     '2_2_1' : 'Layer 5, hippocampus and noncortical gray matter',
        #     '2_2_2' : 'Layers 5 and 6, hippocampus, nuclei, granular layer of the cerebellum',
        # }
        # manual_naming_lipizones_level_4 = {
        #     '1_1_1_1' : 'Core of fiber tracts, arbor vitae and nerves/1',
        #     '1_1_1_2' : 'Core of fiber tracts, arbor vitae and nerves/2',
        #     '1_1_2_1' : 'Bundle and boundary white matter-rich',
        #     '1_1_2_2' : 'Thalamus, midbrain, hindbrain white matter regions',
        #     '1_2_1_1' : 'Ventricular system',
        #     '1_2_1_2' : 'Gray-white matter boundary',
        #     '1_2_2_1' : 'Mostly thalamus, midbrain, hindbrain mixed types',
        #     '1_2_2_2' : 'Myelin-rich deep cortex, striatum, hindbrain and more',
        #     '2_1_1_1' : 'Layer 2/3 and 4, cingulate, striatum, hippocampus, subcortical plate regions',
        #     '2_1_1_2' : 'HPF, AMY, CTXSP, HY and more',
        #     '2_1_2_1' : 'Purkinje layer, L2/3 and boundary with L4',
        #     '2_1_2_2' : 'Layer 1, 2/3, piriform and enthorinal cortex, CA1',
        #     '2_2_1_1' : 'Layer 5, retrosplenial, hippocampus',
        #     '2_2_1_2' : 'Noncortical gray matter',
        #     '2_2_2_1' : 'Layer 5-6, nuclei, granule cells layer',
        #     '2_2_2_2' : 'Layer 6, mixed complex GM, granule cells layer',
        # }

        # lipizones = pd.read_csv("/data/LBA_DATA/lbae/lipizonename2color.csv", index_col=0) # HEX
        # lipizone_to_color = {name: color for name, color in zip(lipizones["lipizone_names"], lipizones["lipizone_color"])}
        # df_hierarchy_lipizones = pd.read_csv("/data/LBA_DATA/lbae/data/annotations/lipizones_hierarchy.csv")

        # # lipizonenames = pd.read_csv("/data/LBA_DATA/lbae/lipizonename2color.csv", index_col=0)['lipizone_names'].values
        # df_hierarchy_lipizones['level_1_name'] = df_hierarchy_lipizones['level_1'].astype(str).map(manual_naming_lipizones_level_1)
        # df_hierarchy_lipizones['level_2_name'] = df_hierarchy_lipizones['level_2'].astype(str).map(manual_naming_lipizones_level_2)
        # df_hierarchy_lipizones['level_3_name'] = df_hierarchy_lipizones['level_3'].astype(str).map(manual_naming_lipizones_level_3)
        # df_hierarchy_lipizones['level_4_name'] = df_hierarchy_lipizones['level_4'].astype(str).map(manual_naming_lipizones_level_4)

        self.df_hierarchy_lipizones = pd.read_csv(os.path.join(self.path_data, "lipizones_hierarchy.csv"))
        self.lipizone_to_color = pickle.load(open(os.path.join(self.path_data, "lipizone_to_color.pkl"), "rb"))

        # New constant for the Zarr store location
        self.LIPIZONES_ZARR_PATH = os.path.join(self.path_data, "3d_lipizones_all.zarr")

        # New constant for the color array file
        self.COLOR_ARRAY_PATH = os.path.join(self.path_data, "color_array_fullres.npy")

    def create_treemap_data_lipizones(self):
        """Create data structure for treemap visualization with color information."""
        # Create a copy to avoid modifying the original
        df = self.df_hierarchy_lipizones.copy()
        
        # Add a constant value column for equal-sized end nodes
        df['value'] = 1
        
        # Create a dictionary to store colors for each node
        node_colors = {}
        
        # First, assign colors to leaf nodes (lipizones)
        for _, row in df.iterrows():
            lipizone = row['lipizone_names']
            if lipizone in self.lipizone_to_color:
                path = '/'.join([str(row[col]) for col in ['level_1_name', 'level_2_name', 'level_3_name', 'level_4_name', 'subclass_name', 'lipizone_names']])
                node_colors[path] = self.lipizone_to_color[lipizone]
        
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

    def create_treemap_figure_lipizones(self, df_treemap, node_colors):
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


