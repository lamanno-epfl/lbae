#!/usr/bin/env python3
"""
FINAL MULTI-USER RANDOMIZED STABILITY & CHAOS TEST SUITE (v2 - Treemap Fix)
=========================================================================

This is the complete, runnable script for simulating N concurrent users.

NEW IN THIS VERSION:
- **CRITICAL FIX**: Re-engineered all treemap interactions to be more robust.
  The script now clicks a random coordinate within the treemap's visible
  area, preventing the 'Element is outside of the viewport' error. This
  restores the stability of the original fine-tuned logic.
- Self-Contained: All class and method definitions are included.
- 8-Second Wait: Added an 8-second delay after navigating to specific pages.
- 1.5-Second Wait: A 1.5-second delay is added before every screenshot.
- Screenshot Logging Fix: Screenshot confirmation messages are now visible.
"""
import asyncio
import logging
import time
import psutil
import os
import random
import argparse
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# --- Argument Parser for Enhanced Configuration ---
parser = argparse.ArgumentParser(description="Run the Final Multi-User Randomized Stability Test Suite.")
parser.add_argument('--num-users', type=int, default=2, help="Number of concurrent users to simulate.")
parser.add_argument('--duration', type=int, default=10, help="Test duration in minutes.")
parser.add_argument('--seed', type=int, default=None, help="Base random seed for reproducibility.")
parser.add_argument('--quiet', action='store_true', help="Log to file only, not to the terminal.")
parser.add_argument('--no-screenshots', action='store_true', help="Disable taking screenshots.")
args = parser.parse_args()

# --- Global Configuration ---
SEED = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
BASE_URL = "http://127.0.0.1:8050"
REFRESH_CHANCE = 0.03

# --- Logging Configuration ---
log_filename = f'final_multi_user_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}_seed_{SEED}.log'
log_handlers = [logging.FileHandler(log_filename)]
if not args.quiet:
    log_handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# --- Test Classes (Reporter & TestSuite) ---
class TestReporter:
    """Accumulates test results for a single user session."""
    def __init__(self, user_id):
        self.user_id = user_id
        self.actions_attempted = 0
        self.actions_succeeded = 0
        self.failures = []

    def record_action_success(self):
        self.actions_succeeded += 1
        self.actions_attempted += 1

    def record_action_failure(self, page_path, action_name, error):
        self.actions_attempted += 1
        self.failures.append({
            'user_id': self.user_id,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'page': page_path,
            'action': action_name,
            'error': str(error)
        })

