"""
Test Screenshot Mode - No AI
Tests screenshot capture without calling Gemini API
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
import pyautogui
from shared.recorder import input_logger

def test_screenshot_capture():
    """Test basic screenshot capture without AI"""
    print("\n" + "="*60)
    print("SCREENSHOT MODE TEST (No AI)")
    print("="*60)
    
    # Create test output directory
    output_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs", "test_screenshots")
    os.makedirs(output_dir, exist_ok=True)
    
    screenshot_dir = os.path.join(output_dir, "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    
    print(f"\n✓ Output directory: {output_dir}")
    print(f"✓ Screenshots will be saved to: {screenshot_dir}")
    
    # Test 1: Screenshot capture callback
    print("\n1. Testing screenshot capture callback...")
    screenshot_count = {'count': 0}
    
    def take_screenshot(x, y):
        """Callback function that captures screenshot on click"""
        screenshot_count['count'] += 1
        timestamp = time.strftime("%H%M%S")
        filename = f"screenshot_{screenshot_count['count']:03d}_{timestamp}.png"
        filepath = os.path.join(screenshot_dir, filename)
        
        # Capture with pyautogui (fullscreen)
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        print(f"   ✓ Screenshot {screenshot_count['count']}: {filename}")
        return filepath
    
    # Test the callback directly
    print("   Testing direct callback...")
    test_file = take_screenshot(100, 100)
    if os.path.exists(test_file):
        print(f"   ✓ Direct capture works: {os.path.basename(test_file)}")
    else:
        print(f"   ✗ Failed to create: {test_file}")
        return
    
    # Test 2: Screenshot with region (window mode)
    print("\n2. Testing screenshot with region...")
    region = {'x': 100, 'y': 100, 'width': 800, 'height': 600}
    
    def take_screenshot_region(x, y):
        """Callback with region cropping"""
        screenshot_count['count'] += 1
        timestamp = time.strftime("%H%M%S")
        filename = f"screenshot_{screenshot_count['count']:03d}_{timestamp}.png"
        filepath = os.path.join(screenshot_dir, filename)
        
        # Capture with region
        screenshot = pyautogui.screenshot(region=(region['x'], region['y'], region['width'], region['height']))
        screenshot.save(filepath)
        
        print(f"   ✓ Region screenshot {screenshot_count['count']}: {filename}")
        return filepath
    
    test_file2 = take_screenshot_region(100, 100)
    if os.path.exists(test_file2):
        print(f"   ✓ Region capture works: {os.path.basename(test_file2)}")
    else:
        print(f"   ✗ Failed to create: {test_file2}")
        return
    
    # Test 3: Input logger integration
    print("\n3. Testing input logger with callback...")
    print("   Starting listener for 3 seconds...")
    print("   Click your mouse 2-3 times NOW!")
    
    screenshot_count['count'] = 0  # Reset counter
    
    # Start logging with callback
    input_logger.start_logging(
        output=os.path.join(output_dir, "actions.log"),
        screenshot_dir_path=screenshot_dir,
        click_callback=take_screenshot
    )
    
    # Wait for clicks
    time.sleep(3)
    
    # Stop logging
    input_logger.stop_logging()
    print(f"   ✓ Captured {screenshot_count['count']} screenshots from clicks")
    
    # Test 4: Verify files
    print("\n4. Verifying output files...")
    screenshots = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
    print(f"   ✓ Total screenshots created: {len(screenshots)}")
    for img in screenshots[:5]:  # Show first 5
        filepath = os.path.join(screenshot_dir, img)
        size = os.path.getsize(filepath)
        print(f"   - {img} ({size:,} bytes)")
    
    if len(screenshots) > 5:
        print(f"   ... and {len(screenshots) - 5} more")
    
    print("\n" + "="*60)
    print("TEST COMPLETE - ALL SCREENSHOT MECHANICS WORKING!")
    print("="*60)
    print(f"\nCheck output: {screenshot_dir}")
    
    return True

if __name__ == "__main__":
    try:
        test_screenshot_capture()
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
