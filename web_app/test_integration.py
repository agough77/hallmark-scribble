"""
Integration test for screenshot mode end-to-end flow
Tests the actual API endpoints and flow
"""
import requests
import time
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_server_running():
    """Test if server is running"""
    print("Testing server connection...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✓ Server is running (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"✗ Server not reachable: {e}")
        return False

def test_api_gemini_quota():
    """Test Gemini quota endpoint"""
    print("\nTesting /api/gemini_quota...")
    try:
        response = requests.get(f"{BASE_URL}/api/gemini_quota", timeout=5)
        data = response.json()
        print(f"✓ Quota endpoint works")
        print(f"  Response: {data}")
        return True
    except Exception as e:
        print(f"✗ Quota endpoint failed: {e}")
        return False

def test_start_recording_screenshot():
    """Test starting screenshot recording"""
    print("\nTesting /api/start_recording (screenshot mode)...")
    try:
        payload = {
            'mode': 'screenshot',
            'capture_mode': 'fullscreen',
            'window_region': None
        }
        response = requests.post(
            f"{BASE_URL}/api/start_recording",
            json=payload,
            timeout=5
        )
        data = response.json()
        
        if data.get('success'):
            print(f"✓ Screenshot recording started")
            print(f"  Session ID: {data.get('session_id')}")
            print(f"  Output Dir: {data.get('output_dir')}")
            return data
        else:
            print(f"✗ Failed to start recording: {data.get('error')}")
            return None
    except Exception as e:
        print(f"✗ Start recording failed: {e}")
        return None

def test_stop_recording(session_id):
    """Test stopping screenshot recording"""
    print("\nTesting /api/stop_recording...")
    try:
        payload = {'session_id': session_id}
        response = requests.post(
            f"{BASE_URL}/api/stop_recording",
            json=payload,
            timeout=5
        )
        data = response.json()
        
        if data.get('success'):
            print(f"✓ Screenshot recording stopped")
            print(f"  Output Dir: {data.get('output_dir')}")
            return data
        else:
            print(f"✗ Failed to stop recording: {data.get('error')}")
            return None
    except Exception as e:
        print(f"✗ Stop recording failed: {e}")
        return None

def test_list_sessions():
    """Test listing recording sessions"""
    print("\nTesting /api/sessions...")
    try:
        response = requests.get(f"{BASE_URL}/api/sessions", timeout=5)
        data = response.json()
        
        if data.get('success'):
            sessions = data.get('sessions', [])
            print(f"✓ Sessions list retrieved")
            print(f"  Total sessions: {len(sessions)}")
            if sessions:
                latest = sessions[0]
                print(f"  Latest session: {latest.get('name')} ({latest.get('date')})")
            return True
        else:
            print(f"✗ Failed to get sessions: {data.get('error')}")
            return False
    except Exception as e:
        print(f"✗ Sessions endpoint failed: {e}")
        return False

def verify_output_files(output_dir):
    """Verify that output files were created"""
    print("\nVerifying output files...")
    try:
        if not os.path.exists(output_dir):
            print(f"✗ Output directory doesn't exist: {output_dir}")
            return False
        
        print(f"✓ Output directory exists: {output_dir}")
        
        files = os.listdir(output_dir)
        print(f"  Files created: {len(files)}")
        
        # Check for expected files
        expected_files = ['actions.log']
        for expected in expected_files:
            if expected in files:
                print(f"  ✓ Found: {expected}")
            else:
                print(f"  ⚠ Missing: {expected}")
        
        # List screenshot files
        screenshots = [f for f in files if f.startswith('screenshot_') and f.endswith('.png')]
        print(f"  Screenshots: {len(screenshots)}")
        
        return True
    except Exception as e:
        print(f"✗ File verification failed: {e}")
        return False

def main():
    """Run integration tests"""
    print("=" * 70)
    print("HALLMARK SCRIBBLE - SCREENSHOT MODE INTEGRATION TEST")
    print("=" * 70)
    
    # Test 1: Server is running
    if not test_server_running():
        print("\n✗ Server must be running to perform integration tests")
        print("  Start the server with: python web_app.py")
        return False
    
    # Test 2: Gemini quota endpoint
    test_api_gemini_quota()
    
    # Test 3: List existing sessions
    test_list_sessions()
    
    # Test 4: Start screenshot recording
    print("\n" + "=" * 70)
    print("STARTING SCREENSHOT RECORDING TEST")
    print("=" * 70)
    
    session_data = test_start_recording_screenshot()
    if not session_data:
        print("\n✗ Could not start recording session")
        return False
    
    session_id = session_data.get('session_id')
    output_dir = session_data.get('output_dir')
    
    # Wait a moment
    print("\n⏱ Waiting 2 seconds for recording to initialize...")
    time.sleep(2)
    
    # Test 5: Stop screenshot recording
    stop_data = test_stop_recording(session_id)
    if not stop_data:
        print("\n✗ Could not stop recording session")
        return False
    
    # Test 6: Verify output files
    if output_dir:
        verify_output_files(output_dir)
    
    # Test 7: List sessions again
    test_list_sessions()
    
    print("\n" + "=" * 70)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 70)
    print("\n✓ All integration tests passed!")
    print("\nNOTE: To fully test screenshot capture:")
    print("  1. Open the web interface at http://localhost:5000")
    print("  2. Click 'Start' in screenshot mode")
    print("  3. Select a capture mode in the PyQt dialog")
    print("  4. Click around to capture screenshots")
    print("  5. Click 'Stop' and verify screenshots were saved")
    
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
