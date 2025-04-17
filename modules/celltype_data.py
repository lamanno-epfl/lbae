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
import zarr
import plotly.express as px

# Make sure to import or define these functions:
# from your_module import create_section_grid, normalize_grid_with_percentiles

from modules.figures import calculate_mean_color

class CelltypeData:

    def __init__(
        self, 
        path_data: str = "./data/celltype_data/"
    ):
        """
        Initializes the shelve database.
        
        Parameters:
            shelf_filename (str): Base filename for the shelve database.
            path_data (str): Directory in which to store the shelve files.
        """
        self.path_data = path_data
        self.filename = "celltype_data_shelve"

        # Create the directory if it does not exist
        if not os.path.exists(self.path_data):
            os.makedirs(self.path_data)
        
        self.shelf_path = os.path.join(self.path_data, self.filename)

        # celltypes = pd.read_csv('/data/LBA_DATA/lbae/assets/hierarchy_celltypes_colors.csv')[["cell_type", "color"]]
        # celltype_to_color = {name: color for name, color in zip(celltypes["cell_type"], celltypes["color"])}
        # df_hierarchy_celltypes = pd.read_csv('/data/LBA_DATA/lbae/assets/hierarchy_celltypes_colors.csv')
        # # Keep hierarchy_code and reorder columns
        # df_hierarchy_celltypes = df_hierarchy_celltypes.iloc[:, 1:]

        # union_celltypes = set()
        # for slice_index in data.get_slice_list("ReferenceAtlas"):
        #     try:
        #         celltype_in_section = list(celltype_data.retrieve_section_data(int(slice_index))['color_masks'].keys())
        #         filtered_df = df_hierarchy_celltypes[df_hierarchy_celltypes["cell_type"].isin(celltype_in_section)]
        #         union_celltypes.update(filtered_df["cell_type"].values)
        #     except:
        #         continue

        # # filter the  df_hierarchy_celltypes to only keep the celltypes in union_celltypes
        # df_hierarchy_celltypes = df_hierarchy_celltypes[df_hierarchy_celltypes["cell_type"].isin(union_celltypes)]
        # df_hierarchy_celltypes = df_hierarchy_celltypes.drop(columns=['level_11', 'level_12', 'level_13', 'level_14', 'level_15', 
        #                                                                 'level_16', 'level_17', 'level_18', 'level_19', 'level_20', 
        #                                                                 'level_21', 'level_22', 'level_23', 'level_24', 'level_25', 
        #                                                                 'level_26'])

        self.df_hierarchy_celltypes = pd.read_csv(os.path.join(self.path_data, "celltypes_hierarchy.csv"))
        self.celltype_to_color = pickle.load(open(os.path.join(self.path_data, "celltype_to_color.pkl"), "rb"))
    
    def store_section_data(self, section, color_masks):
        data = {
            "color_masks": color_masks # dict
        }
        key = str(section)
        with shelve.open(self.shelf_path) as db:
            db[key] = data
        print(f"Stored data for section: {key}")
    
    def retrieve_section_data(self, section):
        key = str(section)
        with shelve.open(self.shelf_path) as db:
            if key in db:
                return db[key]
            else:
                raise KeyError(f"Data for section '{key}' not found.")
                
    def create_treemap_data_celltypes(self, slice_index=1.0,):

        """Create data structure for treemap visualization with color information."""
        # in the case of celltypes, extract only the celltypes that are available in the slice
        celltype_in_section = list(self.retrieve_section_data(int(slice_index))['color_masks'].keys())
        # Filter the DataFrame
        df = self.df_hierarchy_celltypes[self.df_hierarchy_celltypes["cell_type"].isin(celltype_in_section)]

        # Add a constant value column for equal-sized end nodes
        df['value'] = 1
        
        # Create a dictionary to store colors for each node
        node_colors = {}
        
        # First, assign colors to leaf nodes
        for _, row in df.iterrows():
            celltype = row['cell_type']
            if celltype in self.celltype_to_color:
                # Use only the first 10 levels for celltypes
                path = '/'.join([str(row[col]) for col in ['level_1', 'level_2', 'level_3', 'level_4', 'level_5', 
                                                            'level_6', 'level_7', 'level_8', 'level_9', 'level_10', 
                                                            'cell_type']])
                
                node_colors[path] = self.celltype_to_color[celltype]
        
        # Function to get all leaf colors under a node
        def get_leaf_colors(path_prefix):
            colors = []
            for full_path, color in node_colors.items():
                if full_path.startswith(path_prefix):
                    colors.append(color)
            return colors
        
        # Calculate colors for each level, from bottom to top
        columns = ['level_1', 'level_2', 'level_3', 'level_4', 'level_5', 
                    'level_6', 'level_7', 'level_8', 'level_9', 'level_10', 
                    'cell_type']
        
        for i in range(len(columns)-1):  # Don't process the last level
            level_paths = set()
            # Build paths up to current level
            for _, row in df.iterrows():
                path = '/'.join([str(row[col]) for col in columns[:i+1]])
                level_paths.add(path)
            
            # Calculate mean colors for each path
            for path in level_paths:
                leaf_colors = get_leaf_colors(path + '/')
                if leaf_colors:
                    node_colors[path] = calculate_mean_color(leaf_colors, is_celltypes=True)
        
        return df, node_colors

    def create_treemap_figure_celltypes(
        self, df_treemap, node_colors):
        """Create treemap figure using plotly with custom colors."""
        path_columns = ['level_1', 'level_2', 'level_3', 'level_4', 'level_5', 
                        'level_6', 'level_7', 'level_8', 'level_9', 'level_10', 
                        'cell_type']
        
        fig = px.treemap(
            df_treemap,
            path=path_columns,
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
