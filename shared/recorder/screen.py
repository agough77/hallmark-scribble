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
        # Capture entire virtual desktop (all monitors)
        command = [ffmpeg_cmd, "-y", "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "1", "-i", "desktop", "-pix_fmt", "yuv420p", output]
        logging.info(f"FFmpeg command (full screen): {' '.join(command)}")
    else:
        x, y, w, h = region
        logging.info(f"Window region: x={x}, y={y}, w={w}, h={h}")
        # Capture entire virtual desktop and use crop filter to extract the window region
        # This works better for multi-monitor setups than offset_x/offset_y
        crop_filter = f"crop={w}:{h}:{x}:{y}"
        command = [ffmpeg_cmd, "-y", "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "1", "-i", "desktop", 
                   "-vf", crop_filter, "-pix_fmt", "yuv420p", output]
        logging.info(f"FFmpeg command (window): {' '.join(command)}")
    
    try:
        # Capture stderr to log file for debugging
        log_dir = os.path.dirname(output)
        ffmpeg_log = os.path.join(log_dir, "ffmpeg_output.log")
        logging.info(f"FFmpeg output will be logged to: {ffmpeg_log}")
        
        # Hide console window on Windows
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        
        with open(ffmpeg_log, 'w') as log_file:
            ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log_file, stdout=log_file, creationflags=creation_flags)
        
        logging.info(f"✓ FFmpeg process started with PID: {ffmpeg_process.pid}")
    except Exception as e:
        logging.error(f"Failed to start FFmpeg: {e}", exc_info=True)
        raise

def stop_screen_recording():
    global ffmpeg_process
    if ffmpeg_process:
        logging.info(f"Stopping FFmpeg process (PID: {ffmpeg_process.pid})...")
        try:
            # Send 'q' to stdin to gracefully stop
            ffmpeg_process.stdin.write(b'q')
            ffmpeg_process.stdin.close()
            # Wait for process to finish
            ffmpeg_process.wait(timeout=5)
            logging.info("✓ FFmpeg stopped gracefully")
        except Exception as e:
            logging.warning(f"Graceful stop failed: {e}, forcing termination...")
            # Force terminate if graceful stop fails
            try:
                ffmpeg_process.terminate()
                ffmpeg_process.wait(timeout=2)
                logging.info("✓ FFmpeg terminated")
            except Exception as e2:
                logging.error(f"Terminate failed: {e2}, killing process...")
                ffmpeg_process.kill()
                logging.info("✓ FFmpeg killed")
        finally:
            ffmpeg_process = None
    else:
        logging.warning("stop_screen_recording called but no process was running")
