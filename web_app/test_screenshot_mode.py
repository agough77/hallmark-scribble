"""
Test script for screenshot mode functionality
"""
import sys
import os

# Add parent directory to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")
    try:
        from shared.recorder import input_logger
        print("✓ shared.recorder.input_logger")
        
        from shared.utils.screenshot import select_window
        print("✓ shared.utils.screenshot.select_window")
        
        import pyautogui
        print("✓ pyautogui")
        
        from PyQt5.QtWidgets import QApplication
        print("✓ PyQt5.QtWidgets.QApplication")
        
        print("\n✓ All imports successful!\n")
        return True
    except Exception as e:
        print(f"\n✗ Import failed: {e}\n")
        return False

def test_screenshot_capture():
    """Test basic screenshot capture"""
    print("Testing screenshot capture...")
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        print(f"✓ Screenshot captured: {screenshot.size}")
        
        # Test with region
        screenshot_region = pyautogui.screenshot(region=(0, 0, 100, 100))
        print(f"✓ Screenshot with region captured: {screenshot_region.size}")
        
        print("\n✓ Screenshot capture works!\n")
        return True
    except Exception as e:
        print(f"\n✗ Screenshot capture failed: {e}\n")
        return False

def test_output_directory():
    """Test output directory creation"""
    print("Testing output directory creation...")
    try:
        from datetime import datetime
        
        output_base = os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs")
        date_str = datetime.now().strftime('%Y-%m-%d')
        date_dir = os.path.join(output_base, date_str)
        
        print(f"  Base directory: {output_base}")
        print(f"  Date directory: {date_dir}")
        
        if not os.path.exists(output_base):
            os.makedirs(output_base)
            print(f"✓ Created base directory")
        else:
            print(f"✓ Base directory exists")
            
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)
            print(f"✓ Created date directory")
        else:
            print(f"✓ Date directory exists")
        
        # Count existing scribble folders
        scribble_count = len([d for d in os.listdir(date_dir) if d.startswith('Scribble ')])
        print(f"  Existing scribbles today: {scribble_count}")
        
        print("\n✓ Output directory management works!\n")
        return True
    except Exception as e:
        print(f"\n✗ Output directory test failed: {e}\n")
        return False

def test_pyqt_dialog():
    """Test PyQt dialog creation (non-interactive)"""
    print("Testing PyQt dialog creation...")
    try:
        from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout, QLabel
        from PyQt5.QtCore import Qt
        
        # Check if QApplication already exists
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        print("✓ QApplication initialized")
        
        # Create dialog (don't show it)
        dialog = QDialog()
        dialog.setWindowTitle("Test Dialog")
        dialog.resize(300, 200)
        
        layout = QVBoxLayout()
        label = QLabel("Test Label")
        layout.addWidget(label)
        
        btn = QPushButton("Test Button")
        layout.addWidget(btn)
        
        dialog.setLayout(layout)
        print("✓ Dialog created successfully")
        
        # Don't execute the dialog in test mode
        dialog.deleteLater()
        
        print("\n✓ PyQt dialog creation works!\n")
        return True
    except Exception as e:
        print(f"\n✗ PyQt dialog test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_input_logger():
    """Test input logger module"""
    print("Testing input logger...")
    try:
        from shared.recorder import input_logger
        
        # Check if functions exist
        assert hasattr(input_logger, 'start_logging'), "start_logging function not found"
        assert hasattr(input_logger, 'stop_logging'), "stop_logging function not found"
        
        print("✓ input_logger.start_logging exists")
        print("✓ input_logger.stop_logging exists")
        
        print("\n✓ Input logger module is available!\n")
        return True
    except Exception as e:
        print(f"\n✗ Input logger test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """Test config loading from parent directory"""
    print("Testing config loading...")
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.txt')
        print(f"  Config path: {config_path}")
        
        if os.path.exists(config_path):
            print("✓ config.txt found")
            with open(config_path, 'r') as f:
                lines = f.readlines()
                config_keys = [line.split('=')[0].strip() for line in lines if '=' in line and not line.strip().startswith('#')]
                print(f"  Config keys: {config_keys}")
                print("✓ Config can be read")
        else:
            print("⚠ config.txt not found (this is okay for testing)")
        
        print("\n✓ Config loading path is correct!\n")
        return True
    except Exception as e:
        print(f"\n✗ Config loading test failed: {e}\n")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("HALLMARK SCRIBBLE - SCREENSHOT MODE TEST")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Config Loading", test_config_loading),
        ("Output Directory", test_output_directory),
        ("Screenshot Capture", test_screenshot_capture),
        ("Input Logger", test_input_logger),
        ("PyQt Dialog", test_pyqt_dialog),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"Running: {name}")
        print("-" * 60)
        success = test_func()
        results.append((name, success))
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:8} - {name}")
    
    total_pass = sum(1 for _, success in results if success)
    total_tests = len(results)
    print(f"\nTotal: {total_pass}/{total_tests} tests passed")
    print("=" * 60)
    
    return all(success for _, success in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