class RandomizedStabilityTestSuite:
    """Manages the test logic for a single user."""
    def __init__(self, user_id, seed, reporter, screenshot=True):
        self.user_id = user_id
        self.rng = random.Random(seed)
        self.reporter = reporter
        self.screenshot = screenshot
        self.screenshot_counter = 0
        self.screenshot_folder = f"test_screenshots_seed_{SEED}/user_{self.user_id}"
        self.page_states = {}
        self.page_actions = self._define_page_actions()
        self.testable_pages = list(self.page_actions.keys())

        if self.screenshot:
            os.makedirs(self.screenshot_folder, exist_ok=True)

    async def take_screenshot(self, page, description):
        if not self.screenshot or not page: return
        # Per your request, wait 1.5 seconds before every screenshot
        await asyncio.sleep(1.5)
        self.screenshot_counter += 1
        safe_desc = "".join(c for c in description.lower().replace(' ', '_') if c.isalnum() or c in ('_', '-'))
        filename = f"{self.screenshot_counter:04d}_{safe_desc}.png"
        filepath = os.path.join(self.screenshot_folder, filename)
        try:
            await page.screenshot(path=filepath)
            # FIXED: Changed to INFO level for visibility in standard logs.
            logger.info(f"📸 [User {self.user_id}] Screenshot: {description} -> {filepath}")
        except Exception as e:
            logger.error(f"❌ [User {self.user_id}] Failed to take screenshot '{description}': {e}")
            
    async def run_for_duration(self, page, minutes):
        start_time = time.time()
        end_time = start_time + minutes * 60
        current_page_path = self.rng.choice(self.testable_pages)
        while time.time() < end_time:
            await self._perform_one_action_cycle(page, current_page_path)
            if self.rng.random() < 0.25:
                current_page_path = self.rng.choice(self.testable_pages)

    async def _perform_one_action_cycle(self, page, page_path):
        current_url = page.url
        target_url = f"{BASE_URL}{page_path}"
        if page_path not in current_url:
            logger.info(f"🔀 [User {self.user_id}] NAVIGATING to {target_url}")
            try:
                await page.goto(target_url, timeout=90000, wait_until="networkidle")
                # Per your request, add specific wait times on landing
                if page_path in ['/lipizones-selection', '/lipizones-vs-celltypes']:
                    logger.info(f"[User {self.user_id}] Performing special 8-second wait for {page_path}.")
                    await asyncio.sleep(8)
                else:
                    await asyncio.sleep(2) # Standard grace period
                self.page_states[page_path] = {}
            except Exception as e:
                logger.error(f"❌ [User {self.user_id}] FAILED to load {target_url}: {e}")
                self.reporter.record_action_failure(page_path, "Page Navigation", e)
                return

        current_state = self.page_states.setdefault(page_path, {})
        valid_actions = [a for a in self.page_actions.get(page_path, []) if a['pre'](current_state)]
        action_name, action_to_perform, post_condition = "N/A", None, lambda s: None

        if self.rng.random() < REFRESH_CHANCE:
            action_name = "CHAOS: Page Refresh"
            async def refresh_action(p):
                await p.reload(wait_until="networkidle"); self.page_states[page_path] = {}
            action_to_perform = refresh_action
        elif not valid_actions:
            action_name = "RECOVERY: Page Reload"
            logger.warning(f"[User {self.user_id}] No valid actions on {page_path} in state {current_state}, reloading.")
            async def reload_action(p):
                await p.reload(wait_until="networkidle"); self.page_states[page_path] = {}
            action_to_perform = reload_action
        else:
            chosen_action_def = self.rng.choice(valid_actions)
            action_name = chosen_action_def['name']
            action_to_perform = chosen_action_def['func']
            post_condition = chosen_action_def['post']

        logger.info(f"▶️ [User {self.user_id}] Action: '{action_name}' on {page_path}")
        try:
            await action_to_perform(page)
            post_condition(current_state)
            self.reporter.record_action_success()
            await self.take_screenshot(page, action_name)
            await asyncio.sleep(self.rng.uniform(1, 2))
        except Exception as e:
            logger.error(f"❌ [User {self.user_id}] FAILED action '{action_name}': {e}", exc_info=False)
            self.reporter.record_action_failure(page_path, action_name, e)
            await self.take_screenshot(page, f"failed_{action_name}")
            self.page_states[page_path] = {}

    def _define_page_actions(self):
        """Defines all possible actions for every page."""
        return {
            '/lipizones-selection': [
                {'name': 'LS Select Brain', 'func': self._action_select_brain, 'pre': lambda s: True, 'post': lambda s: s.update({'brain_selected': True})},
                {'name': 'LS Move Section Slider', 'func': self._action_move_slider, 'pre': lambda s: s.get('brain_selected', False), 'post': lambda s: None},
                {'name': 'LS Toggle Allen', 'func': self._action_toggle_annotations('page-6-toggle-annotations'), 'pre': lambda s: s.get('brain_selected', False), 'post': lambda s: None},
                {'name': 'LS Click Treemap', 'func': self._action_click_treemap('page-6-lipizones-treemap'), 'pre': lambda s: s.get('selection_cleared', False), 'post': lambda s: s.update({'treemap_clicked': True, 'selection_added': False})},
                {'name': 'LS Add Treemap Selection', 'func': self._action_click_button('page-6-add-selection-button'), 'pre': lambda s: s.get('treemap_clicked', False) and not s.get('selection_added', False), 'post': lambda s: s.update({'selection_added': True, 'num_selected': s.get('num_selected', 0) + 1})},
                {'name': 'LS Clear Selection', 'func': self._action_clear_treemap_selection('page-6-clear-selection-button'), 'pre': lambda s: True, 'post': lambda s: s.update({'selection_cleared': True, 'treemap_clicked': False, 'selection_added': False, 'num_selected': 0})},
                {'name': 'LS Select All Lipizones', 'func': self._action_click_button('page-6-select-all-lipizones-button'), 'pre': lambda s: True, 'post': lambda s: s.update({'selection_added': True, 'num_selected': 999})},
                {'name': 'LS View/Hide ID Cards', 'func': self._action_ls_id_cards, 'pre': lambda s: s.get('selection_added', False) and s.get('num_selected', 0) < 10, 'post': lambda s: None},
            ],
            '/lipizones-vs-celltypes': [
                {'name': 'LVC Move Section Slider', 'func': self._action_move_slider, 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'LVC Toggle Allen', 'func': self._action_toggle_annotations('page-6bis-toggle-annotations'), 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'LVC Select Lipizones from Treemap', 'func': self._action_lvc_select_from_treemap('lipizones'), 'pre': lambda s: True, 'post': lambda s: s.update({'lipizones_selected': True})},
                {'name': 'LVC Select Celltypes from Treemap', 'func': self._action_lvc_select_from_treemap('celltypes'), 'pre': lambda s: True, 'post': lambda s: s.update({'celltypes_selected': True})},
            ],
            '/lipids-vs-genes': [
                {'name': 'LG Select Lipids', 'func': self._action_lg_select_lipids, 'pre': lambda s: True, 'post': lambda s: s.update({'lipids_selected': True})},
                {'name': 'LG Select Genes', 'func': self._action_lg_select_genes, 'pre': lambda s: True, 'post': lambda s: s.update({'genes_selected': True})},
                {'name': 'LG Move Section Slider', 'func': self._action_move_slider, 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'LG Toggle Allen', 'func': self._action_toggle_annotations('page-6tris-toggle-annotations'), 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'LG Move Gene Sliders', 'func': self._action_lg_move_gene_sliders, 'pre': lambda s: s.get('genes_selected', False), 'post': lambda s: None},
            ],
            '/3D-exploration': [
                {'name': '3D Select Lipid', 'func': self._action_3d_select_lipid, 'pre': lambda s: True, 'post': lambda s: s.update({'lipid_selected': True})},
                {'name': '3D Click Treemap Region', 'func': self._action_3d_click_treemap, 'pre': lambda s: True, 'post': lambda s: s.update({'region_selected': True})},
                {'name': '3D Add Structure', 'func': self._action_click_button('page-4-add-structure-button'), 'pre': lambda s: s.get('region_selected', False), 'post': lambda s: s.update({'regions_added': s.get('regions_added', 0) + 1, 'region_selected': False})},
                {'name': '3D Display Button', 'func': self._action_click_button('page-4-display-button'), 'pre': lambda s: s.get('lipid_selected', False) and s.get('regions_added', 0) > 0, 'post': lambda s: s.update({'display_clicked': True})},
            ],
             '/lipid-selection': [
                {'name': 'LiS Select from Heatmap', 'func': self._action_click_heatmap('page-2-graph-heatmap-mz-selection'), 'pre': lambda s: True, 'post': lambda s: s.update({'lipids_selected': True})},
                {'name': 'LiS Select from Dropdown', 'func': self._action_select_from_multiselect('page-2-dropdown-lipids'), 'pre': lambda s: True, 'post': lambda s: s.update({'lipids_selected': True})},
                {'name': 'LiS Select Brain', 'func': self._action_select_brain, 'pre': lambda s: True, 'post': lambda s: s.update({'brain_selected': True})},
                {'name': 'LiS Toggle RGB', 'func': self._action_click_button('page-2-rgb-switch'), 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'LiS Toggle Allen', 'func': self._action_toggle_annotations('page-2-toggle-annotations'), 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'LiS Move Slider', 'func': self._action_move_slider, 'pre': lambda s: True, 'post': lambda s: None},
            ],
            '/peak-selection': [
                {'name': 'PS Select from Dropdown', 'func': self._action_select_from_multiselect('page-2tris-dropdown-peaks'), 'pre': lambda s: True, 'post': lambda s: s.update({'peaks_selected': True})},
                {'name': 'PS Select Brain', 'func': self._action_select_brain, 'pre': lambda s: True, 'post': lambda s: s.update({'brain_selected': True})},
                {'name': 'PS Toggle RGB', 'func': self._action_click_button('page-2tris-rgb-switch'), 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'PS Toggle Allen', 'func': self._action_toggle_annotations('page-2tris-toggle-annotations'), 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'PS Move Slider', 'func': self._action_move_slider, 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'PS Show/Hide Spectrum', 'func': self._action_ps_show_hide_spectrum, 'pre': lambda s: s.get('peaks_selected', False), 'post': lambda s: None},
            ],
            '/region-analysis': [
                {'name': 'RA Select Regions', 'func': self._action_ra_select_regions, 'pre': lambda s: True, 'post': lambda s: s.update({'regions_selected_count': s.get('regions_selected_count', 0) + self.rng.randint(1, 3)})},
                {'name': 'RA Assign to Group A', 'func': self._action_ra_assign_group('page-3-group-a-selector'), 'pre': lambda s: s.get('regions_selected_count', 0) > 0, 'post': lambda s: s.update({'group_a_assigned': True})},
                {'name': 'RA Assign to Group B', 'func': self._action_ra_assign_group('page-3-group-b-selector'), 'pre': lambda s: s.get('regions_selected_count', 0) > 1, 'post': lambda s: s.update({'group_b_assigned': True})},
                {'name': 'RA Compute Volcano', 'func': self._action_click_button('page-3-button-compute-volcano'), 'pre': lambda s: s.get('group_a_assigned', False) and s.get('group_b_assigned', False), 'post': lambda s: s.update({'compute_done': True})},
                {'name': 'RA Reset Regions', 'func': self._action_ra_reset, 'pre': lambda s: True, 'post': lambda s: s.clear()},
                {'name': 'RA Toggle Allen', 'func': self._action_toggle_annotations('page-3-toggle-annotations'), 'pre': lambda s: True, 'post': lambda s: None},
            ],
            '/lp-selection': [
                {'name': 'LP Select from Heatmap', 'func': self._action_click_heatmap('page-2bis-graph-heatmap-mz-selection'), 'pre': lambda s: True, 'post': lambda s: s.update({'programs_selected': True})},
                {'name': 'LP Select from Dropdown', 'func': self._action_select_from_multiselect('page-2bis-dropdown-programs'), 'pre': lambda s: True, 'post': lambda s: s.update({'programs_selected': True})},
                {'name': 'LP Select Brain', 'func': self._action_select_brain, 'pre': lambda s: True, 'post': lambda s: s.update({'brain_selected': True})},
                {'name': 'LP Toggle RGB', 'func': self._action_click_button('page-2bis-rgb-switch'), 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'LP Toggle Allen', 'func': self._action_toggle_annotations('page-2bis-toggle-annotations'), 'pre': lambda s: True, 'post': lambda s: None},
                {'name': 'LP Move Slider', 'func': self._action_move_slider, 'pre': lambda s: True, 'post': lambda s: None},
            ],
        }

    # --- ACTION IMPLEMENTATIONS (ALL METHODS) ---
    async def _action_select_brain(self, page):
        options = ["Reference 1 (M)", "Control 1 (M)", "Control 2 (M)"]
        label = self.rng.choice(options)
        selector = f'[id="main-brain"] .mantine-Chips-label:has-text("{label}")'
        await page.locator(selector).click(timeout=15000)
    
    async def _action_move_slider(self, page):
        slider = page.locator('[id="main-paper-slider"]')
        if not await slider.is_visible(timeout=5000): return
        box = await slider.bounding_box()
        if not box: raise Exception("Slider not visible")
        pos = self.rng.uniform(0.1, 0.9)
        await page.mouse.click(box['x'] + box['width'] * pos, box['y'] + box['height'] / 2)
    
    def _action_toggle_annotations(self, selector_id: str):
        async def action(page): await page.locator(f'[id="{selector_id}"]').click(timeout=10000)
        return action

    def _action_click_button(self, selector_id: str):
        async def action(page): await page.locator(f'[id="{selector_id}"]').click(timeout=10000)
        return action
        
    def _action_click_heatmap(self, selector_id: str):
        async def action(page):
            heatmap = page.locator(f'[id="{selector_id}"]')
            await heatmap.wait_for(state="visible", timeout=10000)
            box = await heatmap.bounding_box()
            if not box: raise Exception("Heatmap not visible")
            x_pos, y_pos = box['x'] + self.rng.uniform(0.1, 0.9) * box['width'], box['y'] + self.rng.uniform(0.1, 0.9) * box['height']
            await page.mouse.click(x_pos, y_pos)
        return action

    def _action_select_from_multiselect(self, selector_id: str):
        async def action(page):
            container = page.locator(f'[id="{selector_id}"]').locator('..')
            await container.click()
            await page.wait_for_selector('.mantine-MultiSelect-item', state='visible', timeout=10000)
            options = await page.locator('.mantine-MultiSelect-item:not([data-selected="true"])').all()
            if not options: await page.keyboard.press("Escape"); return
            num_to_select = self.rng.randint(1, min(3, len(options)))
            for option in self.rng.sample(options, num_to_select):
                await option.click(); await asyncio.sleep(0.5)
            await page.keyboard.press("Escape")
        return action

    def _action_click_treemap(self, selector_id: str):
        """FIXED: Clicks a random point inside the treemap's bounding box."""
        async def action(page):
            treemap = page.locator(f'[id="{selector_id}"]')
            await treemap.scroll_into_view_if_needed()
            box = await treemap.bounding_box()
            if not box: raise Exception("Treemap element not visible or has no dimensions.")
            rand_x = box['x'] + self.rng.uniform(0.1, 0.9) * box['width']
            rand_y = box['y'] + self.rng.uniform(0.1, 0.9) * box['height']
            await page.mouse.click(rand_x, rand_y)
        return action

    def _action_clear_treemap_selection(self, selector_id: str):
        async def action(page):
            await page.locator(f'[id="{selector_id}"]').click(timeout=10000)
            # This action is specific to the /lipizones-selection page state
            if '/lipizones-selection' in page.url:
                self.page_states['/lipizones-selection'] = {'selection_cleared': True}
        return action
        
    async def _action_ls_id_cards(self, page):
        if await page.locator('[id="hide-id-cards-btn"]').is_visible(timeout=2000):
            await page.locator('[id="hide-id-cards-btn"]').click()
        elif await page.locator('[id="view-id-cards-btn"]').is_enabled():
            await page.locator('[id="view-id-cards-btn"]').click()
            await asyncio.sleep(3)
    
    def _action_lvc_select_from_treemap(self, map_type: str):
        """FIXED: Uses the robust bounding box click for LVC treemaps."""
        async def action(page):
            # Your fine-tuned logic: ALWAYS clear before interacting.
            await page.locator(f'[id="page-6bis-clear-{map_type[:-1]}-selection-button"]').click()
            await asyncio.sleep(1.5)
            
            # Use the robust clicking method
            treemap_id = f'page-6bis-{map_type}-treemap'
            await self._action_click_treemap(treemap_id)(page)
            await asyncio.sleep(1.5)
            
            # Add the selection
            await page.locator(f'[id="page-6bis-add-{map_type[:-1]}-selection-button"]').click()
        return action
    
    async def _action_lg_select_lipids(self, page):
        await self._action_select_from_multiselect('page-6tris-dropdown-lipids')(page)

    async def _action_lg_select_genes(self, page):
        known_genes = ["Gad1", "Gfap", "Slc17a7", "Aqp4", "Mbp"]
        gene = self.rng.choice(known_genes)
        container = page.locator('[id="page-6tris-dropdown-genes"]').locator('..')
        await container.click(); await container.type(gene, delay=50); await asyncio.sleep(1)
        option = page.locator(f'.mantine-MultiSelect-item:has-text("{gene}")').first
        if await option.is_visible(): await option.click()
        else: await page.keyboard.press("Escape")

    async def _action_lg_move_gene_sliders(self, page):
        sliders = await page.locator('[id^="page-6tris-gene-slider-"]').all()
        if not sliders: return
        slider = self.rng.choice(sliders)
        await slider.focus()
        for _ in range(self.rng.randint(1, 5)):
            await page.keyboard.press(self.rng.choice(['ArrowRight', 'ArrowLeft']))
            
    async def _action_3d_select_lipid(self, page):
        container = page.locator('[id="page-4-dropdown-lipids"]')
        await container.click()
        await page.wait_for_selector('.mantine-Select-item', state='visible', timeout=10000)
        options = await page.locator('.mantine-Select-item').all()
        if not options: await page.keyboard.press("Escape"); return
        await self.rng.choice(options).click()

    async def _action_3d_click_treemap(self, page):
        # This page uses a specific JS-based click from your original script, which is preserved.
        js_result = await page.evaluate("""
            () => {
                const trace = document.querySelector('[id="page-4-graph-region-selection"] .trace path');
                if (!trace) return 'Trace not found';
                trace.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                return 'Click dispatched';
            }
        """)
        if 'dispatched' not in js_result: raise Exception("JS Click on 3D treemap failed.")
        await asyncio.sleep(1)

    async def _action_ps_show_hide_spectrum(self, page):
        if await page.locator('[id="page-2tris-close-spectrum-button"]').is_visible(timeout=2000):
            await page.locator('[id="page-2tris-close-spectrum-button"]').click()
        else:
            await page.locator('[id="page-2tris-show-spectrum-button"]').click()

    async def _action_ra_select_regions(self, page):
        await self._action_select_from_multiselect('page-3-dropdown-brain-regions')(page)
    
    def _action_ra_assign_group(self, selector_id: str):
        async def action(page):
            await page.locator(f'[id="{selector_id}"]').click()
            await page.wait_for_selector('[role="option"]', state='visible', timeout=10000)
            options = await page.locator('[role="option"]:not([disabled])').all()
            if not options: await page.keyboard.press("Escape"); return
            await self.rng.choice(options).click()
        return action
        
    async def _action_ra_reset(self, page):
        await page.locator('[id="page-3-reset-button"]').click()
        self.page_states['/region-analysis'] = {}

