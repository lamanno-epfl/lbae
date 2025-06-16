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

from scipy import ndimage

# Make sure to import or define these functions:
# from your_module import create_section_grid, normalize_grid_with_percentiles

def create_distance_weighted_kernel(decay_factor=0.5):
    """
    Create a weighting kernel where weights decrease with distance from center.
    
    Parameters:
    -----------
    decay_factor : float
        Factor controlling how quickly weights decrease with distance (0 to 1)
        
    Returns:
    --------
    dict
        Dictionary mapping kernel positions to distance-based weights
    """
    kernel = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]
    
    weights = {}
    for di, dj in kernel:
        # Calculate Euclidean distance
        distance = np.sqrt(di**2 + dj**2)
        # Apply exponential decay
        weights[(di, dj)] = np.exp(-decay_factor * distance)
    
    return weights

def fill_holes_with_neighbor_averaging(pic, max_iterations=100, mask=None, weights=None):
    """
    Fill in the holes (None or NaN values) in an image array using weighted averaging
    from neighboring pixels. Works with continuous numerical values.
    Only fills holes within a mask area (if provided).
    
    Parameters:
    -----------
    pic : numpy.ndarray
        The image array with holes (None or NaN values) and continuous values
    max_iterations : int
        Maximum number of iterations to perform
    mask : numpy.ndarray, optional
        Boolean mask where True indicates areas to fill holes in
    weights : dict, optional
        Dictionary mapping kernel positions to weights for weighted averaging
        Default is equal weights for all neighbors
        
    Returns:
    --------
    numpy.ndarray
        The filled image array
    """
    # Handle both None values and NaN values
    if pic.dtype == object:
        # Convert None values to NaN for easier handling
        numeric_pic = np.zeros(pic.shape, dtype=float)
        for i in range(pic.shape[0]):
            for j in range(pic.shape[1]):
                if pic[i, j] is None:
                    numeric_pic[i, j] = np.nan
                else:
                    try:
                        numeric_pic[i, j] = float(pic[i, j])
                    except (ValueError, TypeError):
                        # If conversion fails, store the original value
                        numeric_pic[i, j] = pic[i, j]
    else:
        # Already numeric array
        numeric_pic = np.array(pic, dtype=float)
    
    height, width = numeric_pic.shape
    
    # Create a copy of the original image
    filled_pic = numeric_pic.copy()
    
    # Create a mask if not provided
    if mask is None:
        # Create a mask where NaN values need to be filled
        mask = np.isnan(filled_pic)
    
    # Define the kernel for 8-neighborhood
    kernel = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]
    
    # Set default weights if not provided
    if weights is None:
        weights = {pos: 1.0 for pos in kernel}
    
    iteration = 0
    holes_filled = 0
    
    # Count initial holes within the mask
    initial_holes = np.sum(np.logical_and(np.isnan(filled_pic), mask))
    
    while iteration < max_iterations:
        # Track whether any changes were made in this iteration
        changes_made = False
        filled_in_iteration = 0
        
        # Create a copy to store the updates
        new_pic = filled_pic.copy()
        
        # Find holes (NaN values) within the mask
        for i in range(height):
            for j in range(width):
                if np.isnan(filled_pic[i, j]) and mask[i, j]:
                    # Collect valid values from the 8-neighborhood with their weights
                    neighbor_values = []
                    neighbor_weights = []
                    
                    for di, dj in kernel:
                        ni, nj = i + di, j + dj
                        # Check boundary conditions
                        if 0 <= ni < height and 0 <= nj < width:
                            if not np.isnan(filled_pic[ni, nj]):
                                neighbor_values.append(filled_pic[ni, nj])
                                neighbor_weights.append(weights[(di, dj)])
                    
                    # Fill the hole if we have neighbors
                    if neighbor_values:
                        # Weighted average
                        total_weight = sum(neighbor_weights)
                        weighted_sum = sum(value * weight for value, weight 
                                          in zip(neighbor_values, neighbor_weights))
                        new_pic[i, j] = weighted_sum / total_weight
                        changes_made = True
                        filled_in_iteration += 1
        
        # Update the image with new values
        filled_pic = new_pic
        holes_filled += filled_in_iteration
        
        # If no changes were made, we're done
        if not changes_made:
            break
            
        iteration += 1
    return filled_pic

