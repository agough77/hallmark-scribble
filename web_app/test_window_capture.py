"""Test window capture to debug screenshot issue"""
import pygetwindow as gw
import pyautogui
from PIL import Image

# Find Outlook window
windows = gw.getAllWindows()
outlook = None
for win in windows:
    if 'Outlook' in win.title and win.visible:
        outlook = win
        break

if outlook:
    print(f"Found Outlook window:")
    print(f"  Title: {outlook.title}")
    print(f"  Position: left={outlook.left}, top={outlook.top}")
    print(f"  Size: width={outlook.width}, height={outlook.height}")
    print(f"  Visible: {outlook.visible}")
    
    # Get all monitors info
    print(f"\nAll monitors size: {pyautogui.size()}")
    
    # Try to capture the window
    print(f"\nAttempting to capture with region=({outlook.left}, {outlook.top}, {outlook.width}, {outlook.height})")
    
    try:
        screenshot = pyautogui.screenshot(region=(
            outlook.left,
            outlook.top,
            outlook.width,
            outlook.height
        ))
        
        print(f"Screenshot captured successfully!")
        print(f"Screenshot size: {screenshot.size}")
        
        # Save it
        screenshot.save("test_outlook_capture.png")
        print("Saved to test_outlook_capture.png")
        
        # Check if it's blank (all same color)
        colors = screenshot.getcolors(maxcolors=10)
        if colors and len(colors) == 1:
            print("⚠️  WARNING: Screenshot appears to be completely blank (single color)")
        else:
            print(f"✓ Screenshot has multiple colors ({len(colors) if colors else 'many'} colors)")
            
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Outlook window not found")
    print("\nAvailable windows:")
    for win in windows:
        if win.title and win.visible:
            print(f"  - {win.title}")
