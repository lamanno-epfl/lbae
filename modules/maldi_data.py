import os
import shelve
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from time import time
from typing import Dict, List, Optional, Tuple
from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
import numpy as np
from scipy.ndimage import generic_filter
from collections import Counter
import pickle

# Set up logging
logging.basicConfig(level=logging.INFO)

ABA_DIM = (528, 320, 456)
ABA_CONTOURS = np.load("/data/francesca/lbae/data/atlas/eroded_annot.npy")
METADATA = pd.read_parquet("/data/LBA_DATA/Explorer2Paper/maindata_2.parquet").iloc[:, 173:221]
ACRONYM_MASKS = pickle.load(open("/data/francesca/lbae/data/atlas/acronyms_masks.pkl", "rb"))

def majority_vote_9x9(window):
    # The window is flattened (9*9=81 elements); the center pixel is at index 40.
    center_index = len(window) // 2  
    center_value = window[center_index]
    
    # If the center is not NaN, keep its original value.
    if not np.isnan(center_value):
        return center_value
    
    # Exclude NaN values from the window.
    valid = window[~np.isnan(window)]
    if valid.size == 0:
        # If all neighbors are NaN, we return NaN (or you could choose another default).
        return np.nan
    
    # Count the occurrences of each valid value.
    counts = Counter(valid)
    # Get the most common value (the mode).
    mode, _ = counts.most_common(1)[0]
    return mode


@dataclass
class LipidImage:
    """Class to store lipid image data and metadata.

    Attributes:
        name: Name of the lipid (without cation)
        image: 2D numpy array containing the lipid distribution
        brain_id: ID of the brain this image is from
        slice_index: Index of the slice in the brain
        is_scatter: Whether this is a scatterplot (True) or image (False)
    """

    name: str
    image: np.ndarray
    brain_id: str
    slice_index: int
    is_scatter: bool = False


