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
import redis
from flask import session, request, render_template_string, jsonify
import time
import threading
import atexit
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

from modules.lipizone_data import LipizoneSampleData, LipizoneSectionData, LipizoneData
logging.info("Memory use after LipizoneSampleData, LipizoneSectionData, LipizoneData import" + logmem())

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

# --- Generate documentation files at startup ---
try:
    from readme.build import write_readme
    write_readme()
except Exception as e:
    print(f"Could not generate README.md: {e}")

try:
    from in_app_documentation.documentation import merge_md
    merge_md(write_doc=True)
except Exception as e:
    print(f"Could not generate documentation.md: {e}")

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
# logging.info("Loading lipizone sample data..." + logmem())
# lipizone_sample_data = LipizoneSampleData(
#     path_data=path_lipizone_data,
# )
# logging.info("Loading lipizone section data..." + logmem())
# lipizone_section_data = LipizoneSectionData(
#     path_data=path_lipizone_data,
# )
logging.info("Loading lipizone data..." + logmem())
lipizone_data = LipizoneData(
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
    celltype_data=celltype_data,
    lipizone_data=lipizone_data,
    # gene_data=gene_data,
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
# stream_figures = Figures(
#     maldi_data=stream_data,
#     celltype_data=celltype_data,
#     lipizone_data=lipizone_data,
#     # gene_data=gene_data,
#     storage=storage,
#     atlas=atlas,
# )

logging.info("Memory use after three main object have been instantiated" + logmem())

# Compute and shelve potentially missing objects
launch = Launch(data, atlas, figures, storage)
if os.environ.get("LBAE_PRECOMPUTE", "1") == "1":
    launch.launch()

logging.info("Memory use after main functions have been compiled" + logmem())

# ==================================================================================================
# --- Instantiate app and caching
# ==================================================================================================

# Launch server
server = flask.Flask(__name__)

# --- ⬇️ ADD THIS ENTIRE BLOCK ⬇️ ---

# Set a secret key for session management.
# For production, it's best to set this from an environment variable.
server.secret_key = 'e54f725a15888eab4eb35f95ec35b59dfa1fef344328d03b'

# --- Queuing System Configuration ---
MAX_ACTIVE_USERS = 25 
INACTIVITY_TIMEOUT_SECONDS = 60
QUEUE_TIMEOUT_SECONDS = 15 * 60 # (15 minutes)
long_callback_limiter = threading.Semaphore(4) 

# --- Connect to Redis ---
# Assumes Redis is running on localhost:6379. decode_responses=True is important.
redis_client = redis.Redis(decode_responses=True)
logging.info("Connected to Redis for session management.")

# --- The "Gatekeeper" Logic (Foundation) ---
# In app.py, replace your @server.before_request function with this one:

@server.before_request
def check_user_queue():
    # Allow requests for assets (CSS, JS) and internal Dash callbacks to pass through unchecked.
    # This is CRITICAL for the app to function.
    if request.path.startswith('/assets') or request.path.startswith('/_dash-') or request.path in ['/check-status', '/heartbeat']:
        return

    # Assign a unique session ID if one doesn't exist
    if 'user_id' not in session:
        session['user_id'] = str(uuid4())
        logging.info(f"New user connected. Assigned ID: {session['user_id']}")

    user_id = session['user_id']
    is_active = redis_client.sismember('active_users', user_id)

    # --- HAPPY PATH: User is already active ---
    if is_active:
        # Update their activity timestamp and let them through.
        redis_client.hset('user_activity', user_id, time.time())
        return  # Let the request proceed to the Dash app

    # --- NEW USER PATH: User is not yet active ---
    active_count = redis_client.scard('active_users')

    # Check if a spot is available
    if active_count < MAX_ACTIVE_USERS:
        # A spot is free! Make this user active.
        logging.info(f"User {user_id} granted access. Active count: {active_count + 1}/{MAX_ACTIVE_USERS}")
        redis_client.sadd('active_users', user_id)
        redis_client.hset('user_activity', user_id, time.time())
        # Just in case they were in the queue from a previous timed-out session
        redis_client.lrem('queued_users', 0, user_id)
        return  # Let the request proceed to the Dash app

    # --- APP IS FULL PATH ---
    else:
        logging.info(f"App is full. User {user_id} is being sent to the queue.")
        
        # Add to the end of the queue only if they aren't already there
        # This check prevents duplicate entries if the user refreshes the waiting page
        current_queue = redis_client.lrange('queued_users', 0, -1)
        if user_id not in current_queue:
            redis_client.rpush('queued_users', user_id)
            redis_client.hset('queued_timestamps', user_id, time.time())

        # For now, just return a simple "waiting" message with a 503 "Service Unavailable" status code.
        try:
            return render_template_string(open('queue.html').read()), 503
        except FileNotFoundError:
            return "<h1>Waiting Room</h1><p>Please wait...</p>", 503 # Fallback if file is missing
# --- ⬆️ END OF NEW BLOCK ⬆️ ---

# Prepare long callback support
launch_uid = uuid4()
cache_long_callback = diskcache.Cache(cache_dir)
long_callback_manager = DiskcacheLongCallbackManager(
    cache_long_callback,
    #####cache_by=[lambda: launch_uid],
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
    suppress_callback_exceptions=True,
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

# ADD THIS: Periodic cache cleanup to prevent memory accumulation
import threading
import time
import psutil

def periodic_cache_cleanup():
    """Clean up caches periodically to prevent memory accumulation."""
    while True:
        try:
            time.sleep(300)  # Every 5 minutes
            
            # Check if memory usage is high
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 75:  # If memory > 75%
                logging.warning(f"High memory usage detected ({memory_percent}%), clearing caches")
                
                # Clear Redis cache
                try:
                    figures.clear_all_redis_cache()
                    logging.info("Cleared Redis cache due to high memory usage")
                except Exception as e:
                    logging.error(f"Failed to clear Redis cache: {e}")
                
                # Clear Flask cache
                try:
                    cache_flask.clear()
                    logging.info("Cleared Flask cache due to high memory usage")
                except Exception as e:
                    logging.error(f"Failed to clear Flask cache: {e}")
                
                # ADD THIS: Clear long callback cache
                try:
                    long_callback_manager.clear_cache()
                    logging.info("Cleared long callback cache due to high memory usage")
                except Exception as e:
                    logging.error(f"Failed to clear long callback cache: {e}")
                
                # Force garbage collection
                import gc
                gc.collect()
                
        except Exception as e:
            logging.error(f"Cache cleanup error: {e}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=periodic_cache_cleanup, daemon=True)
cleanup_thread.start()

# Add basic configuration and slice index
# basic_config = {
#     "brain": "brain_1",
#     "slice_index": 0,
# }
# slice_index = 0

# Add the route to serve PDF files
@app.server.route('/lipizone-id-cards-pdf/<lipizone_name>')
def serve_pdf(lipizone_name):
    """Serve PDF files from the ID cards directory."""
    pdf_filename = f"lipizone_ID_card_{lipizone_name}.pdf"
    return flask.send_from_directory(ID_CARDS_PATH, pdf_filename)


@server.route('/check-status')
def check_status():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'No session'})

    if redis_client.sismember('active_users', user_id):
        return jsonify({'status': 'active'})
    else:
        try:
            queue = redis_client.lrange('queued_users', 0, -1)
            position = queue.index(user_id) + 1
            return jsonify({'status': 'queued', 'position': position, 'total': len(queue)})
        except ValueError:
            # Not in the queue and not active. This can happen if they timed out.
            # Tell the client to reload; the gatekeeper will re-evaluate them.
            return jsonify({'status': 'reload'})

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
    'cache_flask','long_callback_manager' 
    # 'stream_figures',
    ]

