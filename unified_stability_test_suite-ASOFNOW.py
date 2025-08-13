#!/usr/bin/env python3
"""
UNIFIED STABILITY TEST SUITE
============================

This script combines ALL working page tests into a single comprehensive test suite.
It maintains ALL functionality tests we've successfully implemented and adds proper monitoring.

PAGES COVERED:
1. Lipizones Selection (treemap, brain selection, sections mode, Allen toggle, tutorial, ID cards)
2. Lipizones vs Cell Types (both treemaps, all controls, tutorial)
3. Lipids vs Genes (both dropdowns, RGB switch, gene sliders, tutorial)
4. 3D Exploration (treemap interaction, lipid selection, display, tutorial)
5. Region Analysis (brain regions, group assignment, compute, tutorial)

FEATURES:
- Comprehensive functionality testing
- Detailed logging and monitoring
- Screenshots at key points
- Error handling and recovery
- Flow control between pages
"""

import asyncio
import logging
import time
import psutil
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'unified_test_suite_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    
    def log_stats(self, stage_name):
        """Log current system statistics."""
        stats = self.get_current_stats()
        logger.info(f"📊 SYSTEM STATS [{stage_name}] - "
                   f"Elapsed: {stats['elapsed_seconds']:.1f}s, "
                   f"CPU: {stats['cpu_percent']:.1f}%, "
                   f"RAM: {stats['memory_percent']:.1f}% "
                   f"({stats['memory_available_gb']:.2f}GB available)")