class MaldiData:
    """Class to handle the storage of the new MALDI data format with direct lipid images.

    This class provides methods to:
    1. Store and retrieve lipid images for multiple brains
    2. List available brains and lipids
    3. Access metadata about the stored data
    """

    def __init__(
        self, path_db: str = "../new_data/", path_annotations: str = "../data/annotations/"
    ):
        """Initialize the storage system.

        Args:
            path_db: Path to the directory where the shelve database will be stored
        """
        self.path_db = path_db
        if not os.path.exists(self.path_db):
            os.makedirs(self.path_db)
        self._df_annotations = pd.read_csv(os.path.join(path_annotations, "lipid_annotation.csv"))
        
        # Initialize the metadata file if it doesn't exist
        self._init_metadata()

        self.image_shape = (ABA_DIM[1], ABA_DIM[2])

        self.acronyms_masks = ACRONYM_MASKS
        # for slice_idx in self.get_slice_list():
        #     # append get_acronym_mask to the list
        #     self.acronyms_masks[slice_idx] = self.get_acronym_mask(slice_idx)

    def get_annotations(self) -> pd.DataFrame:
        return self._df_annotations

    def get_coordinates(self, indices="ReferenceAtlas"):
        coordinates_csv = pd.read_csv("/data/francesca/lbae/assets/sectionid_to_rostrocaudal_slider_sorted.csv")
        slices = self.get_slice_list(indices=indices)
        return coordinates_csv.loc[coordinates_csv["SectionID"].isin(slices), :]

    def get_brain_id_from_sliceindex(self, slice_index):
        lookup_brainid = pd.read_csv(os.path.join(self.path_db, "lookup_brainid.csv"), index_col=0)

        try:
            sample = lookup_brainid.loc[
                lookup_brainid["SectionID"] == slice_index, "Sample"
            ].values[0]
            return sample

        except:
            print("Missing sample")
            return np.nan

    def _init_metadata(self):
        """Initialize or load the metadata about stored brains and lipids."""
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            if "brain_info" not in db:
                db["brain_info"] = {}  # Dict[brain_id, Dict[slice_index, List[lipid_names]]]

    def add_lipid_image(self, lipid_data: LipidImage, force_update: bool = False):
        """Add a lipid image to the database.

        Args:
            lipid_data: LipidImage object containing the image and metadata
            force_update: If True, overwrite existing data
        """
        # Update metadata
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            brain_info = db["brain_info"]

            if lipid_data.brain_id not in brain_info:
                brain_info[lipid_data.brain_id] = {}

            if lipid_data.slice_index not in brain_info[lipid_data.brain_id]:
                brain_info[lipid_data.brain_id][lipid_data.slice_index] = []

            if lipid_data.name not in brain_info[lipid_data.brain_id][lipid_data.slice_index]:
                brain_info[lipid_data.brain_id][lipid_data.slice_index].append(lipid_data.name)

            db["brain_info"] = brain_info

        # Store the actual image data
        key = f"{lipid_data.brain_id}/slice_{lipid_data.slice_index}/{lipid_data.name}"
        with shelve.open(os.path.join(self.path_db, "lipid_images")) as db:
            if key in db and not force_update:
                logging.warning(
                    f"Lipid image {key} already exists. Use force_update=True to overwrite."
                )
                return
            db[key] = lipid_data

    def get_lipid_image(self, slice_index: int, lipid_name: str) -> Optional[LipidImage]:
        """Retrieve a lipid image from the database.

        Args:
            brain_id: ID of the brain
            slice_index: Index of the slice
            lipid_name: Name of the lipid

        Returns:
            LipidImage object if found, None otherwise
        """
        brain_id = self.get_brain_id_from_sliceindex(slice_index)
        key = f"{brain_id}/slice_{float(slice_index)}/{lipid_name}"
        with shelve.open(os.path.join(self.path_db, "lipid_images")) as db:
            return db.get(key)

    def get_available_brains(self) -> List[str]:
        """Get list of available brain IDs in the database."""
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            return list(db["brain_info"].keys())

    def get_available_slices(self, brain_id: str) -> List[int]:
        """Get list of available slice indices for a given brain."""
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            brain_info = db["brain_info"]
            if brain_id not in brain_info:
                return []
            slices = list(brain_info[brain_id].keys())
            coordinates_csv = pd.read_csv("/data/francesca/lbae/assets/sectionid_to_rostrocaudal_slider_sorted.csv")
            slices = coordinates_csv.loc[coordinates_csv["SectionID"].isin(slices), 'SectionID'].values
            return slices

    def get_available_lipids(self, slice_index: int) -> List[str]:
        """Get list of available lipids for a given brain and slice."""
        brain_id = self.get_brain_id_from_sliceindex(slice_index)
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            brain_info = db["brain_info"]
            if brain_id not in brain_info or slice_index not in brain_info[brain_id]:
                return []
            return brain_info[brain_id][slice_index]
            # Use the parameters passed to the function

    def get_acronym_mask(self, slice_index, fill_holes=True):
        """
        Retrieves the acronyms mask for a given slice index.
        """
        # print(f"slice_index: {slice_index}")
        # z_coord = METADATA[METADATA["SectionID"] == slice_index]["x_index"].values
        # take the acronyms of the rows of metadata that have SectionID == slice_index
        acronym_points = METADATA[METADATA["SectionID"] == slice_index][["z_index", "y_index", "acronym", "x_index"]].values
        acronym_scatter = pd.DataFrame(acronym_points, columns=["x", "y", "acronym", "x_index"])

        # print unique values of the third column
        # if the elements of acronym_scatter["acronym"].values are None, replace them with "undefined"
        if slice_index in [33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0]:
            return np.full(self.image_shape, 'Undefined')
        max_len = max(len(s) for s in acronym_scatter["acronym"].values)
        arr = np.full(self.image_shape, 'Undefined', dtype=f'U{max(max_len, len("Undefined"))}')  # Adjust dimensions if needed

        # Convert coordinates to integers for indexing
        x_indices = acronym_scatter["x"].astype(int).values
        y_indices = acronym_scatter["y"].astype(int).values
        # Ensure indices are within bounds
        valid_indices = (
            (0 <= x_indices) & (x_indices < 1000) & (0 <= y_indices) & (y_indices < 1000)
        )

        # Fill the array with values at the specified coordinates
        arr[y_indices[valid_indices], x_indices[valid_indices]] = acronym_scatter["acronym"].values[
            valid_indices
        ]
        arr_z = np.full(self.image_shape, np.nan)
        arr_z[y_indices[valid_indices], x_indices[valid_indices]] = acronym_scatter["x_index"].values[
            valid_indices
        ]
        arr_z = generic_filter(arr_z, function=majority_vote_9x9, size=(9, 9), mode='constant', cval=np.nan)

        mcc = MouseConnectivityCache(manifest_file='mouse_connectivity_manifest.json')
        structure_tree = mcc.get_structure_tree()

        # pixels = pixels
        annotation, _ = mcc.get_annotation_volume()

        # Check if we need to fill holes
        if fill_holes:
            # Count how many NaN values we have
            # nan_count_before = (arr == 'Undefined').sum()
            # print(f"Found {nan_count_before} NaN values (holes) in the image")

            for i in range(arr.shape[0]):
                for j in range(arr.shape[1]):
                    if arr[i,j] == 'Undefined':
                        x_index = arr_z[i,j]
                        # x_index = z_coord[0]
                        y_index = i
                        z_index = j

                    try:
                        index = annotation[int(x_index), int(y_index), int(z_index)]
                        brain_region = structure_tree.get_structures_by_id([index])[0]
                    
                        if brain_region is not None:
                            arr[y_index, z_index] = brain_region['acronym']
                    except:
                        continue
                        # print error message
                        # print(f"Error at {i}, {j}")

        return arr

    def get_aba_contours(self, slice_index):
        """
        Retrieves the contours of the ABA brain for a given slice.
        
        Args:
            slice_index: Index of the slice to retrieve
            
        Returns:
            array_image_atlas: RGBA image array of shape (320, 456, 4) containing the contours
                            in orange (255, 165, 0) with transparency 243 for lines and 255
                            for background
        """
        acronym_points = METADATA[METADATA["SectionID"] == slice_index][["z_index", "y_index", "x_index"]].values
        acronym_scatter = pd.DataFrame(acronym_points, columns=["x", "y", "x_index"])

        
        # Convert coordinates to integers for indexing
        x_indices = acronym_scatter["x"].astype(int).values
        y_indices = acronym_scatter["y"].astype(int).values
        # Ensure indices are within bounds
        valid_indices = (
            (0 <= x_indices) & (x_indices < 1000) & (0 <= y_indices) & (y_indices < 1000)
        )

        arr_z = np.full(self.image_shape, np.nan)
        arr_z[y_indices[valid_indices], x_indices[valid_indices]] = acronym_scatter["x_index"].values[
            valid_indices
        ]
        arr_z = generic_filter(arr_z, function=majority_vote_9x9, size=(9, 9), mode='constant', cval=np.nan)

        # define array_image_atlas as all values to be (255, 255, 255, 0)
        array_image_atlas = np.ones((arr_z.shape[0], arr_z.shape[1], 4), dtype=np.uint8)
        array_image_atlas[:, :, :3] = 255
        array_image_atlas[:, :, 3] = 0

        for i in range(arr_z.shape[0]):
            for j in range(arr_z.shape[1]):
                k = arr_z[i,j]
                try:
                    is_contour = ABA_CONTOURS[int(k), i, j] == 1
                    if is_contour:
                        array_image_atlas[i, j] = [255, 165, 0, 200]
                except:
                    continue
        
        return array_image_atlas

    def extract_lipid_image(self, slice_index, lipid_name, fill_holes=True):
        """Extract a lipid image from scatter data with optional hole filling.

        Args:
            slice_index: Index of the slice
            lipid_name: Name of the lipid
            fill_holes: Whether to fill holes using nearest neighbor interpolation

        Returns:
            2D numpy array with the lipid distribution or None if not found
        """
        try:
            # Use the parameters passed to the function
            lipid_data = self.get_lipid_image(slice_index, lipid_name)

            if lipid_data is None:
                print(f"{lipid_name} in slice {slice_index} was not found.")
                return None

            # Check if it's scatter data
            if not lipid_data.is_scatter:
                # If it's already an image, just return it
                return lipid_data.image

            # Convert scatter data to image
            scatter_points = lipid_data.image  # This is a numpy array with shape (N, 3)

            # Create a DataFrame from the scatter points
            scatter = pd.DataFrame(scatter_points, columns=["y", "x", "value"])

            # Create an empty array to hold the image
            arr = np.full(self.image_shape, np.nan)  # Adjust dimensions if needed

            # Convert coordinates to integers for indexing
            x_indices = scatter["x"].astype(int).values # z_index
            y_indices = scatter["y"].astype(int).values # y_index

            # Ensure indices are within bounds
            valid_indices = (
                (0 <= x_indices) & (x_indices < 1000) & (0 <= y_indices) & (y_indices < 1000)
            )

            # Fill the array with values at the specified coordinates
            arr[x_indices[valid_indices], y_indices[valid_indices]] = scatter["value"].values[
                valid_indices
            ]

            # Check if we need to fill holes
            if fill_holes:
                # Count how many NaN values we have
                nan_count_before = np.isnan(arr).sum()
                print(f"Found {nan_count_before} NaN values (holes) in the image")

                if nan_count_before > 0:
                    # Fill holes using nearest neighbor interpolation
                    filled_arr = self._fill_holes_nearest_neighbor(arr)

                    # Count remaining NaN values after filling
                    nan_count_after = np.isnan(filled_arr).sum()
                    print(f"After filling: {nan_count_after} NaN values remain")

                    return filled_arr

            return arr

        except Exception as e:
            print(f"Error extracting {lipid_name} in slice {slice_index}: {str(e)}")
            return None

    def _fill_holes_nearest_neighbor(self, arr, max_distance=5):
        """Fill holes (NaN values) using nearest neighbor interpolation.

        Args:
            arr: 2D numpy array with potential NaN values
            max_distance: Maximum distance to search for neighbors

        Returns:
            2D numpy array with holes filled
        """
        # Make a copy to avoid modifying the original
        filled = arr.copy()

        # Find indices of NaN values
        nan_indices = np.where(np.isnan(arr))

        # No NaN values, return the original array
        if len(nan_indices[0]) == 0:
            return filled

        # Find indices of non-NaN values
        valid_indices = np.where(~np.isnan(arr))
        valid_values = arr[valid_indices]

        # For each NaN point, find the nearest non-NaN neighbor
        for i in range(len(nan_indices[0])):
            x, y = nan_indices[0][i], nan_indices[1][i]

            # Skip if we're at the boundary
            if (
                x < max_distance
                or y < max_distance
                or x >= arr.shape[0] - max_distance
                or y >= arr.shape[1] - max_distance
            ):
                continue

            # Extract a window around the NaN point
            window = arr[
                x - max_distance : x + max_distance + 1, y - max_distance : y + max_distance + 1
            ]

            # Skip if all values in the window are NaN
            if np.all(np.isnan(window)):
                continue

            # Get the nearest non-NaN value
            window_values = window.flatten()
            non_nan_values = window_values[~np.isnan(window_values)]

            if len(non_nan_values) > 0:
                # Use the mean of nearby non-NaN values
                filled[x, y] = np.mean(non_nan_values)

        """
        # Optional: For remaining NaN values, use a more aggressive approach
        # This is a simple approach - for any remaining NaNs, find the nearest
        # valid point in the entire array (could be slow for large arrays)
        remaining_nans = np.where(np.isnan(filled))
        if len(remaining_nans[0]) > 0:
            print(f"Using global search for {len(remaining_nans[0])} remaining holes")
            
            from scipy.spatial import cKDTree
            
            # Build a KD-tree of valid points
            valid_points = np.array(valid_indices).T
            tree = cKDTree(valid_points)
            
            # For each remaining NaN, find the nearest valid point
            for i in range(len(remaining_nans[0])):
                x, y = remaining_nans[0][i], remaining_nans[1][i]
                
                # Find the index of the nearest valid point
                _, nearest_idx = tree.query([x, y], k=1)
                
                # Get the coordinates of the nearest valid point
                nearest_x, nearest_y = valid_points[nearest_idx]
                
                # Use the value from the nearest valid point
                filled[x, y] = arr[nearest_x, nearest_y]
        """

        return filled

    def get_slice_number(self):
        """Getter for the number of slice present in the dataset.

        Returns:
            (int): The number of slices in the dataset.
        """
        return np.array(
            [len(self.get_available_slices(b_id)) for b_id in self.get_available_brains()]
        ).sum()

    def get_slice_list(self, indices="all"):
        """Getter for the list of slice indices.

        Args:
            indices (str, optional): If "all", return the list of all slice indices. If "brain_1",
                return the list of slice indices for brain 1. If "brain_2", return the list of
                slice indices for brain 2. Defaults to "all". Indices start at 1.

        Returns:
            (list): The list of requested slice indices.
        """
        # sort slices based on the xccf column in the coordinates_csv
        coordinates_csv = pd.read_csv("/data/francesca/lbae/assets/sectionid_to_rostrocaudal_slider_sorted.csv")

        if indices == "all":
            slices = []
            brains = self.get_available_brains()
            for brain in brains:
                slices.extend(self.get_available_slices(brain))
            slices = sorted(slices, key=lambda x: coordinates_csv.loc[coordinates_csv["SectionID"] == x, "xccf"].values[0])
            
            return slices
        elif indices in ["ReferenceAtlas", "SecondAtlas", "Female1", "Female2", "Female3", 
                        "Male1", "Male2", "Male3", "Pregnant1", "Pregnant2", "Pregnant4"]:
            slices = self.get_available_slices(brain_id=indices)
            # Sort by xccf coordinate
            return sorted(slices, key=lambda x: coordinates_csv.loc[coordinates_csv["SectionID"] == x, "xccf"].values[0])
        else:
            raise ValueError("Invalid string for indices")

    def return_lipid_options(self):
        """Computes and returns the list of lipid names, structures and cation.

        Returns:
            (list): List of lipid names, structures and cations.
        """
        return [
            {
                "label": ln,
                "value": ln,
                "group": "Multiple matches" if len([ln.split(" ")[i] for i in range(0, len(ln.split(" ")), 2)]) > 1 else ln.split(" ")[0],
            }
            for ln in self.get_available_lipids(1)
        ]

    """
    def empty_database(self):
        # Remove all data from the database.
        # Remove metadata
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            db.clear()
        self._init_metadata()
        
        # Remove image data
        with shelve.open(os.path.join(self.path_db, "lipid_images")) as db:
            db.clear()
    """