# --------------------------------------------------------------------------------------------------
# --- Janitor Function (Queue Management) ---
# --------------------------------------------------------------------------------------------------
# In app.py, REPLACE the entire manage_queue function with this one.

# In app.py, REPLACE the entire manage_queue function with this one.

def manage_queue():
    """
    Manages user queue:
    1. Removes stale users from the queue.
    2. Demotes inactive users.
    3. Promotes waiting users to fill empty spots.
    """
    logging.info("✅ Upgraded Queue manager thread started (v2 with queue timeout).")
    while True:
        try:
            lock = redis_client.set('queue_manager_lock', '1', ex=60, nx=True)
            if not lock:
                time.sleep(15)
                continue

            # --- 1. Purge stale users from the queue ---
            queued_timestamps = redis_client.hgetall('queued_timestamps')
            stale_queued_users = []
            for user_id, ts_str in queued_timestamps.items():
                if (time.time() - float(ts_str)) > QUEUE_TIMEOUT_SECONDS:
                    stale_queued_users.append(user_id)
            
            if stale_queued_users:
                logging.warning(f"JANITOR: Purging {len(stale_queued_users)} stale users from queue: {stale_queued_users}")
                for user_id in stale_queued_users:
                    redis_client.lrem('queued_users', 0, user_id)
                    # We will add a set for efficiency later if needed. For now, this is fine.
                    redis_client.hdel('queued_timestamps', user_id)
            
            # --- 2. Demote inactive users ---
            inactive_users = []
            active_users = redis_client.smembers('active_users')
            user_activity = redis_client.hgetall('user_activity')
            
            for user_id in active_users:
                last_seen_str = user_activity.get(user_id)
                if last_seen_str and (time.time() - float(last_seen_str)) > INACTIVITY_TIMEOUT_SECONDS:
                    inactive_users.append(user_id)

            if inactive_users:
                logging.info(f"JANITOR: Demoting {len(inactive_users)} inactive users: {inactive_users}")
                for user_id in inactive_users:
                    redis_client.srem('active_users', user_id)
                    redis_client.hdel('user_activity', user_id)
                    redis_client.rpush('queued_users', user_id)
                    redis_client.hset('queued_timestamps', user_id, time.time()) # Set their queue entry time

            # --- 3. Promote users from the queue ---
            current_active_count = redis_client.scard('active_users')
            if current_active_count < MAX_ACTIVE_USERS:
                slots_to_fill = MAX_ACTIVE_USERS - current_active_count
                for _ in range(slots_to_fill):
                    next_user = redis_client.lpop('queued_users')
                    if next_user:
                        logging.info(f"JANITOR: Promoting user {next_user} from queue.")
                        redis_client.hdel('queued_timestamps', next_user) # Clean up queue timestamp
                        redis_client.sadd('active_users', next_user)
                        redis_client.hset('user_activity', next_user, time.time())
                    else:
                        break
        except Exception as e:
            logging.error(f"Error in queue manager thread: {e}", exc_info=True)
        finally:
            if lock:
                redis_client.delete('queue_manager_lock')
        
        time.sleep(10)


# --- Start the background thread ---
# This check prevents the thread from starting twice in debug mode. It's safe for gunicorn.
if not os.environ.get("WERKZEUG_RUN_MAIN"):
    queue_manager_thread = threading.Thread(target=manage_queue, daemon=True)
    queue_manager_thread.start()

    # A cleanup function to ensure the lock is cleared when the app shuts down cleanly.
    @atexit.register
    def clear_redis_lock():
        logging.info("Application shutting down, clearing queue manager lock.")
        redis_client.delete('queue_manager_lock')


@server.route('/heartbeat', methods=['POST'])
def heartbeat():
    user_id = session.get('user_id')
    if user_id and redis_client.sismember('active_users', user_id):
        redis_client.hset('user_activity', user_id, time.time())
        return jsonify({'status': 'ok'})

    # If a user sends a heartbeat but isn't active (e.g., they timed out),
    # tell them their session is inactive so their page reloads.
    return jsonify({'status': 'inactive'}), 200