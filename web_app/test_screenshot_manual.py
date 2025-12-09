"""
Manual Screenshot Mode Test
Run this while the web server is running to test screenshot capture
"""
import requests
import time
import json

BASE_URL = "http://localhost:5000"

def test_screenshot_flow():
    print("=" * 60)
    print("SCREENSHOT MODE MANUAL TEST")
    print("=" * 60)
    
    # Test 1: Start recording with fullscreen mode (skip picker)
    print("\n1. Starting screenshot session (fullscreen mode)...")
    try:
        response = requests.post(f"{BASE_URL}/api/start_recording", 
            json={
                'mode': 'screenshot',
                'capture_mode': 'fullscreen',
                'window_region': None
            },
            timeout=5
        )
        data = response.json()
        
        if data.get('success'):
            session_id = data['session_id']
            output_dir = data['output_dir']
            print(f"   ✓ Session started: {session_id}")
            print(f"   ✓ Output dir: {output_dir}")
        else:
            print(f"   ✗ Failed: {data.get('error')}")
            return
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Test 2: Simulate screenshots
    print("\n2. Simulating screenshot captures...")
    print("   (Backend will capture on mouse clicks)")
    print("   Click anywhere on your screen 3 times...")
    
    input("\n   Press ENTER after you've clicked 3 times...")
    
    # Test 3: Stop recording
    print("\n3. Stopping screenshot session...")
    try:
        response = requests.post(f"{BASE_URL}/api/stop_recording",
            json={'session_id': session_id},
            timeout=5
        )
        data = response.json()
        
        if data.get('success'):
            print(f"   ✓ Session stopped")
            print(f"   ✓ Screenshots saved to: {output_dir}")
        else:
            print(f"   ✗ Failed: {data.get('error')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: List sessions
    print("\n4. Checking available sessions...")
    try:
        response = requests.get(f"{BASE_URL}/api/sessions", timeout=5)
        data = response.json()
        
        if data.get('success'):
            sessions = data.get('sessions', [])
            print(f"   ✓ Found {len(sessions)} session(s)")
            if sessions:
                latest = sessions[0]
                print(f"   ✓ Latest: {latest['name']}")
                print(f"   ✓ Path: {latest['path']}")
        else:
            print(f"   ✗ Failed: {data.get('error')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nCheck the output directory for captured screenshots!")

if __name__ == "__main__":
    try:
        # Quick server check
        response = requests.get(BASE_URL, timeout=2)
        if response.status_code == 200:
            print("✓ Server is running\n")
            test_screenshot_flow()
        else:
            print("✗ Server returned unexpected status")
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running!")
        print("  Start it with: cd web_app && python web_app.py")
    except Exception as e:
        print(f"✗ Error: {e}")
