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

# Make sure to import or define these functions:
# from your_module import create_section_grid, normalize_grid_with_percentiles


class LipizoneSampleData:
    """
    A class to store and retrieve processed sample data (grid image,
    grayscale image, and color masks) using a shelve database.
    """
    def __init__(
        self, 
        path_data: str = "./new_data_lbae/lipizone_data/",
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
        path_data: str = "./new_data_lbae/lipizone_data/"
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
