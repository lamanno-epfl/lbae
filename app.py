# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" In this module, the app is instantiated with a given server and cache config. Three global 
variables shared across all user sessions are also instantiated: data, atlas and figures.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output
from dash.long_callback import DiskcacheLongCallbackManager
import flask
from flask_caching import Cache
import logging
from uuid import uuid4
import diskcache
import os

# LBAE modules
from modules.tools.misc import logmem
logging.info("Memory use before any LBAE import" + logmem())

from modules.maldi_data import MaldiData
logging.info("Memory use after MaldiData import" + logmem())

from modules.program_data import ProgramData
logging.info("Memory use after ProgramData import" + logmem())

from modules.peak_data import PeakData
logging.info("Memory use after PeakData import" + logmem())

from modules.lipizone_data import LipizoneSampleData, LipizoneSectionData
logging.info("Memory use after LipizoneSampleData, LipizoneSectionData import" + logmem())

from modules.celltype_data import CelltypeData
logging.info("Memory use after CelltypeData import" + logmem())

from modules.stream_data import StreamData
logging.info("Memory use after StreakData import" + logmem())

from modules.grid_data import GridImageShelve
logging.info("Memory use after GridImageShelve import" + logmem())

from modules.figures import Figures
logging.info("Memory use after Figures import" + logmem())

from modules.atlas import Atlas
logging.info("Memory use after Atlas import" + logmem())

from modules.launch import Launch
logging.info("Memory use after Launch import" + logmem())

from modules.storage import Storage
logging.info("Memory use after Storage import" + logmem())

# ==================================================================================================
# --- App pre-computations
# ==================================================================================================

logging.info("Memory use before any global variable declaration" + logmem())

# Define if the app will use only a sample of the dataset, and uses a lower resolution for the atlas
SAMPLE_DATA = False

# Path to the ID cards
ID_CARDS_PATH = "./data/ID_cards"

# # Define paths for the sample/not sample data
# if SAMPLE_DATA:
#     path_data = "/data/LBA_DATA/lbae/data_sample/whole_dataset/"
#     path_program_data = "/data/LBA_DATA/lbae/data_sample/program_data/"
#     path_annotations = "/data/LBA_DATA/lbae/data_sample/annotations/"
#     path_db = "/data/LBA_DATA/lbae/data_sample/app_data/data.db"
#     cache_dir = "/data/LBA_DATA/lbae/data_sample/cache/"
# else:
#     # path_data = "data/whole_dataset/"
#     # path_annotations = "data/annotations/"
#     # path_db = "data/app_data/data.db"

cache_dir = "./data/cache/"

# path_data = "./data"
path_metadata = "./data/metadata"

path_grid_data = "./data/grid_data"
path_celltype_data = "./data/celltype_data"
path_lipid_data = "./data/lipid_data"
path_peak_data = "./data/peak_data"
path_program_data = "./data/program_data"
path_lipizone_data = "./data/lipizone_data"
path_stream_data = "./data/stream_data"

path_annotations = "./data/annotations/"

path_db = "./data/app_data/data.db"

# Load shelve database
logging.info("Loading storage..." + logmem())
storage = Storage(path_db)

# Load lipid data
logging.info("Loading MALDI data..." + logmem())
data = MaldiData(
    path_data=path_lipid_data, 
    path_metadata=path_metadata,
    path_annotations=path_annotations,
    )

# Load peak data
logging.info("Loading peak data..." + logmem())
peak_data = PeakData(
    path_data=path_peak_data,
    path_metadata=path_metadata,
    path_annotations=path_annotations,
)

# Load program data
logging.info("Loading program data..." + logmem())
program_data = ProgramData(
    path_data=path_program_data,
    path_metadata=path_metadata,
    path_annotations=path_annotations,
)

# Load stream data
logging.info("Loading stream data..." + logmem())
stream_data = StreamData(
    path_data=path_stream_data, 
    path_metadata=path_metadata,
    path_annotations=path_annotations,
)

# Load lipizone data
logging.info("Loading lipizone sample data..." + logmem())
lipizone_sample_data = LipizoneSampleData(
    path_data=path_lipizone_data,
)
logging.info("Loading lipizone section data..." + logmem())
lipizone_section_data = LipizoneSectionData(
    path_data=path_lipizone_data,
)