def fill_holes_with_gaussian_average(pic, max_iterations=100, mask=None, sigma=1.0):
    """
    Fill in holes using Gaussian-weighted averaging of neighboring pixels.
    
    Parameters:
    -----------
    pic : numpy.ndarray
        The image array with holes (None or NaN values) and continuous values
    max_iterations : int
        Maximum number of iterations to perform
    mask : numpy.ndarray, optional
        Boolean mask where True indicates areas to fill holes in
    sigma : float
        Standard deviation for the Gaussian kernel
        
    Returns:
    --------
    numpy.ndarray
        The filled image array
    """
    # Create Gaussian weights
    weights = create_distance_weighted_kernel(1.0/(2*sigma**2))
    
    # Use the weighted averaging function
    return fill_holes_with_neighbor_averaging(pic, max_iterations, mask, weights)

def create_brain_mask(pic, closing_radius=3, min_hole_size=100):
    """
    Create a mask of the brain area based on the non-None/non-NaN pixels.
    Uses binary morphological operations to create a clean brain mask.
    
    Parameters:
    -----------
    pic : numpy.ndarray
        The original image with holes
    closing_radius : int
        Radius for morphological closing to smooth brain boundary
    min_hole_size : int
        Minimum size of holes to fill within the brain mask
        
    Returns:
    --------
    numpy.ndarray
        Boolean mask where True indicates the brain area
    """
    height, width = pic.shape
    
    # Create initial binary mask (True for non-None/non-NaN pixels)
    binary_mask = np.zeros((height, width), dtype=bool)
    
    # Handle both None values and NaN values
    if pic.dtype == object:
        # Object array (likely with None values)
        for i in range(height):
            for j in range(width):
                binary_mask[i, j] = pic[i, j] is not None
    else:
        # Numeric array (with potential NaN values)
        binary_mask = ~np.isnan(pic)
    
    # Perform morphological closing to close small gaps in the boundary
    structure = ndimage.generate_binary_structure(2, 2)  # 8-connectivity
    closed_mask = ndimage.binary_closing(
        binary_mask, 
        structure=structure,
        iterations=closing_radius
    )
    
    # Fill holes in the mask to define the brain region
    filled_mask = ndimage.binary_fill_holes(closed_mask)
    
    # Remove small interior structures incorrectly masked as background
    # Label all background regions
    background = ~filled_mask
    labeled_bg, num_bg = ndimage.label(background)
    
    # Find the exterior (main) background region
    exterior_label = labeled_bg[0, 0]  # Assumes corner is exterior
    
    # Create new mask with only large interior holes preserved
    refined_mask = filled_mask.copy()
    
    # Process each labeled background region
    for label in range(1, num_bg + 1):
        if label == exterior_label:
            continue  # Skip the exterior
            
        # Check if this is a small interior hole that should be filled
        region = labeled_bg == label
        if np.sum(region) < min_hole_size:
            refined_mask[region] = True  # Fill small holes
    
    # Keep only the largest connected component (main brain)
    labeled_brain, num_brain = ndimage.label(refined_mask)
    if num_brain > 1:
        sizes = np.bincount(labeled_brain.ravel())[1:]
        largest_label = np.argmax(sizes) + 1
        refined_mask = labeled_brain == largest_label
    
    return refined_mask

def process_section(maindata, section_id, lipid_column, img_height=320, img_width=456):
    """
    Process a single section and generate the visualization array
    
    Parameters:
    -----------
    maindata : pandas.DataFrame
        The main data containing all sections
    section_id : float or int
        The section ID to process
    lipid_column : str
        Column name for the lipid values to visualize
    img_height : int
        Height of the output image
    img_width : int
        Width of the output image
    
    Returns:
    --------
    tuple
        (rgba_image, brain_mask)
    """
    # Filter data for this section
    sec = maindata.loc[maindata['SectionID'] == section_id]
    
    if len(sec) == 0:
        raise ValueError(f"No data found for section ID {section_id}")
    
    # Extract coordinates and values
    # Adjust column names based on your actual data structure
    try:
        scatter = pd.DataFrame({
            "x": sec['z_index'].values,  # Adjust column names as needed
            "y": sec['y_index'].values,  # Adjust column names as needed
            "value": sec[lipid_column].values
        })
    except KeyError as e:
        logging.info(f"Column not found: {e}. Available columns: {sec.columns.tolist()}")
        raise
    
    # Initialize empty image array
    pic = np.full((img_height, img_width), np.nan)
    
    # Get integer indices and values
    try:
        x_indices = scatter["y"].astype(int).values  # Note: x/y are swapped for image coords
        y_indices = scatter["x"].astype(int).values
        values = scatter["value"].values
    except Exception as e:
        logging.info(f"Error processing coordinates: {e}")
        raise
    
    # Handle out of bounds indices
    valid_mask = (
        (x_indices < pic.shape[0]) & 
        (y_indices < pic.shape[1]) & 
        (x_indices >= 0) & 
        (y_indices >= 0) &
        (~np.isnan(values))
    )
    
    if not np.any(valid_mask):
        raise ValueError(f"No valid data points found for section {section_id}")
    
    x_indices = x_indices[valid_mask]
    y_indices = y_indices[valid_mask]
    values = values[valid_mask]
    
    # Populate the image array
    pic[x_indices, y_indices] = values
    
    # Create brain mask
    brain_mask = create_brain_mask(pic, closing_radius=5, min_hole_size=150)
    
    # Fill holes
    filled_pic = fill_holes_with_gaussian_average(pic, mask=brain_mask)
    
    return filled_pic, brain_mask


