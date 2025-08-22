#!/usr/bin/env python3
"""
UNIFIED STABILITY TEST SUITE - PARALLEL EXECUTION (V2 - REALISTIC SIMULATION)
================================================================================

This script simulates N realistic users running a comprehensive test suite in parallel.
It uses asyncio to manage concurrent, stateful, and logic-driven test runs.

PAGES COVERED:
- All pages from the original script, now navigated dynamically.

NEW FEATURES:
- 🧠 Realistic User Behavior Simulation (Stateful journeys, weighted navigation, "stickiness")
- 🛡️ Test Robustness and Resiliency (Intelligent waits, chaos engineering, soft success)
- ⚙️ Refined Automation Patterns (Action-Wait-Capture loop, resilient selectors)
"""

import asyncio
import logging
import time
import psutil
import os
import argparse
import random
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# --- 🧠 CONFIGURATION FOR REALISTIC USER BEHAVIOR ---
# Weighted navigation: Simulates which pages are more "popular".
PAGE_WEIGHTS = {
    '/lipizones-selection': 25,
    '/lipizones-vs-celltypes': 15,
    '/lipids-vs-genes': 20,
    '/3D-exploration': 10,
    '/lipid-selection': 10,
    '/peak-selection': 10,
    '/region-analysis': 5,
    '/lp-selection': 10,
}

# "Stickiness": Probability a user stays on a page to perform more actions after required ones are done.
LONG_STAY_PROB = {
    '/lipizones-selection': 0.8,
    '/lipids-vs-genes': 0.9,
    '/3D-exploration': 0.6,
    'default': 0.5
}

# --- 🛡️ CONFIGURATION FOR ROBUSTNESS & RESILIENCY ---
# Chaos Engineering: Chance (out of 1.0) to randomly reload the page after an action.
REFRESH_CHANCE = 0.02

# Soft Success: Action names that can fail without stopping the test (logged as warnings).
SOFT_SUCCESS = {
    'lis_toggle_annotations', 'lvc_toggle_annotations', 'lvg_toggle_annotations',
    'ra_toggle_annotations', 'ls_toggle_annotations', 'ps_toggle_annotations',
    'lps_toggle_annotations', 'lvg_select_lipid', 'lvg_select_gene',
    'lis_move_slider', 'lvc_move_slider', 'lvg_move_slider', 'ls_move_slider',
    'ps_move_slider', 'lps_move_slider',
    # ADD THESE LINES
    '3d_select_lipid', 'ls_select_lipid_from_dropdown', 'ps_select_peak',
    'lps_select_program', 'ra_select_regions', 'ra_assign_groups'
}


# This class is unchanged
class SystemMonitor:
    """Monitor system resources during testing."""

    def __init__(self):
        self.start_time = time.time()
        self.start_cpu = psutil.cpu_percent()
        self.start_memory = psutil.virtual_memory().percent

    def get_current_stats(self):
        """Get current system statistics."""
        current_time = time.time()
        elapsed = current_time - self.start_time
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        return {
            'elapsed_seconds': elapsed,
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_available_gb': psutil.virtual_memory().available / (1024**3)
        }

    # Modified to accept a logger instance for user-specific logging
    def log_stats(self, logger, stage_name):
        """Log current system statistics."""
        stats = self.get_current_stats()
        logger.info(f"📊 SYSTEM STATS [{stage_name}] - "
                    f"Elapsed: {stats['elapsed_seconds']:.1f}s, "
                    f"CPU: {stats['cpu_percent']:.1f}%, "
                    f"RAM: {stats['memory_percent']:.1f}% "
                    f"({stats['memory_available_gb']:.2f}GB available)")

