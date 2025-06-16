import os
import shelve
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from time import time
from typing import Dict, List, Optional, Tuple

from modules.maldi_data import SliceData, majority_vote_9x9
from modules.atlas import ABA_DIM, ABA_CONTOURS, ACRONYM_MASKS, ACRONYMS_PIXELS
# from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
from scipy.ndimage import generic_filter

# Set up logging
logging.basicConfig(level=logging.INFO)

# @dataclass
# class programImage:
#     """Class to store program image data and metadata.

#     Attributes:
#         name: Name of the program
#         image: 2D numpy array containing the program distribution
#         brain_id: ID of the brain this image is from
#         slice_index: Index of the slice in the brain
#         is_scatter: Whether this is a scatterplot (True) or image (False)
#     """

#     name: str
#     image: np.ndarray   ########## lipid_expression (dim: num_pixels, 1) --> change this!!
#     indices: np.ndarray ########## x_index, y_index, z_index (dim: num_pixels, 3)
#     brain_id: str
#     slice_index: int

class ProgramData:
    """Class to handle the storage of the program data format with direct program images.

    This class provides methods to:
    1. Store and retrieve program images for multiple brains
    2. List available brains and programs
    3. Access metadata about the stored data
    """

    def __init__(
        self, 
        path_data: str = "./data/program_data/",
        path_metadata: str = "./data/metadata/",
        path_annotations: str = "./data/annotations/"
    ):
        """Initialize the storage system.

        Args:
            path_data: Path to the directory where the shelve database will be stored
        """
        self.path_data = path_data
        self.path_metadata = path_metadata
        self.path_annotations = path_annotations

        if not os.path.exists(self.path_data):
            os.makedirs(self.path_data)

        self._df_annotations = pd.read_csv(os.path.join(self.path_annotations, "lp_annotation.csv"))
        
        # Initialize the metadata file if it doesn't exist
        self._init_metadata()

        self.image_shape = (ABA_DIM[1], ABA_DIM[2])

        self.acronyms_masks = ACRONYM_MASKS
        # for slice_idx in self.get_slice_list():
        #     # append get_acronym_mask to the list
        #     self.acronyms_masks[slice_idx] = self.get_acronym_mask(slice_idx)
        # self.acronyms_masks_with_holes = ACRONYM_MASKS_WITH_HOLES

    def get_annotations(self) -> pd.DataFrame:
        return self._df_annotations
    
    # def get_AP_avg_coordinates(self, indices="ReferenceAtlas"):
    #     coordinates_csv = pd.read_csv(os.path.join(self.path_annotations, "sectionid_to_rostrocaudal_slider_new.csv"))
    #     slices = self.get_slice_list(indices=indices)
    #     return coordinates_csv.loc[coordinates_csv["SectionID"].isin(slices), :]

    def get_brain_id_from_sliceindex(self, slice_index):
        try:
            with shelve.open(os.path.join(self.path_metadata, "metadata_programs")) as db_metadata:
                brain_info = db_metadata["brain_info"]
                for brain_id in self.get_available_brains():
                    if slice_index in brain_info[brain_id]["slice_indices"]:
                        return brain_id
        except:
            logging.info("Missing sample")
            return np.nan

    def _init_metadata(self):
        """Initialize or load the metadata about stored brains and lipids."""
        with shelve.open(os.path.join(self.path_metadata, "metadata_programs")) as db_metadata:
            if "brain_info" not in db_metadata:
                db_metadata["brain_info"] = {}

    def add_programs_image(
        self, 
        slice_data: SliceData, 
        force_update: bool = False
        ):
        """Add a slice data to the database.

        Args:
            slice_data: SliceData object containing the image and metadata
            force_update: If True, overwrite existing data
        """
        # Update metadata
        with shelve.open(os.path.join(self.path_metadata, "metadata_programs")) as db_metadata:
            # if "brain_info" not in db_metadata:
            #     db_metadata["brain_info"] = {}
            brain_info = db_metadata["brain_info"]

            if slice_data.brain_id not in brain_info:
                brain_info[slice_data.brain_id] = {}
                brain_info[slice_data.brain_id]['slice_indices'] = []
                brain_info[slice_data.brain_id]['program_names'] = slice_data.content_names

            if slice_data.slice_index not in brain_info[slice_data.brain_id]['slice_indices']:
                brain_info[slice_data.brain_id]['slice_indices'].append(slice_data.slice_index)

            # if slice_data.name not in brain_info[slice_data.brain_id][slice_data.slice_index]:
            #     brain_info[slice_data.brain_id][slice_data.slice_index].append(slice_data.name)

            db_metadata["brain_info"] = brain_info

        # Store the actual image data
        key = f"{slice_data.brain_id}/slice_{slice_data.slice_index}"
        with shelve.open(os.path.join(self.path_data, "program_images")) as db:
            if key in db and not force_update:
                logging.warning(
                    f"Slice data {key} already exists. Use force_update=True to overwrite."
                )
                return
            db[key] = slice_data

    # def get_programs_image(self, slice_index: int, program_name: str) -> Optional[programImage]:
    #     """Retrieve a program image from the database.

    #     Args:
    #         brain_id: ID of the brain
    #         slice_index: Index of the slice
    #         program_name: Name of the program

    #     Returns:
    #         programImage object if found, None otherwise
    #     """
    #     brain_id = self.get_brain_id_from_sliceindex(slice_index)
    #     key = f"{brain_id}/slice_{float(slice_index)}/{program_name}"
    #     with shelve.open(os.path.join(self.path_data, "program_images")) as db:
    #         return db.get(key)

    def get_programs_image(self, slice_index: int):
        """Retrieve a program image from the database.

        Args:
            brain_id: ID of the brain
            slice_index: Index of the slice

        Returns:
            SliceData object if found, None otherwise
        """
        brain_id = self.get_brain_id_from_sliceindex(slice_index)
        key = f"{brain_id}/slice_{float(slice_index)}"
        with shelve.open(os.path.join(self.path_data, "program_images")) as db:
            return db.get(key)

    def get_available_brains(self) -> List[str]:
        """Get list of available brain IDs in the database."""
        with shelve.open(os.path.join(self.path_metadata, "metadata_programs")) as db_metadata:
            return list(db_metadata["brain_info"].keys())

    def get_available_slices(self, brain_id: str) -> List[int]:
        """Get list of available slice indices for a given brain."""
        with shelve.open(os.path.join(self.path_metadata, "metadata_programs")) as db_metadata:
            brain_info = db_metadata["brain_info"]
            if brain_id not in brain_info:
                return []
            # slices = list(brain_info[brain_id].keys())
            slices = brain_info[brain_id]['slice_indices']
            coordinates_csv = pd.read_csv(os.path.join(self.path_annotations, "sectionid_to_rostrocaudal_slider_new.csv"))
            slices = coordinates_csv.loc[coordinates_csv["SectionID"].isin(slices), 'SectionID'].values
            return slices

    def get_available_programs(self, slice_index: Optional[int] = None) -> List[str]:
        """Get list of available programs for a given brain and slice."""
        if slice_index is None:
            slice_index = self.get_slice_list()[0]
        brain_id = self.get_brain_id_from_sliceindex(slice_index)
        with shelve.open(os.path.join(self.path_metadata, "metadata_programs")) as db_metadata:
            brain_info = db_metadata["brain_info"]
            if brain_id not in brain_info or slice_index not in brain_info[brain_id]['slice_indices']:
                return []
            return brain_info[brain_id]['program_names']
            # Use the parameters passed to the function

    def get_image_indices(self, slice_index):
        """Get the indices of a lipid image from the database.

        Args:
            slice_index: Index of the slice
            lipid_name: Name of the lipid
        """
        return self.get_programs_image(slice_index).indices #, self.get_available_programs(slice_index)[0]).indices

    # def get_acronym_mask(self, slice_index, fill_holes=True):
    #     """
    #     Retrieves the acronyms mask for a given slice index.
    #     """
    #     # z_coord = METADATA[METADATA["SectionID"] == slice_index]["x_index"].values
    #     # take the acronyms of the rows of metadata that have SectionID == slice_index
    #     acronym_points = ACRONYMS_PIXELS[slice_index]
    #     coordinates = self.get_image_indices(slice_index)
        
    #     # Create DataFrame with proper column alignment
    #     acronym_scatter = pd.DataFrame({
    #         'x_index': coordinates[:, 0],
    #         'x': coordinates[:, 2],
    #         'y': coordinates[:, 1],
    #         'acronym': acronym_points
    #     })

    #     # if the elements of acronym_scatter["acronym"].values are None, replace them with "undefined"
    #     if slice_index in [33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0]:
    #         return np.full(self.image_shape, 'Undefined')
    #     max_len = max(len(s) for s in acronym_scatter["acronym"].values)
    #     arr = np.full(self.image_shape, 'Undefined', dtype=f'U{max(max_len, len("Undefined"))}')  # Adjust dimensions if needed

    #     # Convert coordinates to integers for indexing
    #     x_indices = acronym_scatter["x"].astype(int).values
    #     y_indices = acronym_scatter["y"].astype(int).values
    #     # Ensure indices are within bounds
    #     valid_indices = (
    #         (0 <= x_indices) & (x_indices < 1000) & (0 <= y_indices) & (y_indices < 1000)
    #     )

    #     # Fill the array with values at the specified coordinates
    #     arr[y_indices[valid_indices], x_indices[valid_indices]] = acronym_scatter["acronym"].values[
    #         valid_indices
    #     ]
    #     arr_z = np.full(self.image_shape, np.nan)
    #     arr_z[y_indices[valid_indices], x_indices[valid_indices]] = acronym_scatter["x_index"].values[
    #         valid_indices
    #     ]
    #     arr_z = generic_filter(arr_z, function=majority_vote_9x9, size=(9, 9), mode='constant', cval=np.nan)

    #     mcc = MouseConnectivityCache(manifest_file='./data/atlas/mouse_connectivity_manifest.json')
    #     structure_tree = mcc.get_structure_tree()

    #     # pixels = pixels
    #     annotation, _ = mcc.get_annotation_volume()

    #     # Check if we need to fill holes
    #     if fill_holes:
    #         # Count how many NaN values we have
    #         # nan_count_before = (arr == 'Undefined').sum()

    #         for i in range(arr.shape[0]):
    #             for j in range(arr.shape[1]):
    #                 if arr[i,j] == 'Undefined':
    #                     x_index = arr_z[i,j]
    #                     # x_index = z_coord[0]
    #                     y_index = i
    #                     z_index = j

    #                 try:
    #                     index = annotation[int(x_index), int(y_index), int(z_index)]
    #                     brain_region = structure_tree.get_structures_by_id([index])[0]
                    
    #                     if brain_region is not None:
    #                         arr[y_index, z_index] = brain_region['acronym']
    #                 except:
    #                     continue

    #     return arr

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
        # acronym_points = METADATA[METADATA["SectionID"] == slice_index][["z_index", "y_index", "x_index"]].values
        coordinates = self.get_image_indices(slice_index)
        coordinates_scatter = pd.DataFrame(coordinates, columns=["x_index", "y", "x"])
        
        # Convert coordinates to integers for indexing
        x_indices = coordinates_scatter["x"].astype(int).values
        y_indices = coordinates_scatter["y"].astype(int).values
        # Ensure indices are within bounds
        valid_indices = (
            (0 <= x_indices) & (x_indices < 1000) & (0 <= y_indices) & (y_indices < 1000)
        )

        arr_z = np.full(self.image_shape, np.nan)
        arr_z[y_indices[valid_indices], x_indices[valid_indices]] = coordinates_scatter["x_index"].values[
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

    def extract_lipid_image(
        self, 
        slice_index, 
        program_name, 
        fill_holes=True):
        """Extract a program image from scatter data with optional hole filling.
        
        Args:
            slice_index: Index of the slice
            program_name: Name of the program
            fill_holes: Whether to fill holes using nearest neighbor interpolation
            
        Returns:
            2D numpy array with the program distribution or None if not found
        """
        try:
            # Use the parameters passed to the function
            # program_data = self.get_program_image(slice_index, program_name)
            # program_data.indices --> x_index, y_index, z_index (dim: num_pixels, 3)
            # program_data.image --> program_expression (dim: num_pixels, 1)
            slice_data = self.get_programs_image(slice_index)
            # slice_data.indices --> x_index, y_index, z_index (dim: num_pixels, 3)
            # slice_data.images --> program_expression (dim: num_pixels, num_programs)
            
            if slice_data is None:
                logging.info(f"Slice {slice_index} was not found.")
                return None

            # # Check if it's scatter data
            # if not lipid_data.is_scatter:
            #     # If it's already an image, just return it
            #     return lipid_data.image

            # Convert scatter data to image
            # scatter_points = lipid_data.image  # This is a numpy array with shape (N, 1)

            # Create a DataFrame from the scatter points
            program_data = slice_data.images[:, slice_data.content_names.index(program_name)]
            scatter = pd.DataFrame({
                            "x": slice_data.indices[:, 2],
                            "y": slice_data.indices[:, 1],
                            "value": program_data # ensure it's 1D
                        })

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
            arr[y_indices[valid_indices], x_indices[valid_indices]] = scatter["value"].values[
                valid_indices
            ]

            # Check if we need to fill holes
            if fill_holes:
                # Count how many NaN values we have
                nan_count_before = np.isnan(arr).sum()

                if nan_count_before > 0:
                    # Fill holes using nearest neighbor interpolation
                    filled_arr = self._fill_holes_nearest_neighbor(arr, slice_index)

                    return filled_arr
                    
################################################################################################################
            p02, p98 = np.nanpercentile(arr, [2, 98])
            arr = np.clip(arr, p02, p98)
            arr = (arr - p02) / (p98 - p02)
################################################################################################################

            return arr
        except Exception as e:
            logging.info(f"Error extracting {program_name} in slice {slice_index}: {str(e)}")
            return None
            
    def _fill_holes_nearest_neighbor(self, arr, slice_index, max_distance=5):
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
            if x < max_distance or y < max_distance or x >= arr.shape[0] - max_distance or y >= arr.shape[1] - max_distance:
                continue
                
            # Extract a window around the NaN point
            window = arr[x-max_distance:x+max_distance+1, y-max_distance:y+max_distance+1]
            
            # Skip if all values in the window are NaN
            if np.all(np.isnan(window)):
                continue
                
            # Get the nearest non-NaN value
            window_values = window.flatten()
            non_nan_values = window_values[~np.isnan(window_values)]
            
            if len(non_nan_values) > 0:
                # Use the mean of nearby non-NaN values
                filled[x, y] = np.mean(non_nan_values)

        binary_mask = np.where(self.acronyms_masks[slice_index] == 'Undefined', np.nan, 1)
        filled = filled * binary_mask

        return filled
    
        # """
        # # Optional: For remaining NaN values, use a more aggressive approach
        # # This is a simple approach - for any remaining NaNs, find the nearest
        # # valid point in the entire array (could be slow for large arrays)
        # remaining_nans = np.where(np.isnan(filled))
        # if len(remaining_nans[0]) > 0:
        #     logging.info(f"Using global search for {len(remaining_nans[0])} remaining holes")
            
        #     from scipy.spatial import cKDTree
            
        #     # Build a KD-tree of valid points
        #     valid_points = np.array(valid_indices).T
        #     tree = cKDTree(valid_points)
            
        #     # For each remaining NaN, find the nearest valid point
        #     for i in range(len(remaining_nans[0])):
        #         x, y = remaining_nans[0][i], remaining_nans[1][i]
                
        #         # Find the index of the nearest valid point
        #         _, nearest_idx = tree.query([x, y], k=1)
                
        #         # Get the coordinates of the nearest valid point
        #         nearest_x, nearest_y = valid_points[nearest_idx]
                
        #         # Use the value from the nearest valid point
        #         filled[x, y] = arr[nearest_x, nearest_y]
        # return filled
        # """
        

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
        coordinates_csv = pd.read_csv(os.path.join(self.path_annotations, "sectionid_to_rostrocaudal_slider_new.csv"))
        
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

    def return_program_options(self):
        """Computes and returns the list of program names, structures and cation.

        Returns:
            (list): List of program names, structures and cations.
        """

        return [
            {
                "label": lp,
                "value": lp,
                "group": "NMF Embeddings" if lp.startswith("globalembedding") else "Lipid Programs"
            }
            for lp in self.get_available_programs()
        ]

    """
    def empty_database(self):
        # Remove all data from the database.
        # Remove metadata
        with shelve.open(self.path_metadata) as db:
            db.clear()
        self._init_metadata()
        
        # Remove image data
        with shelve.open(os.path.join(self.path_data, "program_images")) as db:
            db.clear()
    """
