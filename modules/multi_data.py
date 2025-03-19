import os
import shelve
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from time import time
from typing import Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)

ABA_DIM = (528, 320, 456)

@dataclass
class GeneImage:
    """Class to store gene image data and metadata.

    Attributes:
        name: Name of the gene (without cation)
        image: 2D numpy array containing the gene distribution
        brain_id: ID of the brain this image is from
        slice_index: Index of the slice in the brain
        is_scatter: Whether this is a scatterplot (True) or image (False)
    """

    name: str
    image: np.ndarray
    brain_id: str
    slice_index: int
    is_scatter: bool = False


class GeneData:
    """Class to handle the storage of the new GENE data format with direct gene images.

    This class provides methods to:
    1. Store and retrieve gene images for multiple brains
    2. List available brains and genes
    3. Access metadata about the stored data
    """

    def __init__(
        self, path_db: str = "../multi_data/", path_annotations: str = "../data/annotations/"
    ):
        """Initialize the storage system.

        Args:
            path_db: Path to the directory where the shelve database will be stored
        """
        self.path_db = path_db
        if not os.path.exists(self.path_db):
            os.makedirs(self.path_db)
        self._df_annotations = pd.read_csv(os.path.join(path_annotations, "gene_annotation.csv"))
        
        # Initialize the metadata file if it doesn't exist
        self._init_metadata()

        self.image_shape = (ABA_DIM[1], ABA_DIM[2])

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
        """Initialize or load the metadata about stored brains and genes."""
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            if "brain_info" not in db:
                db["brain_info"] = {}  # Dict[brain_id, Dict[slice_index, List[gene_names]]]

    def add_gene_image(self, gene_data: GeneImage, force_update: bool = False):
        """Add a gene image to the database.

        Args:
            gene_data: GeneImage object containing the image and metadata
            force_update: If True, overwrite existing data
        """
        # Update metadata
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            brain_info = db["brain_info"]

            if gene_data.brain_id not in brain_info:
                brain_info[gene_data.brain_id] = {}

            if gene_data.slice_index not in brain_info[gene_data.brain_id]:
                brain_info[gene_data.brain_id][gene_data.slice_index] = []

            if gene_data.name not in brain_info[gene_data.brain_id][gene_data.slice_index]:
                brain_info[gene_data.brain_id][gene_data.slice_index].append(gene_data.name)

            db["brain_info"] = brain_info

        # Store the actual image data
        key = f"{gene_data.brain_id}/slice_{gene_data.slice_index}/{gene_data.name}"
        with shelve.open(os.path.join(self.path_db, "gene_images")) as db:
            if key in db and not force_update:
                logging.warning(
                    f"Gene image {key} already exists. Use force_update=True to overwrite."
                )
                return
            db[key] = gene_data

    def get_gene_image(self, slice_index: int, gene_name: str) -> Optional[GeneImage]:
        """Retrieve a gene image from the database.

        Args:
            brain_id: ID of the brain
            slice_index: Index of the slice
            gene_name: Name of the gene

        Returns:
            GeneImage object if found, None otherwise
        """
        brain_id = self.get_brain_id_from_sliceindex(slice_index)
        key = f"{brain_id}/slice_{float(slice_index)}/{gene_name}"
        with shelve.open(os.path.join(self.path_db, "gene_images")) as db:
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

    def get_available_genes(self, slice_index: int) -> List[str]:
        """Get list of available genes for a given brain and slice."""
        brain_id = self.get_brain_id_from_sliceindex(slice_index)
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            brain_info = db["brain_info"]
            if brain_id not in brain_info or slice_index not in brain_info[brain_id]:
                return []
            return brain_info[brain_id][slice_index]
            # Use the parameters passed to the function

    def extract_gene_image(self, slice_index, gene_name, fill_holes=True):
        """Extract a gene image from scatter data with optional hole filling.

        Args:
            slice_index: Index of the slice
            gene_name: Name of the gene
            fill_holes: Whether to fill holes using nearest neighbor interpolation

        Returns:
            2D numpy array with the gene distribution or None if not found
        """
        try:
            # Use the parameters passed to the function
            gene_data = self.get_gene_image(slice_index, gene_name)

            if gene_data is None:
                print(f"{gene_name} in slice {slice_index} was not found.")
                return None

            # Check if it's scatter data
            if not gene_data.is_scatter:
                # If it's already an image, just return it
                return gene_data.image

            # Convert scatter data to image
            scatter_points = gene_data.image  # This is a numpy array with shape (N, 3)

            # Create a DataFrame from the scatter points
            scatter = pd.DataFrame(scatter_points, columns=["y", "x", "value"])

            # Create an empty array to hold the image
            arr = np.full(self.image_shape, np.nan)  # Adjust dimensions if needed

            # Convert coordinates to integers for indexing
            x_indices = scatter["x"].astype(int).values
            y_indices = scatter["y"].astype(int).values

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
            print(f"Error extracting {gene_name} in slice {slice_index}: {str(e)}")
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
        return np.array([ 1.,  3.,  4.,  7.,  8.,  9., 11., 12., 14., 15., 16., 17., 18.,
       19., 22., 23., 24., 26., 27., 28., 29., 30., 31., 32.])

    def return_gene_options(self):
        """Computes and returns the list of gene names, structures and cation.

        Returns:
            (list): List of gene names, structures and cations.
        """
        return [
            {
                "label": ln,
                "value": ln,
                "group": "Multiple matches" if len([ln.split(" ")[i] for i in range(0, len(ln.split(" ")), 2)]) > 1 else ln.split(" ")[0],
            }
            for ln in self.get_available_genes(1)
        ]

