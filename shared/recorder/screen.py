import subprocess
import os
import logging

ffmpeg_process = None
region = None

def get_ffmpeg_path():
    """Find ffmpeg executable in common locations"""
    # Get the shared folder (2 levels up from this file: shared/recorder/screen.py -> shared/recorder -> shared)
    shared_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check shared/ffmpeg folder
    local_ffmpeg_bin = os.path.join(shared_folder, "ffmpeg", "bin", "ffmpeg.exe")
    if os.path.exists(local_ffmpeg_bin):
        return local_ffmpeg_bin
    
    local_ffmpeg = os.path.join(shared_folder, "ffmpeg", "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    
    # Otherwise assume it's in PATH
    return "ffmpeg"

def set_region(x, y, width, height):
    global region
    region = (x, y, width, height)

def start_screen_recording(output="assets/recording.mp4", full_screen=True):
    global ffmpeg_process
    ffmpeg_cmd = get_ffmpeg_path()
    
    logging.info(f"FFmpeg path: {ffmpeg_cmd}")
    logging.info(f"Output file: {output}")
    logging.info(f"Full screen: {full_screen}")
    
    if full_screen:
        if region:
            # Capture specific monitor using offset_x/offset_y (works with negative coordinates)
            x, y, w, h = region
            logging.info(f"Monitor region: x={x}, y={y}, w={w}, h={h}")
            
            # H.264 encoding requires dimensions divisible by 2
            # Round down to nearest even number
            if w % 2 != 0:
                w -= 1
                logging.info(f"Adjusted monitor width to even number: {w}")
            if h % 2 != 0:
                h -= 1
                logging.info(f"Adjusted monitor height to even number: {h}")
            
            # Use offset_x/offset_y and video_size to capture specific monitor
            # This works correctly with negative coordinates (secondary monitors)
            command = [ffmpeg_cmd, "-y", "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "1",
                       "-offset_x", str(x), "-offset_y", str(y),
                       "-video_size", f"{w}x{h}",
                       "-i", "desktop",
                       "-pix_fmt", "yuv420p", output]
            logging.info(f"FFmpeg command (specific monitor): {' '.join(command)}")
        else:
            # Capture entire virtual desktop (all monitors)
            command = [ffmpeg_cmd, "-y", "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "1", "-i", "desktop", "-pix_fmt", "yuv420p", output]
            logging.info(f"FFmpeg command (all monitors): {' '.join(command)}")
    else:
        x, y, w, h = region
        logging.info(f"Window region: x={x}, y={y}, w={w}, h={h}")
        
        # Get virtual desktop bounds to validate capture area
        try:
            import win32api
            virtual_left = win32api.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
            virtual_top = win32api.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
            virtual_width = win32api.GetSystemMetrics(78) # SM_CXVIRTUALSCREEN
            virtual_height = win32api.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
            
            # Clip the region to stay within virtual desktop bounds
            right_edge = x + w
            bottom_edge = y + h
            virtual_right = virtual_left + virtual_width
            virtual_bottom = virtual_top + virtual_height
            
            if right_edge > virtual_right:
                w = virtual_right - x
                logging.warning(f"Window extends past desktop boundary, clipping width to {w}")
            if bottom_edge > virtual_bottom:
                h = virtual_bottom - y
                logging.warning(f"Window extends past desktop boundary, clipping height to {h}")
            if x < virtual_left:
                w -= (virtual_left - x)
                x = virtual_left
                logging.warning(f"Window extends past desktop boundary, clipping left to {x}")
            if y < virtual_top:
                h -= (virtual_top - y)
                y = virtual_top
                logging.warning(f"Window extends past desktop boundary, clipping top to {y}")
            
            # H.264 encoding requires dimensions divisible by 2 (preferably 16)
            # Round down to nearest even number
            if w % 2 != 0:
                w -= 1
                logging.info(f"Adjusted width to even number: {w}")
            if h % 2 != 0:
                h -= 1
                logging.info(f"Adjusted height to even number: {h}")
                
            logging.info(f"Validated capture region: x={x}, y={y}, w={w}, h={h}")
        except Exception as e:
            logging.warning(f"Could not validate desktop bounds: {e}, using original values")
        
        # For window capture, also use offset_x/offset_y with video_size
        # This is more reliable than crop filter for multi-monitor setups
        command = [ffmpeg_cmd, "-y", "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "1",
                   "-offset_x", str(x), "-offset_y", str(y),
                   "-video_size", f"{w}x{h}",
                   "-i", "desktop",
                   "-pix_fmt", "yuv420p", output]
        logging.info(f"FFmpeg command (window): {' '.join(command)}")
    
    try:
        # Capture stderr to log file for debugging
        log_dir = os.path.dirname(output)
        ffmpeg_log = os.path.join(log_dir, "ffmpeg_output.log")
        logging.info(f"FFmpeg output will be logged to: {ffmpeg_log}")
        
        # Hide console window on Windows
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        
        # Open stdin as PIPE so we can send 'q' to stop gracefully
        with open(ffmpeg_log, 'w') as log_file:
            ffmpeg_process = subprocess.Popen(
                command, 
                stdin=subprocess.PIPE, 
                stderr=log_file, 
                stdout=log_file, 
                creationflags=creation_flags
            )
        
        logging.info(f"FFmpeg process started with PID: {ffmpeg_process.pid}")
    except Exception as e:
        logging.error(f"Failed to start FFmpeg: {e}", exc_info=True)
        raise

def stop_screen_recording():
    global ffmpeg_process
    if ffmpeg_process:
        logging.info(f"Stopping FFmpeg process (PID: {ffmpeg_process.pid})...")
        try:
            # Send 'q' to stdin to gracefully stop
            if ffmpeg_process.stdin and not ffmpeg_process.stdin.closed:
                ffmpeg_process.stdin.write(b'q')
                ffmpeg_process.stdin.flush()
                ffmpeg_process.stdin.close()
            # Wait for process to finish - give it more time to write moov atom
            ffmpeg_process.wait(timeout=10)
            logging.info("FFmpeg stopped gracefully")
        except Exception as e:
            logging.warning(f"Graceful stop failed: {e}, forcing termination...")
            # Force terminate if graceful stop fails
            try:
                ffmpeg_process.terminate()
                ffmpeg_process.wait(timeout=5)
                logging.info("FFmpeg terminated")
            except Exception as e2:
                logging.error(f"Terminate failed: {e2}, killing process...")
                ffmpeg_process.kill()
                logging.info("FFmpeg killed")
        finally:
            ffmpeg_process = None
    else:
        logging.warning("stop_screen_recording called but no process was running")

