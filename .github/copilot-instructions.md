# Hallmark Scribble - AI Agent Instructions

## Architecture Overview

**Dual-application monorepo**: Desktop (PyQt5) and Web (Flask) apps share common modules via `shared/` directory. Both import from `shared.*` and rely on path resolution patterns.

```
web_app/          # Flask web server
desktop_app/      # PyQt5 desktop UI (legacy)
shared/           # Common modules (recorder, transcription, guide, utils)
  ├── ffmpeg/     # FFmpeg binaries (bundled)
  ├── recorder/   # Screen/audio recording
  ├── guide/      # AI guide generation & HTML editor
  └── transcription/  # Gemini AI integration
```

## Critical Path Resolution Pattern

**Every Python file** must resolve paths for both development and PyInstaller frozen executables:

```python
# Standard pattern used in web_app.py and shared modules
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)  # Frozen
    return os.path.dirname(os.path.abspath(__file__))  # Dev

def get_shared_path():
    base_path = get_base_path()
    if getattr(sys, 'frozen', False):
        # Try: same dir, parent dir, _internal folder
        for p in [os.path.join(base_path, 'shared'),
                  os.path.join(os.path.dirname(base_path), 'shared'),
                  os.path.join(base_path, '_internal', 'shared')]:
            if os.path.exists(p): return p
    return os.path.join(os.path.dirname(base_path), 'shared')
```

**Import setup in web_app.py:**
```python
shared_path = get_shared_path()
sys.path.insert(0, shared_path)
parent_path = os.path.dirname(shared_path)  # CRITICAL: for "from shared.X"
if parent_path not in sys.path:
    sys.path.insert(0, parent_path)
```

Without `parent_path`, `from shared.guide import narration` fails with `ModuleNotFoundError`.

## Build & Release Workflow

**Sequential build process** (3 executables + 1 installer):

```powershell
# 1. Build web application (runs from web_app/)
cd web_app
.\build_exe_web.bat  # Creates web_app\dist\HallmarkScribble_Web\

# 2. Build updater (runs from root)
cd ..
.\BUILD_UPDATER.bat  # Creates HallmarkScribble_Updater.exe

# 3. Build installer (depends on #1 and #2)
.\BUILD_INSTALLER.bat  # Bundles web app + updater → HallmarkScribble_Installer.exe

# 4. Version management
# Edit version.json: bump version, update changelog, update download URL
# Commit, push to GitHub, create release with installer attached
```

**PyInstaller patterns:**
- Web app uses `--add-data="../shared;shared"` (relative path from web_app/)
- Always use `python3.11.exe` explicitly (not `python`) for consistency
- `--noconsole --windowed` hides console windows
- `--collect-all flask` and `--collect-all flask_cors` for Flask dependencies

## Frontend Cache-Busting Pattern

**Problem:** Browser caches prevent updated images/videos from displaying after edits.

**Solution:** Append timestamps to URLs:
```javascript
// In html_editor.py after saving annotated screenshot
imgElement.src = cleanSrc + '?t=' + timestamp;

// In video_editor.html after narration completes
setTimeout(() => loadAvailableVideos(), 1000);  // Refresh dropdown
```

Always invalidate cached resources after server-side modifications.

## Multi-Monitor & FFMPEG Conventions

**Monitor selection UI:** `showMonitorPicker()` in `index.html` populates from `/api/get_monitors`. Desktop app (`main.py`) may auto-select or skip picker based on monitor count.

**FFMPEG path resolution:** All recorder modules (`screen.py`, `audio.py`) use `get_ffmpeg_path()` → checks `shared/ffmpeg/bin/ffmpeg.exe` before falling back to PATH.

**Console window hiding:** Use `subprocess.CREATE_NO_WINDOW` (Windows) or `subprocess.DEVNULL` for stdout/stderr to prevent FFMPEG console windows.

## AI Guide Generation Flow

1. **Recording:** `recorder/input_logger.py` captures mouse clicks → screenshots
2. **Transcription:** `transcription/whisper_transcribe.py` sends screenshots to Gemini AI
3. **HTML Editor:** `guide/html_editor.py` generates 2000+ line interactive HTML with drag-drop
4. **Narration:** `guide/narration.py` uses `edge-tts` (primary) or `gTTS` (fallback)
5. **Video merging:** FFMPEG combines `recording.mp4` + narration audio → `narrated_video.mp4`

**Notes persistence:** `notes.json` stores step metadata (type, file, note, imageSrc). HTML editor reconstructs steps from this on reload.

## Common Pitfalls

1. **Module imports:** Always add both `shared_path` AND `parent_path` to `sys.path`
2. **Browser caching:** Add `?t=timestamp` to dynamically loaded images/videos
3. **Path separators:** Normalize Windows paths (`\\`) to forward slashes (`/`) for JavaScript
4. **FFMPEG bundling:** PyInstaller spec must include `--add-data="../shared/ffmpeg;ffmpeg"`
5. **Video dropdown refresh:** Call `loadAvailableVideos()` after async operations (narration, merging)

## Testing Patterns

**Manual testing workflow:**
```powershell
cd web_app
python web_app.py  # Dev server on localhost:5000
# Open browser console (F12) for debug logs
# Test: fullscreen capture, monitor picker, narration dropdown, screenshot annotations
```

**No automated tests exist.** Integration testing relies on running web server and manually verifying features.

## Debug Logging Conventions

All modules use Python `logging` module. Web app logs to `~/Downloads/Hallmark Scribble Outputs/hallmark_scribble_web.log`.

Frontend uses `console.log()` for troubleshooting:
```javascript
console.log('Capture mode button clicked:', mode);  // index.html
console.log('Monitor picker response:', data);       // monitor selection
```

## Version Update Checklist

1. Edit `version.json`: increment version, update `release_date`, update `download_url`, add changelog
2. Build web app, updater, installer (in order)
3. Test installer on clean machine
4. Commit changes: `git add -A; git commit -m "Release v1.0.X"`
5. Push: `git push origin main`
6. Create GitHub release: tag `v1.0.X`, upload `HallmarkScribble_Installer.exe`
7. Installer auto-updates via `updater.py` checking GitHub's raw `version.json`

## Key Files Reference

- `web_app/web_app.py` (2871 lines): Flask routes, recording state, path resolution
- `shared/guide/html_editor.py` (2070 lines): Interactive HTML generator with drag-drop
- `web_app/templates/index.html`: Main UI with capture controls, monitor picker
- `web_app/templates/video_editor.html`: Narration interface, video dropdown
- `version.json`: Version metadata for updater system
- `BUILD_*.bat`: Build scripts with PyInstaller commands

## Environment Requirements

- Python 3.11 (explicitly referenced in build scripts)
- Required packages: Flask, flask-cors, pynput, pyautogui, Pillow, google-generativeai, edge-tts
- FFmpeg binaries in `shared/ffmpeg/bin/`
- `.env` file with `GEMINI_API_KEY` for AI transcription
