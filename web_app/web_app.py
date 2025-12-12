"""
Hallmark Scribble - Web Server Version
A Flask-based web application for screen recording and guide generation
"""
# Updated video selector functionality

import os
import sys
import logging
import json
import time
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session
import uuid
import pyautogui
import threading
from flask_cors import CORS

# Determine if running as PyInstaller bundle
def get_base_path():
    """Get base path whether running as script or frozen exe"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

def get_shared_path():
    """Get path to shared resources"""
    base_path = get_base_path()
    if getattr(sys, 'frozen', False):
        # When frozen, shared is in the same directory as the exe
        # or one level up if installed (C:\Program Files\HallmarkScribble\Web\shared)
        shared_paths = [
            os.path.join(base_path, 'shared'),  # Next to exe
            os.path.join(os.path.dirname(base_path), 'shared'),  # Parent directory
            os.path.join(base_path, '_internal', 'shared'),  # PyInstaller _internal folder
        ]
        for path in shared_paths:
            if os.path.exists(path):
                return path
        # If none exist, check if we're in an installation directory
        install_base = os.path.dirname(os.path.dirname(base_path))  # Go up two levels
        if 'HallmarkScribble' in install_base:
            shared_path = os.path.join(install_base, 'shared')
            if os.path.exists(shared_path):
                return shared_path
        return os.path.join(base_path, 'shared')
    else:
        # Development mode - shared is in parent directory
        return os.path.join(os.path.dirname(base_path), 'shared')

def get_ffmpeg_path():
    """Get path to ffmpeg executable"""
    shared_path = get_shared_path()
    ffmpeg = os.path.join(shared_path, 'ffmpeg', 'bin', 'ffmpeg.exe')
    if os.path.exists(ffmpeg):
        return ffmpeg
    # Fallback: check if ffmpeg is in PATH
    import shutil
    ffmpeg_in_path = shutil.which('ffmpeg')
    if ffmpeg_in_path:
        return ffmpeg_in_path
    return ffmpeg  # Return expected path even if not found

def get_ffprobe_path():
    """Get path to ffprobe executable"""
    shared_path = get_shared_path()
    ffprobe = os.path.join(shared_path, 'ffmpeg', 'bin', 'ffprobe.exe')
    if os.path.exists(ffprobe):
        return ffprobe
    # Fallback: check if ffprobe is in PATH
    import shutil
    ffprobe_in_path = shutil.which('ffprobe')
    if ffprobe_in_path:
        return ffprobe_in_path
    return ffprobe  # Return expected path even if not found

# Add parent directory to path for shared modules
shared_path = get_shared_path()
sys.path.insert(0, shared_path)
# Also add parent directory so 'shared' can be imported as a module
parent_path = os.path.dirname(shared_path)
if parent_path not in sys.path:
    sys.path.insert(0, parent_path)

# Import shared modules
from recorder import input_logger

# Setup logging
log_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "hallmark_scribble_web.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hallmark-scribble-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
CORS(app)

# Global progress state for polling (replaces socketio)
progress_state = {
    'message': '',
    'status': 'idle',
    'timestamp': time.time(),
    'screenshot_count': 0
}

# Active sessions
active_sessions = {}

# Cache for Gemini models (to avoid rate limiting)
models_cache = {'models': None, 'timestamp': 0}
CACHE_DURATION = 3600  # Cache for 1 hour

# Track last API call for rate limiting
last_api_call = {'timestamp': None, 'cooldown_seconds': 65}  # 65 seconds to be safe

# Load configuration
def get_config_path():
    """Get the config file path - use AppData for frozen exe, dev folder otherwise"""
    if getattr(sys, 'frozen', False):
        # Running as frozen exe - use AppData for write permissions
        appdata = os.getenv('APPDATA')
        if appdata:
            config_dir = os.path.join(appdata, 'HallmarkScribble')
            os.makedirs(config_dir, exist_ok=True)
            return os.path.join(config_dir, 'config.txt')
    
    # Development mode - use local config.txt
    base_path = get_base_path()
    return os.path.join(base_path, 'config.txt')

def load_config():
    config = {}
    config_path = get_config_path()
    
    # Also check old locations for migration
    base_path = get_base_path()
    old_config_paths = [
        os.path.join(base_path, 'config.txt'),
        os.path.join(os.path.dirname(base_path), 'config.txt'),
        os.path.join(os.path.dirname(__file__), '..', 'config.txt'),
    ]
    
    # Try to load from new location first
    if os.path.exists(config_path):
        logging.info(f"Loading config from: {config_path}")
        with open(config_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
                    if key == 'GEMINI_API_KEY':
                        os.environ['GEMINI_API_KEY'] = value
    else:
        # Try old locations for migration
        for old_path in old_config_paths:
            if os.path.exists(old_path):
                logging.info(f"Migrating config from: {old_path} to {config_path}")
                with open(old_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            config[key] = value
                            if key == 'GEMINI_API_KEY':
                                os.environ['GEMINI_API_KEY'] = value
                # Write to new location
                try:
                    with open(config_path, 'w') as f:
                        for key, value in config.items():
                            f.write(f"{key}={value}\n")
                    logging.info(f"Config migrated successfully to {config_path}")
                except Exception as e:
                    logging.warning(f"Could not write migrated config: {e}")
                break
        else:
            logging.warning("No config.txt found in any expected location")
    
    return config

config = load_config()
logging.info(f"Configuration loaded: {list(config.keys())}")

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/get_windows', methods=['GET'])
def get_windows():
    """Get list of open windows for selection"""
    try:
        import pygetwindow as gw
        import win32gui
        import win32con
        
        # Get all windows
        windows = gw.getAllWindows()
        
        # Filter out empty titles and get window info
        window_list = []
        for win in windows:
            if win.title and win.title.strip() and win.visible:
                try:
                    # Check if window is minimized (has negative coords or tiny size)
                    is_minimized = (win.left < -10000 or win.top < -10000 or 
                                  win.width < 100 or win.height < 50)
                    
                    # If minimized but has a real title (not utility window), try to restore to get real dimensions
                    if is_minimized and len(win.title) > 10:
                        try:
                            hwnd = win._hWnd
                            if win32gui.IsIconic(hwnd):
                                # Get the window's restored position from window placement
                                placement = win32gui.GetWindowPlacement(hwnd)
                                # placement[4] is the RECT for restored position (left, top, right, bottom)
                                left, top, right, bottom = placement[4]
                                width = right - left
                                height = bottom - top
                                
                                # Only include if restored size is reasonable
                                if width >= 100 and height >= 50:
                                    window_list.append({
                                        'title': win.title[:100] + ' (minimized)',
                                        'app_name': win.title.split(' - ')[-1] if ' - ' in win.title else win.title,
                                        'region': {
                                            'left': left,
                                            'top': top,
                                            'width': width,
                                            'height': height
                                        },
                                        'is_minimized': True
                                    })
                                    continue
                        except:
                            pass  # Skip if we can't get placement info
                    
                    # Skip if still minimized/tiny
                    if is_minimized:
                        logging.debug(f"Skipping minimized/tiny window: {win.title} ({win.left},{win.top},{win.width}x{win.height})")
                        continue
                    
                    # Get window position and size directly from Win32 API for accuracy
                    # (pygetwindow may cache values that are stale on multi-monitor setups)
                    try:
                        hwnd = win._hWnd
                        rect = win32gui.GetWindowRect(hwnd)
                        left, top, right, bottom = rect
                        width = right - left
                        height = bottom - top
                        
                        logging.debug(f"Window '{win.title[:50]}' at ({left},{top}) size {width}x{height}")
                        
                        window_list.append({
                            'title': win.title[:100],  # Limit title length
                            'app_name': win.title.split(' - ')[-1] if ' - ' in win.title else win.title,
                            'region': {
                                'left': left,
                                'top': top,
                                'width': width,
                                'height': height
                            },
                            'is_minimized': False
                        })
                    except Exception as rect_error:
                        # Fallback to pygetwindow values if Win32 API fails
                        logging.warning(f"Could not get Win32 rect for {win.title}, using pygetwindow values: {rect_error}")
                        window_list.append({
                            'title': win.title[:100],
                            'app_name': win.title.split(' - ')[-1] if ' - ' in win.title else win.title,
                            'region': {
                                'left': win.left,
                                'top': win.top,
                                'width': win.width,
                                'height': win.height
                            },
                            'is_minimized': False
                        })
                except Exception as e:
                    logging.debug(f"Could not get info for window {win.title}: {e}")
                    continue
        
        # Sort by title
        window_list.sort(key=lambda x: x['title'])
        
        return jsonify({
            'success': True,
            'windows': window_list
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'pygetwindow not installed. Run: pip install pygetwindow'
        })
    except Exception as e:
        logging.error(f"Error getting windows: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/get_monitors', methods=['GET'])
def get_monitors():
    """Get list of available monitors for selection"""
    try:
        import win32api
        import win32con
        
        monitors = []
        monitor_info = win32api.EnumDisplayMonitors()
        
        for i, (hMonitor, hdcMonitor, rect) in enumerate(monitor_info):
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            
            # Get monitor info for name if possible
            try:
                info = win32api.GetMonitorInfo(hMonitor)
                device = info.get('Device', f'Monitor {i + 1}')
                is_primary = info.get('Flags', 0) & win32con.MONITORINFOF_PRIMARY
            except:
                device = f'Monitor {i + 1}'
                is_primary = (i == 0)
            
            monitors.append({
                'id': i,
                'name': device,
                'is_primary': bool(is_primary),
                'left': left,
                'top': top,
                'width': width,
                'height': height,
                'right': right,
                'bottom': bottom
            })
        
        return jsonify({
            'success': True,
            'monitors': monitors
        })
        
    except Exception as e:
        logging.error(f"Error getting monitors: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/show_screen_picker', methods=['POST'])
def show_screen_picker():
    """
    For web version, return picker options without showing PyQt dialog.
    The frontend will show its own picker UI.
    """
    try:
        # For now, just return success so frontend can handle the picker
        # In future, we could send available windows list
        return jsonify({
            'success': True,
            'message': 'Use frontend picker',
            'options': ['tab', 'window', 'fullscreen']
        })
    except Exception as e:
        logging.error(f"show_screen_picker error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress', methods=['GET'])
def get_progress():
    """
    Polling endpoint for progress updates (replaces SocketIO)
    """
    session_id = request.args.get('session_id')
    response = dict(progress_state)
    
    # If session_id provided, get session-specific screenshot count
    if session_id and session_id in active_sessions:
        session_data = active_sessions[session_id]
        if 'screenshot_count' in session_data:
            response['screenshot_count'] = session_data['screenshot_count']['count']
    
    return jsonify(response)

@app.route('/api/start_recording', methods=['POST'])
def start_recording():
    """Start a recording session"""
    try:
        data = request.json
        session_id = str(uuid.uuid4())
        mode = data.get('mode', 'screenshot')  # 'screenshot' or 'video'
        
        # Create output directory
        configured_folder = config.get('OUTPUT_FOLDER', os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs"))
        base_dir = configured_folder
        output_dir = os.path.join(base_dir, datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(output_dir, exist_ok=True)
        
        # Find next scribble number
        existing = [d for d in os.listdir(output_dir) if d.startswith("Scribble ")]
        next_num = 1
        if existing:
            numbers = []
            for name in existing:
                try:
                    num = int(name.replace("Scribble ", ""))
                    numbers.append(num)
                except:
                    pass
            next_num = max(numbers) + 1 if numbers else 1
        
        scribble_dir = os.path.join(output_dir, f"Scribble {next_num}")
        os.makedirs(scribble_dir, exist_ok=True)
        
        # Screenshot mode with backend click listener (like desktop app)
        if mode == 'screenshot':
            screenshot_count = {'count': 0}
            capture_mode = data.get('capture_mode', 'fullscreen')  # 'fullscreen', 'window', or 'tab'
            window_region = data.get('window_region')  # For window/tab mode
            
            # Debug logging
            logging.info(f"Screenshot mode started: capture_mode={capture_mode}, window_region={window_region}")
            
            # If window mode, try to bring the window to the front
            if capture_mode == 'window' and window_region:
                try:
                    import pygetwindow as gw
                    import win32gui
                    import win32con
                    import win32api
                    import win32process
                    
                    # Find the window by matching position and size
                    windows = gw.getAllWindows()
                    target_window = None
                    
                    for win in windows:
                        # Check both current position (for visible windows) and restored position (for minimized)
                        matches = False
                        
                        # Try current position first
                        if (win.left == window_region['left'] and 
                            win.top == window_region['top'] and
                            win.width == window_region['width'] and
                            win.height == window_region['height']):
                            matches = True
                        
                        # If no match and window is minimized, check restored position
                        if not matches:
                            try:
                                hwnd = win._hWnd
                                if win32gui.IsIconic(hwnd):
                                    placement = win32gui.GetWindowPlacement(hwnd)
                                    left, top, right, bottom = placement[4]
                                    width = right - left
                                    height = bottom - top
                                    if (left == window_region['left'] and 
                                        top == window_region['top'] and
                                        width == window_region['width'] and
                                        height == window_region['height']):
                                        matches = True
                            except:
                                pass
                        
                        if matches:
                            target_window = win
                            break
                    
                    if target_window:
                        logging.info(f"Bringing window to front: {target_window.title}")
                        hwnd = target_window._hWnd
                        
                        # If minimized, restore it first
                        if win32gui.IsIconic(hwnd):
                            logging.info("Window is minimized, restoring...")
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            import time
                            time.sleep(0.3)  # Give it time to restore
                        
                        # Multi-step window activation process
                        try:
                            current_thread = win32api.GetCurrentThreadId()
                            target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
                            
                            # Attach thread inputs
                            if current_thread != target_thread:
                                win32process.AttachThreadInput(current_thread, target_thread, True)
                            
                            try:
                                # Show window
                                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                                
                                # Alternative: Use keybd_event to release Alt key (Windows workaround)
                                import win32api as w32
                                VK_MENU = 0x12  # Alt key
                                w32.keybd_event(VK_MENU, 0, 0, 0)  # Press Alt
                                
                                # Try multiple methods to bring to foreground
                                win32gui.BringWindowToTop(hwnd)
                                win32gui.SetForegroundWindow(hwnd)
                                
                                # SetFocus and SetActiveWindow may fail for cross-thread windows
                                try:
                                    win32gui.SetFocus(hwnd)
                                except:
                                    pass  # Not critical if this fails
                                
                                try:
                                    win32gui.SetActiveWindow(hwnd)
                                except:
                                    pass  # Not critical if this fails
                                
                                w32.keybd_event(VK_MENU, 0, 2, 0)  # Release Alt
                                
                                logging.info("Window brought to front successfully")
                                
                            finally:
                                # Detach thread input
                                if current_thread != target_thread:
                                    win32process.AttachThreadInput(current_thread, target_thread, False)
                            
                            import time
                            time.sleep(0.5)  # Give window time to come to front
                            
                        except Exception as focus_error:
                            logging.warning(f"Window focus attempt failed: {focus_error}. Window may not be in foreground.")
                        
                        # Update the window region to the actual current position after restoring
                        try:
                            # Refresh window info to get actual current position
                            rect = win32gui.GetWindowRect(hwnd)
                            window_region['left'] = rect[0]
                            window_region['top'] = rect[1]
                            window_region['width'] = rect[2] - rect[0]
                            window_region['height'] = rect[3] - rect[1]
                            logging.info(f"Updated window region to current position: {window_region}")
                        except Exception as e:
                            logging.warning(f"Could not update window region: {e}")
                    else:
                        logging.warning(f"Could not find window matching region: {window_region}")
                        
                except Exception as e:
                    logging.warning(f"Could not bring window to front: {e}")
            
            def take_screenshot(x, y):
                """Callback when user clicks - capture screenshot"""
                try:
                    screenshot_count['count'] += 1
                    filename = f"screenshot_{screenshot_count['count']:03d}_{datetime.now().strftime('%H%M%S')}.png"
                    filepath = os.path.join(scribble_dir, filename)
                    
                    # Capture based on mode
                    if capture_mode == 'window' and window_region:
                        # Capture specific window region
                        logging.info(f"Capturing window region: {window_region}")
                        
                        # Validate region coordinates
                        if (window_region['width'] <= 0 or window_region['height'] <= 0 or
                            window_region['left'] < -10000 or window_region['top'] < -10000):
                            logging.warning(f"Invalid window region detected (minimized or hidden window): {window_region}")
                            logging.info("Falling back to full screen capture")
                            screenshot = pyautogui.screenshot()
                        else:
                            # Use MSS for window capture (more reliable on multi-monitor setups)
                            try:
                                import mss
                                from PIL import Image
                                logging.info(f"Using MSS for window capture (frozen exe compatible)")
                                with mss.mss() as sct:
                                    monitor = {
                                        'left': window_region['left'],
                                        'top': window_region['top'],
                                        'width': window_region['width'],
                                        'height': window_region['height']
                                    }
                                    logging.info(f"MSS capturing window region: {monitor}")
                                    sct_img = sct.grab(monitor)
                                    screenshot = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
                                    logging.info(f"Window capture size: {screenshot.size} (MSS)")
                            except Exception as mss_error:
                                logging.warning(f"MSS failed: {mss_error}, using pyautogui fallback")
                                logging.exception("MSS error details:")
                                screenshot = pyautogui.screenshot(region=(
                                    window_region['left'],
                                    window_region['top'],
                                    window_region['width'],
                                    window_region['height']
                                ))
                                logging.info(f"Window capture size: {screenshot.size} (pyautogui)")
                    elif capture_mode == 'fullscreen' and window_region:
                        # Capture specific monitor (fullscreen on one monitor)
                        logging.info(f"Capturing specific monitor: {window_region}")
                        logging.info(f"Monitor region coordinates - left:{window_region['left']}, top:{window_region['top']}, width:{window_region['width']}, height:{window_region['height']}")
                        
                        # Use MSS for multi-monitor screenshots (more reliable than ImageGrab)
                        try:
                            import mss
                            from PIL import Image
                            logging.info(f"Using MSS for monitor capture (frozen exe compatible)")
                            with mss.mss() as sct:
                                monitor = {
                                    'left': window_region['left'],
                                    'top': window_region['top'],
                                    'width': window_region['width'],
                                    'height': window_region['height']
                                }
                                logging.info(f"MSS capturing monitor: {monitor}")
                                sct_img = sct.grab(monitor)
                                screenshot = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
                                logging.info(f"Monitor capture size: {screenshot.size} (MSS)")
                        except Exception as mss_error:
                            logging.warning(f"MSS failed: {mss_error}, falling back to ImageGrab")
                            logging.exception("MSS error details:")
                            # Fallback to ImageGrab
                            from PIL import ImageGrab
                            bbox = (
                                window_region['left'],
                                window_region['top'],
                                window_region['left'] + window_region['width'],
                                window_region['top'] + window_region['height']
                            )
                            logging.info(f"ImageGrab bbox for monitor: {bbox}")
                            screenshot = ImageGrab.grab(bbox=bbox, all_screens=True)
                            logging.info(f"Monitor capture (ImageGrab fallback) size: {screenshot.size}")
                    else:
                        # Full screen capture (all monitors)
                        logging.info("Capturing full screen (all monitors)")
                        screenshot = pyautogui.screenshot()
                    
                    screenshot.save(filepath)
                    logging.info(f"Screenshot saved: {filepath} ({screenshot.size})")
                    
                    # Update progress state for polling
                    progress_state['message'] = f'Screenshot {screenshot_count["count"]}'
                    progress_state['status'] = 'recording'
                    progress_state['timestamp'] = time.time()
                    progress_state['screenshot_count'] = screenshot_count['count']
                except Exception as e:
                    logging.error(f"Error taking screenshot: {e}")
            
            # Start input logger with screenshot callback (like desktop app)
            input_logger.start_logging(
                output=os.path.join(scribble_dir, "actions.log"),
                screenshot_dir_path=scribble_dir,
                click_callback=take_screenshot
            )
            
            active_sessions[session_id] = {
                'mode': 'screenshot',
                'output_dir': scribble_dir,
                'screenshot_count': screenshot_count,
                'capture_mode': capture_mode,
                'window_region': window_region
            }
        
        # Video mode with screen recording (like desktop app)
        elif mode == 'video':
            from shared.recorder import screen as screen_recorder
            from shared.recorder import audio
            
            capture_mode = data.get('capture_mode', 'fullscreen')
            window_region = data.get('window_region')
            
            logging.info(f"Video mode started: capture_mode={capture_mode}, window_region={window_region}")
            
            # If window mode, set the region and bring window to front
            if capture_mode == 'window' and window_region:
                try:
                    import pygetwindow as gw
                    import win32gui
                    import win32con
                    import win32api
                    import win32process
                    
                    # Find and restore/focus the window (same logic as screenshot mode)
                    windows = gw.getAllWindows()
                    target_window = None
                    
                    for win in windows:
                        matches = False
                        
                        if (win.left == window_region['left'] and 
                            win.top == window_region['top'] and
                            win.width == window_region['width'] and
                            win.height == window_region['height']):
                            matches = True
                        
                        if not matches:
                            try:
                                hwnd = win._hWnd
                                if win32gui.IsIconic(hwnd):
                                    placement = win32gui.GetWindowPlacement(hwnd)
                                    left, top, right, bottom = placement[4]
                                    width = right - left
                                    height = bottom - top
                                    if (left == window_region['left'] and 
                                        top == window_region['top'] and
                                        width == window_region['width'] and
                                        height == window_region['height']):
                                        matches = True
                            except:
                                pass
                        
                        if matches:
                            target_window = win
                            break
                    
                    if target_window:
                        logging.info(f"Bringing window to front for video: {target_window.title}")
                        hwnd = target_window._hWnd
                        
                        # Restore if minimized
                        if win32gui.IsIconic(hwnd):
                            logging.info("Window is minimized, restoring...")
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            import time
                            time.sleep(0.3)
                        
                        # Multi-step window activation process
                        try:
                            current_thread = win32api.GetCurrentThreadId()
                            target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
                            
                            # Attach thread inputs
                            if current_thread != target_thread:
                                win32process.AttachThreadInput(current_thread, target_thread, True)
                            
                            try:
                                # Show window
                                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                                
                                # Alternative: Use keybd_event to release Alt key (Windows workaround)
                                import win32api as w32
                                VK_MENU = 0x12  # Alt key
                                w32.keybd_event(VK_MENU, 0, 0, 0)  # Press Alt
                                
                                # Try multiple methods to bring to foreground
                                win32gui.BringWindowToTop(hwnd)
                                win32gui.SetForegroundWindow(hwnd)
                                
                                # SetFocus and SetActiveWindow may fail for cross-thread windows
                                try:
                                    win32gui.SetFocus(hwnd)
                                except:
                                    pass  # Not critical if this fails
                                
                                try:
                                    win32gui.SetActiveWindow(hwnd)
                                except:
                                    pass  # Not critical if this fails
                                
                                w32.keybd_event(VK_MENU, 0, 2, 0)  # Release Alt
                                
                                logging.info("Window brought to front successfully")
                                
                            finally:
                                # Detach thread inputs
                                if current_thread != target_thread:
                                    win32process.AttachThreadInput(current_thread, target_thread, False)
                            
                            import time
                            time.sleep(0.5)
                            
                        except Exception as focus_error:
                            logging.warning(f"Window focus attempt failed: {focus_error}. Window may not be in foreground.")
                        
                        # Update region to actual position
                        try:
                            rect = win32gui.GetWindowRect(hwnd)
                            window_region['left'] = rect[0]
                            window_region['top'] = rect[1]
                            window_region['width'] = rect[2] - rect[0]
                            window_region['height'] = rect[3] - rect[1]
                            logging.info(f"Updated video window region: {window_region}")
                        except Exception as e:
                            logging.warning(f"Could not update window region: {e}")
                
                except Exception as e:
                    logging.warning(f"Could not bring window to front for video: {e}")
                
                # Set region for screen recorder
                screen_recorder.set_region(
                    window_region['left'],
                    window_region['top'],
                    window_region['width'],
                    window_region['height']
                )
            elif capture_mode == 'fullscreen' and window_region:
                # Handle monitor-specific fullscreen capture
                logging.info(f"Fullscreen capture on specific monitor: {window_region}")
                logging.info(f"Setting video region - left:{window_region['left']}, top:{window_region['top']}, width:{window_region['width']}, height:{window_region['height']}")
                screen_recorder.set_region(
                    window_region['left'],
                    window_region['top'],
                    window_region['width'],
                    window_region['height']
                )
            
            # Start screen and audio recording
            video_path = os.path.join(scribble_dir, "recording.mp4")
            audio_path = os.path.join(scribble_dir, "audio.wav")
            
            # Start screen recording
            # full_screen=True for fullscreen mode (even with specific monitor - uses crop filter)
            # full_screen=False for window mode
            full_screen = (capture_mode == 'fullscreen')
            logging.info(f"Starting screen recording: full_screen={full_screen}, has_region={window_region is not None}")
            screen_recorder.start_screen_recording(output=video_path, full_screen=full_screen)
            
            # Start audio recording (optional - don't fail if no audio device)
            audio_recording_started = False
            try:
                audio.start_audio_recording(output=audio_path)
                audio_recording_started = True
                logging.info("Audio recording started")
            except Exception as audio_error:
                logging.warning(f"Audio recording failed (continuing without audio): {audio_error}")
                audio_path = None
            
            active_sessions[session_id] = {
                'mode': 'video',
                'output_dir': scribble_dir,
                'video_path': video_path,
                'audio_path': audio_path,
                'capture_mode': capture_mode,
                'window_region': window_region,
                'audio_recording_started': audio_recording_started
            }
        
        logging.info(f"Started recording session {session_id} in {scribble_dir}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'output_dir': scribble_dir
        })
    except Exception as e:
        logging.error(f"Error starting recording: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop_recording', methods=['POST'])
def stop_recording():
    """Stop a recording session"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id in active_sessions:
            session_data = active_sessions[session_id]
            
            if session_data['mode'] == 'screenshot':
                input_logger.stop_logging()
                screenshot_count = session_data['screenshot_count']['count']
                
                del active_sessions[session_id]
                logging.info(f"Stopped screenshot session {session_id}")
                
                return jsonify({
                    'success': True,
                    'screenshot_count': screenshot_count
                })
                
            elif session_data['mode'] == 'video':
                from shared.recorder import screen as screen_recorder
                from shared.recorder import audio
                
                # Stop screen recording
                screen_recorder.stop_screen_recording()
                
                # Stop audio recording if it was started
                if session_data.get('audio_recording_started', False):
                    try:
                        audio.stop_audio_recording()
                        logging.info("Audio recording stopped")
                    except Exception as e:
                        logging.warning(f"Error stopping audio recording: {e}")
                
                video_path = session_data.get('video_path')
                audio_path = session_data.get('audio_path')
                
                # Get video duration using ffprobe
                video_duration = 0
                if video_path and os.path.exists(video_path):
                    # Wait for FFmpeg to fully write the moov atom
                    # This is critical for MP4 files - FFmpeg needs time to finalize
                    time.sleep(2.0)
                    
                    try:
                        import subprocess
                        
                        # Get ffprobe path
                        shared_path = get_shared_path()
                        ffprobe_path = os.path.join(shared_path, 'ffmpeg', 'bin', 'ffprobe.exe')
                        
                        if not os.path.exists(ffprobe_path):
                            # Try alternative location
                            ffprobe_path = 'ffprobe'  # Use system PATH
                        
                        logging.info(f"Using ffprobe at: {ffprobe_path}")
                        
                        # Retry up to 3 times with increasing delays
                        for attempt in range(3):
                            cmd = [
                                ffprobe_path,
                                '-v', 'error',
                                '-show_entries', 'format=duration',
                                '-of', 'default=noprint_wrappers=1:nokey=1',
                                video_path
                            ]
                            
                            result = subprocess.run(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                                timeout=5
                            )
                            
                            if result.returncode == 0 and result.stdout.strip():
                                video_duration = float(result.stdout.strip())
                                logging.info(f"Video duration: {video_duration:.2f} seconds (attempt {attempt + 1})")
                                break
                            else:
                                if attempt < 2:
                                    logging.warning(f"ffprobe attempt {attempt + 1} failed, retrying... {result.stderr}")
                                    time.sleep(1.0)
                                else:
                                    logging.warning(f"ffprobe failed after 3 attempts: {result.stderr}")
                    except Exception as e:
                        logging.warning(f"Failed to get video duration: {e}", exc_info=True)
                
                del active_sessions[session_id]
                logging.info(f"Stopped video session {session_id}")
                
                return jsonify({
                    'success': True,
                    'video_path': video_path,
                    'audio_path': audio_path,
                    'duration': video_duration
                })
        else:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
            
    except Exception as e:
        logging.error(f"Error stopping recording: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload_screenshot', methods=['POST'])
def upload_screenshot():
    """Upload a screenshot"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        output_dir = request.form.get('output_dir')
        
        if not output_dir or not os.path.exists(output_dir):
            return jsonify({'success': False, 'error': 'Invalid output directory'}), 400
        
        # Count existing screenshots
        screenshots = [f for f in os.listdir(output_dir) if f.startswith('screenshot_')]
        screenshot_num = len(screenshots) + 1
        
        filename = f"screenshot_{screenshot_num:03d}_{datetime.now().strftime('%H%M%S')}.png"
        filepath = os.path.join(output_dir, filename)
        
        file.save(filepath)
        logging.info(f"Screenshot saved: {filepath}")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': filepath
        })
    except Exception as e:
        logging.error(f"Error uploading screenshot: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate_guide', methods=['POST'])
def generate_guide():
    """Generate AI guide from screenshots"""
    try:
        # Check rate limit before doing anything
        if last_api_call['timestamp']:
            time_since_last = (datetime.now() - last_api_call['timestamp']).total_seconds()
            if time_since_last < last_api_call['cooldown_seconds']:
                wait_time = int(last_api_call['cooldown_seconds'] - time_since_last)
                return jsonify({
                    'success': False,
                    'error': f'Please wait {wait_time} more seconds before retrying to avoid rate limits.',
                    'error_type': 'cooldown',
                    'wait_seconds': wait_time
                }), 429
        
        data = request.json
        output_dir = data.get('output_dir')
        
        if not output_dir:
            return jsonify({'success': False, 'error': 'No output directory specified'}), 400
        
        # Normalize path (convert forward slashes to OS-specific)
        output_dir = os.path.normpath(output_dir)
        
        if not os.path.exists(output_dir):
            return jsonify({'success': False, 'error': f'Invalid output directory: {output_dir}'}), 400
        
        # Check for existing screenshots first (screenshot mode)
        existing_screenshots = sorted([f for f in os.listdir(output_dir) 
                                      if f.startswith('screenshot_') and f.endswith('.png')])
        
        screenshots = []
        temp_dir = None
        
        if existing_screenshots:
            # Use existing screenshots from screenshot mode
            logging.info(f"Found {len(existing_screenshots)} existing screenshots")
            screenshots = [os.path.join(output_dir, f) for f in existing_screenshots[:5]]  # Max 5 to avoid rate limits
        else:
            # Check for video file
            video_path = os.path.join(output_dir, 'recording.mp4')
            if not os.path.exists(video_path):
                return jsonify({'success': False, 'error': 'No video file or screenshots found'}), 400
            
            # Extract frames from video (every 5 seconds)
            import subprocess
            import tempfile
            
            temp_dir = tempfile.mkdtemp()
            frame_pattern = os.path.join(temp_dir, 'frame_%03d.png')
        
            # Use FFmpeg to extract frames
            ffmpeg_path = get_ffmpeg_path()
            if not os.path.exists(ffmpeg_path):
                ffmpeg_path = 'ffmpeg'  # Use system FFmpeg if bundled not found
            
            try:
                # Extract 1 frame every 5 seconds, max 10 frames
                subprocess.run([
                    ffmpeg_path, '-i', video_path,
                    '-vf', 'fps=1/5',  # 1 frame every 5 seconds
                    '-frames:v', '10',  # Max 10 frames
                    '-q:v', '2',  # High quality
                    frame_pattern
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                return jsonify({'success': False, 'error': f'Failed to extract frames from video: {e.stderr.decode() if e.stderr else str(e)}'}), 500
            
            # Get extracted frames
            screenshots = sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.png')])
            
            if not screenshots:
                return jsonify({'success': False, 'error': 'No frames could be extracted from video'}), 400
        
        # Import AI guide generation
        try:
            import google.generativeai as genai
            from PIL import Image
            
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                return jsonify({'success': False, 'error': 'GEMINI_API_KEY not configured'}), 400
            
            genai.configure(api_key=api_key)
            
            # Reload config to get latest model selection
            current_config = load_config()
            model_name = current_config.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')
            logging.info(f"Using Gemini model: {model_name}")
            
            try:
                model = genai.GenerativeModel(model_name)
            except Exception as model_error:
                logging.warning(f"Failed to load model {model_name}: {model_error}. Falling back to gemini-2.0-flash-exp")
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Load images
            images = []
            for screenshot_path in screenshots:
                images.append(Image.open(screenshot_path))
            
            prompt = f"""You are analyzing {len(screenshots)} screenshots to create a professional step-by-step how-to guide.

Carefully examine each screenshot image and create a detailed, educational guide with:

1. A clear, engaging title for the tutorial based on what you see
2. A brief introduction explaining what will be accomplished
3. Step-by-step instructions (one for each screenshot):
   - Start with "Step 1:", "Step 2:", etc.
   - Describe exactly what you SEE in each screenshot
   - Identify specific UI elements, buttons, menus, text fields visible
   - Explain what action should be taken ("Click on...", "Type in...", "Select...")
   - Explain WHY each step matters
   - Use professional but friendly language
4. A brief conclusion or next steps

Analyze the visual content of each screenshot carefully. Reference specific elements you can see like button labels, menu items, window titles, etc.

Write in a natural, human-like style - as if an expert is explaining this to a colleague while showing them the screenshots. Be clear, educational, and encouraging. Keep each step concise but informative (2-4 sentences per step).

IMPORTANT: Write ONLY the guide content. Do NOT include any meta-commentary."""

            logging.info(f"Generating guide for {len(screenshots)} screenshots...")
            
            # Retry logic with exponential backoff for rate limits
            max_retries = 3
            retry_delay = 2  # Start with 2 seconds
            guide_text = None
            
            for attempt in range(max_retries):
                try:
                    response = model.generate_content([prompt] + images)
                    guide_text = response.text.strip()
                    # Update timestamp after successful API call
                    last_api_call['timestamp'] = datetime.now()
                    break  # Success, exit retry loop
                except Exception as gen_error:
                    error_msg = str(gen_error)
                    is_rate_limit = '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower() or 'RESOURCE_EXHAUSTED' in error_msg
                    
                    if is_rate_limit and attempt < max_retries - 1:
                        # Wait and retry
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
                        logging.warning(f"Rate limit hit on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Final attempt failed or non-rate-limit error
                        logging.error(f"Error during guide generation: {error_msg}", exc_info=True)
                        
                        # Check for specific error types
                        if is_rate_limit:
                            return jsonify({
                                'success': False, 
                                'error': 'API rate limit exceeded after retries. Please wait a few minutes and try again.',
                                'error_type': 'rate_limit'
                            }), 429
                        elif 'SAFETY' in error_msg.upper() or 'blocked' in error_msg.lower():
                            return jsonify({
                                'success': False,
                                'error': 'Content was blocked by safety filters. Try different screenshots.',
                                'error_type': 'safety'
                            }), 400
                        elif 'invalid' in error_msg.lower() and 'model' in error_msg.lower():
                            return jsonify({
                                'success': False,
                                'error': f'Invalid model: {model_name}. Please select a different model in settings.',
                                'error_type': 'invalid_model'
                            }), 400
                        else:
                            return jsonify({
                                'success': False,
                                'error': f'Generation failed: {error_msg}',
                                'error_type': 'generation_error'
                            }), 500
            
            # Save guide as both guide.txt and transcript.txt for compatibility
            guide_path = os.path.join(output_dir, 'guide.txt')
            transcript_path = os.path.join(output_dir, 'transcript.txt')
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(guide_text)
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(guide_text)
            
            # Extract title from the first line(s) of the guide
            guide_title = "How-To Guide"
            for line in guide_text.split('\n')[:5]:  # Check first 5 lines
                line_clean = line.strip().lstrip('#').strip()
                if line_clean and not line_clean.startswith('Welcome') and not line_clean.startswith('This guide'):
                    guide_title = line_clean
                    break
            
            # Save title to a separate file for the editor
            title_path = os.path.join(output_dir, 'title.txt')
            with open(title_path, 'w', encoding='utf-8') as f:
                f.write(guide_title)
            
            # Parse guide into individual step notes and save to notes.json
            notes = []
            lines = guide_text.split('\n')
            current_step = 0
            current_note = []
            
            for line in lines:
                line_stripped = line.strip()
                # Remove markdown bold markers and headers
                line_clean = line_stripped.replace('**', '').lstrip('#').strip()
                
                # Check if this is a step header (e.g., "Step 1:", "### Step 2:", etc.)
                if line_clean.startswith('Step ') and ':' in line_clean:
                    # Save previous step if exists
                    if current_note and current_step > 0:
                        notes.append({
                            'step': str(current_step),
                            'note': '\n'.join(current_note).strip(),
                            'type': 'screenshot'
                        })
                        current_note = []
                    
                    # Start new step
                    current_step += 1
                    # Add the step line without the "Step X:" prefix
                    step_content = line_clean.split(':', 1)[1].strip() if ':' in line_clean else line_clean
                    current_note.append(step_content)
                elif current_step > 0 and line_stripped and not line_stripped.startswith('---') and not line_stripped.startswith('!['):
                    # Add content to current step, removing markdown formatting
                    # Skip horizontal rules (---) and image references (![...)
                    clean_content = line_stripped.replace('**', '').lstrip('#').strip()
                    if clean_content:
                        current_note.append(clean_content)
            
            # Save last step
            if current_note and current_step > 0:
                notes.append({
                    'step': str(current_step),
                    'note': '\n'.join(current_note).strip(),
                    'type': 'screenshot'
                })
            
            # Save notes to notes.json
            notes_path = os.path.join(output_dir, 'notes.json')
            with open(notes_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(notes, f, indent=2)
            
            # Clean up temporary frames if created
            if temp_dir:
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    logging.warning(f"Failed to clean up temp directory: {cleanup_error}")
            
            logging.info(f"Guide generated: {guide_path}, {len(notes)} step notes saved to {notes_path}")
            
            return jsonify({
                'success': True,
                'guide': guide_text,
                'guide_path': guide_path,
                'notes_count': len(notes)
            })
            
        except ImportError as e:
            return jsonify({'success': False, 'error': f'Missing dependency: {str(e)}'}), 500
            
    except Exception as e:
        logging.error(f"Error generating guide: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/add_narration', methods=['POST'])
def add_narration():
    """Add AI narration to a video recording"""
    try:
        data = request.json
        output_dir = data.get('output_dir')
        
        if not output_dir:
            return jsonify({'success': False, 'error': 'No output directory specified'}), 400
        
        # Normalize path
        output_dir = os.path.normpath(output_dir)
        
        if not os.path.exists(output_dir):
            return jsonify({'success': False, 'error': 'Invalid output directory'}), 400
        
        transcript_path = os.path.join(output_dir, 'transcript.txt')
        video_path = os.path.join(output_dir, 'recording.mp4')
        
        # Check if video exists
        if not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Video recording not found'}), 400
        
        # Check if transcript exists - if not, create a default one
        if not os.path.exists(transcript_path):
            return jsonify({
                'success': False, 
                'error': 'No transcript found. Please write a transcript or generate a guide first.'
            }), 400
        
        # Import narration module
        from shared.guide import narration
        
        logging.info(f"Adding narration to video in {output_dir}")
        
        try:
            # Generate narrated video
            narrated_video_path = narration.add_narration_to_video(
                scribble_dir=output_dir,
                transcript_path=transcript_path,
                output_name="narrated_video.mp4"
            )
            
            logging.info(f"Narrated video created: {narrated_video_path}")
            
            return jsonify({
                'success': True,
                'narrated_video': narrated_video_path,
                'message': 'Narration added successfully'
            })
            
        except FileNotFoundError as e:
            return jsonify({'success': False, 'error': str(e)}), 404
        except ImportError as e:
            return jsonify({
                'success': False, 
                'error': f'Missing dependency: {str(e)}. Install edge-tts: pip install edge-tts'
            }), 500
        except Exception as e:
            logging.error(f"Error adding narration: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500
            
    except Exception as e:
        logging.error(f"Error in add_narration endpoint: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get_transcript', methods=['GET'])
def get_transcript():
    """Get the transcript file for a video recording"""
    try:
        output_dir = request.args.get('output_dir')
        
        if not output_dir:
            return jsonify({'success': False, 'error': 'No output directory specified'}), 400
        
        if not os.path.exists(output_dir):
            return jsonify({'success': False, 'error': 'Output directory not found'}), 404
        
        transcript_path = os.path.join(output_dir, 'transcript.txt')
        
        if not os.path.exists(transcript_path):
            return jsonify({
                'success': False, 
                'error': 'Transcript not found. Please generate a guide first.'
            }), 404
        
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_content = f.read()
            
            return jsonify({
                'success': True,
                'transcript': transcript_content
            })
        except Exception as read_error:
            logging.error(f"Error reading transcript: {read_error}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Failed to read transcript: {str(read_error)}'
            }), 500
            
    except Exception as e:
        logging.error(f"Error in get_transcript endpoint: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save_transcript', methods=['POST'])
def save_transcript():
    """Save or update the transcript for a video recording"""
    try:
        data = request.json
        output_dir = data.get('output_dir')
        transcript_text = data.get('transcript')
        
        if not output_dir:
            return jsonify({'success': False, 'error': 'No output directory specified'}), 400
        
        # Normalize path
        output_dir = os.path.normpath(output_dir)
        
        if not os.path.exists(output_dir):
            return jsonify({'success': False, 'error': 'Output directory not found'}), 404
        
        if transcript_text is None:
            return jsonify({'success': False, 'error': 'No transcript text provided'}), 400
        
        transcript_path = os.path.join(output_dir, 'transcript.txt')
        
        try:
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            
            logging.info(f"Transcript saved to {transcript_path}")
            
            return jsonify({
                'success': True,
                'message': 'Transcript saved successfully',
                'transcript_path': transcript_path
            })
        except Exception as write_error:
            logging.error(f"Error writing transcript: {write_error}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Failed to write transcript: {str(write_error)}'
            }), 500
            
    except Exception as e:
        logging.error(f"Error in save_transcript endpoint: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate_step_instructions', methods=['POST'])
def generate_step_instructions():
    """Generate AI instructions for a single screenshot"""
    try:
        data = request.json
        image_path = data.get('image_path')
        
        if not image_path or not os.path.exists(image_path):
            return jsonify({'success': False, 'error': 'Invalid image path'}), 400
        
        # Import AI generation
        try:
            import google.generativeai as genai
            from PIL import Image
            
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                return jsonify({'success': False, 'error': 'GEMINI_API_KEY not configured'}), 400
            
            genai.configure(api_key=api_key)
            
            # Get model from config
            current_config = load_config()
            model_name = current_config.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')
            logging.info(f"Using Gemini model for step instructions: {model_name}")
            
            try:
                model = genai.GenerativeModel(model_name)
            except Exception as model_error:
                logging.warning(f"Failed to load model {model_name}: {model_error}. Falling back to gemini-2.0-flash-exp")
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Load image
            image = Image.open(image_path)
            
            prompt = """Analyze this screenshot and provide clear, concise step-by-step instructions for what the user should do.

Focus on:
- Identifying specific UI elements visible (buttons, menus, fields, etc.)
- Describing the exact action to take ("Click on...", "Type into...", "Select...")
- Explaining why this step matters (briefly)

Write 2-4 sentences in a professional but friendly tone, as if guiding a colleague. Be specific about what you see in the image.

IMPORTANT: Write ONLY the instructions. Do NOT include any meta-commentary or labels like "Step 1:"."""

            logging.info(f"Generating instructions for: {image_path}")
            
            # Retry logic with exponential backoff for rate limits
            max_retries = 3
            retry_delay = 2  # Start with 2 seconds
            
            for attempt in range(max_retries):
                try:
                    response = model.generate_content([prompt, image])
                    instructions = response.text.strip()
                    break  # Success, exit retry loop
                except Exception as gen_error:
                    error_msg = str(gen_error)
                    is_rate_limit = '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower() or 'RESOURCE_EXHAUSTED' in error_msg
                    
                    if is_rate_limit and attempt < max_retries - 1:
                        # Wait and retry
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
                        logging.warning(f"Rate limit hit on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Final attempt failed or non-rate-limit error
                        logging.error(f"Error during instruction generation: {error_msg}", exc_info=True)
                        
                        # Check for specific error types
                        if is_rate_limit:
                            return jsonify({
                                'success': False, 
                                'error': 'API rate limit exceeded after retries. Please wait a few minutes and try again.',
                                'error_type': 'rate_limit'
                            }), 429
                        elif 'SAFETY' in error_msg.upper() or 'blocked' in error_msg.lower():
                            return jsonify({
                                'success': False,
                                'error': 'Content was blocked by safety filters. Try different screenshot.',
                                'error_type': 'safety'
                            }), 400
                        else:
                            return jsonify({
                                'success': False,
                                'error': f'Generation failed: {error_msg}',
                                'error_type': 'generation_error'
                            }), 500
            
            return jsonify({
                'success': True,
                'instructions': instructions
            })
            
        except ImportError as e:
            return jsonify({'success': False, 'error': f'Missing dependency: {str(e)}'}), 500
            
    except Exception as e:
        logging.error(f"Error generating step instructions: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate_step_instructions_base64', methods=['POST'])
def generate_step_instructions_base64():
    """Generate AI instructions for a screenshot from base64 data"""
    try:
        data = request.json
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
        
        # Import AI generation
        try:
            import google.generativeai as genai
            from PIL import Image
            import io
            import base64
            
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                return jsonify({'success': False, 'error': 'GEMINI_API_KEY not configured'}), 400
            
            genai.configure(api_key=api_key)
            
            # Get model from config
            current_config = load_config()
            model_name = current_config.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')
            logging.info(f"Using Gemini model for step instructions: {model_name}")
            
            try:
                model = genai.GenerativeModel(model_name)
            except Exception as model_error:
                logging.warning(f"Failed to load model {model_name}: {model_error}. Falling back to gemini-2.0-flash-exp")
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Convert base64 to image
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            prompt = """Analyze this screenshot and provide clear, concise step-by-step instructions for what the user should do.

Focus on:
- Identifying specific UI elements visible (buttons, menus, fields, etc.)
- Describing the exact action to take ("Click on...", "Type into...", "Select...")
- Explaining why this step matters (briefly)

Write 2-4 sentences in a professional but friendly tone, as if guiding a colleague. Be specific about what you see in the image.

IMPORTANT: Write ONLY the instructions. Do NOT include any meta-commentary or labels like "Step 1:"."""

            logging.info(f"Generating instructions for uploaded image")
            
            try:
                response = model.generate_content([prompt, image])
                instructions = response.text.strip()
            except Exception as gen_error:
                error_msg = str(gen_error)
                logging.error(f"Error during instruction generation: {error_msg}", exc_info=True)
                
                # Check for specific error types
                if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                    return jsonify({
                        'success': False, 
                        'error': 'API rate limit exceeded. Please wait a few minutes and try again.',
                        'error_type': 'rate_limit'
                    }), 429
                elif 'SAFETY' in error_msg.upper() or 'blocked' in error_msg.lower():
                    return jsonify({
                        'success': False,
                        'error': 'Content was blocked by safety filters. Try different screenshot.',
                        'error_type': 'safety'
                    }), 400
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Generation failed: {error_msg}',
                        'error_type': 'generation_error'
                    }), 500
            
            return jsonify({
                'success': True,
                'instructions': instructions
            })
            
        except ImportError as e:
            return jsonify({'success': False, 'error': f'Missing dependency: {str(e)}'}), 500
            
    except Exception as e:
        logging.error(f"Error generating step instructions from base64: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/list_recordings', methods=['GET'])
def list_recordings():
    """List all recordings"""
    try:
        # Use the same base directory as start_session
        configured_folder = config.get('OUTPUT_FOLDER', os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs"))
        base_dir = configured_folder
        
        if not os.path.exists(base_dir):
            return jsonify({'success': True, 'recordings': []})
        
        recordings = []
        for date_folder in sorted(os.listdir(base_dir), reverse=True):
            date_path = os.path.join(base_dir, date_folder)
            if not os.path.isdir(date_path):
                continue
            
            for scribble_folder in sorted(os.listdir(date_path)):
                scribble_path = os.path.join(date_path, scribble_folder)
                if not os.path.isdir(scribble_path):
                    continue
                
                # Count files
                file_count = sum(1 for f in os.listdir(scribble_path) if os.path.isfile(os.path.join(scribble_path, f)))
                
                recordings.append({
                    'date': date_folder,
                    'name': scribble_folder,
                    'path': scribble_path,
                    'file_count': file_count
                })
        
        return jsonify({'success': True, 'recordings': recordings})
    except Exception as e:
        logging.error(f"Error listing recordings: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/detect_recording_type', methods=['POST'])
def detect_recording_type():
    """Detect if a recording is video or screenshot based"""
    try:
        data = request.json
        path = data.get('path')
        
        if not path or not os.path.exists(path):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        
        # Check for video file
        has_video = os.path.exists(os.path.join(path, 'recording.mp4'))
        
        # Check for screenshots
        has_screenshots = any(f.startswith('screenshot_') and f.endswith('.png') 
                            for f in os.listdir(path))
        
        if has_video:
            recording_type = 'video'
        elif has_screenshots:
            recording_type = 'screenshot'
        else:
            recording_type = 'unknown'
        
        return jsonify({
            'success': True,
            'type': recording_type,
            'has_video': has_video,
            'has_screenshots': has_screenshots
        })
    except Exception as e:
        logging.error(f"Error detecting recording type: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/gemini_quota', methods=['GET'])
def get_gemini_quota():
    """Get Gemini API quota and usage information"""
    try:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return jsonify({
                'success': False, 
                'error': 'API key not configured',
                'status': 'No API Key'
            })
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Get current model
            current_config = load_config()
            model_name = current_config.get('GEMINI_MODEL', 'gemini-2.5-flash')
            
            # Try to actually list models to test if we're rate limited
            try:
                # This will fail if rate limited
                models = list(genai.list_models())
                
                return jsonify({
                    'success': True,
                    'status': 'Active',
                    'model': model_name,
                    'note': 'Free tier: 15 requests per minute, 1500 requests per day',
                    'info': 'Quota resets daily. If you hit limits, wait a few minutes or upgrade at https://ai.google.dev/pricing'
                })
            except Exception as test_error:
                error_msg = str(test_error)
                # Check if it's a rate limit error
                if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower() or 'resource' in error_msg.lower() and 'exhaust' in error_msg.lower():
                    return jsonify({
                        'success': True,
                        'status': 'Rate Limited',
                        'error': 'API quota exceeded. Wait a few minutes.',
                        'info': 'Free tier limits: 15 requests/min, 1500 requests/day. Try again in 1-2 minutes.',
                        'model': model_name
                    })
                else:
                    raise test_error
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error checking quota: {error_msg}")
            
            if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                return jsonify({
                    'success': True,
                    'status': 'Rate Limited',
                    'error': 'API quota exceeded. Wait a few minutes.',
                    'info': 'Free tier limits: 15 requests/min, 1500 requests/day'
                })
            else:
                return jsonify({
                    'success': False,
                    'status': 'Error',
                    'error': error_msg
                })
            
    except Exception as e:
        logging.error(f"Error checking quota: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'status': 'Error'}), 500

@app.route('/api/gemini_models', methods=['GET'])
def get_gemini_models():
    """Get available Gemini models"""
    import time
    
    try:
        # Check cache first
        if models_cache['models'] and (time.time() - models_cache['timestamp'] < CACHE_DURATION):
            logging.info("Returning cached models list")
            return jsonify({'success': True, 'models': models_cache['models'], 'cached': True})
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            # Return fallback models if no API key
            fallback_models = [
                {'name': 'gemini-2.5-flash', 'display_name': 'Gemini 2.5 Flash', 'description': 'Latest stable multimodal model'},
                {'name': 'gemini-2.5-pro', 'display_name': 'Gemini 2.5 Pro', 'description': 'Most capable model'},
                {'name': 'gemini-2.0-flash', 'display_name': 'Gemini 2.0 Flash', 'description': 'Fast and versatile'},
                {'name': 'gemini-2.0-flash-exp', 'display_name': 'Gemini 2.0 Flash Experimental', 'description': 'Experimental features'}
            ]
            return jsonify({'success': True, 'models': fallback_models, 'fallback': True})
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # List all available models that support generateContent
            models = []
            for model in genai.list_models():
                # Only include models that support generateContent
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.replace('models/', '')
                    display_name = model.display_name
                    description = model.description if model.description else ''
                    
                    # Skip embedding and specialized models
                    if any(skip in model_name.lower() for skip in ['embedding', 'aqa', 'imagen', 'veo', 'live', 'tts', 'audio', 'robotics', 'computer-use']):
                        continue
                    
                    models.append({
                        'name': model_name,
                        'display_name': display_name,
                        'description': description[:100] if description else ''
                    })
            
            # Sort models - put stable releases first, then experimental
            models.sort(key=lambda x: (
                'exp' in x['name'].lower() or 'preview' in x['name'].lower(),
                x['name']
            ))
            
            # Cache the results
            models_cache['models'] = models
            models_cache['timestamp'] = time.time()
            
            logging.info(f"Found {len(models)} available Gemini models (cached)")
            return jsonify({'success': True, 'models': models})
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error fetching Gemini models: {error_msg}")
            
            # Check if it's a rate limit error (429)
            if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                logging.warning("Rate limit hit - using fallback models")
            
            # Return fallback models if API call fails
            fallback_models = [
                {'name': 'gemini-2.5-flash', 'display_name': 'Gemini 2.5 Flash', 'description': 'Latest stable multimodal model'},
                {'name': 'gemini-2.5-pro', 'display_name': 'Gemini 2.5 Pro', 'description': 'Most capable model'},
                {'name': 'gemini-2.0-flash', 'display_name': 'Gemini 2.0 Flash', 'description': 'Fast and versatile'},
                {'name': 'gemini-2.0-flash-exp', 'display_name': 'Gemini 2.0 Flash Experimental', 'description': 'Experimental features'},
                {'name': 'gemini-flash-latest', 'display_name': 'Gemini Flash Latest', 'description': 'Always points to latest Flash'},
                {'name': 'gemini-pro-latest', 'display_name': 'Gemini Pro Latest', 'description': 'Always points to latest Pro'}
            ]
            
            # Cache fallback models too
            models_cache['models'] = fallback_models
            models_cache['timestamp'] = time.time()
            
            return jsonify({'success': True, 'models': fallback_models, 'fallback': True})
            
    except Exception as e:
        logging.error(f"Error in get_gemini_models: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'models': []}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update configuration"""
    try:
        if request.method == 'GET':
            include_api_key = request.args.get('includeApiKey') == 'true'
            config_data = config.copy()
            
            # Default to current user's Downloads folder if not set
            if 'OUTPUT_FOLDER' not in config_data or not config_data['OUTPUT_FOLDER']:
                config_data['OUTPUT_FOLDER'] = os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs")
            
            if not include_api_key and 'GEMINI_API_KEY' in config_data:
                del config_data['GEMINI_API_KEY']
            return jsonify({
                'success': True,
                'config': config_data
            })
        else:
            data = request.json
            config_path = get_config_path()
            
            # Read existing lines
            lines = []
            keys_found = set()
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    lines = f.readlines()
            
            # Update existing keys
            updated_lines = []
            for line in lines:
                if line.strip().startswith('#') or '=' not in line:
                    updated_lines.append(line)
                else:
                    key = line.split('=')[0].strip()
                    keys_found.add(key)
                    if key in data:
                        updated_lines.append(f"{key}={data[key]}\n")
                        config[key] = data[key]
                        if key == 'GEMINI_API_KEY':
                            os.environ['GEMINI_API_KEY'] = data[key]
                    else:
                        updated_lines.append(line)
            
            # Add new keys
            for key, value in data.items():
                if key not in keys_found:
                    updated_lines.append(f"{key}={value}\n")
                    config[key] = value
                    if key == 'GEMINI_API_KEY':
                        os.environ['GEMINI_API_KEY'] = value
            
            # Write config to AppData location
            with open(config_path, 'w') as f:
                f.writelines(updated_lines)
            
            logging.info(f"Configuration saved to: {config_path}")
            return jsonify({'success': True, 'message': 'Configuration updated'})
    except Exception as e:
        logging.error(f"Error handling config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/select_folder', methods=['POST'])
def select_folder():
    """Open folder selection dialog using tkinter"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Create hidden root window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Open folder dialog
        folder_path = filedialog.askdirectory(
            title='Select Output Folder',
            initialdir=config.get('OUTPUT_FOLDER', os.path.expanduser('~'))
        )
        
        # Destroy root window
        root.destroy()
        
        if folder_path:
            # Convert to Windows path format
            folder_path = os.path.normpath(folder_path)
            return jsonify({'success': True, 'folder_path': folder_path})
        else:
            return jsonify({'success': False, 'error': 'No folder selected'})
    except Exception as e:
        logging.error(f"Error selecting folder: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete_recordings', methods=['POST'])
def delete_recordings():
    """Delete selected recordings"""
    try:
        data = request.json
        paths = data.get('paths', [])
        
        import shutil
        deleted = 0
        parent_dirs_to_check = set()
        
        for path in paths:
            if os.path.exists(path) and os.path.isdir(path):
                # Store parent directory before deleting
                parent_dir = os.path.dirname(path)
                parent_dirs_to_check.add(parent_dir)
                
                shutil.rmtree(path)
                deleted += 1
                logging.info(f"Deleted recording: {path}")
        
        # Clean up empty parent directories (date folders)
        for parent_dir in parent_dirs_to_check:
            try:
                if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
                    # Check if directory is empty
                    if not os.listdir(parent_dir):
                        os.rmdir(parent_dir)
                        logging.info(f"Removed empty folder: {parent_dir}")
            except Exception as cleanup_error:
                logging.warning(f"Could not remove empty folder {parent_dir}: {cleanup_error}")
        
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e:
        logging.error(f"Error deleting recordings: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browse_output')
def browse_output():
    """Browse output folder"""
    try:
        base_dir = config.get('OUTPUT_FOLDER', os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs"))
        outputs_dir = os.path.normpath(base_dir)
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Output Folder Browser</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; padding: 0; background: #F5F5F5; margin: 0; }}
                .header {{ background: #005A9C; color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .content {{ padding: 30px; }}
                .path {{ background: white; padding: 15px; border-radius: 4px; margin-bottom: 20px; border: 1px solid #ddd; }}
                .folder {{ background: white; padding: 12px; margin: 8px 0; border-radius: 4px; border-left: 4px solid #005A9C; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .scribble {{ margin-left: 30px; padding: 8px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; }}
                .scribble:last-child {{ border-bottom: none; }}
                .type-badge {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-left: 8px; }}
                .type-video {{ background: #48bb78; color: white; }}
                .type-screenshot {{ background: #ed8936; color: white; }}
                .edit-btn {{ padding: 6px 12px; background: #005A9C; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; text-decoration: none; transition: background 0.3s; }}
                .edit-btn:hover {{ background: #004080; }}
                .back-btn {{ padding: 10px 20px; background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500; text-decoration: none; display: inline-block; transition: all 0.3s; }}
                .back-btn:hover {{ background: rgba(255,255,255,0.3); }}
                h2 {{ color: white; margin: 0; font-size: 1.5em; font-weight: 400; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📁 Output Folder</h2>
                <a href="/" class="back-btn">⬅ Back to Home</a>
            </div>
            <div class="content">
                <div class="path"><strong>Location:</strong> {outputs_dir}</div>
        '''
        
        if os.path.exists(outputs_dir):
            html += '<h3 style="color: #005A9C; margin: 20px 0 15px 0;">Recent Recordings:</h3>'
            for date_folder in sorted(os.listdir(outputs_dir), reverse=True)[:10]:
                date_path = os.path.join(outputs_dir, date_folder)
                if os.path.isdir(date_path):
                    html += f'<div class="folder"><strong>{date_folder}</strong><br>'
                    for scribble in sorted(os.listdir(date_path)):
                        scribble_path = os.path.join(date_path, scribble)
                        if os.path.isdir(scribble_path):
                            # Detect recording type
                            has_video = os.path.exists(os.path.join(scribble_path, 'recording.mp4'))
                            has_screenshots = any(f.startswith('screenshot_') for f in os.listdir(scribble_path))
                            
                            files = len([f for f in os.listdir(scribble_path) if os.path.isfile(os.path.join(scribble_path, f))])
                            
                            # Determine editor type and badge
                            if has_video:
                                editor_type = 'video'
                                badge = '<span class="type-badge type-video">📹 VIDEO</span>'
                            elif has_screenshots:
                                editor_type = 'screenshot'
                                badge = '<span class="type-badge type-screenshot">📸 SCREENSHOTS</span>'
                            else:
                                editor_type = None
                                badge = '<span class="type-badge" style="background: #ccc; color: #666;">❓ UNKNOWN</span>'
                            
                            # Create edit button if we know the type
                            edit_btn = ''
                            if editor_type == 'video':
                                video_rel_path = os.path.join(date_folder, scribble, 'recording.mp4').replace('\\', '/')
                                edit_btn = f'<a href="/video_editor?path={video_rel_path}" class="edit-btn">✏️ Edit Video</a>'
                            elif editor_type == 'screenshot':
                                # Link to HTML editor for screenshots
                                scribble_rel_path = os.path.join(date_folder, scribble).replace('\\', '/')
                                edit_btn = f'<a href="/editor?path={scribble_path}" class="edit-btn">📝 Edit Guide</a>'
                            
                            html += f'<div class="scribble"><span>{scribble} {badge} ({files} files)</span>{edit_btn}</div>'
                    html += '</div>'
        else:
            html += '<p style="color: #666;">Folder does not exist yet. It will be created when you make your first recording.</p>'
        
        html += '</div></body></html>'
        return html
    except Exception as e:
        logging.error(f"Error browsing output: {e}", exc_info=True)
        return f"Error: {{str(e)}}", 500

@app.route('/api/open_folder', methods=['POST'])
def open_folder():
    """Open folder in Windows Explorer"""
    try:
        import subprocess
        import platform
        
        data = request.json
        folder_path = data.get('path')
        
        if not folder_path or not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'}), 404
        
        # Open folder in Windows Explorer
        if platform.system() == 'Windows':
            subprocess.Popen(['explorer', os.path.normpath(folder_path)])
        elif platform.system() == 'Darwin':  # macOS
            subprocess.Popen(['open', folder_path])
        else:  # Linux
            subprocess.Popen(['xdg-open', folder_path])
        
        return jsonify({'success': True, 'message': 'Folder opened'})
    except Exception as e:
        logging.error(f"Error opening folder: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/serve_video/<path:filename>')
def serve_video(filename):
    """Serve video file for playback"""
    try:
        # Get the full path
        base_dir = config.get('OUTPUT_FOLDER', os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs"))
        video_path = os.path.join(base_dir, filename)
        
        if not os.path.exists(video_path):
            return "Video not found", 404
        
        return send_file(video_path, mimetype='video/mp4')
    except Exception as e:
        logging.error(f"Error serving video: {e}", exc_info=True)
        return str(e), 500

@app.route('/api/get_video_info', methods=['POST'])
def get_video_info():
    """Get video metadata (duration, fps, resolution)"""
    try:
        import subprocess
        data = request.json
        video_path = data.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        # Use ffprobe to get video info
        ffprobe_path = get_ffprobe_path()
        
        cmd = [
            ffprobe_path,
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate,duration',
            '-of', 'json',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        video_info = json.loads(result.stdout)
        
        stream = video_info['streams'][0]
        fps_parts = stream['r_frame_rate'].split('/')
        fps = float(fps_parts[0]) / float(fps_parts[1])
        
        return jsonify({
            'success': True,
            'duration': float(stream.get('duration', 0)),
            'width': stream['width'],
            'height': stream['height'],
            'fps': fps
        })
    except Exception as e:
        logging.error(f"Error getting video info: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cut_video', methods=['POST'])
def cut_video():
    """Cut video segment"""
    try:
        import subprocess
        data = request.json
        video_path = data.get('video_path')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        output_name = data.get('output_name', 'cut_video.mp4')
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        video_dir = os.path.dirname(video_path)
        output_path = os.path.join(video_dir, output_name)
        
        ffmpeg_path = get_ffmpeg_path()
        
        # Cut video using ffmpeg - use re-encoding for accurate cuts
        cmd = [
            ffmpeg_path,
            '-ss', str(start_time),
            '-i', video_path,
            '-to', str(end_time - start_time),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"FFmpeg cut error: {result.stderr}")
            return jsonify({'success': False, 'error': f'FFmpeg error: {result.stderr}'}), 500
        
        # Verify output file was created and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
            return jsonify({'success': False, 'error': 'Output file was not created properly'}), 500
        
        return jsonify({
            'success': True,
            'output_path': output_path,
            'message': 'Video cut successfully'
        })
    except Exception as e:
        logging.error(f"Error cutting video: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/merge_videos', methods=['POST'])
def merge_videos():
    """Merge multiple video segments"""
    try:
        import subprocess
        data = request.json
        video_paths = data.get('video_paths', [])
        output_name = data.get('output_name', 'merged_video.mp4')
        
        if not video_paths or len(video_paths) < 2:
            return jsonify({'success': False, 'error': 'Need at least 2 videos to merge'}), 400
        
        # Create concat file
        video_dir = os.path.dirname(video_paths[0])
        concat_file = os.path.join(video_dir, 'concat_list.txt')
        
        with open(concat_file, 'w') as f:
            for path in video_paths:
                # Normalize path for FFmpeg (use forward slashes, escape special chars)
                norm_path = os.path.normpath(path).replace('\\', '/')
                f.write(f"file '{norm_path}'\n")
        
        output_path = os.path.join(video_dir, output_name)
        
        # Get ffmpeg path
        ffmpeg_path = get_ffmpeg_path()
        if not os.path.exists(ffmpeg_path):
            ffmpeg_path = 'ffmpeg'
        
        cmd = [
            ffmpeg_path,
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up concat file
        try:
            os.remove(concat_file)
        except:
            pass
        
        if result.returncode != 0:
            logging.error(f"FFmpeg merge error: {result.stderr}")
            return jsonify({'success': False, 'error': f'FFmpeg error: {result.stderr}'}), 500
        
        # Get duration of merged video
        duration = 0
        if os.path.exists(output_path):
            try:
                probe_cmd = [
                    ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe') if ffmpeg_path.endswith('.exe') else 'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    output_path
                ]
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                if probe_result.returncode == 0:
                    duration = float(probe_result.stdout.strip())
            except:
                pass
        
        return jsonify({
            'success': True,
            'output_path': output_path,
            'duration': duration,
            'message': 'Videos merged successfully'
        })
    except Exception as e:
        logging.error(f"Error merging videos: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/adjust_audio_sync', methods=['POST'])
def adjust_audio_sync():
    """Adjust audio sync offset"""
    try:
        import subprocess
        data = request.json
        video_path = data.get('video_path')
        audio_offset = data.get('audio_offset', 0)  # in seconds
        output_name = data.get('output_name', 'synced_video.mp4')
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        video_dir = os.path.dirname(video_path)
        output_path = os.path.join(video_dir, output_name)
        
        ffmpeg_path = get_ffmpeg_path()
        
        # Adjust audio sync
        cmd = [
            ffmpeg_path,
            '-i', video_path,
            '-itsoffset', str(audio_offset),
            '-i', video_path,
            '-map', '0:v',
            '-map', '1:a',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-y',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        return jsonify({
            'success': True,
            'output_path': output_path,
            'message': f'Audio synced with {audio_offset}s offset'
        })
    except Exception as e:
        logging.error(f"Error adjusting audio sync: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/replace_audio', methods=['POST'])
def replace_audio():
    """Replace video audio with new audio file"""
    try:
        import subprocess
        
        # Check if this is a file upload or JSON request
        if 'audio' in request.files:
            # File upload from frontend
            audio_file = request.files['audio']
            video_path = request.form.get('video_path')
            
            if not video_path or not os.path.exists(video_path):
                return jsonify({'success': False, 'error': 'Video not found'}), 404
            
            # Normalize path
            video_path = os.path.normpath(video_path)
            video_dir = os.path.dirname(video_path)
            
            # Save uploaded audio temporarily
            audio_path = os.path.join(video_dir, 'temp_audio_' + audio_file.filename)
            audio_file.save(audio_path)
        else:
            # JSON request with audio_path
            data = request.json
            video_path = data.get('video_path')
            audio_path = data.get('audio_path')
            
            if not video_path or not os.path.exists(video_path):
                return jsonify({'success': False, 'error': 'Video not found'}), 404
            
            if not audio_path or not os.path.exists(audio_path):
                return jsonify({'success': False, 'error': 'Audio not found'}), 404
            
            video_dir = os.path.dirname(video_path)
        
        output_name = f'audio_replaced_{int(time.time())}.mp4'
        output_path = os.path.join(video_dir, output_name)
        
        # Get ffmpeg path
        ffmpeg_path = get_ffmpeg_path()
        if not os.path.exists(ffmpeg_path):
            # Try alternative path
            ffmpeg_path = 'ffmpeg'
        
        cmd = [
            ffmpeg_path,
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temporary audio if it was uploaded
        if 'audio' in request.files and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
        
        if result.returncode != 0:
            logging.error(f"FFmpeg error: {result.stderr}")
            return jsonify({'success': False, 'error': f'FFmpeg error: {result.stderr}'}), 500
        
        return jsonify({
            'success': True,
            'output_path': output_path,
            'message': 'Audio replaced successfully'
        })
    except Exception as e:
        logging.error(f"Error replacing audio: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save_recorded_audio', methods=['POST'])
def save_recorded_audio():
    """Save recorded audio from browser"""
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file'}), 400
        
        audio_file = request.files['audio']
        video_dir = request.form.get('video_dir')
        
        if not video_dir:
            return jsonify({'success': False, 'error': 'No directory specified'}), 400
        
        # Normalize path (convert forward slashes to OS-specific)
        video_dir = os.path.normpath(video_dir)
        
        if not os.path.exists(video_dir):
            return jsonify({'success': False, 'error': f'Invalid directory: {video_dir}'}), 400
        
        audio_path = os.path.join(video_dir, 'recorded_audio.wav')
        audio_file.save(audio_path)
        
        return jsonify({
            'success': True,
            'audio_path': audio_path,
            'message': 'Audio saved successfully'
        })
    except Exception as e:
        logging.error(f"Error saving recorded audio: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/video_editor')
def video_editor():
    """Advanced video editor page with timeline editing"""
    try:
        video_path = request.args.get('path')
        if not video_path:
            return "No video path provided", 400
        
        # Get base output folder
        base_dir = config.get('OUTPUT_FOLDER', os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs"))
        
        # If path is relative, make it absolute
        if not os.path.isabs(video_path):
            video_path = os.path.join(base_dir, video_path)
        
        # Normalize the path
        video_path = os.path.normpath(video_path)
        video_dir = os.path.dirname(video_path)
        
        # Check for existing files
        transcript_path = os.path.join(video_dir, 'transcript.txt')
        narrated_path = os.path.join(video_dir, 'narrated_video.mp4')
        has_transcript = os.path.exists(transcript_path)
        has_narrated = os.path.exists(narrated_path)
        
        # Get relative path from base output folder for serve_video endpoint
        rel_path = os.path.relpath(video_path, base_dir)
        
        # Normalize paths for JavaScript (use forward slashes)
        video_path_js = video_path.replace('\\', '/')
        video_dir_js = video_dir.replace('\\', '/')
        
        return render_template('video_editor.html',
            video_path=video_path_js,
            video_dir=video_dir_js,
            video_rel_path=rel_path.replace(os.sep, '/'),
            has_transcript=has_transcript,
            has_narrated=has_narrated,
            duration=0  # Will be loaded via JS
        )
    except Exception as e:
        logging.error(f"Error loading video editor: {e}", exc_info=True)
        return f"Error: {str(e)}", 500

@app.route('/api/view_logs')
def view_logs():
    """View log file"""
    try:
        log_file = os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs", "hallmark_scribble_web.log")
        
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hallmark Scribble Logs</title>
            <style>
                body { font-family: 'Consolas', 'Courier New', monospace; padding: 0; background: #F5F5F5; margin: 0; }
                .header { background: #005A9C; color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .content { padding: 30px; }
                .log { background: #2d2d2d; padding: 20px; border-radius: 4px; white-space: pre-wrap; font-size: 12px; max-height: 70vh; overflow-y: auto; border: 1px solid #444; }
                .back-btn { padding: 10px 20px; background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500; text-decoration: none; display: inline-block; transition: all 0.3s; }
                .back-btn:hover { background: rgba(255,255,255,0.3); }
                h2 { color: white; margin: 0; font-size: 1.5em; font-weight: 400; }
                .info { color: #4EC9B0; }
                .error { color: #F48771; }
                .warning { color: #CE9178; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📋 Hallmark Scribble Web Logs</h2>
                <a href="/" class="back-btn">⬅ Back to Home</a>
            </div>
            <div class="content">
                <div class="log">'''
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()[-200:]  # Last 200 lines
                for line in lines:
                    if 'ERROR' in line:
                        html += f'<span class="error">{line}</span>'
                    elif 'WARNING' in line:
                        html += f'<span class="warning">{line}</span>'
                    else:
                        html += f'<span class="info">{line}</span>'
        else:
            html += f'Log file not found: {log_file}'
        
        html += '</div></div></body></html>'
        return html
    except Exception as e:
        logging.error(f"Error viewing logs: {e}", exc_info=True)
        return f"Error: {str(e)}", 500

@app.route('/editor')
def editor():
    """Open HTML editor for a guide"""
    try:
        output_dir = request.args.get('path')
        
        if not output_dir:
            return "No path provided", 400
            
        # Import the editor module
        from shared.guide.html_editor import create_html_editor
        
        if not os.path.exists(output_dir):
            return f"Output directory not found: {output_dir}", 404
        
        # Generate the editor HTML
        editor_html = create_html_editor(output_dir)
        return editor_html
    except Exception as e:
        logging.error(f"Error opening editor: {e}", exc_info=True)
        return f"Error opening editor: {str(e)}<br><br>Path: {output_dir if 'output_dir' in locals() else 'N/A'}", 500

@app.route('/api/editor/save', methods=['POST'])
def save_editor_changes():
    """Save changes from the editor"""
    try:
        data = request.json
        output_dir = data.get('output_dir')
        title = data.get('title', '')
        transcript = data.get('transcript', '')
        notes = data.get('notes', [])
        
        if not output_dir or not os.path.exists(output_dir):
            return jsonify({'success': False, 'error': 'Invalid output directory'}), 400
        
        # Save title
        if title:
            title_path = os.path.join(output_dir, 'title.txt')
            with open(title_path, 'w', encoding='utf-8') as f:
                f.write(title)
        
        # Save transcript
        transcript_path = os.path.join(output_dir, 'transcript.txt')
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        # Save notes if provided
        if notes:
            notes_path = os.path.join(output_dir, 'notes.json')
            import json
            with open(notes_path, 'w', encoding='utf-8') as f:
                json.dump(notes, f, indent=2)
        
        logging.info(f"Editor changes saved to {output_dir}")
        
        return jsonify({'success': True, 'message': 'Changes saved'})
    except Exception as e:
        logging.error(f"Error saving editor changes: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/editor/save_image', methods=['POST'])
def save_annotated_image():
    """Save an annotated/edited image"""
    try:
        data = request.json
        filename = data.get('filename')
        data_url = data.get('dataURL')
        scribble_dir = data.get('scribbleDir')
        
        if not all([filename, data_url, scribble_dir]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Normalize path (convert forward slashes to OS-specific)
        scribble_dir = os.path.normpath(scribble_dir)
        
        if not os.path.exists(scribble_dir):
            return jsonify({'success': False, 'error': f'Output directory not found: {scribble_dir}'}), 404
        
        # Decode base64 image
        import base64
        import re
        
        # Remove data URL prefix
        image_data = re.sub('^data:image/.+;base64,', '', data_url)
        image_bytes = base64.b64decode(image_data)
        
        # Save image
        filepath = os.path.join(scribble_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        logging.info(f"Annotated image saved: {filepath}")
        
        return jsonify({'success': True, 'message': 'Image saved', 'path': filepath})
    except Exception as e:
        logging.error(f"Error saving annotated image: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/editor/image/<path:filepath>')
def serve_image(filepath):
    """Serve images for the editor"""
    try:
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/png')
        return "Image not found", 404
    except Exception as e:
        logging.error(f"Error serving image: {e}", exc_info=True)
        return str(e), 500

@app.route('/api/log_client_error', methods=['POST'])
def log_client_error():
    """Log JavaScript errors from the browser"""
    try:
        data = request.json
        message = data.get('message', 'Unknown error')
        source = data.get('source', 'Unknown source')
        line = data.get('line', '?')
        column = data.get('column', '?')
        stack = data.get('stack', '')
        
        logging.error(f"CLIENT ERROR: {message}")
        logging.error(f"  Source: {source}:{line}:{column}")
        if stack:
            logging.error(f"  Stack: {stack}")
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error logging client error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/restart', methods=['POST'])
def restart():
    """Restart the web server"""
    try:
        logging.info("Server restart requested")
        
        # Stop any active recording sessions
        input_logger.stop_logging()
        
        # Note: Restarting a Flask server gracefully requires external process management
        # For now, inform the user to manually restart
        return jsonify({
            'success': True, 
            'message': 'To restart the server, please close and reopen the application.'
        })
    except Exception as e:
        logging.error(f"Error processing restart request: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate_sop', methods=['POST'])
def generate_sop():
    """Generate a Standard Operating Procedure from a guide with screenshots"""
    try:
        data = request.json
        guide_content = data.get('guide_content', '')
        title = data.get('title', 'Procedure')
        output_dir = data.get('output_dir', '')
        
        if not guide_content:
            return jsonify({'success': False, 'error': 'No guide content provided'}), 400
        
        if not output_dir or not os.path.exists(output_dir):
            return jsonify({'success': False, 'error': 'Invalid output directory'}), 400
        
        # Get screenshots from output directory
        all_files = os.listdir(output_dir) if os.path.exists(output_dir) else []
        screenshots = sorted([f for f in all_files 
                            if f.startswith('screenshot_') and (f.endswith('.png') or f.endswith('.jpg') or f.endswith('.jpeg'))])
        
        # If no screenshots found with screenshot_ prefix, try looking for any image files
        if not screenshots:
            screenshots = sorted([f for f in all_files 
                                if f.endswith(('.png', '.jpg', '.jpeg')) and not f.startswith('.')])
        
        logging.info(f"SOP Generation - Output dir: {output_dir}")
        logging.info(f"SOP Generation - All files: {all_files}")
        logging.info(f"SOP Generation - Found {len(screenshots)} screenshots: {screenshots}")
        
        # Load notes.json if available for fallback
        notes_path = os.path.join(output_dir, 'notes.json')
        notes = []
        if os.path.exists(notes_path):
            try:
                with open(notes_path, 'r', encoding='utf-8') as f:
                    notes = json.load(f)
                logging.info(f"Loaded {len(notes)} notes from {notes_path}")
            except Exception as notes_error:
                logging.warning(f"Failed to load notes.json: {notes_error}")
        
        sop_content = None
        ai_generated = False
        
        # Try to use Gemini AI to generate SOP from the guide
        try:
            import google.generativeai as genai
            
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                model_name = config.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')
                model = genai.GenerativeModel(model_name)
                
                # Create prompt for SOP generation
                prompt = f"""You are an expert technical writer. Convert the following how-to guide into a formal Standard Operating Procedure (SOP).

The SOP should follow this format:
- Title: {title}
- Purpose (what this procedure accomplishes)
- Scope (when and where to use this)
- Responsibilities (who performs this)
- Prerequisites (what's needed before starting)
- Procedure (numbered steps with clear instructions)
- References/Notes (if applicable)

Make the language professional, clear, and concise. Each step should be actionable and specific.

HERE IS THE GUIDE:
{guide_content}

Generate a well-formatted SOP document in HTML format with proper headings (<h1>, <h2>), paragraphs (<p>), and ordered lists (<ol><li>). Include basic CSS styling for a professional appearance."""
                
                logging.info(f"Generating SOP using {model_name}")
                response = model.generate_content(prompt)
                sop_html = response.text
                
                # Strip code block markers if present
                sop_html = re.sub(r'^```(?:html)?\s*\n', '', sop_html, flags=re.MULTILINE)
                sop_html = re.sub(r'\n```\s*$', '', sop_html)
                sop_html = sop_html.strip()
                
                # Wrap in full HTML document if not already
                if not sop_html.lower().startswith('<!doctype') and not sop_html.lower().startswith('<html'):
                    sop_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Standard Operating Procedure</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }}
        ol {{ padding-left: 25px; }}
        li {{ margin-bottom: 10px; }}
        .meta {{ color: #7f8c8d; font-style: italic; margin-bottom: 30px; }}
    </style>
</head>
<body>
{sop_html}
</body>
</html>"""
                else:
                    sop_content = sop_html
                
                ai_generated = True
                logging.info("SOP generated using AI")
            else:
                logging.warning("GEMINI_API_KEY not configured, falling back to notes-based generation")
        except Exception as ai_error:
            logging.warning(f"AI generation failed: {ai_error}, falling back to notes-based generation")
        
        # Fallback: Generate SOP from notes if AI failed or not available
        if not sop_content:
            logging.info("Generating SOP from notes.json")
            steps_html = ""
            if notes:
                for i, note in enumerate(notes, 1):
                    step_note = note.get('note', '').strip()
                    if step_note:
                        steps_html += f"<li>{step_note}</li>\n"
                    else:
                        steps_html += f"<li>Refer to Screenshot {i} for this step.</li>\n"
            
            sop_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Standard Operating Procedure</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }}
        ol {{ padding-left: 25px; }}
        li {{ margin-bottom: 10px; }}
        .meta {{ color: #7f8c8d; font-style: italic; margin-bottom: 30px; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p class="meta">Standard Operating Procedure</p>
    
    <h2>Purpose</h2>
    <p>This Standard Operating Procedure (SOP) provides step-by-step instructions for completing the {title} process.</p>
    
    <h2>Scope</h2>
    <p>This procedure applies to all personnel who need to perform {title}.</p>
    
    <h2>Prerequisites</h2>
    <ul>
        <li>Access to required systems and applications</li>
        <li>Necessary permissions and credentials</li>
        <li>Understanding of basic system navigation</li>
    </ul>
    
    <h2>Procedure</h2>
    <ol>
{steps_html}
    </ol>
</body>
</html>"""
        
        # Create HTML version with embedded screenshots
        import base64
        
        # Extract the body content from AI-generated HTML if present
        if ai_generated and sop_content:
            # Extract content between <body> tags if it's a full HTML document
            body_match = re.search(r'<body[^>]*>(.*?)</body>', sop_content, re.DOTALL | re.IGNORECASE)
            if body_match:
                sop_body_content = body_match.group(1)
            else:
                # If no body tags, use the entire content
                sop_body_content = sop_content
        else:
            # For notes-based generation, sop_content is already in HTML format
            body_match = re.search(r'<body[^>]*>(.*?)</body>', sop_content, re.DOTALL | re.IGNORECASE)
            if body_match:
                sop_body_content = body_match.group(1)
            else:
                sop_body_content = sop_content
        
        # Create complete HTML with screenshots embedded
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Standard Operating Procedure</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #34495e;
            margin-top: 20px;
        }}
        .screenshot {{
            margin: 20px 0;
            text-align: center;
        }}
        .screenshot img {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .screenshot-caption {{
            font-style: italic;
            color: #666;
            margin-top: 8px;
            font-size: 14px;
        }}
        .step {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #3498db;
        }}
        .meta {{
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 30px;
        }}
        pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        ol, ul {{
            padding-left: 25px;
        }}
        li {{
            margin-bottom: 10px;
        }}
        p {{
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="meta">
            Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
            Method: {'AI-Generated' if ai_generated else 'Template-Based'}<br>
            Screenshots: {len(screenshots)}
        </div>
        
        <div class="sop-content">
{sop_body_content}
        </div>
        
        <h2>📸 Visual Reference</h2>
        <p>The following steps provide visual and textual guidance for this procedure:</p>
"""
        
        # Process steps from notes.json which includes all step types
        image_step_count = 0  # Track actual number of steps with images
        if notes:
            logging.info(f"SOP: Processing {len(notes)} notes")
            for i, note_item in enumerate(notes, 1):
                step_type = note_item.get('type', 'screenshot')
                note_text = note_item.get('note', '').strip()
                image_file = note_item.get('file')  # Actual filename
                logging.info(f"SOP Step {i}: type={step_type}, file={image_file}, has_note={bool(note_text)}")
                
                html_content += f"""
        <div class="screenshot">
            <h3>Step {i}</h3>
"""
                
                # Handle different step types
                if step_type == 'text':
                    # Text-only step (no image)
                    if note_text:
                        html_content += f"""            <div style="text-align: left; padding: 20px; background: #fff3cd; border-radius: 4px;">
                <strong>📝 Note:</strong><br>{note_text}
            </div>
"""
                elif step_type in ['screenshot', 'upload'] and (image_file or note_item.get('imageSrc')):
                    # Step with image (screenshot or uploaded)
                    img_data = None
                    
                    if step_type == 'screenshot':
                        # For screenshots, read from file
                        image_path = os.path.join(output_dir, image_file)
                        try:
                            with open(image_path, 'rb') as img_file:
                                img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        except Exception as img_error:
                            logging.warning(f"SOP: Failed to read screenshot file {image_file}: {img_error}")
                    
                    elif step_type == 'upload':
                        # For uploads, extract base64 from imageSrc data URL
                        image_src = note_item.get('imageSrc', '')
                        if image_src.startswith('data:image/'):
                            try:
                                # Split on comma to separate header from base64 data
                                parts = image_src.split(',', 1)
                                if len(parts) == 2:
                                    img_data = parts[1]
                                    logging.info(f"SOP: Extracted base64 data from uploaded image (length: {len(img_data)})")
                            except Exception as img_error:
                                logging.warning(f"SOP: Failed to extract uploaded image data: {img_error}")
                        else:
                            logging.warning(f"SOP: Invalid imageSrc format for uploaded image (does not start with 'data:image/')")
                    
                    # Embed image if we have data
                    if img_data:
                        image_step_count += 1  # Count this as an image step
                        html_content += f"""            <img src="data:image/png;base64,{img_data}" alt="Step {i}">
            <div class="screenshot-caption">{'Uploaded image' if step_type == 'upload' else 'Screenshot'} {i} of {len(notes)}</div>
"""
                        if note_text:
                            html_content += f"""            <p style="margin-top: 10px; text-align: left; padding: 0 20px;"><strong>Instructions:</strong> {note_text}</p>
"""
                    else:
                        # Show error if image data couldn't be loaded
                        logging.warning(f"SOP: No image data available for step {i} (type={step_type})")
                        html_content += f"""            <div style="text-align: left; padding: 20px; background: #ffcccc; border-radius: 4px;">
                <strong>⚠️ Image not found</strong>
            </div>
"""
                        if note_text:
                            html_content += f"""            <p style="text-align: left; padding: 0 20px;"><strong>Note:</strong> {note_text}</p>
"""
                else:
                    # Fallback: just show the note
                    if note_text:
                        html_content += f"""            <p style="text-align: left; padding: 0 20px;"><strong>Note:</strong> {note_text}</p>
"""
                
                html_content += """        </div>
"""
        else:
            # Fallback to screenshots array if no notes
            image_step_count = len(screenshots)
            for i, screenshot_file in enumerate(screenshots, 1):
                screenshot_path = os.path.join(output_dir, screenshot_file)
                try:
                    with open(screenshot_path, 'rb') as img_file:
                        img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        
                        html_content += f"""
        <div class="screenshot">
            <h3>Step {i}</h3>
            <img src="data:image/png;base64,{img_data}" alt="Step {i}">
            <div class="screenshot-caption">Screenshot {i} of {len(screenshots)}</div>
        </div>
"""
                except Exception as img_error:
                    logging.warning(f"Failed to embed screenshot {screenshot_file}: {img_error}")
        
        html_content += """    </div>
</body>
</html>
"""
        
        # Save both text and HTML versions
        sop_txt_path = os.path.join(output_dir, 'SOP.txt')
        sop_html_path = os.path.join(output_dir, 'SOP.html')
        
        with open(sop_txt_path, 'w', encoding='utf-8') as f:
            f.write(sop_content)
        
        with open(sop_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info(f"SOP saved to {sop_txt_path} and {sop_html_path}")
        
        # Create URL for serving the SOP HTML file
        from urllib.parse import quote
        sop_url = f'/api/serve_sop/{quote(sop_html_path)}'
        
        return jsonify({
            'success': True,
            'sop_content': html_content,  # Return complete HTML with screenshots
            'sop_html_path': sop_html_path,
            'sop_html_url': sop_url,  # Add URL for frontend to fetch
            'sop_txt_path': sop_txt_path,
            'filename': f'SOP_{title.replace(" ", "_")}.html',
            'ai_generated': ai_generated,
            'generation_method': 'AI' if ai_generated else 'Notes-based',
            'screenshots': image_step_count  # Return actual count of image steps
        })
    except Exception as e:
        logging.error(f"Error generating SOP: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/serve_sop/<path:filepath>')
def serve_sop(filepath):
    """Serve SOP HTML file for viewing in browser"""
    try:
        # Normalize path
        filepath = os.path.normpath(filepath)
        if os.path.exists(filepath) and filepath.endswith('.html'):
            return send_file(filepath, mimetype='text/html')
        return "SOP file not found", 404
    except Exception as e:
        logging.error(f"Error serving SOP: {e}", exc_info=True)
        return str(e), 500

if __name__ == '__main__':
    logging.info("="*50)
    logging.info("Hallmark Scribble Web Server Starting")
    logging.info(f"Log file: {log_file}")
    logging.info("="*50)
    
    # Get local IP address
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
    
    # Determine if running as frozen executable
    is_frozen = getattr(sys, 'frozen', False)
    
    # Open browser to localhost (only when frozen as exe)
    if is_frozen:
        import webbrowser
        import threading
        def open_browser():
            import time
            time.sleep(1.5)  # Wait for server to start
            # Use port 5000 for frozen exe, 5010 for development
            port = 5000 if is_frozen else 5010
            url = f"http://localhost:{port}"
            logging.info(f"Opening browser to {url}")
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Flask app (disable debug mode when frozen to prevent reloader issues)
    # Port 5000 for frozen exe, 5010 for development
    port = 5000 if is_frozen else 5010
    app.run(host='0.0.0.0', port=port, debug=not is_frozen)
