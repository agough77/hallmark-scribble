import subprocess
import os
import re
audio_process = None
selected_audio_device = None

def get_ffmpeg_path():
    """Find ffmpeg executable in common locations"""
    # Check in ffmpeg subfolder
    local_ffmpeg = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ffmpeg", "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    
    local_ffmpeg_bin = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ffmpeg", "bin", "ffmpeg.exe")
    if os.path.exists(local_ffmpeg_bin):
        return local_ffmpeg_bin
    
    # Otherwise assume it's in PATH
    return "ffmpeg"

def list_audio_devices():
    """Get list of available audio devices"""
    ffmpeg_cmd = get_ffmpeg_path()
    try:
        result = subprocess.run(
            [ffmpeg_cmd, "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        output = result.stderr
        
        # Parse audio devices from output
        devices = []
        for line in output.split('\n'):
            # Look for lines with (audio) indicating audio devices
            if '(audio)' in line.lower():
                match = re.search(r'"([^"]+)"', line)
                if match:
                    devices.append(match.group(1))
        
        return devices
    except Exception as e:
        return []

def set_audio_device(device_name):
    """Set the audio device to use for recording"""
    global selected_audio_device
    selected_audio_device = device_name

def start_audio_recording(output="assets/audio.wav"):
    global audio_process, selected_audio_device
    if selected_audio_device is None:
        raise ValueError("No audio device selected")
    
    ffmpeg_cmd = get_ffmpeg_path()
    command = [ffmpeg_cmd, "-y", "-f", "dshow", "-i", f"audio={selected_audio_device}", output]
    # Hide console window on Windows
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    audio_process = subprocess.Popen(command, stdin=subprocess.PIPE, creationflags=creation_flags)

def stop_audio_recording():
    global audio_process
    if audio_process:
        try:
            audio_process.stdin.write(b'q')
            audio_process.stdin.close()
            audio_process.wait(timeout=5)
        except:
            try:
                audio_process.terminate()
                audio_process.wait(timeout=2)
            except:
                audio_process.kill()
        finally:
            audio_process = None