import os
import shelve
import numpy as np
from tqdm import tqdm

# Make sure to import or define these functions:
# from your_module import create_section_grid, normalize_grid_with_percentiles

class GridImageShelve:
    """
    A class to generate, store, and retrieve grid images for given lipid and sample.
    The images are stored in a shelve database located in the 'grid_data' folder.
    """
    def __init__(self, shelf_dir="grid_data", shelf_filename="grid_shelve"):
        """
        Initializes the shelve database in the given directory.
        """
        self.shelf_dir = shelf_dir
        # self.shelf_dir = os.path.abspath(shelf_dir)
        print("QUIIII shelf_dir:", self.shelf_dir)
        # Create the grid_data folder if it does not exist
        if not os.path.exists(self.shelf_dir):
            os.makedirs(self.shelf_dir)
        # Shelve uses the given filename as the base for its files
        self.shelf_path = os.path.join(self.shelf_dir, shelf_filename)

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
        lookup_brainid = pd.read_csv("./new_data/lookup_brainid.csv", index_col=0)

        try:
            sample = lookup_brainid.loc[
                lookup_brainid["SectionID"] == slice_index, "Sample"
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
        print("self.shelf_path:", self.shelf_path)
        print("key:", key)
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

class SampleDataShelve:
    """
    A class to store and retrieve processed sample data (grid image,
    grayscale image, and color masks) using a shelve database.
    """
    def __init__(self, shelf_filename="sample_data_shelve", shelf_dir="sample_data"):
        """
        Initializes the shelve database.
        
        Parameters:
            shelf_filename (str): Base filename for the shelve database.
            shelf_dir (str): Directory in which to store the shelve files.
        """
        self.shelf_dir = shelf_dir
        # Create the directory if it does not exist
        if not os.path.exists(shelf_dir):
            os.makedirs(shelf_dir)
        self.shelf_path = os.path.join(shelf_dir, shelf_filename)
    
    def store_sample_data(self, sample, grid_image, rgb_image, grayscale_image, color_masks):
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
            "color_masks": color_masks
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


class SectionDataShelve:
    """
    A class to store and retrieve processed section data (grid image, RGB image,
    grayscale image, and color masks) using a shelve database.
    """
    def __init__(self, shelf_filename="section_data_shelve", shelf_dir="section_data"):
        """
        Initializes the shelve database.
        
        Parameters:
            shelf_filename (str): Base filename for the shelve database.
            shelf_dir (str): Directory in which to store the shelve files.
        """
        self.shelf_dir = shelf_dir
        # Create the directory if it does not exist
        if not os.path.exists(shelf_dir):
            os.makedirs(shelf_dir)
        self.shelf_path = os.path.join(shelf_dir, shelf_filename)
    
    def store_section_data(self, section, grid_image, grayscale_image, color_masks):
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
            "grid_image": grid_image,
            "grayscale_image": grayscale_image,
            "color_masks": color_masks
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