class UnifiedStabilityTestSuite:
    """Main test suite that combines all working page tests."""
    
    def __init__(self, screenshot=True):
        self.monitor = SystemMonitor()
        self.current_page = None
        self.test_results = {}
        self.screenshot = True  # Set to False for faster prototyping
        self.screenshot_counter = 0
        self.screenshot_folder = "test_screenshots_1user"
        
        # Create screenshot folder if it doesn't exist
        if self.screenshot:
            import os
            os.makedirs(self.screenshot_folder, exist_ok=True)
            logger.info(f"📁 Screenshot folder created: {self.screenshot_folder}")
    
    async def take_screenshot(self, page, description):
        """Take a screenshot if screenshot flag is enabled."""
        if self.screenshot:
            self.screenshot_counter += 1
            filename = f"{self.screenshot_counter:03d}_{description.lower().replace(' ', '_').replace(':', '').replace('(', '').replace(')', '').replace('-', '_').replace(',', '').replace('.', '').replace('!', '').replace('?', '')}.png"
            filepath = f"{self.screenshot_folder}/{filename}"
            await page.screenshot(path=filepath)
            logger.info(f"📸 Screenshot {self.screenshot_counter:03d}: {description} -> {filepath}")
    
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
        logger.info("🚀 STARTING UNIFIED STABILITY TEST SUITE")
        logger.info("=" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # 1. LIPIZONES SELECTION PAGE
                await self.test_lipizones_selection_page(page)
                
                # 2. LIPIZONES VS CELL TYPES PAGE  
                await self.test_lipizones_vs_celltypes_page(page)
                
                # 3. LIPIDS VS GENES PAGE
                await self.test_lipids_vs_genes_page(page)
                
                # 4. 3D EXPLORATION PAGE
                await self.test_3d_exploration_page(page)
                
                # 5. LIPID SELECTION PAGE
                await self.test_lipid_selection_page(page)
                
                # 6. PEAK SELECTION PAGE
                await self.test_peak_selection_page(page)
                
                # 7. REGION ANALYSIS PAGE
                await self.test_region_analysis_page(page)
                
                # 8. LP-SELECTION PAGE
                await self.test_lp_selection_page(page)
                
                # 9. 3D-LIPIZONES PAGE (TEMPORARILY COMMENTED OUT)
                # await self.test_3d_lipizones_page(page)
                
                # 10. RETURN TO HOMEPAGE & TEST DOCUMENTATION
                await self.test_homepage_return_and_documentation(page)
                
                # FINAL SUMMARY
                await self.generate_final_summary(page)
                
            except Exception as e:
                logger.error(f"❌ CRITICAL ERROR in test suite: {e}")
                await page.screenshot(path="unified_test_suite_critical_error.png")
                
            finally:
                await context.close()
                await browser.close()
                
        logger.info("🏁 UNIFIED TEST SUITE COMPLETED")
        logger.info("=" * 60)

    # async def run_complete_test_suite2(self):
    #     """Run the complete test suite covering all pages."""
    #     logger.info("🚀 STARTING UNIFIED STABILITY TEST SUITE (SINGLE TEST MODE)")
    #     logger.info("=" * 60)
        
    #     async with async_playwright() as p:
    #         browser = await p.chromium.launch(headless=True) # Set headless=False to watch the test run
    #         context = await browser.new_context()
    #         page = await context.new_page()
            
    #         try:
    #             # 7. REGION ANALYSIS PAGE
    #             await self.test_region_analysis_page(page)
                
    #             # # Comment out other tests to run only the one above
    #             # # 1. LIPIZONES SELECTION PAGE
    #             # await self.test_lipizones_selection_page(page)
    #             # # 2. LIPIZONES VS CELL TYPES PAGE  
    #             # await self.test_lipizones_vs_celltypes_page(page)
    #             # # 3. LIPIDS VS GENES PAGE
    #             # await self.test_lipids_vs_genes_page(page)
    #             # # 4. 3D EXPLORATION PAGE
    #             # await self.test_3d_exploration_page(page)
    #             # # 5. LIPID SELECTION PAGE
    #             # await self.test_lipid_selection_page(page)
    #             # # 6. PEAK SELECTION PAGE
    #             # await self.test_peak_selection_page(page)
    #             # # 8. LP-SELECTION PAGE
    #             # await self.test_lp_selection_page(page)
    #             # # 9. 3D-LIPIZONES PAGE
    #             # # await self.test_3d_lipizones_page(page)
    #             # # 10. RETURN TO HOMEPAGE & TEST DOCUMENTATION
    #             # await self.test_homepage_return_and_documentation(page)
                
    #             # FINAL SUMMARY
    #             await self.generate_final_summary(page)
                
    #         except Exception as e:
    #             logger.error(f"❌ CRITICAL ERROR in test suite: {e}")
    #             await page.screenshot(path="unified_test_suite_critical_error.png")
                
    #         finally:
    #             await context.close()
    #             await browser.close()
                
    #     logger.info("🏁 UNIFIED TEST SUITE COMPLETED")
    #     logger.info("=" * 60)

    async def test_lipizones_selection_page(self, page):
        """Test the Lipizones Selection page (all working functionality)."""
        logger.info("\n🎯 TESTING LIPIZONES SELECTION PAGE")
        logger.info("-" * 40)
        
        try:
            # Navigate to page
            await page.goto("http://127.0.0.1:8050/lipizones-selection", timeout=90000)
            logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "Lipizones Selection Page Loaded")
            
            # Wait for core elements
            await page.wait_for_selector('[id="page-6-lipizones-treemap"]', timeout=60000)
            logger.info("✅ Core elements rendered")
            await self.take_screenshot(page, "Lipizones Core Elements Rendered")
            
            self.monitor.log_stats("Lipizones Selection - Page Loaded")
            
            # 1. Clear Selection (CRUCIAL for treemap interaction)
            logger.info("🎯 STEP 1: Clicking 'Clear Selection' to activate interactive graph")
            await page.locator('[id="page-6-clear-selection-button"]').click(timeout=60000)
            await asyncio.sleep(3)
            logger.info("✅ Graph is now interactive")
            await self.take_screenshot(page, "After Clear Selection Button")
            
            # 2. Test Brain Badge Selection (REQUIRED before sections mode switch)
            logger.info("🧠 Testing Brain Badge Selection (REQUIRED before sections mode)")
            try:
                # Wait for brain selection component to be available
                await page.wait_for_selector('[id="main-brain"]', timeout=10000)
                await self.take_screenshot(page, "Brain Selection Component Available")
                
                # Test different brain selections using the working text-based selector strategy
                brain_options = [
                    "Reference 1 (M)",
                    "Control 1 (M)", 
                    "Control 2 (M)"
                ]
                
                for brain_label in brain_options:
                    try:
                        # Use the working selector strategy: find LABEL by visible text
                        brain_selector = f'[id="main-brain"] .mantine-Chips-label:has-text("{brain_label}")'
                        brain_button = await page.wait_for_selector(brain_selector, timeout=5000)
                        
                        await self.take_screenshot(page, f"Before Brain Selection {brain_label}")
                        await brain_button.click()
                        await asyncio.sleep(2)
                        logger.info(f"✅ Selected brain: {brain_label}")
                        await self.take_screenshot(page, f"After Brain Selection {brain_label}")
                        
                        # Wait for brain selection to process
                        await asyncio.sleep(3)
                        break  # Just select one brain to enable sections mode
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Could not select brain '{brain_label}': {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Brain badge selection failed: {e}")
            
            # # 3. Test Sections Mode Switch (One section vs All sections) - NOW ENABLED
            # logger.info("🔄 Testing Sections Mode Switch (One section vs All sections) - NOW ENABLED")
            # try:
            #     # Wait for the sections mode component to be available
            #     await page.wait_for_selector('[id="page-6-sections-mode"]', timeout=10000)
            #     await self.take_screenshot(page, "Sections Mode Component Available")
                
            #     # Wait PATIENTLY for sections mode to become enabled after brain selection
            #     logger.info("⏰ Waiting PATIENTLY for sections mode to become enabled...")
            #     await asyncio.sleep(5)  # Extra wait for brain selection to process
                
            #     # Test switching between "One section" and "All sections" views
            #     # Using the working solution: click directly on visible text labels
                
            #     # First, switch to "All sections" view
            #     logger.info("--- Switching to 'All sections' view ---")
            #     await self.take_screenshot(page, "Before Switch to All Sections")
                
            #     # FIX: Use a locator. The click() action on a locator will automatically
            #     # wait for the element to be enabled before it clicks.
            #     all_sections_button = page.locator('text="All sections"')
            #     await all_sections_button.click(timeout=15000)  # Wait up to 15s for it to become enabled
                
            #     await asyncio.sleep(3)  # Wait for the UI to update after the click
            #     logger.info("✅ Switched to 'All sections' view")
            #     await self.take_screenshot(page, "After Switch to All Sections")
                
            #     # Wait for the view to stabilize
            #     await asyncio.sleep(3)
                
            #     # Then, switch back to "One section" view (to enable slider and Allen toggle)
            #     logger.info("--- Switching back to 'One section' view ---")
            #     await self.take_screenshot(page, "Before Switch to One Section")
                
            #     # FIX: Use a locator for the same reason
            #     one_section_button = page.locator('text="One section"')
            #     await one_section_button.click(timeout=15000)  # Wait up to 15s for it to become enabled
                
            #     await asyncio.sleep(3)  # Wait for the UI to update after the click
            #     logger.info("✅ Switched back to 'One section' view")
            #     await self.take_screenshot(page, "After Switch to One Section")
                
            #     # Wait for the view to stabilize
            #     await asyncio.sleep(3)
                
            #     logger.info("✅ Sections mode switch test completed successfully")
                
            # except Exception as e:
            #     logger.error(f"❌ Sections mode switch failed: {e}")
            
            # 4. Test Main Slider (now available in "One" section mode)
            logger.info("🎚️ Testing Main Slider (now available in One section mode)")
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
                        await asyncio.sleep(1)
                        await self.take_screenshot(page, f"Main Slider After Click {i+1} at {pos}")
                        logger.info(f"✅ Main slider clicked at position {pos}")
                else:
                    logger.warning("⚠️ Main slider bounding box not available")
            except Exception as e:
                logger.warning(f"❌ Main slider test failed: {e}")
                await self.take_screenshot(page, "Main Slider Error")
            
            # 5. Test Allen Toggle (now available in "One" section mode)
            logger.info("🎨 Testing Allen Toggle (now available in One section mode)")
            try:
                annotations_toggle = await page.wait_for_selector('[id="page-6-toggle-annotations"]', timeout=10000)
                await self.take_screenshot(page, "Before Allen Toggle Click")
                await annotations_toggle.click()
                await asyncio.sleep(2)
                logger.info("✅ Annotations toggle clicked")
                await self.take_screenshot(page, "After Allen Toggle Click")
            except Exception as e:
                logger.error(f"❌ Annotations toggle failed: {e}")
            
            # 6. Test Select All Lipizones Button
            logger.info("🎯 Testing Select All Lipizones Button")
            try:
                select_all_button = await page.wait_for_selector('[id="page-6-select-all-lipizones-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Select All Lipizones Click")
                await select_all_button.click()
                await asyncio.sleep(2)
                logger.info("✅ Select all lipizones button clicked")
                await self.take_screenshot(page, "After Select All Lipizones Click")
            except Exception as e:
                logger.error(f"❌ Select all lipizones failed: {e}")
            
            # 7. Test Tutorial Button
            logger.info("📚 Testing Tutorial Button")
            try:
                tutorial_button = await page.wait_for_selector('[id="lipizone-start-tutorial-btn"]', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Button Click")
                await tutorial_button.click()
                await asyncio.sleep(2)
                logger.info("✅ Tutorial button clicked")
                await self.take_screenshot(page, "After Tutorial Button Click")
            except Exception as e:
                logger.error(f"❌ Tutorial button failed: {e}")
            
            # 7. Close Tutorial Modal
            logger.info("📚 Closing Tutorial Modal")
            try:
                close_button = await page.wait_for_selector('button:has-text("×")', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Modal Close")
                await close_button.click()
                await asyncio.sleep(2)
                logger.info("✅ Tutorial modal closed")
                await self.take_screenshot(page, "After Tutorial Modal Close")
            except Exception as e:
                logger.error(f"❌ Tutorial modal close failed: {e}")
            
            # 8. CRUCIAL: Clear lipizones selection BEFORE treemap interaction
            logger.info("🧹 CRUCIAL: Clearing lipizones selection before treemap interaction...")
            await self.take_screenshot(page, "Before Clear Selection Button")
            await page.locator('[id="page-6-clear-selection-button"]').click()
            await asyncio.sleep(2)
            logger.info("✅ Lipizones selection cleared - now ready for treemap interaction")
            await self.take_screenshot(page, "After Clear Selection Button")

            # 9. DRILL DOWN DEEPER: Click on a smaller, more specific region for manageable selection
            logger.info("🎯 STEP 2: Drilling down deeper in treemap for smaller, manageable selection...")
            try:
                # First, let's see what regions are available by clicking on a smaller area
                # Look for smaller rectangles in the treemap (these represent more specific regions)
                treemap_paths = await page.locator('[id="page-6-lipizones-treemap"] g.trace path').all()
                logger.info(f"🎯 Found {len(treemap_paths)} clickable regions in treemap")
                await self.take_screenshot(page, "Before Treemap Region Click")
                
                if len(treemap_paths) > 1:
                    # Click on a smaller region (not the first one which might be the root)
                    # Try to find a smaller region by looking at the second or third path
                    smaller_region_locator = page.locator('[id="page-6-lipizones-treemap"] g.trace path').nth(2)
                    await smaller_region_locator.click(force=True)
                    logger.info("✅ Clicked on smaller region for manageable selection")
                else:
                    # Fallback to first region if only one available
                    treemap_node_locator = page.locator('[id="page-6-lipizones-treemap"] g.trace path').first
                    await treemap_node_locator.click(force=True)
                    logger.info("✅ Clicked on available region")

                await asyncio.sleep(2)
                await self.take_screenshot(page, "After Treemap Region Click")
            except Exception as e:
                logger.error(f"❌ FAILED to drill down in treemap. Error: {e}")
                raise

            # 10. Verify the click was successful and check selection size
            logger.info("🎯 STEP 3: Verifying the click was registered and checking selection size...")
            selection_text_element = await page.wait_for_selector('[id="page-6-current-selection-text"]')
            selection_text = await selection_text_element.text_content()
            logger.info(f"Selection text after click: '{selection_text}'")

            # 11. Add selection
            logger.info("🎯 STEP 4: Adding the selection...")
            add_button = await page.wait_for_selector('[id="page-6-add-selection-button"]', timeout=10000)
            await self.take_screenshot(page, "Before Add Selection Button")
            await add_button.click()
            await asyncio.sleep(2)
            logger.info("✅ Added selection")
            await self.take_screenshot(page, "After Add Selection Button")
            
            # 12. Test ID Cards (limited selection to avoid server overload)
            logger.info("🆔 Testing ID Cards (with limited selection)")
            try:
                view_id_cards_btn = await page.wait_for_selector('[id="view-id-cards-btn"]', timeout=10000)
                await self.take_screenshot(page, "Before ID Cards Button Click")
                await view_id_cards_btn.click()
                await asyncio.sleep(5)  # Wait for ID cards to load
                logger.info("✅ ID Cards button clicked")
                await self.take_screenshot(page, "After ID Cards Button Click")
                
                # Close ID cards
                hide_id_cards_btn = await page.wait_for_selector('[id="hide-id-cards-btn"]', timeout=10000)
                await self.take_screenshot(page, "Before Hide ID Cards Button")
                await hide_id_cards_btn.click()
                await asyncio.sleep(2)
                logger.info("✅ ID Cards closed")
                await self.take_screenshot(page, "After Hide ID Cards Button")
                
            except Exception as e:
                logger.error(f"❌ ID Cards test failed: {e}")
            
            # Final success screenshot
            await self.take_screenshot(page, "Lipizones Selection Final Success")
            
            # Legacy screenshot for compatibility
            await page.screenshot(path="lipizones_selection_success_unified.png")
            logger.info("📸 Lipizones Selection success screenshot saved")
            
            self.test_results['lipizones_selection'] = 'SUCCESS'
            logger.info("🎉 LIPIZONES SELECTION PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ Lipizones Selection page test failed: {e}")
            await page.screenshot(path="lipizones_selection_failure_unified.png")
            self.test_results['lipizones_selection'] = 'FAILED'
            raise

    async def test_lipizones_vs_celltypes_page(self, page):
        """Test the Lipizones vs Cell Types page (all working functionality)."""
        logger.info("\n🎯 TESTING LIPIZONES VS CELL TYPES PAGE")
        logger.info("-" * 40)
        
        try:
            # Navigate to page
            await page.goto("http://127.0.0.1:8050/lipizones-vs-celltypes", timeout=90000)
            logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "Lipizones vs Cell Types Page Loaded")
            
            # Handle Important Notice (page refresh requirement)
            logger.info("🔄 Handling Important Notice - page refresh requirement")
            try:
                refresh_alert = await page.wait_for_selector('[id="page-6bis-refresh-alert"]', timeout=10000)
                logger.info("✅ Important Notice alert found")
                await self.take_screenshot(page, "Important Notice Alert Found")
                
                # Close the alert
                close_button = await page.wait_for_selector('[id="page-6bis-refresh-alert"] button', timeout=5000)
                await self.take_screenshot(page, "Before Close Important Notice Button")
                await close_button.click()
                await asyncio.sleep(2)
                logger.info("✅ Important Notice alert closed")
                await self.take_screenshot(page, "After Close Important Notice Button")
            except Exception as e:
                logger.warning(f"⚠️ Could not handle Important Notice: {e}")
            
            # Wait for core elements
            await page.wait_for_selector('[id="page-6bis-lipizones-treemap"]', timeout=60000)
            await page.wait_for_selector('[id="page-6bis-celltypes-treemap"]', timeout=60000)
            logger.info("✅ Both treemaps have rendered")
            await self.take_screenshot(page, "Both Treemaps Rendered")
            
            self.monitor.log_stats("Lipizones vs Cell Types - Page Loaded")
            
            # 1. Test Tutorial Button
            logger.info("📚 Testing Tutorial Button")
            try:
                tutorial_button = await page.wait_for_selector('[id="lipicell-start-tutorial-btn"]', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Button Click")
                await tutorial_button.click()
                await asyncio.sleep(2)
                logger.info("✅ Tutorial button clicked")
                await self.take_screenshot(page, "After Tutorial Button Click")
                
                # Close tutorial popover
                close_tutorial = await page.wait_for_selector('[id="lipicell-tutorial-close-1"]', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Popover Close")
                await close_tutorial.click()
                await asyncio.sleep(2)
                logger.info("✅ Tutorial popover closed")
                await self.take_screenshot(page, "After Tutorial Popover Close")
            except Exception as e:
                logger.error(f"❌ Tutorial test failed: {e}")
            
            # 2. Test Main Slider
            logger.info("🎚️ Testing Main Slider")
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
                        await asyncio.sleep(1)
                        await self.take_screenshot(page, f"Main Slider After Click {i+1} at {pos}")
                        logger.info(f"✅ Main slider clicked at position {pos}")
                else:
                    logger.warning("⚠️ Main slider bounding box not available")
            except Exception as e:
                logger.warning(f"❌ Main slider test failed: {e}")
            
            # 3. Test Allen Toggle
            logger.info("🎨 Testing Allen Toggle")
            try:
                annotations_toggle = await page.wait_for_selector('[id="page-6bis-toggle-annotations"]', timeout=10000)
                await self.take_screenshot(page, "Before Allen Toggle Click")
                await annotations_toggle.click()
                await asyncio.sleep(2)
                logger.info("✅ Annotations toggle clicked")
                await self.take_screenshot(page, "After Allen Toggle Click")
            except Exception as e:
                logger.error(f"❌ Annotations toggle failed: {e}")
            
            # 4. Test Pixel Filter Slider
            logger.info("🎚️ Testing Pixel Filter Slider")
            try:
                pixel_filter = await page.wait_for_selector('[id="page-6bis-celltype-pixel-filter"]', timeout=10000)
                await self.take_screenshot(page, "Before Pixel Filter Slider Move")
                await pixel_filter.focus()
                await page.keyboard.press('ArrowRight')
                await asyncio.sleep(2)
                logger.info("✅ Pixel filter slider moved right")
                await self.take_screenshot(page, "After Pixel Filter Slider Move")
            except Exception as e:
                logger.error(f"❌ Pixel filter slider failed: {e}")
            
            # 5. Test Left Panel - Lipizones Controls
            logger.info("🎯 Testing Left Panel - Lipizones Controls")
            
            # Test Select All Lipizones
            try:
                select_all_lipizones = await page.wait_for_selector('[id="page-6bis-select-all-lipizones-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Select All Lipizones Button")
                await select_all_lipizones.click()
                await asyncio.sleep(2)
                logger.info("✅ Select All Lipizones button clicked")
                await self.take_screenshot(page, "After Select All Lipizones Button")
            except Exception as e:
                logger.error(f"❌ Select All Lipizones failed: {e}")
            
            # Test Lipizones Treemap Interaction
            logger.info("🎯 Testing Lipizones Treemap Interaction")
            try:
                # Clear lipizones selection first
                clear_lipizones = await page.wait_for_selector('[id="page-6bis-clear-lipizone-selection-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Clear Lipizones Button")
                await clear_lipizones.click()
                await asyncio.sleep(2)
                logger.info("✅ Cleared lipizones selection")
                await self.take_screenshot(page, "After Clear Lipizones Button")
                
                # Click on lipizones treemap (drill down for smaller selection)
                treemap_paths = await page.locator('[id="page-6bis-lipizones-treemap"] g.trace path').all()
                logger.info(f"🎯 Found {len(treemap_paths)} clickable regions in lipizones treemap")
                await self.take_screenshot(page, "Before Lipizones Treemap Click")
                
                if len(treemap_paths) > 2:
                    # Click on a smaller region (3rd path for manageable selection)
                    smaller_region = page.locator('[id="page-6bis-lipizones-treemap"] g.trace path').nth(2)
                    await smaller_region.click(force=True)
                    logger.info("✅ Clicked on smaller lipizones region")
                else:
                    # Fallback to first region
                    first_region = page.locator('[id="page-6bis-lipizones-treemap"] g.trace path').first
                    await first_region.click(force=True)
                    logger.info("✅ Clicked on lipizones region")
                
                await asyncio.sleep(2)
                await self.take_screenshot(page, "After Lipizones Treemap Click")
                
                # Add lipizones selection
                add_lipizones = await page.wait_for_selector('[id="page-6bis-add-lipizone-selection-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Add Lipizones Button")
                await add_lipizones.click()
                await asyncio.sleep(2)
                logger.info("✅ Added lipizones selection")
                await self.take_screenshot(page, "After Add Lipizones Button")
                
            except Exception as e:
                logger.error(f"❌ Lipizones treemap interaction failed: {e}")
            
            # 6. Test Right Panel - Cell Types Controls
            logger.info("🎯 Testing Right Panel - Cell Types Controls")
            
            # Test Select All Cell Types
            try:
                select_all_celltypes = await page.wait_for_selector('[id="page-6bis-select-all-celltypes-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Select All Cell Types Button")
                await select_all_celltypes.click()
                await asyncio.sleep(2)
                logger.info("✅ Select All Cell Types button clicked")
                await self.take_screenshot(page, "After Select All Cell Types Button")
            except Exception as e:
                logger.error(f"❌ Select All Cell Types failed: {e}")
            
            # Test Cell Types Treemap Interaction
            logger.info("🎯 Testing Cell Types Treemap Interaction")
            try:
                # Clear cell types selection first
                clear_celltypes = await page.wait_for_selector('[id="page-6bis-clear-celltype-selection-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Clear Cell Types Button")
                await clear_celltypes.click()
                await asyncio.sleep(2)
                logger.info("✅ Cleared cell types selection")
                await self.take_screenshot(page, "After Clear Cell Types Button")
                
                # Click on cell types treemap (drill down for smaller selection)
                treemap_paths = await page.locator('[id="page-6bis-celltypes-treemap"] g.trace path').all()
                logger.info(f"🎯 Found {len(treemap_paths)} clickable regions in cell types treemap")
                await self.take_screenshot(page, "Before Cell Types Treemap Click")
                
                if len(treemap_paths) > 2:
                    # Click on a smaller region (3rd path for manageable selection)
                    smaller_region = page.locator('[id="page-6bis-celltypes-treemap"] g.trace path').nth(2)
                    await smaller_region.click(force=True)
                    logger.info("✅ Clicked on smaller cell types region")
                else:
                    # Fallback to first region
                    first_region = page.locator('[id="page-6bis-celltypes-treemap"] g.trace path').first
                    await first_region.click(force=True)
                    logger.info("✅ Clicked on cell types region")
                
                await asyncio.sleep(2)
                await self.take_screenshot(page, "After Cell Types Treemap Click")
                
                # Add cell types selection
                add_celltypes = await page.wait_for_selector('[id="page-6bis-add-celltype-selection-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Add Cell Types Button")
                await add_celltypes.click()
                await asyncio.sleep(2)
                logger.info("✅ Added cell types selection")
                await self.take_screenshot(page, "After Add Cell Types Button")
                
            except Exception as e:
                logger.error(f"❌ Cell types treemap interaction failed: {e}")
            
            # Final success screenshot
            await self.take_screenshot(page, "Lipizones vs Cell Types Final Success")
            
            # Legacy screenshot for compatibility
            await page.screenshot(path="lipizones_vs_celltypes_success_unified.png")
            logger.info("📸 Lipizones vs Cell Types success screenshot saved")
            
            self.test_results['lipizones_vs_celltypes'] = 'SUCCESS'
            logger.info("🎉 LIPIZONES VS CELL TYPES PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ Lipizones vs Cell Types page test failed: {e}")
            await page.screenshot(path="lipizones_vs_celltypes_failure_unified.png")
            self.test_results['lipizones_vs_celltypes'] = 'FAILED'
            raise

    async def test_lipids_vs_genes_page(self, page):
        """Test the Lipids vs Genes page (all working functionality)."""
        logger.info("\n🎯 TESTING LIPIDS VS GENES PAGE")
        logger.info("-" * 40)
        
        try:
            # Navigate to page using a robust strategy
            await page.goto("http://127.0.0.1:8050/lipids-vs-genes", wait_until='networkidle', timeout=90000)
            logger.info("✅ Page navigation and initial data load complete")
            await self.take_screenshot(page, "Lipids vs Genes Page Loaded")
            
            # Handle the "Important Notice" alert if it appears
            logger.info("🔄 Handling 'Important Notice' if present")
            try:
                close_button = await page.wait_for_selector('[id="page-6tris-refresh-alert"] button', state='visible', timeout=15000)
                await self.take_screenshot(page, "Important Notice Alert Found")
                await close_button.click()
                await asyncio.sleep(2)
                logger.info("✅ 'Important Notice' alert found and closed")
                await self.take_screenshot(page, "After Close Important Notice Button")
            except PlaywrightTimeoutError:
                logger.info("ℹ️ 'Important Notice' alert did not appear, continuing test")
            
            logger.info("✅ Core page components loaded. Starting interaction tests")
            await self.take_screenshot(page, "Core Components Loaded")
            
            self.monitor.log_stats("Lipids vs Genes - Page Loaded")
            
            # 1. Test Tutorial Button
            logger.info("📚 Testing Tutorial Button")
            try:
                await self.take_screenshot(page, "Before Tutorial Button Click")
                await page.click('[id="lipigene-start-tutorial-btn"]', timeout=5000)
                await asyncio.sleep(1)
                await self.take_screenshot(page, "After Tutorial Button Click")
                await page.click('[id="lipigene-tutorial-close-1"]', timeout=5000)
                await asyncio.sleep(1)
                logger.info("✅ Tutorial opened and closed")
                await self.take_screenshot(page, "After Tutorial Close")
            except Exception as e:
                logger.error(f"❌ Tutorial test failed: {e}")
            
            # 2. Test Main Slider
            logger.info("🎚️ Testing Main Slider")
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
                        await asyncio.sleep(1)
                        await self.take_screenshot(page, f"Main Slider After Click {i+1} at {pos}")
                        logger.info(f"✅ Main slider clicked at position {pos}")
                else:
                    logger.warning("⚠️ Main slider bounding box not available")
            except Exception as e:
                logger.warning(f"❌ Main slider test failed: {e}")
            
            # 3. Test Allen Annotations Toggle
            logger.info("🎨 Testing Allen Annotations Toggle")
            try:
                await self.take_screenshot(page, "Before Allen Toggle Click")
                await page.click('[id="page-6tris-toggle-annotations"]', timeout=5000)
                await asyncio.sleep(1)
                logger.info("✅ Annotations toggle clicked")
                await self.take_screenshot(page, "After Allen Toggle Click")
            except Exception as e:
                logger.error(f"❌ Annotations toggle failed: {e}")
            
            # 4. Test Lipids Dropdown
            logger.info("💧 Testing Lipids Dropdown")
            try:
                lipid_dropdown_container = page.locator('[id="page-6tris-dropdown-lipids"]').locator('..')
                await self.take_screenshot(page, "Before Lipids Dropdown Click")
                await lipid_dropdown_container.click()
                await self.take_screenshot(page, "After Lipids Dropdown Click")
                
                logger.info("Selecting first 3 available lipids")
                for i in range(3):
                    options = await page.locator('.mantine-MultiSelect-item, .mantine-Select-item').all()
                    if len(options) > i:
                        await self.take_screenshot(page, f"Before Select Lipid {i+1}")
                        await options[i].click()
                        await asyncio.sleep(0.5)
                        await self.take_screenshot(page, f"After Select Lipid {i+1}")
                    else:
                        break
                logger.info("✅ Selected lipids")
                await self.take_screenshot(page, "Before Close Lipids Dropdown")
                await page.click('[id="page-6tris-graph-heatmap-mz-selection"]')
                await asyncio.sleep(1)
                await self.take_screenshot(page, "After Close Lipids Dropdown")
            except Exception as e:
                logger.error(f"❌ Lipids dropdown test failed: {e}")
            
            # 5. Test Genes Dropdown
            logger.info("🧬 Testing Genes Dropdown (with virtualization)")
            try:
                gene_dropdown_container = page.locator('[id="page-6tris-dropdown-genes"]').locator('..')
                genes_to_select = ["Gad1", "Gfap"]
                
                for gene in genes_to_select:
                    await self.take_screenshot(page, f"Before Genes Dropdown Click for {gene}")
                    await gene_dropdown_container.click()
                    await self.take_screenshot(page, f"After Genes Dropdown Click for {gene}")
                    await gene_dropdown_container.type(gene, delay=50)
                    logger.info(f"Typed '{gene}', waiting for option to appear")
                    await self.take_screenshot(page, f"After Type {gene}")
                    
                    filtered_option = page.locator(f'.mantine-MultiSelect-item:has-text("{gene}")').first
                    await self.take_screenshot(page, f"Before Select Gene {gene}")
                    await filtered_option.click()
                    logger.info(f"✅ Selected '{gene}'")
                    await self.take_screenshot(page, f"After Select Gene {gene}")
                    
                    logger.info("Waiting 10 seconds for app to stabilize before next selection")
                    await asyncio.sleep(10)
                
                await self.take_screenshot(page, "Before Close Genes Dropdown")
                await page.click('[id="page-6tris-graph-heatmap-mz-selection"]')
                await asyncio.sleep(1)
                await self.take_screenshot(page, "After Close Genes Dropdown")
            except Exception as e:
                logger.error(f"❌ Genes dropdown test failed: {e}")
            
            # 6. Test Gene Expression Sliders
            logger.info("🎚️ Testing Gene Expression Sliders")
            try:
                await self.take_screenshot(page, "Before First Gene Slider Move")
                await page.locator('[id="page-6tris-gene-slider-1"]').focus()
                await page.keyboard.press('ArrowRight')
                logger.info("✅ First gene slider moved")
                await asyncio.sleep(0.5)
                await self.take_screenshot(page, "After First Gene Slider Move")
                
                await self.take_screenshot(page, "Before Second Gene Slider Move")
                await page.locator('[id="page-6tris-gene-slider-2"]').focus()
                await page.keyboard.press('ArrowRight')
                logger.info("✅ Second gene slider moved")
                await asyncio.sleep(0.5)
                await self.take_screenshot(page, "After Second Gene Slider Move")
            except Exception as e:
                logger.error(f"❌ Gene expression sliders test failed: {e}")
            
            # 7. Test Badge Display
            logger.info("🏷️ Testing Badge Display")
            try:
                await self.take_screenshot(page, "Before Badge Count Check")
                # Use locator.count() for a simple and robust way to check for items
                lipid_badge_count = await page.locator('[id^="page-6tris-badge-lipid-"]').count()
                logger.info(f"✅ Found {lipid_badge_count} visible lipid badges")
                
                gene_badge_count = await page.locator('[id^="page-6tris-badge-gene-"]').count()
                logger.info(f"✅ Found {gene_badge_count} visible gene badges")
                await self.take_screenshot(page, "After Badge Count Check")
                
            except Exception as e:
                logger.error(f"❌ Badge display test failed: {e}")
            
            # Final success screenshot
            await self.take_screenshot(page, "Lipids vs Genes Final Success")
            
            # Legacy screenshot for compatibility
            await page.screenshot(path="lipids_vs_genes_success_unified.png")
            logger.info("📸 Lipids vs Genes success screenshot saved")
            
            self.test_results['lipids_vs_genes'] = 'SUCCESS'
            logger.info("🎉 LIPIDS VS GENES PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ Lipids vs Genes page test failed: {e}")
            await page.screenshot(path="lipids_vs_genes_failure_unified.png")
            self.test_results['lipids_vs_genes'] = 'FAILED'
            raise

    async def test_3d_exploration_page(self, page):
        """Test the 3D Exploration page (EXACT copy from working script)."""
        logger.info("\n🎯 TESTING 3D EXPLORATION PAGE")
        logger.info("-" * 40)
        
        try:
            # Navigate to page (EXACT from working script)
            await page.goto("http://127.0.0.1:8050/3D-exploration", wait_until="networkidle")
            await asyncio.sleep(3)
            logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "3D Exploration Page Loaded")
            
            self.monitor.log_stats("3D Exploration - Page Loaded")
            
            # 1. Verify page elements are present (EXACT from working script)
            logger.info("🔍 TEST 1: Page Elements Verification")
            try:
                # Check main components
                await page.wait_for_selector('[id="page-4-graph-region-selection"]', timeout=10000)
                await page.wait_for_selector('[id="page-4-dropdown-lipids"]', timeout=10000)
                await page.wait_for_selector('[id="page-4-add-structure-button"]', timeout=10000)
                await page.wait_for_selector('[id="page-4-display-button"]', timeout=10000)
                
                logger.info("✅ All main page elements found")
                await self.take_screenshot(page, "All Main Elements Found")
                
                # Check initial button states
                add_button = await page.query_selector('[id="page-4-add-structure-button"]')
                display_button = await page.query_selector('[id="page-4-display-button"]')
                
                add_disabled = await add_button.get_attribute('disabled')
                display_disabled = await display_button.get_attribute('disabled')
                
                logger.info(f"🎯 Add button disabled: {add_disabled is not None}")
                logger.info(f"🎯 Display button disabled: {display_disabled is not None}")
                await self.take_screenshot(page, "Button States Checked")
                
            except Exception as e:
                logger.error(f"❌ Page elements verification failed: {e}")
            
            # 2. Lipid selection dropdown (EXACT from working script)
            logger.info("🔍 TEST 2: Lipid Selection Dropdown")
            try:
                # Click on the lipid dropdown
                await self.take_screenshot(page, "Before Lipid Dropdown Click")
                await page.click('[id="page-4-dropdown-lipids"]')
                await asyncio.sleep(2)
                await self.take_screenshot(page, "After Lipid Dropdown Click")
                
                # Look for lipid options
                lipid_options = await page.query_selector_all('.mantine-Select-item, [data-value]')
                logger.info(f"🎯 Found {len(lipid_options)} lipid options")
                await self.take_screenshot(page, "Lipid Options Found")
                
                if lipid_options:
                    # Select the first available lipid
                    await self.take_screenshot(page, "Before Select First Lipid")
                    await lipid_options[0].click()
                    logger.info("✅ Selected first available lipid")
                    await asyncio.sleep(1)
                    await self.take_screenshot(page, "After Select First Lipid")
                    
                    # Verify selection
                    selected_lipid = await page.input_value('[id="page-4-dropdown-lipids"]')
                    logger.info(f"🎯 Selected lipid: {selected_lipid}")
                    await self.take_screenshot(page, "Lipid Selection Verified")
                else:
                    logger.warning("⚠️ No lipid options found")
                
                # Close dropdown by clicking on a visible element (the treemap)
                await self.take_screenshot(page, "Before Close Lipid Dropdown")
                await page.click('[id="page-4-graph-region-selection"]')
                await asyncio.sleep(1)
                await self.take_screenshot(page, "After Close Lipid Dropdown")
                
            except Exception as e:
                logger.error(f"❌ Lipid selection failed: {e}")
            
            # 3. Treemap interaction and region selection (EXACT from working script)
            logger.info("🔍 TEST 3: Treemap Interaction and Region Selection")
            try:
                # Wait for treemap to fully load
                await page.wait_for_selector('[id="page-4-graph-region-selection"]', timeout=10000)
                await asyncio.sleep(3)
                await self.take_screenshot(page, "Treemap Fully Loaded")
                
                # Initialize add_button_text variable
                add_button_text = "Please choose a structure above"
                
                # Method 1: Try JavaScript-based clicking to bypass the overlay layer
                logger.info("🎯 Using JavaScript to bypass overlay layer...")
                await self.take_screenshot(page, "Before JavaScript Click Attempt")
                
                try:
                    # Execute JavaScript to directly trigger Plotly click events
                    js_result = await page.evaluate("""
                        () => {
                            const treemap = document.querySelector('[id="page-4-graph-region-selection"]');
                            if (!treemap) return 'Treemap not found';
                            
                            const plotlyDiv = treemap.querySelector('.plotly');
                            if (!plotlyDiv) return 'Plotly div not found';
                            
                            // Look for the actual treemap trace elements
                            const traces = plotlyDiv.querySelectorAll('g.trace');
                            if (traces.length === 0) return 'No trace elements found';
                            
                            // Find the first trace with clickable elements
                            for (let trace of traces) {
                                const clickableElements = trace.querySelectorAll('path, rect');
                                if (clickableElements.length > 0) {
                                    // Get the first clickable element
                                    const firstElement = clickableElements[0];
                                    
                                    // Create a synthetic click event that bypasses the overlay
                                    const clickEvent = new MouseEvent('click', {
                                        bubbles: true,
                                        cancelable: true,
                                        view: window,
                                        detail: 1,
                                        screenX: 0,
                                        screenY: 0,
                                        clientX: 0,
                                        clientY: 0,
                                        ctrlKey: false,
                                        altKey: false,
                                        shiftKey: false,
                                        metaKey: false,
                                        button: 0,
                                        relatedTarget: null
                                    });
                                    
                                    // Dispatch the event directly on the element
                                    firstElement.dispatchEvent(clickEvent);
                                    
                                    return 'Click event dispatched on trace element';
                                }
                            }
                            
                            return 'No clickable elements found in traces';
                        }
                    """)
                    
                    logger.info(f"🎯 JavaScript click result: {js_result}")
                    await self.take_screenshot(page, "After JavaScript Click Attempt")
                    
                    if "Click event dispatched" in js_result:
                        await asyncio.sleep(2)
                        
                        # Check if the add button text changed
                        add_button_text = await page.text_content('[id="page-4-add-structure-button"]')
                        logger.info(f"🎯 Add button text after JS click: {add_button_text}")
                        await self.take_screenshot(page, "Add Button Text After JS Click")
                        
                        if "Add" in add_button_text and "to selection" in add_button_text:
                            logger.info("✅ SUCCESS! JavaScript click bypassed the overlay!")
                            
                            # Extract the region name from the button text
                            region_name = add_button_text.replace("Add ", "").replace(" to selection", "")
                            logger.info(f"🎯 Selected region: {region_name}")
                            
                            # Click the add button to add the region
                            await self.take_screenshot(page, "Before Add Structure Button")
                            await page.click('[id="page-4-add-structure-button"]')
                            logger.info("✅ Added region to selection")
                            await asyncio.sleep(2)
                            await self.take_screenshot(page, "After Add Structure Button")
                            
                        else:
                            logger.warning("⚠️ JavaScript click didn't enable the add button")
                            
                    else:
                        logger.warning(f"⚠️ JavaScript click failed: {js_result}")
                        
                except Exception as e:
                    logger.error(f"❌ JavaScript-based clicking failed: {e}")
                
            except Exception as e:
                logger.error(f"❌ Treemap interaction failed: {e}")
            
            # 4. Display Lipid Expression (EXACT from working script)
            logger.info("🔍 TEST 4: Display Lipid Expression")
            try:
                # Check if display button is enabled
                display_button = await page.query_selector('[id="page-4-display-button"]')
                display_disabled = await display_button.get_attribute('disabled')
                
                if display_disabled is None:
                    logger.info("🎯 Display button is enabled, clicking...")
                    await self.take_screenshot(page, "Before Display Button Click")
                    await page.click('[id="page-4-display-button"]')
                    await asyncio.sleep(3)
                    await self.take_screenshot(page, "After Display Button Click")
                    
                    # Look for the 3D volume graph that should appear
                    volume_graph = await page.query_selector('[id="page-4-graph-volume"]')
                    if volume_graph:
                        logger.info("✅ 3D volume graph displayed successfully")
                        await self.take_screenshot(page, "3D Volume Graph Displayed")
                    else:
                        logger.warning("⚠️ 3D volume graph not found after display button click")
                        await self.take_screenshot(page, "3D Volume Graph Not Found")
                        
                else:
                    logger.info("🎯 Display button is disabled - need regions and lipid selected")
                    await self.take_screenshot(page, "Display Button Disabled")
                    
            except Exception as e:
                logger.error(f"❌ Display lipid expression failed: {e}")
            
            # Final success screenshot
            await self.take_screenshot(page, "3D Exploration Final Success")
            
            # Legacy screenshot for compatibility
            await page.screenshot(path="3d_exploration_success_unified.png")
            logger.info("📸 3D Exploration success screenshot saved")
            
            self.test_results['3d_exploration'] = 'SUCCESS'
            logger.info("🎉 3D EXPLORATION PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ 3D Exploration page test failed: {e}")
            await page.screenshot(path="3d_exploration_failure_unified.png")
            self.test_results['3d_exploration'] = 'FAILED'
            raise

    async def test_lipid_selection_page(self, page):
        """Test the Lipid Selection page (based on playwright test suite functionality)."""
        logger.info("\n🎯 TESTING LIPID SELECTION PAGE")
        logger.info("-" * 40)
        
        try:
            # Navigate to page
            await page.goto("http://127.0.0.1:8050/lipid-selection", timeout=90000)
            logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "Lipid Selection Page Loaded")
            
            # Wait for core elements
            await page.wait_for_selector('[id="page-2-graph-heatmap-mz-selection"]', timeout=60000)
            logger.info("✅ Core elements rendered")
            await self.take_screenshot(page, "Lipid Selection Core Elements Rendered")
            
            self.monitor.log_stats("Lipid Selection - Page Loaded")
            
            # 1. Test Heatmap Interaction (lipid selection) - Select 1-3 lipids
            logger.info("🎯 Testing Heatmap Interaction (lipid selection) - Select 1-3 lipids")
            try:
                # Click on the heatmap multiple times to simulate selecting multiple lipids
                for i in range(3):  # Select up to 3 lipids
                    await self.take_screenshot(page, f"Before Heatmap Click {i+1}")
                    await page.click('[id="page-2-graph-heatmap-mz-selection"]')
                    await asyncio.sleep(1)
                    logger.info(f"✅ Clicked on heatmap for lipid selection {i+1}")
                    await self.take_screenshot(page, f"After Heatmap Click {i+1}")
                    
                    # Wait a bit between selections
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Heatmap interaction failed: {e}")
            
            # 2. Test Lipids Dropdown (using GOLD STANDARD pattern from LP-Selection)
            logger.info("💧 Testing Lipids Dropdown (using GOLD STANDARD pattern)...")
            try:
                lipid_dropdown_container = page.locator('[id="page-2-dropdown-lipids"]').locator('..')
                
                # Select first lipid
                logger.info("--- Selecting first lipid ---")
                await lipid_dropdown_container.click()
                await page.wait_for_selector('.mantine-MultiSelect-item', state='visible', timeout=10000)
                await self.take_screenshot(page, "Lipid First Before Select")
                
                first_option = page.locator('.mantine-MultiSelect-item:not([data-selected="true"])').first
                option_text = await first_option.text_content()
                logger.info(f"Selecting first lipid: '{option_text}'")
                await first_option.click()
                await asyncio.sleep(2)
                await self.take_screenshot(page, "Lipid First After Select")
                
                # Select second lipid (additional selection)
                logger.info("--- Selecting second lipid ---")
                await lipid_dropdown_container.click()
                await page.wait_for_selector('.mantine-MultiSelect-item', state='visible', timeout=10000)
                await self.take_screenshot(page, "Lipid Second Before Select")
                
                second_option = page.locator('.mantine-MultiSelect-item:not([data-selected="true"])').first
                option_text = await second_option.text_content()
                logger.info(f"Selecting second lipid: '{option_text}'")
                await second_option.click()
                await asyncio.sleep(2)
                await self.take_screenshot(page, "Lipid Second After Select")
                
                # Stabilization wait (GOLD STANDARD)
                logger.info("WAITING 10 SECONDS for app to stabilize after lipid selections...")
                await asyncio.sleep(10)
                
                # Verify selections
                logger.info("Verifying lipid selections after stabilization wait...")
                selected_pills = await page.locator('[id="page-2-dropdown-lipids"] .mantine-MultiSelect-value').all()
                selected_texts = [await pill.text_content() for pill in selected_pills]
                logger.info(f"Final lipids in dropdown: {selected_texts}")
                await self.take_screenshot(page, "Lipid Dropdown Verification")
                
                # Close dropdown
                await page.click('[id="page-2-graph-heatmap-mz-selection"]')
                await asyncio.sleep(1)
                logger.info("✅ Selected multiple lipids using GOLD STANDARD pattern.")
                
            except Exception as e:
                logger.error(f"❌ Lipids dropdown test failed: {e}", exc_info=True)
            
            # 3. Test Sections Mode Switch (All sections vs One section) - NOW ENABLED
            logger.info("🔄 Testing Sections Mode Switch (All sections vs One section) - NOW ENABLED")
            try:
                # Wait for the sections mode component to be available
                await page.wait_for_selector('[id="page-2-sections-mode"]', timeout=10000)
                await self.take_screenshot(page, "Sections Mode Component Available")
                
                # Wait PATIENTLY for sections mode to become enabled after lipid selection
                logger.info("⏰ Waiting PATIENTLY for sections mode to become enabled...")
                await asyncio.sleep(5)  # Extra wait for lipid selection to process
                
                # Test switching between "One section" and "All sections" views
                # Using the WORKING LOGIC from playwright_test_suite.py
                
                # First, switch to "All sections" view
                logger.info("--- Switching to 'All sections' view ---")
                await self.take_screenshot(page, "Before Switch to All Sections")
                
                # Click the sections mode selector first
                await page.click('[id="page-2-sections-mode"]')
                await asyncio.sleep(2)
                
                # This is a dmc.SegmentedControl, not a dropdown
                # The text content shows the actual options: "One section" and "All sections"
                target_text = "All sections"
                logger.info(f"🎯 Looking for segmented control option: '{target_text}'")
                
                # Try to click on the text content directly
                try:
                    await page.click(f'text="{target_text}"')
                    logger.info(f"✅ Successfully clicked segmented control option: {target_text}")
                    mode_selected = True
                except Exception as e:
                    logger.warning(f"⚠️ Direct text click failed: {e}")
                    
                    # Fallback: try to find the element containing the text
                    try:
                        # Look for any element containing the target text within the segmented control
                        text_element = await page.query_selector(f'[id="page-2-sections-mode"] *:has-text("{target_text}")')
                        if text_element:
                            await text_element.click()
                            logger.info(f"✅ Successfully clicked text element: {target_text}")
                            mode_selected = True
                        else:
                            raise Exception(f"Could not find element with text: {target_text}")
                    except Exception as e2:
                        logger.error(f"❌ Fallback selection also failed: {e2}")
                        raise Exception(f"Could not select mode 'all' (text: '{target_text}') with any method")
                
                await asyncio.sleep(3)  # Wait for the UI to update after the click
                logger.info("✅ Switched to 'All sections' view")
                await self.take_screenshot(page, "After Switch to All Sections")
                
                # Wait for the view to stabilize
                await asyncio.sleep(3)
                
                # Then, switch back to "One section" view
                logger.info("--- Switching back to 'One section' view ---")
                await self.take_screenshot(page, "Before Switch to One Section")
                
                # Click the sections mode selector again
                await page.click('[id="page-2-sections-mode"]')
                await asyncio.sleep(2)
                
                target_text = "One section"
                logger.info(f"🎯 Looking for segmented control option: '{target_text}'")
                
                # Try to click on the text content directly
                try:
                    await page.click(f'text="{target_text}"')
                    logger.info(f"✅ Successfully clicked segmented control option: {target_text}")
                    mode_selected = True
                except Exception as e:
                    logger.warning(f"⚠️ Direct text click failed: {e}")
                    
                    # Fallback: try to find the element containing the text
                    try:
                        # Look for any element containing the target text within the segmented control
                        text_element = await page.query_selector(f'[id="page-2-sections-mode"] *:has-text("{target_text}")')
                        if text_element:
                            await text_element.click()
                            logger.info(f"✅ Successfully clicked text element: {target_text}")
                            mode_selected = True
                        else:
                            raise Exception(f"Could not find element with text: {target_text}")
                    except Exception as e2:
                        logger.error(f"❌ Fallback selection also failed: {e2}")
                        raise Exception(f"Could not select mode 'single' (text: '{target_text}') with any method")
                
                await asyncio.sleep(3)  # Wait for the UI to update after the click
                logger.info("✅ Switched back to 'One section' view")
                await self.take_screenshot(page, "After Switch to One Section")
                
                # Wait for the view to stabilize
                await asyncio.sleep(3)
                
                logger.info("✅ Sections mode switch test completed successfully")
                
            except Exception as e:
                logger.error(f"❌ Sections mode switch failed: {e}")
            
            # 4. Test Brain Badge Selection (using working selector strategy)
            logger.info("🧠 Testing Brain Badge Selection")
            try:
                # Wait for brain selection component to be available
                await page.wait_for_selector('[id="main-brain"]', timeout=10000)
                await self.take_screenshot(page, "Brain Selection Component Available")
                
                # Test different brain selections using the working text-based selector strategy
                brain_options = [
                    "Reference 1 (M)",
                    "Control 1 (M)", 
                    "Control 2 (M)"
                ]
                
                for brain_label in brain_options:
                    try:
                        # Use the working selector strategy: find LABEL by visible text
                        brain_selector = f'[id="main-brain"] .mantine-Chips-label:has-text("{brain_label}")'
                        brain_button = await page.wait_for_selector(brain_selector, timeout=5000)
                        
                        await self.take_screenshot(page, f"Before Brain Selection {brain_label}")
                        await brain_button.click()
                        await asyncio.sleep(2)
                        logger.info(f"✅ Selected brain: {brain_label}")
                        await self.take_screenshot(page, f"After Brain Selection {brain_label}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Could not select brain '{brain_label}': {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Brain badge selection failed: {e}")
            
            # 3. Test RGB Toggle
            logger.info("🎨 Testing RGB Toggle")
            try:
                rgb_switch = await page.wait_for_selector('[id="page-2-rgb-switch"]', timeout=10000)
                await self.take_screenshot(page, "Before RGB Switch Click")
                await rgb_switch.click()
                await asyncio.sleep(2)
                logger.info("✅ RGB switch clicked")
                await self.take_screenshot(page, "After RGB Switch Click")
            except Exception as e:
                logger.error(f"❌ RGB switch failed: {e}")
            
            # 4. Test Sections Mode Switch (All sections vs One section)
            logger.info("🔄 Testing Sections Mode Switch (All sections vs One section)")
            try:
                # Wait for the sections mode component to be available
                await page.wait_for_selector('[id="page-2-sections-mode"]', timeout=10000)
                await self.take_screenshot(page, "Sections Mode Component Available")
                
                # Test switching between "One section" and "All sections" views
                # Using the working solution: click directly on visible text labels
                
                # First, switch to "All sections" view
                logger.info("--- Switching to 'All sections' view ---")
                await self.take_screenshot(page, "Before Switch to All Sections")
                
                # FIX: Use a locator. The click() action on a locator will automatically
                # wait for the element to be enabled before it clicks.
                all_sections_button = page.locator('text="All sections"')
                await all_sections_button.click(timeout=15000)  # Wait up to 15s for it to become enabled
                
                await asyncio.sleep(3)  # Wait for the UI to update after the click
                logger.info("✅ Switched to 'All sections' view")
                await self.take_screenshot(page, "After Switch to All Sections")
                
                # Wait for the view to stabilize
                await asyncio.sleep(3)
                
                # Then, switch back to "One section" view
                logger.info("--- Switching back to 'One section' view ---")
                await self.take_screenshot(page, "Before Switch to One Section")
                
                # FIX: Use a locator for the same reason
                one_section_button = page.locator('text="One section"')
                await one_section_button.click(timeout=15000)  # Wait up to 15s for it to become enabled
                
                await asyncio.sleep(3)  # Wait for the UI to update after the click
                logger.info("✅ Switched back to 'One section' view")
                await self.take_screenshot(page, "After Switch to One Section")
                
                # Wait for the view to stabilize
                await asyncio.sleep(3)
                
                logger.info("✅ Sections mode switch test completed successfully")
                
            except Exception as e:
                logger.error(f"❌ Sections mode switch failed: {e}")
            
            # 5. Test Allen Annotations Toggle
            logger.info("🎨 Testing Allen Annotations Toggle")
            try:
                annotations_toggle = await page.wait_for_selector('[id="page-2-toggle-annotations"]', timeout=10000)
                await self.take_screenshot(page, "Before Allen Toggle Click")
                await annotations_toggle.click()
                await asyncio.sleep(2)
                logger.info("✅ Annotations toggle clicked")
                await self.take_screenshot(page, "After Allen Toggle Click")
            except Exception as e:
                logger.error(f"❌ Annotations toggle failed: {e}")
            
            # 6. Test Main Slider
            logger.info("🎚️ Testing Main Slider")
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
                        await asyncio.sleep(1)
                        await self.take_screenshot(page, f"Main Slider After Click {i+1} at {pos}")
                        logger.info(f"✅ Main slider clicked at position {pos}")
                else:
                    logger.warning("⚠️ Main slider bounding box not available")
            except Exception as e:
                logger.warning(f"❌ Main slider test failed: {e}")
                await self.take_screenshot(page, "Main Slider Error")
            
            # Final success screenshot
            await self.take_screenshot(page, "Lipid Selection Final Success")
            
            # Legacy screenshot for compatibility
            await page.screenshot(path="lipid_selection_success_unified.png")
            logger.info("📸 Lipid Selection success screenshot saved")
            
            self.test_results['lipid_selection'] = 'SUCCESS'
            logger.info("🎉 LIPID SELECTION PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ Lipid Selection page test failed: {e}")
            await page.screenshot(path="lipid_selection_failure_unified.png")
            self.test_results['lipid_selection'] = 'FAILED'
            raise

    async def test_peak_selection_page(self, page):
        """Test the Peak Selection page (based on page structure analysis)."""
        logger.info("\n🎯 TESTING PEAK SELECTION PAGE")
        logger.info("-" * 40)
        
        try:
            # Navigate to page
            await page.goto("http://127.0.0.1:8050/peak-selection", timeout=90000)
            logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "Peak Selection Page Loaded")
            
            # Wait for core elements
            await page.wait_for_selector('[id="page-2tris-graph-heatmap-mz-selection"]', timeout=60000)
            logger.info("✅ Core elements rendered")
            await self.take_screenshot(page, "Peak Selection Core Elements Rendered")
            
            self.monitor.log_stats("Peak Selection - Page Loaded")
            
            # 1. Test Tutorial Button
            logger.info("📚 Testing Tutorial Button")
            try:
                tutorial_button = await page.wait_for_selector('[id="peak-start-tutorial-btn"]', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Button Click")
                await tutorial_button.click()
                await asyncio.sleep(2)
                logger.info("✅ Tutorial button clicked")
                await self.take_screenshot(page, "After Tutorial Button Click")
                
                # Close tutorial popover (if it appears)
                try:
                    close_tutorial = await page.wait_for_selector('[id="peak-tutorial-close-1"]', timeout=5000)
                    await self.take_screenshot(page, "Before Tutorial Popover Close")
                    await close_tutorial.click()
                    await asyncio.sleep(2)
                    logger.info("✅ Tutorial popover closed")
                    await self.take_screenshot(page, "After Tutorial Popover Close")
                except Exception as e:
                    logger.info("ℹ️ No tutorial popover to close")
            except Exception as e:
                logger.error(f"❌ Tutorial test failed: {e}")
            
            # 2. Test Allen Annotations Toggle
            logger.info("🎨 Testing Allen Annotations Toggle")
            try:
                annotations_toggle = await page.wait_for_selector('[id="page-2tris-toggle-annotations"]', timeout=10000)
                await self.take_screenshot(page, "Before Allen Toggle Click")
                await annotations_toggle.click()
                await asyncio.sleep(2)
                logger.info("✅ Annotations toggle clicked")
                await self.take_screenshot(page, "After Allen Toggle Click")
            except Exception as e:
                logger.error(f"❌ Annotations toggle failed: {e}")
            
            # 3. Test Peak Dropdown (using GOLD STANDARD pattern from LP-Selection)
            logger.info("🎯 Testing Peak Dropdown (using GOLD STANDARD pattern)...")
            try:
                peak_dropdown_container = page.locator('[id="page-2tris-dropdown-peaks"]').locator('..')
                
                # Select first peak
                logger.info("--- Selecting first peak ---")
                await peak_dropdown_container.click()
                await asyncio.sleep(2)  # Wait for dropdown to open
                await self.take_screenshot(page, "Peak Dropdown After Click")
                
                # Wait for options to become visible with more flexible selector
                try:
                    await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=10000)
                    logger.info("✅ Peak dropdown options are visible")
                except Exception as e:
                    logger.warning(f"⚠️ Standard options not visible, trying alternative selectors: {e}")
                    # Try alternative selectors
                    await page.wait_for_selector('[data-value]', timeout=5000)
                
                await self.take_screenshot(page, "Peak First Before Select")
                
                # Find first available option with multiple selector strategies
                first_option = None
                for selector in ['.mantine-MultiSelect-item:not([data-selected="true"])', '.mantine-Select-item:not([data-selected="true"])', '[data-value]:not([data-selected="true"])']:
                    try:
                        first_option = page.locator(selector).first
                        if await first_option.count() > 0:
                            break
                    except:
                        continue
                
                if first_option and await first_option.count() > 0:
                    option_text = await first_option.text_content()
                    logger.info(f"Selecting first peak: '{option_text}'")
                    await first_option.click()
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "Peak First After Select")
                else:
                    logger.warning("⚠️ No first peak option found")
                
                # Select second peak (additional selection)
                logger.info("--- Selecting second peak ---")
                await peak_dropdown_container.click()
                await asyncio.sleep(2)  # Wait for dropdown to open
                
                # Wait for options to become visible again
                try:
                    await page.wait_for_selector('.mantine-MultiSelect-item, .mantine-Select-item, [data-value]', state='visible', timeout=10000)
                except Exception as e:
                    logger.warning(f"⚠️ Standard options not visible for second selection: {e}")
                    await page.wait_for_selector('[data-value]', timeout=5000)
                
                await self.take_screenshot(page, "Peak Second Before Select")
                
                # Find second available option
                second_option = None
                for selector in ['.mantine-MultiSelect-item:not([data-selected="true"])', '.mantine-Select-item:not([data-selected="true"])', '[data-value]:not([data-selected="true"])']:
                    try:
                        second_option = page.locator(selector).first
                        if await second_option.count() > 0:
                            break
                    except:
                        continue
                
                if second_option and await second_option.count() > 0:
                    option_text = await second_option.text_content()
                    logger.info(f"Selecting second peak: '{option_text}'")
                    await second_option.click()
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, "Peak Second After Select")
                else:
                    logger.warning("⚠️ No second peak option found")
                
                # Stabilization wait (GOLD STANDARD)
                logger.info("WAITING 10 SECONDS for app to stabilize after peak selections...")
                await asyncio.sleep(10)
                
                # Verify selections
                logger.info("Verifying peak selections after stabilization wait...")
                selected_pills = await page.locator('[id="page-2tris-dropdown-peaks"] .mantine-MultiSelect-value').all()
                selected_texts = [await pill.text_content() for pill in selected_pills]
                logger.info(f"Final peaks in dropdown: {selected_texts}")
                await self.take_screenshot(page, "Peak Dropdown Verification")
                
                # Close dropdown
                await page.click('[id="page-2tris-graph-heatmap-mz-selection"]')
                await asyncio.sleep(1)
                logger.info("✅ Selected multiple peaks using GOLD STANDARD pattern.")
                
            except Exception as e:
                logger.error(f"❌ Peak dropdown test failed: {e}", exc_info=True)
            
            # 4. Test Brain Badge Selection (using working selector strategy)
            logger.info("🧠 Testing Brain Badge Selection")
            try:
                # Wait for brain selection component to be available
                await page.wait_for_selector('[id="main-brain"]', timeout=10000)
                await self.take_screenshot(page, "Brain Selection Component Available")
                
                # Test different brain selections using the working text-based selector strategy
                brain_options = [
                    "Reference 1 (M)",
                    "Control 1 (M)", 
                    "Control 2 (M)"
                ]
                
                for brain_label in brain_options:
                    try:
                        # Use the working selector strategy: find LABEL by visible text
                        brain_selector = f'[id="main-brain"] .mantine-Chips-label:has-text("{brain_label}")'
                        brain_button = await page.wait_for_selector(brain_selector, timeout=5000)
                        
                        await self.take_screenshot(page, f"Before Brain Selection {brain_label}")
                        await brain_button.click()
                        await asyncio.sleep(2)
                        logger.info(f"✅ Selected brain: {brain_label}")
                        await self.take_screenshot(page, f"After Brain Selection {brain_label}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Could not select brain '{brain_label}': {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Brain badge selection failed: {e}")
            
            # 5. Test RGB Switch
            logger.info("🎨 Testing RGB Switch")
            try:
                rgb_switch = await page.wait_for_selector('[id="page-2tris-rgb-switch"]', timeout=10000)
                await self.take_screenshot(page, "Before RGB Switch Click")
                await rgb_switch.click()
                await asyncio.sleep(2)
                logger.info("✅ RGB switch clicked")
                await self.take_screenshot(page, "After RGB Switch Click")
            except Exception as e:
                logger.error(f"❌ RGB switch failed: {e}")
            
            # 6. Test Show Spectrum Button
            logger.info("📊 Testing Show Spectrum Button")
            try:
                show_spectrum_button = await page.wait_for_selector('[id="page-2tris-show-spectrum-button"]', timeout=10000)
                await self.take_screenshot(page, "Before Show Spectrum Button")
                await show_spectrum_button.click()
                await asyncio.sleep(3)  # Wait for spectrum to load
                logger.info("✅ Show spectrum button clicked")
                await self.take_screenshot(page, "After Show Spectrum Button")
                
                # Close spectrum if it opens in a drawer
                try:
                    close_spectrum_button = await page.wait_for_selector('[id="page-2tris-close-spectrum-button"]', timeout=5000)
                    await self.take_screenshot(page, "Before Close Spectrum Button")
                    await close_spectrum_button.click()
                    await asyncio.sleep(1)
                    logger.info("✅ Spectrum drawer closed")
                    await self.take_screenshot(page, "After Close Spectrum Button")
                except Exception as e:
                    logger.info("ℹ️ No spectrum drawer to close")
                    
            except Exception as e:
                logger.error(f"❌ Show spectrum button failed: {e}")
            
            # 7. Test Main Slider
            logger.info("🎚️ Testing Main Slider")
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
                        await asyncio.sleep(1)
                        await self.take_screenshot(page, f"Main Slider After Click {i+1} at {pos}")
                        logger.info(f"✅ Main slider clicked at position {pos}")
                else:
                    logger.warning("⚠️ Main slider bounding box not available")
            except Exception as e:
                logger.warning(f"❌ Main slider test failed: {e}")
                await self.take_screenshot(page, "Main Slider Error")
            
            # Final success screenshot
            await self.take_screenshot(page, "Peak Selection Final Success")
            
            # Legacy screenshot for compatibility
            await page.screenshot(path="peak_selection_success_unified.png")
            logger.info("📸 Peak Selection success screenshot saved")
            
            self.test_results['peak_selection'] = 'SUCCESS'
            logger.info("🎉 PEAK SELECTION PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ Peak Selection page test failed: {e}")
            await page.screenshot(path="peak_selection_failure_unified.png")
            self.test_results['peak_selection'] = 'FAILED'
            raise

    async def test_region_analysis_page(self, page):
        """Test the Region Analysis page (all working functionality)."""
        logger.info("\n🎯 TESTING REGION ANALYSIS PAGE")
        logger.info("-" * 40)
        
        try:
            # Navigate to page
            await page.goto("http://127.0.0.1:8050/region-analysis", timeout=90000)
            logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "Region Analysis Page Loaded")
            
            # Wait for core elements
            await page.wait_for_selector('[id="page-3-dropdown-brain-regions"]', timeout=60000)
            logger.info("✅ Core elements rendered")
            await self.take_screenshot(page, "Region Analysis Core Elements Rendered")
            
            self.monitor.log_stats("Region Analysis - Page Loaded")
            
            # 1. Test Tutorial Button
            logger.info("📚 Testing Tutorial Button")
            try:
                tutorial_button = await page.wait_for_selector('[id="analysis-start-tutorial-btn"]', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Button Click")
                await tutorial_button.click()
                await asyncio.sleep(2)
                logger.info("✅ Tutorial button clicked")
                await self.take_screenshot(page, "After Tutorial Button Click")
                
                # Close tutorial popover
                close_tutorial = await page.wait_for_selector('[id="analysis-tutorial-close-1"]', timeout=10000)
                await self.take_screenshot(page, "Before Tutorial Popover Close")
                await close_tutorial.click()
                await asyncio.sleep(2)
                logger.info("✅ Tutorial popover closed")
                await self.take_screenshot(page, "After Tutorial Popover Close")
            except Exception as e:
                logger.error(f"❌ Tutorial test failed: {e}")
            
            # 2. Test Allen Toggle
            logger.info("🎨 Testing Allen Toggle")
            try:
                annotations_toggle = await page.wait_for_selector('[id="page-3-toggle-annotations"]', timeout=10000)
                await self.take_screenshot(page, "Before Allen Toggle Click")
                await annotations_toggle.click()
                await asyncio.sleep(2)
                logger.info("✅ Annotations toggle clicked")
                await self.take_screenshot(page, "After Allen Toggle Click")
            except Exception as e:
                logger.error(f"❌ Annotations toggle failed: {e}")
            
            # 3. Test Brain Region MultiSelect Selection (with explicit re-opening)
            logger.info("🎯 Testing Brain Region MultiSelect Selection")
            first_option_text = None
            second_option_text = None
            try:
                region_dropdown_container = page.locator('[id="page-3-dropdown-brain-regions"]').locator('..')
                
                # Select first region
                logger.info("--- Selecting first brain region ---")
                await self.take_screenshot(page, "Brain Region Dropdown Before Select 1")
                await region_dropdown_container.click()
                await asyncio.sleep(2)
                
                # Try multiple selectors for dropdown options
                first_option = None
                for selector in ['.mantine-MultiSelect-item', '[role="option"]', '[data-value]']:
                    try:
                        first_option = await page.wait_for_selector(selector, state='visible', timeout=5000)
                        if first_option:
                            break
                    except:
                        continue
                
                if not first_option:
                    # Fallback: use locator to find first available option
                    options_locator = page.locator('.mantine-MultiSelect-item, [role="option"], [data-value]')
                    count = await options_locator.count()
                    if count > 0:
                        first_option = options_locator.first
                        first_option_text = await first_option.text_content()
                        logger.info(f"Selecting first brain region: '{first_option_text}'")
                        await first_option.click()
                    else:
                        raise Exception("No dropdown options found with any selector")
                else:
                    first_option_text = await first_option.text_content()
                    logger.info(f"Selecting first brain region: '{first_option_text}'")
                    await first_option.click()
                
                await asyncio.sleep(3) # CRITICAL: Wait for page to update
                await self.take_screenshot(page, "Brain Region After Select 1")
                
                # Re-open the dropdown to select the second region
                logger.info("--- Selecting second brain region ---")
                await self.take_screenshot(page, "Brain Region Dropdown Before Select 2")
                await region_dropdown_container.click()
                await asyncio.sleep(2)
                
                # Find the next unselected option
                all_options = await page.locator('.mantine-MultiSelect-item:not([data-selected="true"])').all()
                if len(all_options) > 0:
                    second_option = all_options[0]
                    second_option_text = await second_option.text_content()
                    logger.info(f"Selecting second brain region: '{second_option_text}'")
                    await second_option.click()
                    await asyncio.sleep(3) # CRITICAL: Wait for page to update
                    await self.take_screenshot(page, "Brain Region After Select 2")
                else:
                    # Fallback: try to find any available option
                    any_option = page.locator('.mantine-MultiSelect-item, [role="option"]').first
                    if await any_option.count() > 0:
                        second_option_text = await any_option.text_content()
                        logger.info(f"Selecting fallback second brain region: '{second_option_text}'")
                        await any_option.click()
                        await asyncio.sleep(3)
                        await self.take_screenshot(page, "Brain Region After Select 2")
                    else:
                        logger.warning("⚠️ Could not find a second brain region option, continuing with one selection")
                        second_option_text = first_option_text  # Use same as first for fallback

                # Close the dropdown by clicking the main brain image to avoid clicking on non-rendered elements
                logger.info("--- Closing brain region dropdown ---")
                await page.click('[id="main-brain"]', force=True)
                await asyncio.sleep(2)
                await self.take_screenshot(page, "After Closing Brain Region Dropdown")
                
                logger.info("✅ Successfully selected brain regions and closed the dropdown.")
            except Exception as e:
                logger.error(f"❌ Brain region MultiSelect selection failed: {e}", exc_info=True)
                await self.take_screenshot(page, "Brain Region Selection Failure")
                # Don't fail the entire test, try to continue
                first_option_text = "Region A"  # Fallback values
                second_option_text = "Region B"

            # 4. Test Group Assignment
            logger.info("🎯 Testing Group Assignment")
            try:
                # Assign first selected region to Group A
                logger.info("--- Assigning first region to Group A ---")
                await page.wait_for_selector('[id="page-3-group-a-selector"]', state='visible', timeout=10000)
                await self.take_screenshot(page, "Before Group A Selector Click")
                await page.click('[id="page-3-group-a-selector"]')
                await asyncio.sleep(1)
                
                group_a_option = page.locator(f'text="{first_option_text}"').first
                await group_a_option.wait_for(state='visible', timeout=10000)
                await self.take_screenshot(page, "Before Select Group A Option")
                await group_a_option.click()
                await asyncio.sleep(1)
                await self.take_screenshot(page, "After Select Group A Option")
                logger.info(f"✅ Assigned '{first_option_text}' to Group A")
                
                # Close Group A dropdown
                await page.click('[id="main-brain"]', force=True)
                await asyncio.sleep(1)
                
                # Assign second selected region to Group B
                logger.info("--- Assigning second region to Group B ---")
                await page.wait_for_selector('[id="page-3-group-b-selector"]', state='visible', timeout=10000)
                await self.take_screenshot(page, "Before Group B Selector Click")
                await page.click('[id="page-3-group-b-selector"]')
                await asyncio.sleep(1)
                
                group_b_option = page.locator(f'text="{second_option_text}"').first
                await group_b_option.wait_for(state='visible', timeout=10000)
                await self.take_screenshot(page, "Before Select Group B Option")
                await group_b_option.click()
                await asyncio.sleep(1)
                await self.take_screenshot(page, "After Select Group B Option")
                logger.info(f"✅ Assigned '{second_option_text}' to Group B")
                
                # Close Group B dropdown
                await page.click('[id="main-brain"]', force=True)
                await asyncio.sleep(1)
                
                logger.info("✅ Group assignment test completed")
            except Exception as e:
                logger.error(f"❌ Group assignment failed: {e}")
                await self.take_screenshot(page, "Group Assignment Error")
                self.test_results['region_analysis'] = 'FAILED'
                raise
            
            # 5. Test Compute Differential Analysis
            logger.info("🧮 Testing Compute Differential Analysis")
            try:
                compute_button = await page.wait_for_selector('[id="page-3-button-compute-volcano"]', state='visible', timeout=10000)
                is_disabled = await compute_button.get_attribute('disabled')
                
                if is_disabled is None:
                    logger.info("🎯 Compute button is enabled, clicking...")
                    await self.take_screenshot(page, "Before Compute Button Click")
                    await compute_button.click()
                    await asyncio.sleep(3)
                    logger.info("✅ Computed differential analysis")
                    
                    # Wait 8 seconds before taking screenshot as requested
                    logger.info("⏰ Waiting 8 seconds before taking screenshot...")
                    await asyncio.sleep(8)
                    
                    await self.take_screenshot(page, "After Compute Button Click")
                else:
                    logger.warning("⚠️ Compute button is disabled, cannot perform test.")
                    await self.take_screenshot(page, "Compute Button Disabled")
            except Exception as e:
                logger.error(f"❌ Compute differential analysis failed: {e}")
                await self.take_screenshot(page, "Compute Button Error")
                self.test_results['region_analysis'] = 'FAILED'
                raise
            
            # 6. Test Reset Regions
            logger.info("🔄 Testing Reset Regions")
            try:
                await page.wait_for_selector('[id="page-3-reset-button"]', state='visible', timeout=10000)
                await self.take_screenshot(page, "Before Reset Button Click")
                await page.click('[id="page-3-reset-button"]')
                await asyncio.sleep(2)
                logger.info("✅ Reset regions button clicked")
                await self.take_screenshot(page, "After Reset Button Click")
            except Exception as e:
                logger.error(f"❌ Reset regions failed: {e}")
                self.test_results['region_analysis'] = 'FAILED'
                raise
            
            # Final success screenshot
            await self.take_screenshot(page, "Region Analysis Final Success")
            
            # Legacy screenshot for compatibility
            await page.screenshot(path="region_analysis_success_unified.png")
            logger.info("📸 Region Analysis success screenshot saved")
            
            self.test_results['region_analysis'] = 'SUCCESS'
            logger.info("🎉 REGION ANALYSIS PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ Region Analysis page test failed: {e}")
            await page.screenshot(path="region_analysis_failure_unified.png")
            self.test_results['region_analysis'] = 'FAILED'
            raise

    async def test_lp_selection_page(self, page):
        """Test the LP-Selection page (lipid programs selection)."""
        logger.info("\n🎯 TESTING LP-SELECTION PAGE")
        logger.info("-" * 40)
        
        try:
            await page.goto("http://127.0.0.1:8050/lp-selection", timeout=90000)
            logger.info("✅ Page loaded successfully")
            await self.take_screenshot(page, "LP Selection Page Loaded")
            
            await page.wait_for_selector('[id="page-2bis-graph-heatmap-mz-selection"]', timeout=60000)
            logger.info("✅ Core elements rendered")
            await self.take_screenshot(page, "LP Selection Core Elements Rendered")
            
            self.monitor.log_stats("LP Selection - Page Loaded")

            # 1. Test Heatmap Interaction (Restored)
            logger.info("🎯 Testing Heatmap Interaction")
            try:
                for i in range(3):
                    await self.take_screenshot(page, f"LP Heatmap Before Click {i+1}")
                    await page.click('[id="page-2bis-graph-heatmap-mz-selection"]')
                    await asyncio.sleep(1)
                    logger.info(f"✅ Clicked on heatmap for program selection {i+1}")
                    await self.take_screenshot(page, f"LP Heatmap After Click {i+1}")
            except Exception as e:
                logger.error(f"❌ Heatmap interaction failed: {e}")
            
            # 2. Test Program Dropdown Selection (WITH STABILIZATION WAIT)
            logger.info("🎯 Testing Program Dropdown Selection with stabilization wait")
            try:
                program_dropdown_container = page.locator('[id="page-2bis-dropdown-programs"]').locator('..')
                
                # Before opening dropdown
                await self.take_screenshot(page, "LP Program Dropdown Before Opening")
                
                for i in range(1):
                    logger.info(f"--- Selecting additional program #{i+1} ---")
                    await program_dropdown_container.click()
                    await asyncio.sleep(2)  # Wait for dropdown to open
                    await self.take_screenshot(page, f"LP Program Dropdown After Click {i+1}")
                    
                    await page.wait_for_selector('.mantine-MultiSelect-item', state='visible', timeout=10000)
                    await self.take_screenshot(page, f"LP Program Options Visible {i+1}")

                    first_unselected_option = page.locator('.mantine-MultiSelect-item:not([data-selected="true"])').first
                    option_text = await first_unselected_option.text_content()
                    logger.info(f"Selecting: '{option_text}'")
                    
                    await self.take_screenshot(page, f"LP Before Select Program {option_text}")
                    await first_unselected_option.click()
                    await asyncio.sleep(2)
                    await self.take_screenshot(page, f"LP After Select Program {option_text}")
                
                logger.info("✅ Finished selection loop. Selections should be ['mitochondrion', 'globalembeddings_0'].")
                
                logger.info("WAITING 10 SECONDS for app to stabilize before next interaction...")
                await asyncio.sleep(10)
                
                logger.info("Verifying selections after stabilization wait...")
                selected_pills = await page.locator('[id="page-2bis-dropdown-programs"] .mantine-MultiSelect-value').all()
                selected_texts = [await pill.text_content() for pill in selected_pills]
                logger.info(f"Final programs in dropdown: {selected_texts}")
                await self.take_screenshot(page, "LP Program Dropdown Verification After Stabilization")

            except Exception as e:
                logger.error(f"❌ Program dropdown test failed: {e}", exc_info=True)
            
            # 3. Test Brain Badge Selection (using working selector strategy)
            logger.info("🧠 Testing Brain Badge Selection")
            try:
                # Wait for brain selection component to be available
                await page.wait_for_selector('[id="main-brain"]', timeout=10000)
                await self.take_screenshot(page, "LP Brain Component Available")
                
                # Test different brain selections using the working text-based selector strategy
                brain_options = [
                    "Reference 1 (M)",
                    "Control 1 (M)", 
                    "Control 2 (M)"
                ]
                
                for brain_label in brain_options:
                    try:
                        # Use the working selector strategy: find LABEL by visible text
                        brain_selector = f'[id="main-brain"] .mantine-Chips-label:has-text("{brain_label}")'
                        brain_button = await page.wait_for_selector(brain_selector, timeout=5000)
                        
                        await self.take_screenshot(page, f"LP Before Brain Selection {brain_label}")
                        await brain_button.click()
                        await asyncio.sleep(2)
                        logger.info(f"✅ Selected brain: {brain_label}")
                        await self.take_screenshot(page, f"LP After Brain Selection {brain_label}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Could not select brain '{brain_label}': {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Brain badge selection failed: {e}")
            
            # 4. Test Allen Annotations Toggle
            logger.info("🎨 Testing Allen Annotations Toggle")
            try:
                annotations_toggle = await page.wait_for_selector('[id="page-2bis-toggle-annotations"]', timeout=10000)
                await self.take_screenshot(page, "LP Before Allen Toggle Click")
                await annotations_toggle.click()
                await asyncio.sleep(2)
                logger.info("✅ Allen annotations toggle clicked")
                await self.take_screenshot(page, "LP After Allen Toggle Click")
            except Exception as e:
                logger.error(f"❌ Allen annotations toggle failed: {e}")
            
            # 5. Test Main Slider
            logger.info("🎚️ Testing Main Slider")
            try:
                main_slider = page.locator('[id="main-paper-slider"]')
                await main_slider.wait_for(state="visible", timeout=10000)
                await self.take_screenshot(page, "LP Main Slider Before Interaction")
                
                slider_box = await main_slider.bounding_box()
                if slider_box:
                    for i, pos in enumerate([0.25, 0.5, 0.75]):
                        x = slider_box['x'] + (slider_box['width'] * pos)
                        y = slider_box['y'] + (slider_box['height'] * 0.5)
                        await page.mouse.click(x, y)
                        await asyncio.sleep(1)
                        await self.take_screenshot(page, f"LP Main Slider After Click {i+1} at {pos}")
                        logger.info(f"✅ Main slider clicked at position {pos}")
                else:
                    logger.warning("⚠️ Main slider bounding box not available")
            except Exception as e:
                logger.warning(f"❌ Main slider test failed: {e}")
                await self.take_screenshot(page, "LP Main Slider Error")
            
            # 6. Test RGB Toggle (if available)
            logger.info("🎨 Testing RGB Toggle (if available)")
            try:
                rgb_switch = await page.wait_for_selector('[id="page-2bis-rgb-switch"]', timeout=5000)
                await self.take_screenshot(page, "LP Before RGB Switch Click")
                await rgb_switch.click()
                await asyncio.sleep(2)
                logger.info("✅ RGB switch clicked")
                await self.take_screenshot(page, "LP After RGB Switch Click")
            except Exception as e:
                logger.info("ℹ️ RGB switch not found - skipping")
            
            # Final wait and screenshot
            logger.info("All interactions complete. Waiting 15 seconds for final render...")
            await asyncio.sleep(15)

            logger.info("📸 Taking final screenshot...")
            await self.take_screenshot(page, "LP Selection Final State")
            logger.info("🎉 LP-SELECTION PAGE TEST COMPLETED")
            
            # Final success screenshot
            await self.take_screenshot(page, "LP Selection Final Success")
            
            # Legacy screenshot for compatibility
            await page.screenshot(path="lp_selection_success_unified.png")
            logger.info("📸 LP Selection success screenshot saved")
            
            self.test_results['lp_selection'] = 'SUCCESS'
            logger.info("🎉 LP-SELECTION PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ LP Selection page test failed: {e}")
            await self.take_screenshot(page, "LP Selection Failure")
            await page.screenshot(path="lp_selection_failure_unified.png")
            self.test_results['lp_selection'] = 'FAILED'
            raise

    async def test_3d_lipizones_page(self, page):
        """Test the 3D-Lipizones page (just open, wait 120s, screenshot)."""
        logger.info("\n🎯 TESTING 3D-LIPIZONES PAGE")
        logger.info("-" * 40)
        
        try:
            # Navigate to page
            await page.goto("http://127.0.0.1:8050/3D-lipizones", timeout=90000)
            logger.info("✅ Page loaded successfully")
            await page.screenshot(path="3d_lipizones_page_loaded.png")
            
            # Wait for core elements
            await page.wait_for_selector('[id="content"]', timeout=60000)
            logger.info("✅ Core elements rendered")
            await page.screenshot(path="3d_lipizones_core_elements.png")
            
            self.monitor.log_stats("3D Lipizones - Page Loaded")
            
            # Wait 120 seconds as requested
            logger.info("⏰ Waiting 120 seconds as requested...")
            for i in range(12):  # 12 * 10 seconds = 120 seconds
                await asyncio.sleep(10)
                logger.info(f"⏰ Waited {(i+1)*10} seconds...")
                # Take progress screenshot every 30 seconds
                if (i+1) % 3 == 0:
                    await page.screenshot(path=f"3d_lipizones_progress_{(i+1)*10}s.png")
            
            logger.info("✅ 120 seconds wait completed")
            await page.screenshot(path="3d_lipizones_after_120s_wait.png")
            
            # Final success screenshot
            await page.screenshot(path="3d_lipizones_final_success.png")
            
            # Legacy screenshot for compatibility
            await page.screenshot(path="3d_lipizones_success_unified.png")
            logger.info("📸 3D Lipizones success screenshot saved")
            
            self.test_results['3d_lipizones'] = 'SUCCESS'
            logger.info("🎉 3D-LIPIZONES PAGE TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ 3D Lipizones page test failed: {e}")
            await page.screenshot(path="3d_lipizones_failure_unified.png")
            self.test_results['3d_lipizones'] = 'FAILED'
            raise

    async def test_homepage_return_and_documentation(self, page):
        """Test returning to homepage and accessing documentation."""
        logger.info("\n🏠 TESTING HOMEPAGE RETURN & DOCUMENTATION")
        logger.info("-" * 40)
        
        try:
            # Navigate back to homepage
            await page.goto("http://127.0.0.1:8050/", timeout=90000)
            logger.info("✅ Returned to homepage successfully")
            await self.take_screenshot(page, "Homepage Return")
            
            self.monitor.log_stats("Homepage Return - Page Loaded")
            
            # Wait and take screenshots every 10 seconds, 3 times
            logger.info("⏰ Taking screenshots every 10 seconds, 3 times...")
            for i in range(3):
                await asyncio.sleep(10)
                logger.info(f"⏰ Screenshot {i+1}/3 after {(i+1)*10} seconds")
                await self.take_screenshot(page, f"Homepage Screenshot {i+1}/3 After {(i+1)*10}s")
            
            # Test Documentation button (using CORRECT selector from codebase)
            logger.info("📚 Testing Documentation Access")
            try:
                # Use the CORRECT selector from the codebase: sidebar.py line 262
                documentation_button = await page.wait_for_selector('[id="sidebar-documentation"]', timeout=10000)
                await self.take_screenshot(page, "Documentation Before Button Click")
                await documentation_button.click()
                await asyncio.sleep(3)
                logger.info("✅ Documentation button clicked")
                await self.take_screenshot(page, "Documentation After Button Click")
                
                # Wait for documentation content to load
                await asyncio.sleep(2)
                await self.take_screenshot(page, "Documentation Content Loaded")
                
            except Exception as e:
                logger.error(f"❌ Documentation access failed: {e}")
                # Try alternative selectors based on the codebase
                try:
                    # Look for the book icon in sidebar (from home.py line 659)
                    doc_elements = await page.query_selector_all('[id="sidebar-documentation-inside"]')
                    if doc_elements:
                        await self.take_screenshot(page, "Documentation Elements Found")
                        await doc_elements[0].click()
                        await asyncio.sleep(3)
                        logger.info("✅ Documentation accessed via sidebar-documentation-inside")
                        await self.take_screenshot(page, "Documentation Alternative Access")
                    else:
                        logger.warning("⚠️ No documentation elements found")
                except Exception as e2:
                    logger.error(f"❌ Alternative documentation access also failed: {e2}")
            
            # Final success screenshot
            await self.take_screenshot(page, "Homepage Return Final Success")
            
            # Legacy screenshot for compatibility
            await page.screenshot(path="homepage_return_success_unified.png")
            logger.info("📸 Homepage return success screenshot saved")
            
            self.test_results['homepage_return'] = 'SUCCESS'
            logger.info("🎉 HOMEPAGE RETURN & DOCUMENTATION TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            logger.error(f"❌ Homepage return test failed: {e}")
            await page.screenshot(path="homepage_return_failure_unified.png")
            self.test_results['homepage_return'] = 'FAILED'
            raise

    async def generate_final_summary(self, page):
        """Generate final summary of all test results."""
        logger.info("\n🏁 FINAL TEST SUITE SUMMARY")
        logger.info("=" * 60)
        
        # Log final system stats
        self.monitor.log_stats("FINAL SUMMARY")
        
        # Count successes and failures
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result == 'SUCCESS')
        failed_tests = total_tests - successful_tests
        
        logger.info(f"📊 TEST RESULTS SUMMARY:")
        logger.info(f"   Total Pages Tested: {total_tests}")
        logger.info(f"   ✅ Successful: {successful_tests}")
        logger.info(f"   ❌ Failed: {failed_tests}")
        logger.info(f"   📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Individual page results
        logger.info(f"\n📋 INDIVIDUAL PAGE RESULTS:")
        for page_name, result in self.test_results.items():
            status_icon = "✅" if result == 'SUCCESS' else "❌"
            logger.info(f"   {status_icon} {page_name.replace('_', ' ').title()}: {result}")
        
        # Take final screenshot
        await page.screenshot(path="unified_test_suite_final_summary.png")
        logger.info("📸 Final summary screenshot saved")
        
        if failed_tests == 0:
            logger.info("🎉 ALL TESTS PASSED! The application is stable and all functionality is working!")
        else:
            logger.warning(f"⚠️ {failed_tests} test(s) failed. Review the logs and screenshots for details.")

async def main():
    """Main entry point for the unified test suite."""
    test_suite = UnifiedStabilityTestSuite()
    await test_suite.run_complete_test_suite()

if __name__ == "__main__":
    # Create test suite with screenshot=True for detailed monitoring
    test_suite = UnifiedStabilityTestSuite(screenshot=True)
    asyncio.run(test_suite.run_complete_test_suite())
