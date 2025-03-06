import os
import shelve
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)

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
    
    def __init__(self, path_db: str = "new_data/"):
        """Initialize the storage system.
        
        Args:
            path_db: Path to the directory where the shelve database will be stored
        """
        self.path_db = path_db
        if not os.path.exists(self.path_db):
            os.makedirs(self.path_db)
            
        # Initialize the metadata file if it doesn't exist
        self._init_metadata()
    
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
                logging.warning(f"Lipid image {key} already exists. Use force_update=True to overwrite.")
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
        key = f"{brain_id}/slice_{slice_index}/{lipid_name}"
        with shelve.open(os.path.join(self.path_db, "lipid_images")) as db:
            return db.get(key)
    
    # def get_available_brains(self) -> List[str]:
    #     """Get list of available brain IDs in the database."""
    #     with shelve.open(os.path.join(self.path_db, "metadata")) as db:
    #         return list(db["brain_info"].keys())
    
    # def get_available_slices(self, brain_id: str) -> List[int]:
    #     """Get list of available slice indices for a given brain."""
    #     with shelve.open(os.path.join(self.path_db, "metadata")) as db:
    #         brain_info = db["brain_info"]
    #         if brain_id not in brain_info:
    #             return []
    #         return list(brain_info[brain_id].keys())
    
    # def get_available_lipids(self, brain_id: str, slice_index: int) -> List[str]:
    #     """Get list of available lipids for a given brain and slice."""
    #     with shelve.open(os.path.join(self.path_db, "metadata")) as db:
    #         brain_info = db["brain_info"]
    #         if brain_id not in brain_info or slice_index not in brain_info[brain_id]:
    #             return []
    #         return brain_info[brain_id][slice_index]

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