def create_section_grid(maindata, section_ids, lipid_column, cols=8):
    """
    Create a grid of processed section images
    
    Parameters:
    -----------
    maindata : pandas.DataFrame
        The main data containing all sections
    section_ids : list
        List of section IDs to process
    lipid_column : str
        Column name for the lipid values to visualize
    cols : int
        Number of columns in the grid
    
    Returns:
    --------
    numpy.ndarray
        Grid of RGBA images as a single numpy array
    """
    # Process all sections first to get image arrays
    section_images = []
    section_masks = []
    actual_sections = []
    
    for section_id in section_ids:
        try:
            # Check if section exists
            sec = maindata.loc[maindata['SectionID'] == section_id]
            
            # Skip if section doesn't exist in the data
            if len(sec) == 0:
                logging.info(f"Section {section_id} not found in data, skipping...")
                continue
                
            logging.info(f"Processing section {section_id}...")
            rgba_image, mask = process_section(maindata, section_id, lipid_column)
            section_images.append(rgba_image)
            section_masks.append(mask)
            actual_sections.append(section_id)
        except Exception as e:
            logging.info(f"Error processing section {section_id}: {e}")
            continue
    
    # Return early if no sections were processed
    if len(section_images) == 0:
        raise ValueError("No sections were successfully processed")
    
    # Calculate grid dimensions based on actual number of sections
    num_sections = len(section_images)
    rows = (num_sections + cols - 1) // cols  # Ceiling division
    
    # Get image dimensions from the first image
    img_height, img_width = section_images[0].shape
    
    # Create an empty grid
    grid = np.full((rows * img_height, cols * img_width), np.nan)
    
    # Fill the grid with images
    for i, (img, mask, section_id) in enumerate(zip(section_images, section_masks, actual_sections)):
        
        row = i // cols
        col = i % cols
        
        # Adjust alpha channel based on mask
        img_with_mask = img.copy()
        # Make non-brain regions transparent
        #img_with_mask[:, :, 3] = np.where(mask, 0.9, 0)
        
        # Place the image in the grid
        row_start = row * img_height
        row_end = (row + 1) * img_height
        col_start = col * img_width
        col_end = (col + 1) * img_width
        
        grid[row_start:row_end, col_start:col_end] = img_with_mask
        
    return grid


def normalize_grid_with_percentiles(grid_image):
    """
    Min-max normalize a 2D numpy array using the 1st and 99th percentiles.
    This function preserves NaN values and clips outliers.
    
    Args:
        grid_image: 2D numpy array that may contain NaN values
        
    Returns:
        Normalized 2D numpy array with preserved NaN values
    """
    # Create a copy to avoid modifying the original
    normalized = grid_image.copy()
    
    # Get mask of non-NaN values
    mask = ~np.isnan(grid_image)
    
    # Calculate 1st and 99th percentiles of non-NaN values
    p1 = np.percentile(grid_image[mask], 0.5)
    p99 = np.percentile(grid_image[mask], 99.5)
    
    # Clip values outside the percentile range
    normalized[mask] = np.clip(grid_image[mask], p1, p99)
    
    # Min-max normalize the non-NaN values
    if p99 > p1:  # Avoid division by zero
        normalized[mask] = (normalized[mask] - p1) / (p99 - p1)
    
    return normalized

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
            cols = 7
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
            logging.info("Missing sample")
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
                # add many nans as a padding on top and bottom of the image
                grid_image = np.pad(grid_image, ((400, 400), (0, 0)), mode='edge')
                self.store_grid_image(lipid, sample, grid_image)
