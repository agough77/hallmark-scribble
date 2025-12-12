"""Test ImageGrab with secondary monitor coordinates"""
from PIL import ImageGrab
import os

# Test coordinates from the window on secondary monitor
bbox = (3432, -8, 3432 + 1936, -8 + 1048)
print(f"Testing ImageGrab with bbox: {bbox}")
print(f"all_screens=True")

try:
    screenshot = ImageGrab.grab(bbox=bbox, all_screens=True)
    print(f"SUCCESS: Captured {screenshot.size} image")
    
    # Save to test location
    test_path = r"C:\Users\AGough\Downloads\test_imagegrab_secondary_monitor.png"
    screenshot.save(test_path)
    print(f"Saved to: {test_path}")
    
    # Check if it's all black
    pixels = list(screenshot.getdata())
    black_pixels = sum(1 for p in pixels if p == (0, 0, 0))
    total_pixels = len(pixels)
    black_percent = (black_pixels / total_pixels) * 100
    
    print(f"Black pixels: {black_pixels}/{total_pixels} ({black_percent:.1f}%)")
    
    if black_percent > 90:
        print("WARNING: Image is mostly black!")
    else:
        print("SUCCESS: Image has content!")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