# --- Simulation Orchestrator ---
async def run_user_session(browser, user_id, seed, duration_minutes, screenshot_enabled):
    """Runs a complete test session for a single user."""
    logger.info(f"🚀 Starting session for User {user_id} with seed {seed}...")
    context = await browser.new_context()
    page = await context.new_page()
    reporter = TestReporter(user_id=user_id)
    test_suite = RandomizedStabilityTestSuite(user_id, seed, reporter, screenshot_enabled)
    try:
        await test_suite.run_for_duration(page, duration_minutes)
    except Exception as e:
        logger.critical(f"💥 [User {user_id}] Unrecoverable error in session: {e}", exc_info=True)
    finally:
        logger.info(f"🏁 Session finished for User {user_id}.")
        await context.close()
        return reporter

async def run_simulation(num_users, duration_minutes, base_seed, screenshot_enabled):
    """Orchestrates the multi-user simulation."""
    start_time = time.time()
    system_stats = []

    async def monitor_system():
        while time.time() - start_time < duration_minutes * 60 + 5:
            system_stats.append({'cpu_percent': psutil.cpu_percent(),'ram_percent': psutil.virtual_memory().percent})
            await asyncio.sleep(30)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        monitor_task = asyncio.create_task(monitor_system())
        user_tasks = [run_user_session(browser, i + 1, base_seed + i, duration_minutes, screenshot_enabled) for i in range(num_users)]
        results = await asyncio.gather(*user_tasks)
        monitor_task.cancel()
        await browser.close()

    # --- Generate Aggregated Report ---
    total_actions, total_successes = sum(r.actions_attempted for r in results), sum(r.actions_succeeded for r in results)
    all_failures = [f for r in results for f in r.failures]
    success_rate = (total_successes / total_actions * 100) if total_actions > 0 else 100

    logger.info("\n" + "="*70 + "\n📊 AGGREGATED MULTI-USER TEST REPORT\n" + "="*70)
    logger.info(f"Simulation complete. {num_users} users ran for {duration_minutes} minutes with base seed {base_seed}.")
    logger.info(f"--- 📈 Overall Action Summary ---\nTotal Actions: {total_actions}, Succeeded: {total_successes}, Failed: {len(all_failures)}, Success Rate: {success_rate:.2f}%")
    if all_failures:
        logger.info("\n--- ❌ Detailed Failure Log ---")
        for i, f in enumerate(all_failures, 1):
            logger.error(f"{i}. User: {f['user_id']}, Time: {f['timestamp']}, Page: {f['page']}, Action: {f['action']}\n   Error: {f['error']}")
    else:
        logger.info("\n--- 🎉 NO FAILURES DETECTED ACROSS ALL USERS ---")
    if system_stats:
        logger.info("\n--- 🖥️ System Resource Usage During Test ---")
        avg_cpu, max_cpu = sum(s['cpu_percent'] for s in system_stats) / len(system_stats), max(s['cpu_percent'] for s in system_stats)
        avg_ram, max_ram = sum(s['ram_percent'] for s in system_stats) / len(system_stats), max(s['ram_percent'] for s in system_stats)
        logger.info(f"Average CPU: {avg_cpu:.2f}% | Peak CPU: {max_cpu:.2f}%")
        logger.info(f"Average RAM: {avg_ram:.2f}% | Peak RAM: {max_ram:.2f}%")
    logger.info("="*70)

if __name__ == "__main__":
    logger.info(f"Orchestrating simulation for {args.num_users} users for {args.duration} minutes.")
    logger.info("WARNING: This can be very resource-intensive. Monitor your system's CPU and RAM.")
    try:
        asyncio.run(run_simulation(num_users=args.num_users, duration_minutes=args.duration, base_seed=SEED, screenshot_enabled=not args.no_screenshots))
    except KeyboardInterrupt:
        logger.info("\nSimulation interrupted by user.")
    except Exception as e:
        logger.critical(f"💥 Simulation failed with a critical error: {e}", exc_info=True)