# Load celltype data
logging.info("Loading celltype data..." + logmem())
celltype_data = CelltypeData(
    path_data=path_celltype_data,
)

# Load grid data
logging.info("Loading grid data..." + logmem())
grid_data = GridImageShelve(
    path_data=path_grid_data,
)

# Load Atlas and Figures objects
logging.info("Loading Atlas..." + logmem())
atlas = Atlas(
    maldi_data=data,
    storage=storage,
    resolution=25,
)

logging.info("Loading Figures..." + logmem())
figures = Figures(
    maldi_data=data,
    storage=storage,
    atlas=atlas,
)
program_figures = Figures(
    maldi_data=program_data,
    storage=storage,
    atlas=atlas,
)
peak_figures = Figures(
    maldi_data=peak_data,
    storage=storage,
    atlas=atlas,
)
stream_figures = Figures(
    maldi_data=stream_data,
    storage=storage,
    atlas=atlas,
)

logging.info("Memory use after three main object have been instantiated" + logmem())

# Compute and shelve potentially missing objects
launch = Launch(data, atlas, figures, storage)
launch.launch()

logging.info("Memory use after main functions have been compiled" + logmem())

# ==================================================================================================
# --- Instantiate app and caching
# ==================================================================================================

# Launch server
server = flask.Flask(__name__)

# Prepare long callback support
launch_uid = uuid4()
cache_long_callback = diskcache.Cache(cache_dir)
long_callback_manager = DiskcacheLongCallbackManager(
    cache_long_callback,
    cache_by=[lambda: launch_uid],
    expire=500,
)

# Instantiate app
app = dash.Dash(
    title="Lipid Brain Atlas Explorer",
    external_stylesheets=[dbc.themes.DARKLY],
    external_scripts=[
        {"src": "https://cdn.jsdelivr.net/npm/dom-to-image@2.6.0/dist/dom-to-image.min.js"}
    ],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    server=server,
    suppress_callback_exceptions=False,
    long_callback_manager=long_callback_manager,
    compress=True,
    # use_pages=True  # Enable pages feature for Dash 3.0.1
)


# Add a class attribute to specify if redis is being used
app.use_redis = False

# Set up flask caching in addition to long_callback_manager
if app.use_redis:
    CACHE_CONFIG = {
        # We use 'redis' for faster file retrieval
        "CACHE_TYPE": "redis",
        "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379"),
    }
else:
    CACHE_CONFIG = {
        # We use 'FileSystemCache' as we want the application to be lightweight in term of RAM
        "CACHE_TYPE": "FileSystemCache",
        "CACHE_DIR": cache_dir,
        "CACHE_THRESHOLD": 200,
    }

# Initiate Cache
cache_flask = Cache()
cache_flask.init_app(app.server, config=CACHE_CONFIG)

# Initiate the cache as unlocked
cache_flask.set("locked-cleaning", False)
cache_flask.set("locked-reading", False)

# Add basic configuration and slice index
# basic_config = {
#     "brain": "brain_1",
#     "slice_index": 0,
# }
# slice_index = 0

#################################################################################################### ????

# Add the route to serve PDF files
@app.server.route('/lipizone-id-cards-pdf/<lipizone_name>')
def serve_pdf(lipizone_name):
    """Serve PDF files from the ID cards directory."""
    pdf_filename = f"lipizone_ID_card_{lipizone_name}.pdf"
    return flask.send_from_directory(ID_CARDS_PATH, pdf_filename)

# Make grid_data available for import
__all__ = [
    'data', 
    'program_data',
    'peak_data',
    'lipizone_sample_data', 
    'lipizone_section_data',
    'celltype_data',
    'grid_data', 
    'stream_data',
    'atlas',
    'figures', 
    'program_figures',
    'peak_figures',
    'stream_figures',
    ]

# Add a callback to combine the styles from both pages and apply them to the main-slider
@app.callback(
    Output("main-slider", "style"),
    Input("page-2-main-slider-style", "data"),
    Input("page-2bis-main-slider-style", "data"),
)
def combine_slider_styles(style1, style2):
    """Combines the styles from both pages and applies them to the main-slider."""
    # If either style is None, use the other one
    if style1 is None:
        return style2
    if style2 is None:
        return style1
    
    # If both styles are present, use the one that has display: block
    if style1.get("display") == "block":
        return style1
    if style2.get("display") == "block":
        return style2
    
    # Default to the first style
    return style1