import os
import shelve
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from time import time
from typing import Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)

ABA_DIM = (528, 320, 456)

@dataclass
class StreamImage:
    """Class to store stream image data and metadata.

    Attributes:
        name: Name of the stream (without cation)
        image: 2D numpy array containing the stream distribution
        brain_id: ID of the brain this image is from
        slice_index: Index of the slice in the brain
        is_scatter: Whether this is a scatterplot (True) or image (False)
    """

    name: str
    image: np.ndarray
    brain_id: str
    slice_index: int
    is_scatter: bool = False


class StreamData:
    """Class to handle the storage of the new STREAM data format with direct stream images.

    This class provides methods to:
    1. Store and retrieve stream images for multiple brains
    2. List available brains and streams
    3. Access metadata about the stored data
    """

    def __init__(
        self, path_db: str = "../multi_data/", path_annotations: str = "../data/annotations/"
    ):
        """Initialize the storage system.

        Args:
            path_db: Path to the directory where the shelve database will be stored
        """
        self.path_db = path_db
        if not os.path.exists(self.path_db):
            os.makedirs(self.path_db)
        self._df_annotations = pd.read_csv(os.path.join(path_annotations, "stream_annotation.csv"))
        
        # Initialize the metadata file if it doesn't exist
        self._init_metadata()

        self.image_shape = (ABA_DIM[1], ABA_DIM[2])

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
        """Initialize or load the metadata about stored brains and streams."""
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            if "brain_info" not in db:
                db["brain_info"] = {}  # Dict[brain_id, Dict[slice_index, List[stream_names]]]

    def add_stream_image(self, stream_data: StreamImage, force_update: bool = False):
        """Add a stream image to the database.

        Args:
            stream_data: StreamImage object containing the image and metadata
            force_update: If True, overwrite existing data
        """
        # Update metadata
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            brain_info = db["brain_info"]

            if stream_data.brain_id not in brain_info:
                brain_info[stream_data.brain_id] = {}

            if stream_data.slice_index not in brain_info[stream_data.brain_id]:
                brain_info[stream_data.brain_id][stream_data.slice_index] = []

            if stream_data.name not in brain_info[stream_data.brain_id][stream_data.slice_index]:
                brain_info[stream_data.brain_id][stream_data.slice_index].append(stream_data.name)

            db["brain_info"] = brain_info

        # Store the actual image data
        key = f"{stream_data.brain_id}/slice_{stream_data.slice_index}/{stream_data.name}"
        with shelve.open(os.path.join(self.path_db, "stream_images")) as db:
            if key in db and not force_update:
                logging.warning(
                    f"Stream image {key} already exists. Use force_update=True to overwrite."
                )
                return
            db[key] = stream_data

    def get_stream_image(self, slice_index: int, stream_name: str) -> Optional[StreamImage]:
        """Retrieve a stream image from the database.

        Args:
            brain_id: ID of the brain
            slice_index: Index of the slice
            stream_name: Name of the stream

        Returns:
            StreamImage object if found, None otherwise
        """
        brain_id = self.get_brain_id_from_sliceindex(slice_index)
        key = f"{brain_id}/slice_{float(slice_index)}/{stream_name}"
        with shelve.open(os.path.join(self.path_db, "stream_images")) as db:
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

    def get_available_streams(self, slice_index: int) -> List[str]:
        """Get list of available streams for a given brain and slice."""
        brain_id = self.get_brain_id_from_sliceindex(slice_index)
        with shelve.open(os.path.join(self.path_db, "metadata")) as db:
            brain_info = db["brain_info"]
            if brain_id not in brain_info or slice_index not in brain_info[brain_id]:
                return []
            return brain_info[brain_id][slice_index]
            # Use the parameters passed to the function

    def extract_stream_image(self, slice_index, stream_name, fill_holes=True):
        """Extract a stream image from scatter data with optional hole filling.

        Args:
            slice_index: Index of the slice
            stream_name: Name of the stream
            fill_holes: Whether to fill holes using nearest neighbor interpolation

        Returns:
            2D numpy array with the stream distribution or None if not found
        """
        try:
            # Use the parameters passed to the function
            stream_data = self.get_stream_image(slice_index, stream_name)

            if stream_data is None:
                print(f"{stream_name} in slice {slice_index} was not found.")
                return None

            # Check if it's scatter data
            if not stream_data.is_scatter:
                # If it's already an image, just return it
                return stream_data.image

            # Convert scatter data to image
            scatter_points = stream_data.image  # This is a numpy array with shape (N, 3)

            # Create a DataFrame from the scatter points
            scatter = pd.DataFrame(scatter_points, columns=["y", "x", "value"])

            # Create an empty array to hold the image
            arr = np.full(self.image_shape, np.nan)  # Adjust dimensions if needed

            # Convert coordinates to integers for indexing
            x_indices = scatter["x"].astype(int).values
            y_indices = scatter["y"].astype(int).values

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
            print(f"Error extracting {stream_name} in slice {slice_index}: {str(e)}")
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
        return self.get_available_slices(brain_id="ReferenceAtlas")


    def return_stream_options(self):
        """Computes and returns the list of stream names, structures and cation.

        Returns:
            (list): List of stream names, structures and cations.
        """
        return [
            {
                "label": ln,
                "value": ln,
                "group": "Multiple matches" if len([ln.split(" ")[i] for i in range(0, len(ln.split(" ")), 2)]) > 1 else ln.split(" ")[0],
            }
            for ln in self.get_available_streams(1)
        ]