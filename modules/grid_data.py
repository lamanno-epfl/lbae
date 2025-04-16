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

class GridImageShelve:
    """
    A class to generate, store, and retrieve grid images for given lipid and sample.
    The images are stored in a shelve database located in the 'grid_data' folder.
    """
    def __init__(
        self, 
        path_data: str = "./data/grid_data/"
    ):
        """
        Initializes the shelve database in the given directory.
        """
        self.path_data = path_data
        self.filename = "grid_shelve"
        # Create the grid_data folder if it does not exist
        if not os.path.exists(self.path_data):
            os.makedirs(self.path_data)
        # Shelve uses the given filename as the base for its files
        self.shelf_path = os.path.join(self.path_data, self.filename)
        self.lookup_brainid = pd.read_csv("./data/annotations/lookup_brainid.csv", index_col=0)

    def create_grid_image(self, maindata, lipid, sample):
        """
        Given the main DataFrame, a lipid, and a sample,
        this method generates the grid image.
        
        Parameters:
            maindata (DataFrame): The complete data.
            lipid (str): The lipid column to process.
            sample (str): The sample identifier.
        
        Returns:
            grid_image (np.ndarray): The processed grid image.
        """
        # Get the unique sorted SectionIDs for the sample
        section_ids = np.sort(maindata.loc[maindata['Sample'] == sample, 'SectionID'].unique())
        
        # Determine number of columns based on sample name
        if sample in ["ReferenceAtlas", "SecondAtlas"]:
            cols = 8
        else:
            cols = 3
        
        # Create the grid and normalize it
        grid = create_section_grid(maindata, section_ids, lipid, cols=cols)
        grid_image = normalize_grid_with_percentiles(grid)
        return grid_image

    def get_brain_id_from_sliceindex(self, slice_index):
        # lookup_brainid = pd.read_csv("./new_data/lookup_brainid.csv", index_col=0)

        try:
            sample = self.lookup_brainid.loc[
                self.lookup_brainid["SectionID"] == slice_index, "Sample"
            ].values[0]
            return sample

        except:
            print("Missing sample")
            return np.nan

    def store_grid_image(self, lipid, sample, grid_image):
        """
        Stores the grid image in the shelve database with a key based on lipid and sample.
        
        Parameters:
            lipid (str): The lipid identifier.
            sample (str): The sample identifier.
            grid_image (np.ndarray): The grid image to store.
        """
        key = f"{lipid}_{sample}_grid"
        with shelve.open(self.shelf_path) as db:
            db[key] = grid_image

    def retrieve_grid_image(self, lipid, sample=None, slice_index=None):
        """
        Retrieves the grid image for the given lipid and sample from the shelve database.
        
        Parameters:
            lipid (str): The lipid identifier.
            sample (str, optional): The sample identifier. If provided, this is used directly.
            slice_index (int, optional): The slice index. If provided and sample is None, 
                                        this is converted to a sample using get_brain_id_from_sliceindex.
        
        Returns:
            grid_image (np.ndarray): The retrieved grid image.
            
        Raises:
            KeyError: If no grid image is found for the given key.
            ValueError: If neither sample nor slice_index is provided.
        """
        if sample is None and slice_index is None:
            raise ValueError("Either sample or slice_index must be provided")
            
        if sample is None:
            sample = self.get_brain_id_from_sliceindex(slice_index)

        key = f"{lipid}_{sample}_grid"
        with shelve.open(self.shelf_path) as db:
            if key in db:
                return db[key]
            else:
                raise KeyError(f"Grid image for lipid '{lipid}' and sample '{sample}' not found.")

    def process_maindata(self, maindata, lipids=None, samples=None):
        """
        Processes the main DataFrame by generating and storing grid images for each
        combination of lipid and sample.
        
        Parameters:
            maindata (DataFrame): The complete data.
            lipids (iterable, optional): List of lipids to process. If None, uses the first 173 columns.
            samples (iterable, optional): List of samples to process. If None, uses all unique samples from maindata.
        """
        # Use default selections if none provided
        if lipids is None:
            lipids = maindata.columns[:173].values
        if samples is None:
            samples = maindata['Sample'].unique()

        for lipid in tqdm(lipids):
            for sample in samples:
                grid_image = self.create_grid_image(maindata, lipid, sample)
                self.store_grid_image(lipid, sample, grid_image)
                print(f"Stored grid image for lipid '{lipid}' and sample '{sample}'.")