class UnifiedStabilityTestSuite:
    """
    Main test suite that simulates a single, stateful user journey.
    """

    def __init__(self, user_id: int, browser_instance, screenshot: bool = False, duration_minutes: int = 5):
        self.user_id = user_id
        self.browser = browser_instance
        self.logger = self._setup_logger(user_id)
        self.monitor = SystemMonitor()
        self.screenshot = screenshot
        self.screenshot_counter = 0
        
        self.start_time = datetime.now()
        
        # --- MODIFICATION ---
        # Stop user journeys after a random interval between 1 and 10 minutes.
        random_duration_minutes = random.uniform(1, 10)
        self.end_time = self.start_time + timedelta(minutes=random_duration_minutes)
        self.logger.info(f"⏳ This user journey will run for a random duration of {random_duration_minutes:.2f} minutes.")

        # --- MODIFICATION ---
        # Schedule the first timed page change.
        self._schedule_next_page_change()

        # 🧠 STATE MANAGEMENT
        self.current_page_path = "/" # User starts at the homepage
        self.user_context = {'brain_selected': False, 'lipizones_selected': False}
        self.required_actions = {} # Tracks required actions left on the current page
        self.page_actions_map = self._map_page_actions()

        self.test_results = {
            'actions_succeeded': 0,
            'actions_failed': 0,
            'actions_soft_failed': 0,
            'pages_visited': set()
        }
        
        # Screenshot folder is now unique per user.
        self.screenshot_folder = f"screenshots/user_{self.user_id}"
        if self.screenshot:
            os.makedirs(self.screenshot_folder, exist_ok=True)
            self.logger.info(f"📁 Screenshot folder created: {self.screenshot_folder}")

    def _setup_logger(self, user_id: int):
        """Configures and returns a logger unique to this test instance."""
        os.makedirs("logs", exist_ok=True)
        
        logger = logging.getLogger(f"TestSuite_User_{user_id}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        if logger.hasHandlers():
            return logger

        log_filename = f'logs/user_{user_id}_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(logging.Formatter(f'%(asctime)s - USER {user_id} - %(levelname)s - %(message)s'))
        
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(f'%(asctime)s - USER {user_id} - %(levelname)s - %(message)s'))

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        
        return logger

    # --- ⚙️ REFINED AUTOMATION PATTERNS ---
    # --- MODIFICATION ---
    # New helper method to schedule random page changes.
    def _schedule_next_page_change(self):
        """Schedules the next random page change between 1 and 3 minutes from now."""
        stay_duration = timedelta(minutes=random.uniform(1, 3))
        self.next_page_change_time = datetime.now() + stay_duration
        self.logger.info(f"🕒 New page change scheduled for ~{self.next_page_change_time.strftime('%H:%M:%S')} ({stay_duration.total_seconds()/60:.1f} mins)")

    async def _handle_queue_if_present(self, page):
        """Checks for the queue page and waits if necessary."""
        try:
            # Check for a unique element on the queue page, like the H1 tag.
            # The timeout is short because the check should be fast.
            queue_header = await page.locator('h1:has-text("Receiving Exceptional Usage")').is_visible(timeout=2000)
            
            if queue_header:
                self.logger.warning("🐌 User is in the queue. Waiting for admission...")
                await self.take_screenshot(page, "in_queue")
                
                # Now, wait until the page reloads and the queue header is GONE.
                # This indicates we've been admitted to the main app.
                # We give it a long timeout because the queue wait could be long.
                await page.wait_for_selector('h1:has-text("Receiving Exceptional Usage")', state='hidden', timeout=300000) # 5-minute timeout
                
                await page.wait_for_load_state("networkidle", timeout=30000)
                self.logger.info("✅ User has been admitted from the queue!")
                await self.take_screenshot(page, "admitted_from_queue")
                return True # We were in the queue

        except PlaywrightTimeoutError:
            # This is the normal case: the queue header wasn't found, so we are not in the queue.
            pass
        except Exception as e:
            self.logger.error(f"❌ Error while handling queue: {e}")
            
        return False # We were not in the queue

    async def _try_click(self, page, selectors, description, timeout=10000):
        """🛡️ Resilient Selector Strategy: Tries a list of selectors to find and click an element."""
        for selector in selectors:
            try:
                element = await page.wait_for_selector(selector, state='visible', timeout=timeout/len(selectors))
                await element.click()
                self.logger.info(f"✅ Clicked '{description}' using selector: {selector}")
                return True
            except PlaywrightTimeoutError:
                self.logger.debug(f"Selector failed, trying next: {selector}")
        self.logger.warning(f"⚠️ Could not find element for '{description}' with any selector.")
        return False

    async def wait_for_graph_ready(self, page, graph_id, timeout=60000):
        """🛡️ Custom, Intelligent Wait for Dash/Plotly graphs to be fully rendered."""
        self.logger.info(f"🧠 Intelligently waiting for graph '{graph_id}' to render...")
        try:
            # This JS function checks if the pending class is gone from the graph's container
            await page.wait_for_function(f"""
                () => {{
                    const graph = document.getElementById('{graph_id}');
                    return graph && !graph.querySelector('.dash-graph--pending');
                }}
            """, timeout=timeout)
            self.logger.info(f"✅ Graph '{graph_id}' is ready.")
        except PlaywrightTimeoutError:
            self.logger.warning(f"⚠️ Timed out waiting for graph '{graph_id}' to finish rendering.")

    async def _perform_action(self, page, action_func, action_name, description):
        """
        ⚙️ Refined Action-Wait-Capture Loop with integrated resiliency patterns.
        This is the new core of all interactions.
        """
        self.logger.info(f"▶️ ATTEMPT: {description}")
        try:
            # 1. Perform Action
            await action_func()

            # 2. Intelligent Wait
            await page.wait_for_load_state("networkidle", timeout=30000)

            # 3. Capture State
            await self.take_screenshot(page, f"After {action_name}")
            
            self.logger.info(f"✅ SUCCESS: {description}")
            self.test_results['actions_succeeded'] += 1

            # 🛡️ Chaos Engineering: Random Refreshes
            if random.random() < REFRESH_CHANCE:
                self.logger.warning("🌪️ CHAOS: Performing random page refresh.")
                await page.reload(wait_until="networkidle")
                await self.take_screenshot(page, "After random refresh")

            # 4. Simulate "Think Time"
            await asyncio.sleep(random.uniform(1.0, 3.5))
            
            return True

        except Exception as e:
            self.logger.error(f"❌ FAILED on action '{action_name}': {e}", exc_info=False)
            await self.take_screenshot(page, f"FAIL_{action_name}")

            # 🛡️ "Soft Success" Logic
            if action_name in SOFT_SUCCESS:
                self.logger.warning(f"⚠️ Soft failure for '{action_name}'. Continuing test.")
                self.test_results['actions_soft_failed'] += 1
                return True # Treat as success for flow control
            else:
                self.test_results['actions_failed'] += 1
                # --- MODIFICATION ---
                # Never stop the journey. Always return True to continue.
                self.logger.warning(f"⚠️ Hard failure for '{action_name}'. Continuing test anyway.")
                return True # Hard failure, but we continue the journey

    async def take_screenshot(self, page, description):
        """Take a screenshot if screenshot flag is enabled."""
        if self.screenshot:
            self.screenshot_counter += 1
            # Sanitize filename
            safe_desc = "".join(c for c in description if c.isalnum() or c in " -_").rstrip()
            filename = f"{self.screenshot_counter:03d}_{safe_desc.lower().replace(' ', '_')}.png"
            filepath = os.path.join(self.screenshot_folder, filename)
            try:
                await page.screenshot(path=filepath)
                self.logger.info(f"📸 Screenshot {self.screenshot_counter:03d}: {description} -> {filepath}")
            except Exception as e:
                self.logger.error(f"📸 Failed to take screenshot {filepath}: {e}")

    # --- 🧠 REALISTIC USER BEHAVIOR ---

    def _get_next_page(self):
        """Weighted, Randomized Navigation: Chooses the next page based on weights."""
        pages, weights = zip(*PAGE_WEIGHTS.items())
        next_page = random.choices(pages, weights=weights, k=1)[0]
        self.logger.info(f"🧠 User decided to navigate. Next page: {next_page} (based on weights)")
        return next_page
    
    def _draw_linger(self):
        """'Stickiness' and Linger Time: Decides if the user stays on a page for longer."""
        prob = LONG_STAY_PROB.get(self.current_page_path, LONG_STAY_PROB['default'])
        should_linger = random.random() < prob
        if should_linger:
            self.logger.info(f"🧠 User decided to 'linger' on {self.current_page_path} (Prob: {prob:.2f})")
        return should_linger

    def _map_page_actions(self):
        """
        Maps page paths to their available actions, separating required from optional.
        This enables Coverage-Driven action selection.
        """
        return {
            '/lipizones-selection': {
                'required': {'lis_select_brain', 'lis_clear_and_select_treemap', 'lis_add_selection'},
                'optional': {'lis_move_slider', 'lis_toggle_annotations', 'lis_select_all', 'lis_open_tutorial'}
            },
            '/lipizones-vs-celltypes': {
                'required': {'lvc_select_lipizone', 'lvc_select_celltype'},
                'optional': {'lvc_move_slider', 'lvc_toggle_annotations', 'lvc_pixel_filter'}
            },
            '/lipids-vs-genes': {
                'required': {'lvg_select_lipid', 'lvg_select_gene'},
                'optional': {'lvg_move_slider', 'lvg_toggle_annotations', 'lvg_move_gene_slider'}
            },
            '/3D-exploration': {
                'required': {'3d_select_lipid', '3d_select_region', '3d_add_structure', '3d_display'},
                'optional': {}
            },
             '/lipid-selection': {
                'required': {'ls_select_brain', 'ls_select_lipid_from_dropdown'},
                'optional': {'ls_toggle_rgb', 'ls_toggle_annotations', 'ls_move_slider'}
            },
            '/peak-selection': {
                'required': {'ps_select_brain', 'ps_select_peak'},
                'optional': {'ps_toggle_rgb', 'ps_toggle_annotations', 'ps_move_slider', 'ps_show_spectrum'}
            },
            '/region-analysis': {
                'required': {'ra_select_regions', 'ra_assign_groups', 'ra_compute'},
                'optional': {'ra_toggle_annotations', 'ra_reset'}
            },
            '/lp-selection': {
                'required': {'lps_select_brain', 'lps_select_program'},
                'optional': {'lps_toggle_rgb', 'lps_toggle_annotations', 'lps_move_slider'}
            },
        }

    # --- INDIVIDUAL PAGE ACTIONS (Refactored from original test methods) ---

    async def _resilient_select_from_dropdown(self, page, trigger_locator, option_selector, description, is_multiselect=True):
        """
        🛡️ Handles dropdown selection with a retry-on-refresh mechanism.
        Clicks a trigger, waits for options, and selects one. If it times out,
        it refreshes the page and tries one more time.
        """
        for attempt in range(2): # Attempt up to two times
            try:
                await trigger_locator.click(timeout=15000)
                await page.wait_for_selector(option_selector, state='visible', timeout=15000)
                
                options = await page.locator(f'{option_selector}:not([data-selected="true"])').all()
                if options:
                    await random.choice(options).click()
                    self.logger.info(f"✅ Selected an option from '{description}' dropdown.")
                else:
                    self.logger.warning(f"⚠️ No unselected options found in '{description}' dropdown.")
                
                if is_multiselect:
                    await page.keyboard.press('Escape')
                return True # Success

            except PlaywrightTimeoutError:
                self.logger.warning(f"⚠️ Timed out on '{description}' dropdown on attempt {attempt + 1}.")
                if attempt == 0:
                    self.logger.info("🔄 Refreshing the page and retrying...")
                    await page.reload(wait_until="networkidle")
                else:
                    self.logger.error(f"❌ Dropdown '{description}' failed even after a refresh.")
                    return False # Persistent failure
        return False
    
    # Actions for /lipizones-selection
    async def _lis_select_brain(self, page):
        brain_options = ["Reference 1 (M)", "Control 1 (M)", "Control 2 (M)"]
        brain_label = random.choice(brain_options)
        selector = f'[id="main-brain"] .mantine-Chips-label:has-text("{brain_label}")'
        await page.click(selector)
        self.user_context['brain_selected'] = True
    
    async def _lis_clear_and_select_treemap(self, page):
        if not self.user_context.get('brain_selected'): return # Precondition
        await page.locator('[id="page-6-clear-selection-button"]').click()
        await self.wait_for_graph_ready(page, 'page-6-lipizones-treemap')
        await asyncio.sleep(2) # Wait for interactivity
        region_locator = page.locator('[id="page-6-lipizones-treemap"] g.trace path').nth(random.randint(1, 5))
        await region_locator.click(force=True)

    async def _lis_add_selection(self, page):
        await page.locator('[id="page-6-add-selection-button"]').click()
        self.user_context['lipizones_selected'] = True

    async def _lis_move_slider(self, page):
        slider = page.locator('[id="main-paper-slider"]')
        box = await slider.bounding_box()
        if box:
            pos = random.uniform(0.1, 0.9)
            await page.mouse.click(box['x'] + box['width'] * pos, box['y'] + box['height'] / 2)
    
    async def _lis_toggle_annotations(self, page):
        await page.locator('[id="page-6-toggle-annotations"]').click()
        
    async def _lis_select_all(self, page):
        await page.locator('[id="page-6-select-all-lipizones-button"]').click()
        
    async def _lis_open_tutorial(self, page):
        await self._try_click(page, ['[id="lipizone-start-tutorial-btn"]'], "Open Tutorial")
        await asyncio.sleep(1)
        await self._try_click(page, ['button:has-text("×")', '.shepherd-cancel-icon'], "Close Tutorial")

    # Actions for /lipizones-vs-celltypes
    async def _lvc_select_lipizone(self, page):
        await page.locator('[id="page-6bis-clear-lipizone-selection-button"]').click()
        await self.wait_for_graph_ready(page, 'page-6bis-lipizones-treemap')
        await page.locator('[id="page-6bis-lipizones-treemap"] g.trace path').nth(random.randint(1, 4)).click(force=True)
        await asyncio.sleep(1)
        await page.locator('[id="page-6bis-add-lipizone-selection-button"]').click()

    async def _lvc_select_celltype(self, page):
        await page.locator('[id="page-6bis-clear-celltype-selection-button"]').click()
        await self.wait_for_graph_ready(page, 'page-6bis-celltypes-treemap')
        await page.locator('[id="page-6bis-celltypes-treemap"] g.trace path').nth(random.randint(1, 4)).click(force=True)
        await asyncio.sleep(1)
        await page.locator('[id="page-6bis-add-celltype-selection-button"]').click()
        
    async def _lvc_move_slider(self, page):
        await self._lis_move_slider(page) # Re-use generic slider logic
    
    async def _lvc_toggle_annotations(self, page):
        await page.locator('[id="page-6bis-toggle-annotations"]').click()

    async def _lvc_pixel_filter(self, page):
        slider = page.locator('[id="page-6bis-celltype-pixel-filter"]')
        await slider.focus()
        for _ in range(random.randint(1,5)): await page.keyboard.press('ArrowRight')

    # ... other action methods refactored similarly ...
    async def _lvg_select_lipid(self, page):
        trigger = page.locator('[id="page-6tris-dropdown-lipids"]').locator('..')
        if not await self._resilient_select_from_dropdown(page, trigger, '.mantine-MultiSelect-item', "Lipid Selection"):
            raise PlaywrightTimeoutError("Lipid dropdown failed after retry.")

    async def _lvg_select_gene(self, page):
        for attempt in range(2):
            try:
                container = page.locator('[id="page-6tris-dropdown-genes"]').locator('..')
                gene = random.choice(["Gad1", "Gfap", "Aqp4", "Syt1", "Slc1a2"])
                await container.click(timeout=15000)
                await page.type('[id="page-6tris-dropdown-genes"]', gene, delay=50)
                await page.locator(f'.mantine-MultiSelect-item:has-text("{gene}")').first.click(timeout=10000)
                await page.keyboard.press('Escape')
                return # Success
            except PlaywrightTimeoutError:
                self.logger.warning(f"⚠️ Timed out on Gene dropdown on attempt {attempt + 1}.")
                if attempt == 0:
                    self.logger.info("🔄 Refreshing page to retry Gene selection...")
                    await page.reload(wait_until="networkidle")
                else:
                    raise PlaywrightTimeoutError("Gene selection failed after refresh.")


    async def _lvg_move_slider(self, page): await self._lis_move_slider(page)
    async def _lvg_toggle_annotations(self, page): await page.locator('[id="page-6tris-toggle-annotations"]').click()
    async def _lvg_move_gene_slider(self, page):
        sliders = await page.locator('[id^="page-6tris-gene-slider-"]').all()
        if sliders: await random.choice(sliders).focus(); await page.keyboard.press('ArrowRight')

    async def _3d_select_lipid(self, page):
        trigger = page.locator('[id="page-4-dropdown-lipids"]')
        if not await self._resilient_select_from_dropdown(page, trigger, '.mantine-Select-item', "3D Lipid Selection", is_multiselect=False):
            raise PlaywrightTimeoutError("3D Lipid dropdown failed after retry.")
            
    async def _3d_select_region(self, page):
        await self.wait_for_graph_ready(page, 'page-4-graph-region-selection')
        await page.locator('[id="page-4-graph-region-selection"] g.trace path').nth(random.randint(0, 3)).click(force=True)

    async def _3d_add_structure(self, page):
        await page.locator('[id="page-4-add-structure-button"]').click()
    
    async def _3d_display(self, page):
        await page.locator('[id="page-4-display-button"]').click()
        # --- MODIFICATION ---
        # Increased waiting time for 3D rendering.
        self.logger.info("⏳ Waiting an extra 45s for 3D model to render...")
        await asyncio.sleep(45)

    # Generic method for lipid/peak/program selection pages
    async def _generic_multiselect_and_brain(self, page, page_prefix, item_name):
        await self._lis_select_brain(page)
        trigger = page.locator(f'[id="{page_prefix}-dropdown-{item_name}s"]').locator('..')
        if not await self._resilient_select_from_dropdown(page, trigger, '.mantine-MultiSelect-item', f"{item_name} Selection"):
            raise PlaywrightTimeoutError(f"{item_name} dropdown failed after retry.")
    
    async def _ls_select_brain(self, page): await self._lis_select_brain(page)
    async def _ls_select_lipid_from_dropdown(self, page): await self._generic_multiselect_and_brain(page, 'page-2', 'lipid')
    async def _ls_toggle_rgb(self, page): await page.locator('[id="page-2-rgb-switch"]').click()
    async def _ls_toggle_annotations(self, page): await page.locator('[id="page-2-toggle-annotations"]').click()
    async def _ls_move_slider(self, page): await self._lis_move_slider(page)
    
    async def _ps_select_brain(self, page): await self._lis_select_brain(page)
    async def _ps_select_peak(self, page):
        # --- MODIFICATION ---
        # Commented out the dropdown click for peak selection as requested.
        self.logger.warning("🚫 SKIPPING peak selection dropdown click as requested.")
        # await self._generic_multiselect_and_brain(page, 'page-2tris', 'peak')
        await asyncio.sleep(1) # Add a small sleep to simulate the action's time.

    async def _ps_toggle_rgb(self, page): await page.locator('[id="page-2tris-rgb-switch"]').click()
    async def _ps_toggle_annotations(self, page): await page.locator('[id="page-2tris-toggle-annotations"]').click()
    async def _ps_move_slider(self, page): await self._lis_move_slider(page)
    async def _ps_show_spectrum(self, page):
        await page.locator('[id="page-2tris-show-spectrum-button"]').click()
        await asyncio.sleep(1)
        await page.locator('[id="page-2tris-close-spectrum-button"]').click()

    async def _lps_select_brain(self, page): await self._lis_select_brain(page)
    async def _lps_select_program(self, page): await self._generic_multiselect_and_brain(page, 'page-2bis', 'program')
    async def _lps_toggle_rgb(self, page): await page.locator('[id="page-2bis-rgb-switch"]').click()
    async def _lps_toggle_annotations(self, page): await page.locator('[id="page-2bis-toggle-annotations"]').click()
    async def _lps_move_slider(self, page): await self._lis_move_slider(page)

    async def _ra_select_regions(self, page):
        for _ in range(2): # Loop to select two regions
            for attempt in range(2):
                try:
                    container = page.locator('[id="page-3-dropdown-brain-regions"]').locator('..')
                    await container.click(timeout=15000)
                    await page.wait_for_selector('.mantine-MultiSelect-item', state='visible', timeout=10000)
                    options = await page.locator('.mantine-MultiSelect-item:not([data-selected="true"])').all()
                    if options:
                        self.logger.warning("🚫 SKIPPING region selection dropdown click as requested.")
                        # --- MODIFICATION ---
                        # Commented out the click as requested.
                        # await random.choice(options).click()
                        await asyncio.sleep(0.5)
                        break # Success for this selection, continue to next region
                    else:
                        await page.keyboard.press('Escape')
                        return # No more options, exit function
                except PlaywrightTimeoutError:
                    self.logger.warning(f"⚠️ Region selection dropdown failed on attempt {attempt + 1}.")
                    if attempt == 0:
                        self.logger.info("🔄 Refreshing page to retry region selection...")
                        await page.reload(wait_until="networkidle")
                    else:
                        raise PlaywrightTimeoutError("Region selection failed after refresh.")
    
    async def _ra_assign_groups(self, page):
        selected = await page.locator('[id="page-3-dropdown-brain-regions"] .mantine-MultiSelect-value span').all_text_contents()
        if len(selected) >= 2:
            await page.click('[id="page-3-group-a-selector"]'); await page.locator(f'text="{selected[0]}"').first.click()
            await page.click('[id="page-3-group-b-selector"]'); await page.locator(f'text="{selected[1]}"').first.click()

    async def _ra_compute(self, page): await page.locator('[id="page-3-button-compute-volcano"]').click()
    async def _ra_toggle_annotations(self, page): await page.locator('[id="page-3-toggle-annotations"]').click()
    async def _ra_reset(self, page): await page.locator('[id="page-3-reset-button"]').click()

    async def run_complete_test_suite(self):
        """
        Run the complete test suite as a stateful, dynamic user journey.
        """
        self.logger.info(f"🚀 STARTING REALISTIC USER SIMULATION (Scheduled End: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')})")
        self.logger.info("=" * 60)
        
        context = await self.browser.new_context()
        page = await context.new_page()
        try:
            # Initial navigation
            await page.goto("http://127.0.0.1:8081/", timeout=60000)
            self.monitor.log_stats(self.logger, "Initial Page Load")

            await self._handle_queue_if_present(page)

            # Main simulation loop
            while datetime.now() < self.end_time:
                # --- MODIFICATION ---
                # Check if it's time to force a page change.
                if datetime.now() >= self.next_page_change_time:
                    self.logger.info("⏰ Time limit reached for this page. Forcing navigation.")
                    next_page_path = self._get_next_page()
                
                self.logger.info(f"----- Current Page: {self.current_page_path} -----")
                self.test_results['pages_visited'].add(self.current_page_path)
                
                page_config = self.page_actions_map.get(self.current_page_path)
                if not page_config:
                    self.logger.info("On a non-testable page (e.g., homepage), navigating to a new one.")
                    next_page_path = self._get_next_page()
                # Only execute action logic if we are not already forcing a navigation
                elif 'next_page_path' not in locals():
                    # Coverage-Driven Actions
                    if not self.required_actions:
                        self.required_actions = page_config['required'].copy()
                    
                    action_name = None
                    if self.required_actions:
                        action_name = self.required_actions.pop()
                        self.logger.info(f"🎯 Performing REQUIRED action: {action_name}")
                    elif self._draw_linger() and page_config['optional']:
                        action_name = random.choice(list(page_config['optional']))
                        self.logger.info(f"- LINGERING with optional action: {action_name}")
                    
                    if action_name:
                        # Dynamically get the action method and execute it
                        action_method = getattr(self, f"_{action_name}", None)
                        # --- MODIFICATION ---
                        # Uncommented the action execution block and removed the hard-fail 'break'.
                        if action_method:
                            success = await self._perform_action(page, lambda: action_method(page), action_name, f"({self.current_page_path}) {action_name}")
                            # The journey no longer stops on hard failure.
                        else:
                           self.logger.error(f"Action method '_{action_name}' not implemented!")
                    else:
                        # No more actions to do, navigate away
                        next_page_path = self._get_next_page()
                        
                # If navigation is decided
                if 'next_page_path' in locals() and next_page_path != self.current_page_path:
                    self.logger.info(f"➡️ Navigating from {self.current_page_path} to {next_page_path}")
                    await page.goto(f"http://127.0.0.1:8081{next_page_path}", wait_until="networkidle", timeout=60000)
                    self.current_page_path = next_page_path
                    self.required_actions.clear() # Reset required actions for the new page
                    # --- MODIFICATION ---
                    # Reset the page change timer after navigating.
                    self._schedule_next_page_change()
                    del next_page_path


        except Exception as e:
            self.logger.error(f"❌ CRITICAL ERROR in test suite: {e}", exc_info=True)
            await self.take_screenshot(page, "critical_error")
        
        finally:
            await self.generate_final_summary()
            await context.close()
            
        self.logger.info("🏁 USER SIMULATION COMPLETED")
        self.logger.info("=" * 60)

    async def generate_final_summary(self):
        """Generate final summary of the user journey."""
        self.logger.info("\n🏁 FINAL JOURNEY SUMMARY")
        self.logger.info("=" * 60)
        
        self.monitor.log_stats(self.logger, "FINAL SUMMARY")
        
        self.logger.info("📊 JOURNEY STATS:")
        self.logger.info(f"  - ✅ Actions Succeeded: {self.test_results['actions_succeeded']}")
        self.logger.info(f"  - ⚠️ Actions Soft-Failed: {self.test_results['actions_soft_failed']}")
        self.logger.info(f"  - ❌ Actions Hard-Failed: {self.test_results['actions_failed']}")
        
        visited_list = sorted(list(self.test_results['pages_visited']))
        self.logger.info(f"  - 🗺️ Pages Visited ({len(visited_list)}): {', '.join(visited_list)}")
        
        if self.test_results['actions_failed'] == 0:
            self.logger.info("\n🎉 JOURNEY COMPLETED SUCCESSFULLY! The user navigated the app without critical errors.")
        else:
            self.logger.warning(f"\n⚠️ JOURNEY COMPLETED WITH {self.test_results['actions_failed']} hard failure(s) logged.")


