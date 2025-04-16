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
