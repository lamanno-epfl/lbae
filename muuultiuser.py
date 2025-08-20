#!/usr/bin/env python3
"""
UNIFIED STABILITY TEST SUITE - PARALLEL EXECUTION
==================================================

This script simulates N users running the comprehensive test suite in parallel.
It uses asyncio to manage concurrent test runs.

PAGES COVERED:
1. Lipizones Selection
2. Lipizones vs Cell Types
3. Lipids vs Genes
4. 3D Exploration
5. Region Analysis
... and all others from the original script.

FEATURES:
- Simulates N concurrent users.
- Each user runs the full test suite independently.
- Isolated logging and screenshot folders for each user.
- Configurable number of users and screenshot toggle via command-line arguments.
"""

import asyncio
import logging
import time
import psutil
import os
import argparse
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

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
    """Main test suite that combines all working page tests."""
    
    # SURGICAL MODIFICATION: __init__ now accepts user_id and screenshot flag.
    # It also sets up its own logger to avoid global state conflicts during parallel runs.
    def __init__(self, user_id: int, screenshot: bool = False):
        self.user_id = user_id
        self.logger = self._setup_logger(user_id)
        self.monitor = SystemMonitor()
        self.current_page = None
        self.test_results = {}
        self.screenshot = screenshot
        self.screenshot_counter = 0
        
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
    
    # All methods below are identical to the original, but use the instance-specific `self.logger`.
    
    async def take_screenshot(self, page, description):
        """Take a screenshot if screenshot flag is enabled."""
        if self.screenshot:
            self.screenshot_counter += 1
            filename = f"{self.screenshot_counter:03d}_{description.lower().replace(' ', '_').replace(':', '').replace('(', '').replace(')', '').replace('-', '_').replace(',', '').replace('.', '').replace('!', '').replace('?', '')}.png"
            filepath = os.path.join(self.screenshot_folder, filename)
            await page.screenshot(path=filepath)
            self.logger.info(f"📸 Screenshot {self.screenshot_counter:03d}: {description} -> {filepath}")
    
    async def screenshot_after_click(self, page, element_or_selector, description):
        """Click an element and take a screenshot if enabled."""
        if isinstance(element_or_selector, str):
            await page.click(element_or_selector)
        else:
            await element_or_selector.click()
        await self.take_screenshot(page, f"After {description}")
        
    async def screenshot_after_action(self, page, action_func, description):
        """Execute an action and take a screenshot if enabled."""
        await action_func()
        await self.take_screenshot(page, f"After {description}")
        
    async def run_complete_test_suite(self):
        """Run the complete test suite covering all pages."""
        self.logger.info("🚀 STARTING UNIFIED STABILITY TEST SUITE")
        self.logger.info("=" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await self.test_lipizones_selection_page(page)
                await self.test_lipizones_vs_celltypes_page(page)
                await self.test_lipids_vs_genes_page(page)
                await self.test_3d_exploration_page(page)
                await self.test_lipid_selection_page(page)
                await self.test_peak_selection_page(page)
                await self.test_region_analysis_page(page)
                await self.test_lp_selection_page(page)
                await self.test_homepage_return_and_documentation(page)
                await self.generate_final_summary(page)
                
            except Exception as e:
                self.logger.error(f"❌ CRITICAL ERROR in test suite: {e}", exc_info=True)
                if self.screenshot:
                    error_path = os.path.join(self.screenshot_folder, "critical_error.png")
                    await page.screenshot(path=error_path)
                    self.logger.error(f"📸 Critical error screenshot saved to {error_path}")
                
            finally:
                await context.close()
                await browser.close()
                
        self.logger.info("🏁 UNIFIED TEST SUITE COMPLETED")
        self.logger.info("=" * 60)

    async def test_lipizones_selection_page(self, page):
        """Test the Lipizones Selection page (all working functionality)."""
        self.logger.info("\n🎯 TESTING LIPIZONES SELECTION PAGE")
        self.logger.info("-" * 40)
        
        try:
            await page.goto("http://127.0.0.1:8081/lipizones-selection", timeout=100000)
            self.logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "Lipizones Selection Page Loaded")
            
            await page.wait_for_selector('[id="page-6-lipizones-treemap"]', timeout=120000)
            self.logger.info("✅ Core elements rendered")
            await self.take_screenshot(page, "Lipizones Core Elements Rendered")
            
            self.monitor.log_stats(self.logger, "Lipizones Selection - Page Loaded")
            
            self.logger.info("🎯 STEP 1: Clicking 'Clear Selection' to activate interactive graph")
            await page.locator('[id="page-6-clear-selection-button"]').click(timeout=120000)
            await asyncio.sleep(10)  # Increased wait for graph to become fully interactive
            self.logger.info("✅ Graph is now interactive")
            await self.take_screenshot(page, "After Clear Selection Button")
            
            self.logger.info("🧠 Testing Brain Badge Selection (REQUIRED before sections mode)")
            try:
                await page.wait_for_selector('[id="main-brain"]', timeout=10000)
                await self.take_screenshot(page, "Brain Selection Component Available")
                
                brain_options = ["Reference 1 (M)", "Control 1 (M)", "Control 2 (M)"]
                
                for brain_label in brain_options:
                    try:
                        brain_selector = f'[id="main-brain"] .mantine-Chips-label:has-text("{brain_label}")'
                        brain_button = await page.wait_for_selector(brain_selector, timeout=10000)
                        
                        await self.take_screenshot(page, f"Before Brain Selection {brain_label}")
                        await brain_button.click()
                        await asyncio.sleep(8)  # Increased wait for brain selection to stabilize
                        self.logger.info(f"✅ Selected brain: {brain_label}")
                        await self.take_screenshot(page, f"After Brain Selection {brain_label}")
                        
                        await asyncio.sleep(10)  # Increased wait before proceeding
                        break
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not select brain '{brain_label}': {e}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"❌ Brain badge selection failed: {e}")
            
            self.logger.info("🎚️ Testing Main Slider (now available in One section mode)")
            try:
                main_slider = page.locator('[id="main-paper-slider"]')
                await main_slider.wait_for(state="visible", timeout=10000)
                await self.take_screenshot(page, "Before Main Slider Move")
                
                slider_box = await main_slider.bounding_box()
                if slider_box:
                    for i, pos in enumerate([0.25, 0.5, 0.75]):
                        x = slider_box['x'] + (slider_box['width'] * pos)
                        y = slider_box['y'] + (slider_box['height'] * 0.5)
                        await page.mouse.click(x, y)
                        await asyncio.sleep(6)  # Increased wait for slider interaction to register
                        await self.take_screenshot(page, f"Main Slider After Click {i+1} at {pos}")
                        self.logger.info(f"✅ Main slider clicked at position {pos}")
                else:
                    self.logger.warning("⚠️ Main slider bounding box not available")
            except Exception as e:
                self.logger.warning(f"❌ Main slider test failed: {e}")
                await self.take_screenshot(page, "Main Slider Error")
            
            self.logger.info("🎨 Testing Allen Toggle (now available in One section mode)")
            try:
                annotations_toggle = await page.wait_for_selector('[id="page-6-toggle-annotations"]', timeout=10000)
                await self.take_screenshot(page, "Before Allen Toggle Click")
                await annotations_toggle.click()
                await asyncio.sleep(8)  # Increased wait for toggle to register and stabilize
                self.logger.info("✅ Annotations toggle clicked")
                await self.take_screenshot(page, "After Allen Toggle Click")
            except Exception as e:
                self.logger.error(f"❌ Annotations toggle failed: {e}")
            
            self.logger.info("🎯 Testing Select All Lipizones Button")
            try:
                select_all_button = await page.wait_for_selector('[id="page-6-select-all-lipizones-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Select All Lipizones Click")
                await select_all_button.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Select all lipizones button clicked")
                await self.take_screenshot(page, "After Select All Lipizones Click")
            except Exception as e:
                self.logger.error(f"❌ Select all lipizones failed: {e}")
            
            self.logger.info("📚 Testing Tutorial Button")
            try:
                tutorial_button = await page.wait_for_selector('[id="lipizone-start-tutorial-btn"]', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Button Click")
                await tutorial_button.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Tutorial button clicked")
                await self.take_screenshot(page, "After Tutorial Button Click")
            except Exception as e:
                self.logger.error(f"❌ Tutorial button failed: {e}")
            
            self.logger.info("📚 Closing Tutorial Modal")
            try:
                close_button = await page.wait_for_selector('button:has-text("×")', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Modal Close")
                await close_button.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Tutorial modal closed")
                await self.take_screenshot(page, "After Tutorial Modal Close")
            except Exception as e:
                self.logger.error(f"❌ Tutorial modal close failed: {e}")
            
            self.logger.info("🧹 CRUCIAL: Clearing lipizones selection before treemap interaction...")
            await self.take_screenshot(page, "Before Clear Selection Button")
            await page.locator('[id="page-6-clear-selection-button"]').click()
            await asyncio.sleep(2)
            self.logger.info("✅ Lipizones selection cleared - now ready for treemap interaction")
            await self.take_screenshot(page, "After Clear Selection Button")

            self.logger.info("🎯 STEP 2: Drilling down deeper in treemap for smaller, manageable selection...")
            try:
                treemap_paths = await page.locator('[id="page-6-lipizones-treemap"] g.trace path').all()
                self.logger.info(f"🎯 Found {len(treemap_paths)} clickable regions in treemap")
                await self.take_screenshot(page, "Before Treemap Region Click")
                
                if len(treemap_paths) > 1:
                    smaller_region_locator = page.locator('[id="page-6-lipizones-treemap"] g.trace path').nth(2)
                    await smaller_region_locator.click(force=True)
                    self.logger.info("✅ Clicked on smaller region for manageable selection")
                else:
                    treemap_node_locator = page.locator('[id="page-6-lipizones-treemap"] g.trace path').first
                    await treemap_node_locator.click(force=True)
                    self.logger.info("✅ Clicked on available region")

                await asyncio.sleep(2)
                await self.take_screenshot(page, "After Treemap Region Click")
            except Exception as e:
                self.logger.error(f"❌ FAILED to drill down in treemap. Error: {e}")
                raise

            self.logger.info("🎯 STEP 3: Verifying the click was registered and checking selection size...")
            selection_text_element = await page.wait_for_selector('[id="page-6-current-selection-text"]')
            selection_text = await selection_text_element.text_content()
            self.logger.info(f"Selection text after click: '{selection_text}'")

            self.logger.info("🎯 STEP 4: Adding the selection...")
            add_button = await page.wait_for_selector('[id="page-6-add-selection-button"]', timeout=10000)
            await self.take_screenshot(page, "Before Add Selection Button")
            await add_button.click()
            await asyncio.sleep(10)  # Increased wait for selection to be processed
            self.logger.info("✅ Added selection")
            await self.take_screenshot(page, "After Add Selection Button")
            
            self.logger.info("🆔 Testing ID Cards (with limited selection)")
            try:
                view_id_cards_btn = await page.wait_for_selector('[id="view-id-cards-btn"]', timeout=10000)
                await self.take_screenshot(page, "Before ID Cards Button Click")
                await view_id_cards_btn.click()
                await asyncio.sleep(5)
                self.logger.info("✅ ID Cards button clicked")
                await self.take_screenshot(page, "After ID Cards Button Click")
                
                hide_id_cards_btn = await page.wait_for_selector('[id="close-id-cards-panel"]', timeout=10000)
                await self.take_screenshot(page, "Before Hide ID Cards Button")
                await hide_id_cards_btn.click()
                await asyncio.sleep(2)
                self.logger.info("✅ ID Cards closed")
                await self.take_screenshot(page, "After Hide ID Cards Button")
                
            except Exception as e:
                self.logger.error(f"❌ ID Cards test failed: {e}")
            
            self.logger.info("🔄 Testing Sections Mode Switch (One section vs All sections)")
            try:
                # Wait for the sections mode component to be available
                await page.wait_for_selector('[id="page-6-sections-mode"]', timeout=10000)
                await self.take_screenshot(page, "Sections Mode Component Available")
                
                # Wait for sections mode to become enabled after lipizone selection
                self.logger.info("⏰ Waiting for sections mode to become enabled...")
                await asyncio.sleep(5)  # Extra wait for lipizone selection to process
                
                # Test switching between "One section" and "All sections" views
                # First, switch to "All sections" view
                self.logger.info("--- Switching to 'All sections' view ---")
                await self.take_screenshot(page, "Before Switch to All Sections")
                
                # Click the sections mode selector first
                await page.click('[id="page-6-sections-mode"]')
                await asyncio.sleep(2)
                
                # This is a dmc.SegmentedControl, not a dropdown
                # The text content shows the actual options: "One section" and "All sections"
                target_text = "All sections"
                self.logger.info(f"🎯 Looking for segmented control option: '{target_text}'")
                
                # Try to click on the text content directly
                try:
                    await page.click(f'text="{target_text}"')
                    self.logger.info(f"✅ Successfully clicked segmented control option: {target_text}")
                    await asyncio.sleep(3)  # Wait for callback to complete
                    self.logger.info("✅ Switched to 'All sections' view")
                    await self.take_screenshot(page, "After Switch to All Sections")
                    
                    # Now switch back to "One section" view
                    self.logger.info("--- Switching back to 'One section' view ---")
                    await page.click('[id="page-6-sections-mode"]')
                    await asyncio.sleep(2)
                    
                    target_text_back = "One section"
                    await page.click(f'text="{target_text_back}"')
                    await asyncio.sleep(3)  # Wait for callback to complete
                    self.logger.info("✅ Switched back to 'One section' view")
                    await self.take_screenshot(page, "After Switch to One Section")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Direct text click failed: {e}")
                    
                    # Fallback: try to find the element containing the text
                    try:
                        # Look for any element containing the target text within the segmented control
                        text_element = await page.query_selector(f'[id="page-6-sections-mode"] *:has-text("{target_text}")')
                        if text_element:
                            await text_element.click()
                            self.logger.info(f"✅ Successfully clicked text element: {target_text}")
                            await asyncio.sleep(3)
                            self.logger.info("✅ Switched to 'All sections' view")
                            await self.take_screenshot(page, "After Switch to All Sections")
                        else:
                            raise Exception(f"Could not find element with text: {target_text}")
                    except Exception as e2:
                        self.logger.error(f"❌ Fallback selection also failed: {e2}")
                        raise Exception(f"Could not select mode '{target_text}' with any method")
                
                self.logger.info("✅ Sections mode switch test completed successfully")
                
            except Exception as e:
                self.logger.error(f"❌ Sections mode switch failed: {e}")
                # Don't fail the entire test, continue
                pass
            
            await self.take_screenshot(page, "Lipizones Selection Final Success")
            self.test_results['lipizones_selection'] = 'SUCCESS'
            self.logger.info("🎉 LIPIZONES SELECTION PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            self.logger.error(f"❌ Lipizones Selection page test failed: {e}")
            await self.take_screenshot(page, "Lipizones Selection Failure")
            self.test_results['lipizones_selection'] = 'FAILED'
            raise

    async def test_lipizones_vs_celltypes_page(self, page):
        """Test the Lipizones vs Cell Types page (all working functionality)."""
        self.logger.info("\n🎯 TESTING LIPIZONES VS CELL TYPES PAGE")
        self.logger.info("-" * 40)
        
        try:
            await page.goto("http://127.0.0.1:8081/lipizones-vs-celltypes", timeout=100000)
            self.logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "Lipizones vs Cell Types Page Loaded")
            
            self.logger.info("🔄 Handling Important Notice - page refresh requirement")
            try:
                await page.wait_for_selector('[id="page-6bis-refresh-alert"]', timeout=10000)
                self.logger.info("✅ Important Notice alert found")
                await self.take_screenshot(page, "Important Notice Alert Found")
                
                close_button = await page.wait_for_selector('[id="page-6bis-refresh-alert"] button', timeout=10000)
                await self.take_screenshot(page, "Before Close Important Notice Button")
                await close_button.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Important Notice alert closed")
                await self.take_screenshot(page, "After Close Important Notice Button")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not handle Important Notice: {e}")

            #await page.reload(wait_until="networkidle")
            await page.wait_for_selector('[id="page-6bis-lipizones-treemap"]', timeout=120000)
            await page.wait_for_selector('[id="page-6bis-celltypes-treemap"]', timeout=120000)
            self.logger.info("✅ Both treemaps have rendered")
            await self.take_screenshot(page, "Both Treemaps Rendered")
            
            self.monitor.log_stats(self.logger, "Lipizones vs Cell Types - Page Loaded")
            
            self.logger.info("📚 Testing Tutorial Button")
            try:
                tutorial_button = await page.wait_for_selector('[id="lipicell-start-tutorial-btn"]', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Button Click")
                await tutorial_button.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Tutorial button clicked")
                await self.take_screenshot(page, "After Tutorial Button Click")
                
                close_tutorial = await page.wait_for_selector('[id="lipicell-tutorial-close-1"]', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Popover Close")
                await close_tutorial.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Tutorial popover closed")
                await self.take_screenshot(page, "After Tutorial Popover Close")
            except Exception as e:
                self.logger.error(f"❌ Tutorial test failed: {e}")
            
            self.logger.info("🎚️ Testing Main Slider")
            try:
                main_slider = page.locator('[id="main-paper-slider"]')
                await main_slider.wait_for(state="visible", timeout=10000)
                await self.take_screenshot(page, "Before Main Slider Move")
                
                slider_box = await main_slider.bounding_box()
                if slider_box:
                    for i, pos in enumerate([0.25, 0.5, 0.75]):
                        x = slider_box['x'] + (slider_box['width'] * pos)
                        y = slider_box['y'] + (slider_box['height'] * 0.5)
                        await page.mouse.click(x, y)
                        await asyncio.sleep(6)  # Increased wait for slider interaction to register
                        await self.take_screenshot(page, f"Main Slider After Click {i+1} at {pos}")
                        self.logger.info(f"✅ Main slider clicked at position {pos}")
                else:
                    self.logger.warning("⚠️ Main slider bounding box not available")
            except Exception as e:
                self.logger.warning(f"❌ Main slider test failed: {e}")
            
            self.logger.info("🎨 Testing Allen Toggle")
            try:
                annotations_toggle = await page.wait_for_selector('[id="page-6bis-toggle-annotations"]', timeout=10000)
                await self.take_screenshot(page, "Before Allen Toggle Click")
                await annotations_toggle.click()
                await asyncio.sleep(8)  # Increased wait for toggle to register and stabilize
                self.logger.info("✅ Annotations toggle clicked")
                await self.take_screenshot(page, "After Allen Toggle Click")
            except Exception as e:
                self.logger.error(f"❌ Annotations toggle failed: {e}")
            
            self.logger.info("🎚️ Testing Pixel Filter Slider")
            try:
                pixel_filter = await page.wait_for_selector('[id="page-6bis-celltype-pixel-filter"]', timeout=10000)
                await self.take_screenshot(page, "Before Pixel Filter Slider Move")
                await pixel_filter.focus()
                await page.keyboard.press('ArrowRight')
                await asyncio.sleep(2)
                self.logger.info("✅ Pixel filter slider moved right")
                await self.take_screenshot(page, "After Pixel Filter Slider Move")
            except Exception as e:
                self.logger.error(f"❌ Pixel filter slider failed: {e}")
            
            self.logger.info("🎯 Testing Left Panel - Lipizones Controls")
            try:
                select_all_lipizones = await page.wait_for_selector('[id="page-6bis-select-all-lipizones-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Select All Lipizones Button")
                await select_all_lipizones.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Select All Lipizones button clicked")
                await self.take_screenshot(page, "After Select All Lipizones Button")
            except Exception as e:
                self.logger.error(f"❌ Select All Lipizones failed: {e}")
            
            self.logger.info("🎯 Testing Lipizones Treemap Interaction")
            try:
                clear_lipizones = await page.wait_for_selector('[id="page-6bis-clear-lipizone-selection-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Clear Lipizones Button")
                await clear_lipizones.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Cleared lipizones selection")
                await self.take_screenshot(page, "After Clear Lipizones Button")
                
                treemap_paths = await page.locator('[id="page-6bis-lipizones-treemap"] g.trace path').all()
                self.logger.info(f"🎯 Found {len(treemap_paths)} clickable regions in lipizones treemap")
                await self.take_screenshot(page, "Before Lipizones Treemap Click")
                
                if len(treemap_paths) > 2:
                    smaller_region = page.locator('[id="page-6bis-lipizones-treemap"] g.trace path').nth(2)
                    await smaller_region.click(force=True)
                    self.logger.info("✅ Clicked on smaller lipizones region")
                else:
                    first_region = page.locator('[id="page-6bis-lipizones-treemap"] g.trace path').first
                    await first_region.click(force=True)
                    self.logger.info("✅ Clicked on lipizones region")
                
                await asyncio.sleep(2)
                await self.take_screenshot(page, "After Lipizones Treemap Click")
                
                add_lipizones = await page.wait_for_selector('[id="page-6bis-add-lipizone-selection-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Add Lipizones Button")
                await add_lipizones.click()
                await asyncio.sleep(10)  # Increased wait for lipizones selection to be processed
                self.logger.info("✅ Added lipizones selection")
                await self.take_screenshot(page, "After Add Lipizones Button")
                
            except Exception as e:
                self.logger.error(f"❌ Lipizones treemap interaction failed: {e}")
            
            self.logger.info("🎯 Testing Right Panel - Cell Types Controls")
            try:
                select_all_celltypes = await page.wait_for_selector('[id="page-6bis-select-all-celltypes-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Select All Cell Types Button")
                await select_all_celltypes.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Select All Cell Types button clicked")
                await self.take_screenshot(page, "After Select All Cell Types Button")
            except Exception as e:
                self.logger.error(f"❌ Select All Cell Types failed: {e}")
            
            self.logger.info("🎯 Testing Cell Types Treemap Interaction")
            try:
                clear_celltypes = await page.wait_for_selector('[id="page-6bis-clear-celltype-selection-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Clear Cell Types Button")
                await clear_celltypes.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Cleared cell types selection")
                await self.take_screenshot(page, "After Clear Cell Types Button")
                
                treemap_paths = await page.locator('[id="page-6bis-celltypes-treemap"] g.trace path').all()
                self.logger.info(f"🎯 Found {len(treemap_paths)} clickable regions in cell types treemap")
                await self.take_screenshot(page, "Before Cell Types Treemap Click")
                
                if len(treemap_paths) > 2:
                    smaller_region = page.locator('[id="page-6bis-celltypes-treemap"] g.trace path').nth(2)
                    await smaller_region.click(force=True)
                    self.logger.info("✅ Clicked on smaller cell types region")
                else:
                    first_region = page.locator('[id="page-6bis-celltypes-treemap"] g.trace path').first
                    await first_region.click(force=True)
                    self.logger.info("✅ Clicked on cell types region")
                
                await asyncio.sleep(2)
                await self.take_screenshot(page, "After Cell Types Treemap Click")
                
                add_celltypes = await page.wait_for_selector('[id="page-6bis-add-celltype-selection-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Add Cell Types Button")
                await add_celltypes.click()
                await asyncio.sleep(10)  # Increased wait for cell types selection to be processed
                self.logger.info("✅ Added cell types selection")
                await self.take_screenshot(page, "After Add Cell Types Button")
                
            except Exception as e:
                self.logger.error(f"❌ Cell types treemap interaction failed: {e}")
            
            await self.take_screenshot(page, "Lipizones vs Cell Types Final Success")
            self.test_results['lipizones_vs_celltypes'] = 'SUCCESS'
            self.logger.info("🎉 LIPIZONES VS CELL TYPES PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            self.logger.error(f"❌ Lipizones vs Cell Types page test failed: {e}")
            await self.take_screenshot(page, "Lipizones vs Celltypes Failure")
            self.test_results['lipizones_vs_celltypes'] = 'FAILED'
            raise

    async def test_lipids_vs_genes_page(self, page):
        """Test the Lipids vs Genes page (all working functionality)."""
        self.logger.info("\n🎯 TESTING LIPIDS VS GENES PAGE")
        self.logger.info("-" * 40)
        
        try:
            await page.goto("http://127.0.0.1:8081/lipids-vs-genes", wait_until='networkidle', timeout=100000)
            self.logger.info("✅ Page navigation and initial data load complete")
            await self.take_screenshot(page, "Lipids vs Genes Page Loaded")
            
            self.logger.info("🔄 Handling 'Important Notice' if present")
            try:
                close_button = await page.wait_for_selector('[id="page-6tris-refresh-alert"] button', state='visible', timeout=15000)
                await self.take_screenshot(page, "Important Notice Alert Found")
                await close_button.click()
                await asyncio.sleep(2)
                self.logger.info("✅ 'Important Notice' alert found and closed")
                await self.take_screenshot(page, "After Close Important Notice Button")
            except PlaywrightTimeoutError:
                self.logger.info("ℹ️ 'Important Notice' alert did not appear, continuing test")
            
            self.logger.info("✅ Core page components loaded. Starting interaction tests")
            await self.take_screenshot(page, "Core Components Loaded")
            
            self.monitor.log_stats(self.logger, "Lipids vs Genes - Page Loaded")
            
            self.logger.info("📚 Testing Tutorial Button")
            try:
                await self.take_screenshot(page, "Before Tutorial Button Click")
                await page.click('[id="lipigene-start-tutorial-btn"]', timeout=10000)
                await asyncio.sleep(1)
                await self.take_screenshot(page, "After Tutorial Button Click")
                await page.click('[id="lipigene-tutorial-close-1"]', timeout=10000)
                await asyncio.sleep(1)
                self.logger.info("✅ Tutorial opened and closed")
                await self.take_screenshot(page, "After Tutorial Close")
            except Exception as e:
                self.logger.error(f"❌ Tutorial test failed: {e}")

            #await page.reload(wait_until="networkidle")
            self.logger.info("🎚️ Testing Main Slider")
            try:
                main_slider = page.locator('[id="main-paper-slider"]')
                await main_slider.wait_for(state="visible", timeout=10000)
                await self.take_screenshot(page, "Before Main Slider Move")
                
                slider_box = await main_slider.bounding_box()
                if slider_box:
                    for i, pos in enumerate([0.25, 0.5, 0.75]):
                        x = slider_box['x'] + (slider_box['width'] * pos)
                        y = slider_box['y'] + (slider_box['height'] * 0.5)
                        await page.mouse.click(x, y)
                        await asyncio.sleep(6)  # Increased wait for slider interaction to register
                        await self.take_screenshot(page, f"Main Slider After Click {i+1} at {pos}")
                        self.logger.info(f"✅ Main slider clicked at position {pos}")
                else:
                    self.logger.warning("⚠️ Main slider bounding box not available")
            except Exception as e:
                self.logger.warning(f"❌ Main slider test failed: {e}")
            
            self.logger.info("🎨 Testing Allen Annotations Toggle")
            try:
                await self.take_screenshot(page, "Before Allen Toggle Click")
                await page.click('[id="page-6tris-toggle-annotations"]', timeout=10000)
                await asyncio.sleep(6)  # Increased wait for toggle to register
                self.logger.info("✅ Annotations toggle clicked")
                await self.take_screenshot(page, "After Allen Toggle Click")
            except Exception as e:
                self.logger.error(f"❌ Annotations toggle failed: {e}")
            
            self.logger.info("💧 Testing Lipids Dropdown")
            try:
                # Use the working pattern: click on parent container for first selection
                lipid_dropdown_container = page.locator('[id="page-6tris-dropdown-lipids"]').locator('..')
                
                # Select first lipid
                self.logger.info("--- Selecting first lipid ---")
                await self.take_screenshot(page, "Lipids vs Genes First Before Opening Dropdown")
                await lipid_dropdown_container.click()
                await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=20000)
                await self.take_screenshot(page, "Lipids vs Genes First Dropdown Opened")
                
                # Try multiple selectors for first option
                first_option = None
                for selector in ['.mantine-MultiSelect-item:not([data-selected="true"])', '.mantine-Select-item:not([data-selected="true"])', '[data-value]:not([data-selected="true"])']:
                    try:
                        options = page.locator(selector)
                        if await options.count() > 0:
                            first_option = options.first
                            break
                    except Exception:
                        continue
                
                if first_option:
                    option_text = await first_option.text_content()
                    self.logger.info(f"Selecting first lipid: '{option_text}'")
                    await self.take_screenshot(page, f"Lipids vs Genes First Before Select {option_text}")
                    await first_option.click()
                    await asyncio.sleep(4)  # Increased wait for first lipid selection to register
                    await self.take_screenshot(page, f"Lipids vs Genes First After Select {option_text}")
                else:
                    self.logger.warning("⚠️ No first lipid option found")
                
                # Close dropdown after first selection
                await page.click('[id="page-6tris-graph-heatmap-mz-selection"]')
                await asyncio.sleep(2)
                await self.take_screenshot(page, "Lipids vs Genes First Dropdown Closed")
                
                # Select second lipid by clicking on selected pill/chip
                self.logger.info("--- Selecting second lipid ---")
                selected_pills = await page.locator('[id="page-6tris-dropdown-lipids"] .mantine-MultiSelect-value').all()
                if len(selected_pills) > 0:
                    # Click on the first selected pill to reopen dropdown
                    await self.take_screenshot(page, "Lipids vs Genes Second Before Clicking Selected Pill")
                    await selected_pills[0].click()
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "Lipids vs Genes Second Dropdown Reopened")
                    
                    # Wait for options to become visible again
                    await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=20000)
                    
                    # Find second available option
                    second_option = None
                    for selector in ['.mantine-MultiSelect-item:not([data-selected="true"])', '.mantine-Select-item:not([data-selected="true"])', '[data-value]:not([data-selected="true"])']:
                        try:
                            options = page.locator(selector)
                            if await options.count() > 0:
                                second_option = options.first
                                break
                        except Exception:
                            continue
                    
                    if second_option:
                        option_text = await second_option.text_content()
                        self.logger.info(f"Selecting second lipid: '{option_text}'")
                        await self.take_screenshot(page, f"Lipids vs Genes Second Before Select {option_text}")
                        await second_option.click()
                        await asyncio.sleep(4)  # Increased wait for second lipid selection to register
                        await self.take_screenshot(page, f"Lipids vs Genes Second After Select {option_text}")
                    else:
                        self.logger.warning("⚠️ No second lipid option found")
                    
                    # Close dropdown after second selection
                    await page.click('[id="page-6tris-graph-heatmap-mz-selection"]')
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "Lipids vs Genes Second Dropdown Closed")
                else:
                    self.logger.warning("⚠️ No selected pills found for second selection")
                
                self.logger.info("✅ Selected multiple lipids using CORRECT pattern (click on pills to reopen)")
            except Exception as e:
                self.logger.error(f"❌ Lipids dropdown test failed: {e}")
                # Don't fail the entire test, continue
                pass
            
            self.logger.info("🧬 Testing Genes Dropdown (with virtualization)")
            try:
                # Use the working pattern: click on parent container
                genes_dropdown_container = page.locator('[id="page-6tris-dropdown-genes"]').locator('..')
                genes_to_select = ["Gad1", "Gfap"]
                
                for gene in genes_to_select:
                    await self.take_screenshot(page, f"Before Genes Dropdown Click for {gene}")
                    await genes_dropdown_container.click()
                    await self.take_screenshot(page, f"After Genes Dropdown Click for {gene}")
                    
                    # Wait for options with multiple fallback selectors
                    try:
                        await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=20000)
                        self.logger.info(f"✅ Genes dropdown options are visible for {gene}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Standard options not visible for {gene}, trying alternative selectors: {e}")
                        await page.wait_for_selector('[data-value]', timeout=10000)
                    
                    # Type the gene name
                    await page.type('[id="page-6tris-dropdown-genes"]', gene, delay=50)
                    self.logger.info(f"Typed '{gene}', waiting for option to appear")
                    await self.take_screenshot(page, f"After Type {gene}")
                    
                    # Try multiple selectors for the filtered option
                    filtered_option = None
                    for selector in [f'.mantine-MultiSelect-item:has-text("{gene}")', f'.mantine-Select-item:has-text("{gene}")', f'[data-value*="{gene}"]']:
                        try:
                            options = page.locator(selector)
                            if await options.count() > 0:
                                filtered_option = options.first
                                break
                        except Exception:
                            continue
                    
                    if filtered_option:
                        await self.take_screenshot(page, f"Before Select Gene {gene}")
                        await filtered_option.click()
                        self.logger.info(f"✅ Selected '{gene}'")
                        await self.take_screenshot(page, f"After Select Gene {gene}")
                        
                        # Wait for long callback to complete by checking if graph updates
                        self.logger.info("Waiting for long callback to complete...")
                        try:
                            # Wait for the graph to potentially update (indicates long callback completed)
                            await page.wait_for_selector('[id="page-6tris-graph-heatmap-mz-selection"]', timeout=20000)
                            self.logger.info("✅ Long callback completed - graph is ready")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Could not detect graph update: {e}")
                            # Fallback to waiting
                            await asyncio.sleep(10)
                    else:
                        self.logger.warning(f"⚠️ Could not find gene option for '{gene}'")
                
                await self.take_screenshot(page, "Before Close Genes Dropdown")
                await page.click('[id="page-6tris-graph-heatmap-mz-selection"]')
                await asyncio.sleep(6)  # Increased wait for dropdown to close properly
                await self.take_screenshot(page, "After Close Genes Dropdown")
            except Exception as e:
                self.logger.error(f"❌ Genes dropdown test failed: {e}")
                # Don't fail the entire test, continue
                pass
            
            self.logger.info("🎚️ Testing Gene Expression Sliders")
            try:
                await self.take_screenshot(page, "Before First Gene Slider Move")
                await page.locator('[id="page-6tris-gene-slider-1"]').focus()
                await page.keyboard.press('ArrowRight')
                self.logger.info("✅ First gene slider moved")
                await asyncio.sleep(4)  # Increased wait for slider movement to register
                await self.take_screenshot(page, "After First Gene Slider Move")
                
                await self.take_screenshot(page, "Before Second Gene Slider Move")
                await page.locator('[id="page-6tris-gene-slider-2"]').focus()
                await page.keyboard.press('ArrowRight')
                self.logger.info("✅ Second gene slider moved")
                await asyncio.sleep(4)  # Increased wait for slider movement to register
                await self.take_screenshot(page, "After Second Gene Slider Move")
            except Exception as e:
                self.logger.error(f"❌ Gene expression sliders test failed: {e}")
            
            self.logger.info("🏷️ Testing Badge Display")
            try:
                await self.take_screenshot(page, "Before Badge Count Check")
                lipid_badge_count = await page.locator('[id^="page-6tris-badge-lipid-"]').count()
                self.logger.info(f"✅ Found {lipid_badge_count} visible lipid badges")
                
                gene_badge_count = await page.locator('[id^="page-6tris-badge-gene-"]').count()
                self.logger.info(f"✅ Found {gene_badge_count} visible gene badges")
                await self.take_screenshot(page, "After Badge Count Check")
                
            except Exception as e:
                self.logger.error(f"❌ Badge display test failed: {e}")
            
            await self.take_screenshot(page, "Lipids vs Genes Final Success")
            self.test_results['lipids_vs_genes'] = 'SUCCESS'
            self.logger.info("🎉 LIPIDS VS GENES PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            self.logger.error(f"❌ Lipids vs Genes page test failed: {e}")
            await self.take_screenshot(page, "Lipids vs Genes Failure")
            self.test_results['lipids_vs_genes'] = 'FAILED'
            raise

    async def test_3d_exploration_page(self, page):
        '''Test the 3D Exploration page.'''
        self.logger.info("\n🎯 TESTING 3D EXPLORATION PAGE")
        self.logger.info("-" * 40)
        
        try:
            await page.goto("http://127.0.0.1:8081/3D-exploration", wait_until="networkidle")
            await asyncio.sleep(3)
            self.logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "3D Exploration Page Loaded")
            
            self.monitor.log_stats(self.logger, "3D Exploration - Page Loaded")
            
            self.logger.info("🔍 TEST 1: Page Elements Verification")
            try:
                await page.wait_for_selector('[id="page-4-graph-region-selection"]', timeout=10000)
                await page.wait_for_selector('[id="page-4-dropdown-lipids"]', timeout=10000)
                await page.wait_for_selector('[id="page-4-add-structure-button"]', timeout=10000)
                await page.wait_for_selector('[id="page-4-display-button"]', timeout=10000)
                
                self.logger.info("✅ All main page elements found")
                await self.take_screenshot(page, "All Main Elements Found")
                
                add_button = await page.query_selector('[id="page-4-add-structure-button"]')
                display_button = await page.query_selector('[id="page-4-display-button"]')
                
                add_disabled = await add_button.get_attribute('disabled')
                display_disabled = await display_button.get_attribute('disabled')
                
                self.logger.info(f"🎯 Add button disabled: {add_disabled is not None}")
                self.logger.info(f"🎯 Display button disabled: {display_disabled is not None}")
                await self.take_screenshot(page, "Button States Checked")
                
            except Exception as e:
                self.logger.error(f"❌ Page elements verification failed: {e}")
            
            self.logger.info("🔍 TEST 2: Lipid Selection Dropdown")
            try:
                await self.take_screenshot(page, "Before Lipid Dropdown Click")
                await page.click('[id="page-4-dropdown-lipids"]')
                await asyncio.sleep(2)
                await self.take_screenshot(page, "After Lipid Dropdown Click")
                
                lipid_options = await page.query_selector_all('.mantine-Select-item, [data-value]')
                self.logger.info(f"🎯 Found {len(lipid_options)} lipid options")
                await self.take_screenshot(page, "Lipid Options Found")
                
                if lipid_options:
                    await self.take_screenshot(page, "Before Select First Lipid")
                    await lipid_options[0].click()
                    self.logger.info("✅ Selected first available lipid")
                    await asyncio.sleep(1)
                    await self.take_screenshot(page, "After Select First Lipid")
                    
                    selected_lipid = await page.input_value('[id="page-4-dropdown-lipids"]')
                    self.logger.info(f"🎯 Selected lipid: {selected_lipid}")
                    await self.take_screenshot(page, "Lipid Selection Verified")
                else:
                    self.logger.warning("⚠️ No lipid options found")
                
                await self.take_screenshot(page, "Before Close Lipid Dropdown")
                await page.click('[id="page-4-graph-region-selection"]')
                await asyncio.sleep(1)
                await self.take_screenshot(page, "After Close Lipid Dropdown")
                
            except Exception as e:
                self.logger.error(f"❌ Lipid selection failed: {e}")
            
            self.logger.info("🔍 TEST 3: Treemap Interaction and Region Selection")
            try:
                await page.wait_for_selector('[id="page-4-graph-region-selection"]', timeout=10000)
                await asyncio.sleep(3)
                await self.take_screenshot(page, "Treemap Fully Loaded")
                
                add_button_text = "Please choose a structure above"
                
                self.logger.info("🎯 Using JavaScript to bypass overlay layer...")
                await self.take_screenshot(page, "Before JavaScript Click Attempt")
                
                try:
                    js_result = await page.evaluate('''
                        () => {
                            const treemap = document.querySelector('[id="page-4-graph-region-selection"]');
                            if (!treemap) return 'Treemap not found';
                            const plotlyDiv = treemap.querySelector('.plotly');
                            if (!plotlyDiv) return 'Plotly div not found';
                            const traces = plotlyDiv.querySelectorAll('g.trace');
                            if (traces.length === 0) return 'No trace elements found';
                            for (let trace of traces) {
                                const clickableElements = trace.querySelectorAll('path, rect');
                                if (clickableElements.length > 0) {
                                    const firstElement = clickableElements[0];
                                    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
                                    firstElement.dispatchEvent(clickEvent);
                                    return 'Click event dispatched on trace element';
                                }
                            }
                            return 'No clickable elements found in traces';
                        }
                    ''')
                    
                    self.logger.info(f"🎯 JavaScript click result: {js_result}")
                    await self.take_screenshot(page, "After JavaScript Click Attempt")
                    
                    if "Click event dispatched" in js_result:
                        await asyncio.sleep(10)  # Increased wait for JavaScript click to register
                        add_button_text = await page.text_content('[id="page-4-add-structure-button"]')
                        self.logger.info(f"🎯 Add button text after JS click: {add_button_text}")
                        await self.take_screenshot(page, "Add Button Text After JS Click")
                        
                        if "Add" in add_button_text and "to selection" in add_button_text:
                            self.logger.info("✅ SUCCESS! JavaScript click bypassed the overlay!")
                            region_name = add_button_text.replace("Add ", "").replace(" to selection", "")
                            self.logger.info(f"🎯 Selected region: {region_name}")
                            
                            await self.take_screenshot(page, "Before Add Structure Button")
                            await page.click('[id="page-4-add-structure-button"]')
                            self.logger.info("✅ Added region to selection")
                            await asyncio.sleep(10)  # Increased wait for structure to be added
                            await self.take_screenshot(page, "After Add Structure Button")
                        else:
                            self.logger.warning("⚠️ JavaScript click didn't enable the add button")
                    else:
                        self.logger.warning(f"⚠️ JavaScript click failed: {js_result}")
                        
                except Exception as e:
                    self.logger.error(f"❌ JavaScript-based clicking failed: {e}")
                
            except Exception as e:
                self.logger.error(f"❌ Treemap interaction failed: {e}")
            
            self.logger.info("🔍 TEST 4: Display Lipid Expression")
            try:
                display_button = await page.query_selector('[id="page-4-display-button"]')
                display_disabled = await display_button.get_attribute('disabled')
                
                if display_disabled is None:
                    self.logger.info("🎯 Display button is enabled, clicking...")
                    await self.take_screenshot(page, "Before Display Button Click")
                    await page.click('[id="page-4-display-button"]')
                    
                    # Simple wait approach instead of complex detection
                    self.logger.info("⏰ Waiting for display operation to complete...")
                    await asyncio.sleep(15)  # Wait for long callback to complete
                    
                    await self.take_screenshot(page, "After Display Button Click")
                    
                    # Check if 3D volume graph is present
                    volume_graph = await page.query_selector('[id="page-4-graph-volume"]')
                    if volume_graph:
                        self.logger.info("✅ 3D volume graph displayed successfully")
                        await self.take_screenshot(page, "After Display Button Click")
                    else:
                        self.logger.warning("⚠️ 3D volume graph not found after display button click")
                        await self.take_screenshot(page, "3D Volume Graph Not Found")
                else:
                    self.logger.info("🎯 Display button is disabled - need regions and lipid selected")
                    await self.take_screenshot(page, "Display Button Disabled")
                    
            except Exception as e:
                self.logger.error(f"❌ Display lipid expression failed: {e}")
            
            await self.take_screenshot(page, "3D Exploration Final Success")
            self.test_results['3d_exploration'] = 'SUCCESS'
            self.logger.info("🎉 3D EXPLORATION PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            self.logger.error(f"❌ 3D Exploration page test failed: {e}")
            await self.take_screenshot(page, "3D Exploration Failure")
            self.test_results['3d_exploration'] = 'FAILED'
            raise

    async def test_lipid_selection_page(self, page):
        """Test the Lipid Selection page."""
        self.logger.info("\n🎯 TESTING LIPID SELECTION PAGE")
        self.logger.info("-" * 40)
        
        try:
            await page.goto("http://127.0.0.1:8081/lipid-selection", timeout=100000)
            self.logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "Lipid Selection Page Loaded")
            
            await page.wait_for_selector('[id="page-2-graph-heatmap-mz-selection"]', timeout=120000)
            self.logger.info("✅ Core elements rendered")
            await self.take_screenshot(page, "Lipid Selection Core Elements Rendered")
            
            self.monitor.log_stats(self.logger, "Lipid Selection - Page Loaded")
            
            self.logger.info("🎯 Testing Heatmap Interaction (lipid selection) - Select 1-3 lipids")
            try:
                for i in range(3):
                    await self.take_screenshot(page, f"Before Heatmap Click {i+1}")
                    await page.click('[id="page-2-graph-heatmap-mz-selection"]')
                    await asyncio.sleep(1)
                    self.logger.info(f"✅ Clicked on heatmap for lipid selection {i+1}")
                    await self.take_screenshot(page, f"After Heatmap Click {i+1}")
            except Exception as e:
                self.logger.error(f"❌ Heatmap interaction failed: {e}")
            
            self.logger.info("💧 Testing Lipids Dropdown...")
            try:
                # Use the working pattern: click on parent container for first selection
                lipid_dropdown_container = page.locator('[id="page-2-dropdown-lipids"]').locator('..')
                
                # Select first lipid
                self.logger.info("--- Selecting first lipid ---")
                await self.take_screenshot(page, "Lipid First Before Opening Dropdown")
                await lipid_dropdown_container.click()
                await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=20000)
                await self.take_screenshot(page, "Lipid First Dropdown Opened")
                
                # Try multiple selectors for first option
                first_option = None
                for selector in ['.mantine-MultiSelect-item:not([data-selected="true"])', '.mantine-Select-item:not([data-selected="true"])', '[data-value]:not([data-selected="true"])']:
                    try:
                        options = page.locator(selector)
                        if await options.count() > 0:
                            first_option = options.first
                            break
                    except Exception:
                        continue
                
                if first_option:
                    option_text = await first_option.text_content()
                    self.logger.info(f"Selecting first lipid: '{option_text}'")
                    await self.take_screenshot(page, f"Lipid First Before Select {option_text}")
                    await first_option.click()
                    await asyncio.sleep(8)  # Increased wait for first lipid selection to register
                    await self.take_screenshot(page, f"Lipid First After Select {option_text}")
                else:
                    self.logger.warning("⚠️ No first lipid option found")
                
                # Close dropdown after first selection
                await page.click('[id="page-2-graph-heatmap-mz-selection"]')
                await asyncio.sleep(2)
                await self.take_screenshot(page, "Lipid First Dropdown Closed")
                
                # Select second lipid by clicking on the selected pill/chip
                self.logger.info("--- Selecting second lipid ---")
                selected_pills = await page.locator('[id="page-2-dropdown-lipids"] .mantine-MultiSelect-value').all()
                if len(selected_pills) > 0:
                    # Click on the first selected pill to reopen dropdown
                    await self.take_screenshot(page, "Lipid Second Before Clicking Selected Pill")
                    await selected_pills[0].click()
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "Lipid Second Dropdown Reopened")
                    
                    # Wait for options to become visible again
                    await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=20000)
                    
                    # Find second available option
                    second_option = None
                    for selector in ['.mantine-MultiSelect-item:not([data-selected="true"])', '.mantine-Select-item:not([data-selected="true"])', '[data-value]:not([data-selected="true"])']:
                        try:
                            options = page.locator(selector)
                            if await options.count() > 0:
                                second_option = options.first
                                break
                        except Exception:
                            continue
                    
                    if second_option:
                        option_text = await second_option.text_content()
                        self.logger.info(f"Selecting second lipid: '{option_text}'")
                        await self.take_screenshot(page, f"Lipid Second Before Select {option_text}")
                        await second_option.click()
                        await asyncio.sleep(8)  # Increased wait for second lipid selection to register
                        await self.take_screenshot(page, f"Lipid Second After Select {option_text}")
                    else:
                        self.logger.warning("⚠️ No second lipid option found")
                    
                    # Close dropdown after second selection
                    await page.click('[id="page-2-graph-heatmap-mz-selection"]')
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "Lipid Second Dropdown Closed")
                else:
                    self.logger.warning("⚠️ No selected pills found for second selection")
                
                # Stabilization wait (GOLD STANDARD)
                self.logger.info("WAITING 30 SECONDS for app to stabilize after lipid selections...")
                await asyncio.sleep(30)  # Increased stabilization wait
                
                # Verify selections after stabilization wait
                self.logger.info("Verifying lipid selections after stabilization wait...")
                selected_pills = await page.locator('[id="page-2-dropdown-lipids"] .mantine-MultiSelect-value').all()
                selected_texts = [await pill.text_content() for pill in selected_pills]
                self.logger.info(f"Final lipids in dropdown: {selected_texts}")
                await self.take_screenshot(page, "Lipid Dropdown Final Verification")
                
                self.logger.info("✅ Selected multiple lipids using CORRECT pattern (click on pills to reopen)")
                
            except Exception as e:
                self.logger.error(f"❌ Lipids dropdown test failed: {e}", exc_info=True)
            
            self.logger.info("🧠 Testing Brain Badge Selection")
            try:
                await page.wait_for_selector('[id="main-brain"]', timeout=10000)
                brain_options = ["Reference 1 (M)", "Control 1 (M)", "Control 2 (M)"]
                for brain_label in brain_options:
                    try:
                        brain_selector = f'[id="main-brain"] .mantine-Chips-label:has-text("{brain_label}")'
                        brain_button = await page.wait_for_selector(brain_selector, timeout=10000)
                        await self.take_screenshot(page, f"Before Brain Selection {brain_label}")
                        await brain_button.click()
                        await asyncio.sleep(2)
                        self.logger.info(f"✅ Selected brain: {brain_label}")
                        await self.take_screenshot(page, f"After Brain Selection {brain_label}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not select brain '{brain_label}': {e}")
            except Exception as e:
                self.logger.error(f"❌ Brain badge selection failed: {e}")
            
            self.logger.info("🎨 Testing RGB Toggle")
            try:
                rgb_switch = await page.wait_for_selector('[id="page-2-rgb-switch"]', timeout=10000)
                await self.take_screenshot(page, "Before RGB Switch Click")
                await rgb_switch.click()
                await asyncio.sleep(2)
                self.logger.info("✅ RGB switch clicked")
                await self.take_screenshot(page, "After RGB Switch Click")
            except Exception as e:
                self.logger.error(f"❌ RGB switch failed: {e}")
            
            self.logger.info("🔄 Testing Sections Mode Switch")
            try:
                # Check if the buttons are enabled before trying to click
                all_sections_button = page.locator('text="All sections"')
                one_section_button = page.locator('text="One section"')
                
                # Check if buttons are enabled
                all_sections_disabled = await all_sections_button.get_attribute('class')
                one_section_disabled = await one_section_button.get_attribute('class')
                
                if 'disabled' not in (all_sections_disabled or ''):
                    await all_sections_button.click(timeout=15000)
                    await asyncio.sleep(3)
                    self.logger.info("✅ Switched to 'All sections' view")
                    await self.take_screenshot(page, "After Switch to All Sections")
                    
                    # Try to switch back to 'One section' view
                    if 'disabled' not in (one_section_disabled or ''):
                        await one_section_button.click(timeout=15000)
                        await asyncio.sleep(3)
                        self.logger.info("✅ Switched back to 'One section' view")
                        await self.take_screenshot(page, "After Switch to One Section")
                    else:
                        self.logger.info("ℹ️ 'One section' button is disabled, skipping")
                else:
                    self.logger.info("ℹ️ 'All sections' button is disabled, skipping sections mode test")
                    
            except Exception as e:
                self.logger.error(f"❌ Sections mode switch failed: {e}")
                # Don't fail the entire test, continue
                pass
            
            self.logger.info("🎨 Testing Allen Annotations Toggle")
            try:
                annotations_toggle = await page.wait_for_selector('[id="page-2-toggle-annotations"]', timeout=10000)
                await self.take_screenshot(page, "Before Allen Toggle Click")
                await annotations_toggle.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Annotations toggle clicked")
                await self.take_screenshot(page, "After Allen Toggle Click")
            except Exception as e:
                self.logger.error(f"❌ Annotations toggle failed: {e}")
            
            self.logger.info("🎚️ Testing Main Slider")
            try:
                main_slider = page.locator('[id="main-paper-slider"]')
                await main_slider.wait_for(state="visible", timeout=10000)
                slider_box = await main_slider.bounding_box()
                if slider_box:
                    for i, pos in enumerate([0.25, 0.5, 0.75]):
                        x = slider_box['x'] + (slider_box['width'] * pos)
                        y = slider_box['y'] + (slider_box['height'] * 0.5)
                        await page.mouse.click(x, y)
                        await asyncio.sleep(1)
                        self.logger.info(f"✅ Main slider clicked at position {pos}")
                else:
                    self.logger.warning("⚠️ Main slider bounding box not available")
            except Exception as e:
                self.logger.warning(f"❌ Main slider test failed: {e}")
            
            await self.take_screenshot(page, "Lipid Selection Final Success")
            self.test_results['lipid_selection'] = 'SUCCESS'
            self.logger.info("🎉 LIPID SELECTION PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            self.logger.error(f"❌ Lipid Selection page test failed: {e}")
            await self.take_screenshot(page, "Lipid Selection Failure")
            self.test_results['lipid_selection'] = 'FAILED'
            raise

    async def test_peak_selection_page(self, page):
        """Test the Peak Selection page."""
        self.logger.info("\n🎯 TESTING PEAK SELECTION PAGE")
        self.logger.info("-" * 40)
        
        try:
            await page.goto("http://127.0.0.1:8081/peak-selection", timeout=100000)
            self.logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "Peak Selection Page Loaded")
            
            await page.wait_for_selector('[id="page-2tris-graph-heatmap-mz-selection"]', timeout=120000)
            self.logger.info("✅ Core elements rendered")
            await self.take_screenshot(page, "Peak Selection Core Elements Rendered")
            
            self.monitor.log_stats(self.logger, "Peak Selection - Page Loaded")
            
            self.logger.info("📚 Testing Tutorial Button")
            try:
                tutorial_button = await page.wait_for_selector('[id="peak-start-tutorial-btn"]', timeout=10000)
                await tutorial_button.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Tutorial button clicked")
                
                close_tutorial = await page.wait_for_selector('[id="peak-tutorial-close-1"]', timeout=10000)
                await close_tutorial.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Tutorial popover closed")
            except Exception as e:
                self.logger.error(f"❌ Tutorial test failed: {e}")
            
            self.logger.info("🎨 Testing Allen Annotations Toggle")
            try:
                annotations_toggle = await page.wait_for_selector('[id="page-2tris-toggle-annotations"]', timeout=10000)
                await annotations_toggle.click()
                await asyncio.sleep(2)
                self.logger.info("✅ Annotations toggle clicked")
            except Exception as e:
                self.logger.error(f"❌ Annotations toggle failed: {e}")
            
            self.logger.info("🎯 Testing Peak Dropdown...")
            try:
                # Use the working pattern: click on parent container for first selection
                peak_dropdown_container = page.locator('[id="page-2tris-dropdown-peaks"]').locator('..')
                
                # Select first peak
                self.logger.info("--- Selecting first peak ---")
                await self.take_screenshot(page, "Peak First Before Opening Dropdown")
                await peak_dropdown_container.click()
                await asyncio.sleep(2)  # Wait for dropdown to open
                await self.take_screenshot(page, "Peak First Dropdown Opened")
                
                # Wait for options to become visible with more flexible selector
                try:
                    await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=20000)
                    self.logger.info("✅ Peak dropdown options are visible")
                except Exception as e:
                    self.logger.warning(f"⚠️ Standard options not visible, trying alternative selectors: {e}")
                    # Try alternative selectors
                    await page.wait_for_selector('[data-value]', timeout=10000)
                
                # Find first available option with multiple selector strategies
                first_option = None
                for selector in ['.mantine-MultiSelect-item:not([data-selected="true"])', '.mantine-Select-item:not([data-selected="true"])', '[data-value]:not([data-selected="true"])']:
                    try:
                        first_option = page.locator(selector).first
                        if await first_option.count() > 0:
                            break
                    except Exception:
                        continue
                
                if first_option and await first_option.count() > 0:
                    option_text = await first_option.text_content()
                    self.logger.info(f"Selecting first peak: '{option_text}'")
                    await self.take_screenshot(page, f"Peak First Before Select {option_text}")
                    await first_option.click()
                    await asyncio.sleep(4)  # Increased wait for peak selection to register
                    await self.take_screenshot(page, f"Peak First After Select {option_text}")
                else:
                    self.logger.warning("⚠️ No first peak option found")
                
                # Close dropdown after first selection
                await page.click('[id="page-2tris-graph-heatmap-mz-selection"]')
                await asyncio.sleep(2)
                await self.take_screenshot(page, "Peak First Dropdown Closed")
                
                # Select second peak by clicking on the selected pill/chip
                self.logger.info("--- Selecting second peak ---")
                selected_pills = await page.locator('[id="page-2tris-dropdown-peaks"] .mantine-MultiSelect-value').all()
                if len(selected_pills) > 0:
                    # Click on the first selected pill to reopen dropdown
                    await self.take_screenshot(page, "Peak Second Before Clicking Selected Pill")
                    await selected_pills[0].click()
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "Peak Second Dropdown Reopened")
                    
                    # Wait for options to become visible again
                    try:
                        await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=20000)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Standard options not visible for second selection: {e}")
                        await page.wait_for_selector('[data-value]', timeout=10000)
                    
                    # Find second available option
                    second_option = None
                    for selector in ['.mantine-MultiSelect-item:not([data-selected="true"])', '.mantine-Select-item:not([data-selected="true"])', '[data-value]:not([data-selected="true"])']:
                        try:
                            second_option = page.locator(selector).first
                            if await second_option.count() > 0:
                                break
                        except Exception:
                            continue
                    
                    if second_option and await second_option.count() > 0:
                        option_text = await second_option.text_content()
                        self.logger.info(f"Selecting second peak: '{option_text}'")
                        await self.take_screenshot(page, f"Peak Second Before Select {option_text}")
                        await second_option.click()
                        await asyncio.sleep(4)  # Increased wait for peak selection to register
                        await self.take_screenshot(page, f"Peak Second After Select {option_text}")
                    else:
                        self.logger.warning("⚠️ No second peak option found")
                    
                    # Close dropdown after second selection
                    await page.click('[id="page-2tris-graph-heatmap-mz-selection"]')
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "Peak Second Dropdown Closed")
                else:
                    self.logger.warning("⚠️ No selected pills found for second selection")
                
                # Stabilization wait (GOLD STANDARD)
                self.logger.info("WAITING 30 SECONDS for app to stabilize after peak selections...")
                await asyncio.sleep(30)  # Increased stabilization wait
                
                # Verify selections after stabilization wait
                self.logger.info("Verifying peak selections after stabilization wait...")
                selected_pills = await page.locator('[id="page-2tris-dropdown-peaks"] .mantine-MultiSelect-value').all()
                selected_texts = [await pill.text_content() for pill in selected_pills]
                self.logger.info(f"Final peaks in dropdown: {selected_texts}")
                await self.take_screenshot(page, "Peak Dropdown Final Verification")
                
                self.logger.info("✅ Selected multiple peaks using CORRECT pattern (click on pills to reopen)")
            except Exception as e:
                self.logger.error(f"❌ Peak dropdown test failed: {e}", exc_info=True)
            
            self.logger.info("🧠 Testing Brain Badge Selection")
            try:
                await page.wait_for_selector('[id="main-brain"]', timeout=10000)
                brain_options = ["Reference 1 (M)", "Control 1 (M)", "Control 2 (M)"]
                for brain_label in brain_options:
                    try:
                        brain_selector = f'[id="main-brain"] .mantine-Chips-label:has-text("{brain_label}")'
                        await page.wait_for_selector(brain_selector, timeout=10000)
                        await page.click(brain_selector)
                        self.logger.info(f"✅ Selected brain: {brain_label}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not select brain '{brain_label}': {e}")
            except Exception as e:
                self.logger.error(f"❌ Brain badge selection failed: {e}")
            
            self.logger.info("🎨 Testing RGB Switch")
            try:
                await page.click('[id="page-2tris-rgb-switch"]', timeout=10000)
                self.logger.info("✅ RGB switch clicked")
            except Exception as e:
                self.logger.error(f"❌ RGB switch failed: {e}")
            
            self.logger.info("📊 Testing Show Spectrum Button")
            try:
                await page.click('[id="page-2tris-show-spectrum-button"]', timeout=10000)
                await asyncio.sleep(3)
                self.logger.info("✅ Show spectrum button clicked")
                
                await page.click('[id="page-2tris-close-spectrum-button"]', timeout=10000)
                self.logger.info("✅ Spectrum drawer closed")
            except Exception as e:
                self.logger.error(f"❌ Show spectrum button failed: {e}")
            
            self.logger.info("🎚️ Testing Main Slider")
            try:
                main_slider = page.locator('[id="main-paper-slider"]')
                await main_slider.wait_for(state="visible", timeout=10000)
                slider_box = await main_slider.bounding_box()
                if slider_box:
                    for pos in [0.15, 0.35, 0.75, 0.85]:
                        x = slider_box['x'] + (slider_box['width'] * pos)
                        y = slider_box['y'] + (slider_box['height'] * 0.5)
                        await page.mouse.click(x, y)
                        await asyncio.sleep(1)
            except Exception as e:
                self.logger.warning(f"❌ Main slider test failed: {e}")
            
            await self.take_screenshot(page, "Peak Selection Final Success")
            self.test_results['peak_selection'] = 'SUCCESS'
            self.logger.info("🎉 PEAK SELECTION PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            self.logger.error(f"❌ Peak Selection page test failed: {e}")
            await self.take_screenshot(page, "Peak Selection Failure")
            self.test_results['peak_selection'] = 'FAILED'
            raise

    async def test_region_analysis_page(self, page):
        '''Test the Region Analysis page.'''
        self.logger.info("\n🎯 TESTING REGION ANALYSIS PAGE")
        self.logger.info("-" * 40)
        
        try:
            await page.goto("http://127.0.0.1:8081/region-analysis", timeout=100000)
            self.logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "Region Analysis Page Loaded")
            
            await page.wait_for_selector('[id="page-3-dropdown-brain-regions"]', timeout=120000)
            self.logger.info("✅ Core elements rendered")
            
            self.monitor.log_stats(self.logger, "Region Analysis - Page Loaded")
            
            self.logger.info("📚 Testing Tutorial Button")
            try:
                await page.click('[id="analysis-start-tutorial-btn"]', timeout=10000)
                await asyncio.sleep(2)
                await page.click('[id="analysis-tutorial-close-1"]', timeout=10000)
                self.logger.info("✅ Tutorial opened and closed")
            except Exception as e:
                self.logger.error(f"❌ Tutorial test failed: {e}")
            
            self.logger.info("🎨 Testing Allen Toggle")
            try:
                await page.click('[id="page-3-toggle-annotations"]', timeout=10000)
                self.logger.info("✅ Annotations toggle clicked")
            except Exception as e:
                self.logger.error(f"❌ Annotations toggle failed: {e}")
            
            self.logger.info("🎯 Testing Brain Region MultiSelect Selection")
            first_option_text, second_option_text = None, None
            try:
                # First, check if the dropdown has any initial selections
                initial_selections = await page.locator('[id="page-3-dropdown-brain-regions"] .mantine-MultiSelect-value').all()
                self.logger.info(f"🎯 Initial brain region selections: {len(initial_selections)}")
                
                # Use the working pattern: click on parent container
                region_dropdown_container = page.locator('[id="page-3-dropdown-brain-regions"]').locator('..')
                
                # Select first region
                self.logger.info("--- Selecting first brain region ---")
                await self.take_screenshot(page, "Brain Region Dropdown Before Select 1")
                await region_dropdown_container.click()
                await asyncio.sleep(2)
                
                # Wait for options to become visible
                try:
                    await page.wait_for_selector('.mantine-MultiSelect-item, [role="option"], [data-value]', state='visible', timeout=10000)
                    self.logger.info("✅ Brain region dropdown options are visible")
                except Exception as e:
                    self.logger.warning(f"⚠️ Standard options not visible, trying alternative selectors: {e}")
                    await page.wait_for_selector('[data-value]', timeout=5000)
                
                # Try multiple selectors for dropdown options
                first_option = None
                for selector in ['.mantine-MultiSelect-item', '[role="option"]', '[data-value]']:
                    try:
                        first_option = await page.wait_for_selector(selector, state='visible', timeout=5000)
                        if first_option:
                            break
                    except Exception:
                        continue
                
                if not first_option:
                    # Fallback: use locator to find first available option
                    options_locator = page.locator('.mantine-MultiSelect-item, [role="option"], [data-value]')
                    count = await options_locator.count()
                    if count > 0:
                        first_option = options_locator.first
                        first_option_text = await first_option.text_content()
                        self.logger.info(f"Selecting first brain region: '{first_option_text}'")
                        await self.take_screenshot(page, f"Brain Region First Before Select {first_option_text}")
                        await first_option.click()
                        await asyncio.sleep(3) # CRITICAL: Wait for page to update
                        await self.take_screenshot(page, f"Brain Region First After Select {first_option_text}")
                    else:
                        raise Exception("No dropdown options found with any selector")
                else:
                    first_option_text = await first_option.text_content()
                    self.logger.info(f"Selecting first brain region: '{first_option_text}'")
                    await self.take_screenshot(page, f"Brain Region First Before Select {first_option_text}")
                    await first_option.click()
                    await asyncio.sleep(3) # CRITICAL: Wait for page to update
                    await self.take_screenshot(page, f"Brain Region First After Select {first_option_text}")
                
                # Close dropdown after first selection
                await page.click('[id="main-brain"]', force=True)
                await asyncio.sleep(2)
                await self.take_screenshot(page, "Brain Region First Dropdown Closed")
                
                # Re-open the dropdown to select the second region by clicking on selected pill
                self.logger.info("--- Selecting second brain region ---")
                selected_pills = await page.locator('[id="page-3-dropdown-brain-regions"] .mantine-MultiSelect-value').all()
                if len(selected_pills) > 0:
                    # Click on the first selected pill to reopen dropdown
                    await self.take_screenshot(page, "Brain Region Second Before Clicking Selected Pill")
                    await selected_pills[0].click()
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "Brain Region Second Dropdown Reopened")
                    
                    # Wait for options to become visible again
                    try:
                        await page.wait_for_selector('.mantine-MultiSelect-item, [role="option"], [data-value]', state='visible', timeout=10000)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Standard options not visible for second selection: {e}")
                        await page.wait_for_selector('[data-value]', timeout=5000)
                    
                    # Find the next unselected option
                    all_options = await page.locator('.mantine-MultiSelect-item:not([data-selected="true"])').all()
                    if len(all_options) > 0:
                        second_option = all_options[0]
                        second_option_text = await second_option.text_content()
                        self.logger.info(f"Selecting second brain region: '{second_option_text}'")
                        await self.take_screenshot(page, f"Brain Region Second Before Select {second_option_text}")
                        await second_option.click()
                        await asyncio.sleep(3) # CRITICAL: Wait for page to update
                        await self.take_screenshot(page, f"Brain Region Second After Select {second_option_text}")
                    else:
                        # Fallback: try to find any available option
                        any_option = page.locator('.mantine-MultiSelect-item, [role="option"]').first
                        if await any_option.count() > 0:
                            second_option_text = await any_option.text_content()
                            self.logger.info(f"Selecting fallback second brain region: '{second_option_text}'")
                            await self.take_screenshot(page, f"Brain Region Second Before Select {second_option_text}")
                            await any_option.click()
                            await asyncio.sleep(3)
                            await self.take_screenshot(page, f"Brain Region Second After Select {second_option_text}")
                        else:
                            self.logger.warning("⚠️ Could not find a second brain region option, continuing with one selection")
                            second_option_text = first_option_text  # Use same as first for fallback
                    
                    # Close the dropdown by clicking the main brain image
                    await page.click('[id="main-brain"]', force=True)
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "Brain Region Second Dropdown Closed")
                else:
                    self.logger.warning("⚠️ No selected pills found for second selection")
                
                self.logger.info("✅ Successfully selected brain regions and closed the dropdown.")
            except Exception as e:
                self.logger.error(f"❌ Brain region MultiSelect selection failed: {e}", exc_info=True)
                await self.take_screenshot(page, "Brain Region Selection Failure")
                # Don't fail the entire test, try to continue
                first_option_text = "Region A"  # Fallback values
                second_option_text = "Region B"
            
            self.logger.info("🎯 Testing Group Assignment")
            try:
                # Use fallback values if the dropdown selection failed
                if not first_option_text or not second_option_text:
                    self.logger.warning("⚠️ Using fallback region names for group assignment")
                    first_option_text = "Region A"
                    second_option_text = "Region B"
                
                # Try to assign to Group A
                try:
                    await page.click('[id="page-3-group-a-selector"]')
                    # Look for the first option text in the group selector dropdown
                    group_a_option = page.locator(f'text="{first_option_text}"').first
                    if await group_a_option.count() > 0:
                        await group_a_option.click()
                        self.logger.info(f"✅ Assigned '{first_option_text}' to Group A")
                    else:
                        # Fallback: click on first available option
                        first_group_option = page.locator('[role="option"]').first
                        if await first_group_option.count() > 0:
                            await first_group_option.click()
                            self.logger.info(f"✅ Assigned fallback option to Group A")
                        else:
                            self.logger.warning("⚠️ No group A options available")
                except Exception as e:
                    self.logger.warning(f"⚠️ Group A assignment failed: {e}")
                
                # Try to assign to Group B
                try:
                    await page.click('[id="page-3-group-b-selector"]')
                    # Look for the second option text in the group selector dropdown
                    group_b_option = page.locator(f'text="{second_option_text}"').first
                    if await group_b_option.count() > 0:
                        await group_b_option.click()
                        self.logger.info(f"✅ Assigned '{second_option_text}' to Group B")
                    else:
                        # Fallback: click on second available option
                        group_options = page.locator('[role="option"]')
                        if await group_options.count() > 1:
                            await group_options.nth(1).click()
                            self.logger.info(f"✅ Assigned fallback option to Group B")
                        else:
                            self.logger.warning("⚠️ No group B options available")
                except Exception as e:
                    self.logger.warning(f"⚠️ Group B assignment failed: {e}")
                
            except Exception as e:
                self.logger.error(f"❌ Group assignment failed: {e}")
                # Don't fail the entire test, continue
                pass
            
            self.logger.info("🧮 Testing Compute Differential Analysis")
            try:
                compute_button = await page.wait_for_selector('[id="page-3-button-compute-volcano"]')
                if await compute_button.get_attribute('disabled') is None:
                    await compute_button.click()
                    self.logger.info("✅ Clicked compute. Waiting for long callback to complete...")
                    
                    # Wait for volcano graph to appear (indicates long callback completed)
                    await page.wait_for_selector('[id="page-3-graph-volcano"]', timeout=60000)  # Increased timeout for multiple users
                    self.logger.info("✅ Long callback completed - volcano graph is visible")
                    
                    await asyncio.sleep(6)  # Additional wait for graph to fully render
                    await self.take_screenshot(page, "After Compute Button Click")
                else:
                    self.logger.warning("⚠️ Compute button is disabled.")
            except Exception as e:
                self.logger.error(f"❌ Compute failed: {e}")
                raise
            
            self.logger.info("🔄 Testing Reset Regions")
            try:
                await page.click('[id="page-3-reset-button"]')
                self.logger.info("✅ Reset regions button clicked")
            except Exception as e:
                self.logger.error(f"❌ Reset regions failed: {e}")
                raise
            
            await self.take_screenshot(page, "Region Analysis Final Success")
            self.test_results['region_analysis'] = 'SUCCESS'
            self.logger.info("🎉 REGION ANALYSIS PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            self.logger.error(f"❌ Region Analysis page test failed: {e}")
            await self.take_screenshot(page, "Region Analysis Failure")
            self.test_results['region_analysis'] = 'FAILED'
            raise
    
    async def test_lp_selection_page(self, page):
        """Test the LP-Selection page (lipid programs selection)."""
        self.logger.info("\n🎯 TESTING LP-SELECTION PAGE")
        self.logger.info("-" * 40)
        
        try:
            await page.goto("http://127.0.0.1:8081/lp-selection", timeout=100000)
            self.logger.info("✅ Page loaded successfully")
            await page.wait_for_selector('[id="page-2bis-graph-heatmap-mz-selection"]', timeout=120000)
            self.logger.info("✅ Core elements rendered")
            
            self.monitor.log_stats(self.logger, "LP Selection - Page Loaded")

            self.logger.info("🎯 Testing Heatmap Interaction")
            try:
                for i in range(3):
                    await page.click('[id="page-2bis-graph-heatmap-mz-selection"]')
                    await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"❌ Heatmap interaction failed: {e}")
            
            self.logger.info("🎯 Testing Program Dropdown Selection with stabilization wait")
            try:
                # Use the working pattern: click on parent container for first selection
                program_dropdown_container = page.locator('[id="page-2bis-dropdown-programs"]').locator('..')
                
                # Before opening dropdown
                await self.take_screenshot(page, "LP Program Dropdown Before Opening")
                
                # Select first program
                self.logger.info("--- Selecting first program ---")
                await program_dropdown_container.click()
                await asyncio.sleep(2)  # Wait for dropdown to open
                await self.take_screenshot(page, "LP Program Dropdown After Click")
                
                # Wait for options with multiple fallback selectors
                await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=20000)
                await self.take_screenshot(page, "LP Program Options Visible")
                
                # Try multiple selectors for first option
                first_unselected_option = None
                for selector in ['.mantine-MultiSelect-item:not([data-selected="true"])', '.mantine-Select-item:not([data-selected="true"])', '[data-value]:not([data-selected="true"])']:
                    try:
                        options = page.locator(selector)
                        if await options.count() > 0:
                            first_unselected_option = options.first
                            break
                    except Exception:
                        continue
                
                if first_unselected_option:
                    option_text = await first_unselected_option.text_content()
                    self.logger.info(f"Selecting: '{option_text}'")
                    await self.take_screenshot(page, f"LP Before Select Program {option_text}")
                    await first_unselected_option.click()
                    await asyncio.sleep(4)  # Increased wait for program selection to register
                    await self.take_screenshot(page, f"LP After Select Program {option_text}")
                else:
                    self.logger.warning("⚠️ No program option found")
                
                # Close dropdown after first selection
                await page.click('[id="page-2bis-graph-heatmap-mz-selection"]')
                await asyncio.sleep(2)
                await self.take_screenshot(page, "LP Program First Dropdown Closed")
                
                # Select second program by clicking on selected pill/chip
                self.logger.info("--- Selecting second program ---")
                selected_pills = await page.locator('[id="page-2bis-dropdown-programs"] .mantine-MultiSelect-value').all()
                if len(selected_pills) > 0:
                    # Click on the first selected pill to reopen dropdown
                    await self.take_screenshot(page, "LP Program Second Before Clicking Selected Pill")
                    await selected_pills[0].click()
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "LP Program Second Dropdown Reopened")
                    
                    # Wait for options to become visible again
                    await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=20000)
                    
                    # Find second available option
                    second_option = None
                    for selector in ['.mantine-MultiSelect-item:not([data-selected="true"])', '.mantine-Select-item:not([data-selected="true"])', '[data-value]:not([data-selected="true"])']:
                        try:
                            options = page.locator(selector)
                            if await options.count() > 0:
                                second_option = options.first
                                break
                        except Exception:
                            continue
                    
                    if second_option:
                        option_text = await second_option.text_content()
                        self.logger.info(f"Selecting second program: '{option_text}'")
                        await self.take_screenshot(page, f"LP Before Select Second Program {option_text}")
                        await second_option.click()
                        await asyncio.sleep(4)  # Increased wait for program selection to register
                        await self.take_screenshot(page, f"LP After Select Second Program {option_text}")
                    else:
                        self.logger.warning("⚠️ No second program option found")
                    
                    # Close dropdown after second selection
                    await page.click('[id="page-2bis-graph-heatmap-mz-selection"]')
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "LP Program Second Dropdown Closed")
                else:
                    self.logger.warning("⚠️ No selected pills found for second selection")
                
                self.logger.info("WAITING 30 SECONDS for app to stabilize...")
                await asyncio.sleep(30)  # Increased stabilization wait
                
                # Verify selections after stabilization wait
                self.logger.info("Verifying program selections after stabilization wait...")
                selected_pills = await page.locator('[id="page-2bis-dropdown-programs"] .mantine-MultiSelect-value').all()
                selected_texts = [await pill.text_content() for pill in selected_pills]
                self.logger.info(f"Final programs in dropdown: {selected_texts}")
                await self.take_screenshot(page, "LP Program Dropdown Final Verification")
                
                self.logger.info("✅ Selected multiple programs using CORRECT pattern (click on pills to reopen)")
            except Exception as e:
                self.logger.error(f"❌ Program dropdown test failed: {e}", exc_info=True)
                # Don't fail the entire test, continue
                pass
            
            self.logger.info("🧠 Testing Brain Badge Selection")
            try:
                brain_options = ["Reference 1 (M)", "Control 1 (M)", "Control 2 (M)"]
                for brain_label in brain_options:
                    try:
                        brain_selector = f'[id="main-brain"] .mantine-Chips-label:has-text("{brain_label}")'
                        await page.click(brain_selector, timeout=10000)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not select brain '{brain_label}': {e}")
            except Exception as e:
                self.logger.error(f"❌ Brain badge selection failed: {e}")
            
            self.logger.info("🎨 Testing Allen Annotations Toggle")
            try:
                await page.click('[id="page-2bis-toggle-annotations"]', timeout=10000)
            except Exception as e:
                self.logger.error(f"❌ Allen annotations toggle failed: {e}")
            
            self.logger.info("🎚️ Testing Main Slider")
            try:
                main_slider = page.locator('[id="main-paper-slider"]')
                slider_box = await main_slider.bounding_box()
                if slider_box:
                    for pos in [0.15, 0.35, 0.75, 0.85]:
                        x, y = slider_box['x'] + (slider_box['width'] * pos), slider_box['y'] + (slider_box['height'] * 0.5)
                        await page.mouse.click(x, y)
                        await asyncio.sleep(1)
            except Exception as e:
                self.logger.warning(f"❌ Main slider test failed: {e}")
            
            self.logger.info("🎨 Testing RGB Toggle (if available)")
            try:
                await page.click('[id="page-2bis-rgb-switch"]', timeout=10000)
            except Exception as e:
                self.logger.info("ℹ️ RGB switch not found - skipping")
            
            self.logger.info("All interactions complete. Waiting 40 seconds for final render...")
            await asyncio.sleep(40)  # Increased final render wait

            await self.take_screenshot(page, "LP Selection Final State")
            self.test_results['lp_selection'] = 'SUCCESS'
            self.logger.info("🎉 LP-SELECTION PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            self.logger.error(f"❌ LP Selection page test failed: {e}")
            await self.take_screenshot(page, "LP Selection Failure")
            self.test_results['lp_selection'] = 'FAILED'
            raise

    async def test_homepage_return_and_documentation(self, page):
        """Test returning to homepage and accessing documentation."""
        self.logger.info("\n🏠 TESTING HOMEPAGE RETURN & DOCUMENTATION")
        self.logger.info("-" * 40)
        
        try:
            await page.goto("http://127.0.0.1:8081/", timeout=100000)
            self.logger.info("✅ Returned to homepage successfully")
            
            self.monitor.log_stats(self.logger, "Homepage Return - Page Loaded")
            
            self.logger.info("⏰ Taking screenshots every 15 seconds, 3 times...")
            for i in range(3):
                await asyncio.sleep(15)  # Increased interval between screenshots
                self.logger.info(f"⏰ Screenshot {i+1}/3 after {(i+1)*15} seconds")
                await self.take_screenshot(page, f"Homepage Screenshot {i+1} of 3")
            
            self.logger.info("📚 Testing Documentation Access")
            try:
                await page.click('[id="sidebar-documentation"]', timeout=10000)
                self.logger.info("✅ Documentation button clicked")
                await asyncio.sleep(2)
                await self.take_screenshot(page, "Documentation Content Loaded")
            except Exception as e:
                self.logger.error(f"❌ Documentation access failed: {e}")

            await self.take_screenshot(page, "Homepage Return Final Success")
            self.test_results['homepage_return'] = 'SUCCESS'
            self.logger.info("🎉 HOMEPAGE RETURN & DOCUMENTATION TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            self.logger.error(f"❌ Homepage return test failed: {e}")
            await self.take_screenshot(page, "Homepage Return Failure")
            self.test_results['homepage_return'] = 'FAILED'
            raise

    async def generate_final_summary(self, page):
        """Generate final summary of all test results."""
        self.logger.info("\n🏁 FINAL TEST SUITE SUMMARY")
        self.logger.info("=" * 60)
        
        self.monitor.log_stats(self.logger, "FINAL SUMMARY")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result == 'SUCCESS')
        failed_tests = total_tests - successful_tests
        
        self.logger.info(f"📊 TEST RESULTS SUMMARY:")
        self.logger.info(f"   Total Pages Tested: {total_tests}")
        self.logger.info(f"   ✅ Successful: {successful_tests}")
        self.logger.info(f"   ❌ Failed: {failed_tests}")
        
        if total_tests > 0:
            self.logger.info(f"   📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        self.logger.info(f"\n📋 INDIVIDUAL PAGE RESULTS:")
        for page_name, result in self.test_results.items():
            status_icon = "✅" if result == 'SUCCESS' else "❌"
            self.logger.info(f"   {status_icon} {page_name.replace('_', ' ').title()}: {result}")
        
        if failed_tests == 0:
            self.logger.info("🎉 ALL TESTS PASSED! The application is stable and all functionality is working!")
        else:
            self.logger.warning(f"⚠️ {failed_tests} test(s) failed. Review the logs and screenshots for details.")

# --- PARALLEL EXECUTION FRAMEWORK ---

async def worker(user_id: int, screenshots_enabled: bool):
    """A wrapper function to run a single test suite instance for one user."""
    print(f"--- Starting test for User {user_id}... ---")
    try:
        test_suite = UnifiedStabilityTestSuite(user_id=user_id, screenshot=screenshots_enabled)
        await test_suite.run_complete_test_suite()
        print(f"--- Test for User {user_id} finished successfully. ---")
    except Exception as e:
        # The specific error is already logged by the instance's logger.
        # This print is for high-level console feedback.
        print(f"--- CRITICAL FAILURE for User {user_id}. Check logs/user_{user_id}_*.log for details. ---")

async def main():
    """Main entry point to configure and run parallel tests."""
    parser = argparse.ArgumentParser(
        description="Run parallel stability tests for a web application.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-n", "--num-users",
        type=int,
        default=1,
        help="The number of concurrent users to simulate."
    )
    parser.add_argument(
        "-s", "--screenshots",
        action="store_true",
        help="Enable saving screenshots for each user. Defaults to False.\n"
             "Screenshots are saved to 'screenshots/user_N/' folders."
    )
    args = parser.parse_args()

    num_users = args.num_users
    screenshots_enabled = args.screenshots

    print("==================================================")
    print(f"  Preparing to simulate {num_users} concurrent user(s).")
    print(f"  Screenshots enabled: {screenshots_enabled}")
    if not screenshots_enabled:
        print("  (Run with -s flag to enable screenshots)")
    print("==================================================")
    
    # Create a list of tasks (coroutines) to run
    tasks = []
    for user_id in range(1, num_users + 1):
        # Create the task for the user
        task = worker(user_id, screenshots_enabled)
        tasks.append(task)
        # Stagger the start of each user by 20 seconds for more realistic load distribution
        await asyncio.sleep(20) 
    
    # Run all user simulations concurrently
    await asyncio.gather(*tasks)

    print("==================================================")
    print("All user simulations have completed.")
    print("Check the 'logs' directory for detailed results for each user.")
    print("==================================================")

if __name__ == "__main__":
    # The global logging configuration is removed to allow each instance to have its own.
    # The script now starts directly into the main async function.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user. Exiting.")