# --- PARALLEL EXECUTION FRAMEWORK (with staggered start) ---

async def worker(user_id: int, browser, screenshots_enabled: bool, duration: int): # Add "browser"
    """A wrapper function to run a single test suite instance for one user."""
    print(f"--- User {user_id}: Test instance created. Will start after its ramp-up delay. ---")
    try:
        # Pass the shared browser object directly to the test suite
        test_suite = UnifiedStabilityTestSuite(user_id=user_id, browser_instance=browser, screenshot=screenshots_enabled, duration_minutes=duration)
        await test_suite.run_complete_test_suite()
        print(f"--- ✅ User {user_id}: Simulation finished. ---")
    except Exception:
        # This will now catch errors inside the test, not the launch failure
        print(f"--- ❌ CRITICAL FAILURE for User {user_id}. Check logs/user_{user_id}_*.log for details. ---")


async def main():
    """Main entry point to configure and run parallel tests."""
    parser = argparse.ArgumentParser(
        description="Run parallel, realistic stability tests for a web application.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-n", "--num-users", type=int, default=1,
        help="The number of concurrent users to simulate."
    )
    parser.add_argument(
        "-d", "--duration", type=int, default=5,
        help="The duration in minutes for each user's test journey.\n(NOTE: This is now overridden by a random 1-10 min duration per user)."
    )
    parser.add_argument(
        "-s", "--screenshots", action="store_true",
        help="Enable saving screenshots for each user. Saved to 'screenshots/user_N/'."
    )
    # 🛡️ Chaos Engineering Principle: Staggered Starts
    parser.add_argument(
        "--ramp-up-seconds", type=int, default=10,
        help="Total time in seconds over which to start all users."
    )
    args = parser.parse_args()

    print("==================================================")
    print(f"  Preparing to simulate {args.num_users} concurrent user(s).")
    print(f"  Test duration per user: RANDOM (1-10 minutes).")
    print(f"  Total ramp-up time: {args.ramp_up_seconds} second(s).")
    print(f"  Screenshots enabled: {args.screenshots}")
    print("==================================================")
    
    # Launch ONE Playwright instance and ONE browser for everyone
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        tasks = []
        delay_per_user = args.ramp_up_seconds / args.num_users if args.num_users > 1 else 0
        
        for user_id in range(1, args.num_users + 1):
            # Pass the SAME browser instance to each worker
            task = asyncio.create_task(worker(user_id, browser, args.screenshots, args.duration))
            tasks.append(task)
            if user_id < args.num_users:
                print(f"--- Main: Waiting {delay_per_user:.2f}s before starting next user... ---")
                await asyncio.sleep(delay_per_user)
        
        await asyncio.gather(*tasks)
        
        await browser.close() # Close the single browser at the very end

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user. Exiting.")