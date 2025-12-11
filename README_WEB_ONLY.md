# Hallmark Scribble - Web Application

**Version 1.0.9** - Simplified web-only architecture

## Overview

Hallmark Scribble is a web-based screen recording and guide generation tool that creates interactive how-to guides with AI-powered transcription and narration.

## Architecture

**Web-only application** - All functionality runs through a Flask web server accessible via browser at `http://localhost:5000`

### Project Structure

```
Hallmark Scribble/
├── web_app/                    # Main application
│   ├── web_app.py              # Flask server (2900+ lines)
│   ├── requirements.txt        # Python dependencies
│   ├── build_exe_web.bat       # Build script
│   └── templates/              # HTML templates
│       ├── index.html          # Main UI
│       └── video_editor.html   # Narration editor
├── shared/                     # Shared modules
│   ├── ffmpeg/                 # FFmpeg binaries (bundled)
│   ├── recorder/               # Screen/audio recording
│   ├── guide/                  # AI guide generation
│   ├── transcription/          # Gemini AI integration
│   └── utils/                  # Utilities
├── BUILD_COMPLETE.bat          # Build all components
├── BUILD_INSTALLER.bat         # Build installer
├── BUILD_UPDATER.bat           # Build updater
└── version.json                # Version metadata

```

## Requirements

- **Python 3.11** (Windows Store or standard installation)
- **FFmpeg** (bundled in `shared/ffmpeg/`)
- **Gemini API Key** (in `.env` file)

### Dependencies

All dependencies in `web_app/requirements.txt`:
- Flask 3.0.0 - Web framework
- flask-cors - CORS support
- pynput - Input logging
- pyautogui - Screen automation
- mss 9.0+ - Multi-monitor screenshot
- Pillow 10.0+ - Image processing
- google-generativeai 0.3+ - AI transcription
- edge-tts 6.1+ - Primary text-to-speech
- gTTS 2.3+ - Fallback text-to-speech
- pywin32 - Windows system integration
- keyboard - Keyboard input
- pygetwindow 0.0.9+ - Window management

## Build Process

### Quick Build (All Components)

```powershell
.\BUILD_COMPLETE.bat
```

Builds in order:
1. **Web Application** → `web_app\dist\HallmarkScribble_Web\`
2. **Updater** → `HallmarkScribble_Updater.exe`
3. **Installer** → `HallmarkScribble_Installer.exe` (~400 MB)

### Individual Builds

**Web App Only:**
```powershell
cd web_app
.\build_exe_web.bat
```

**Updater Only:**
```powershell
.\BUILD_UPDATER.bat
```

**Installer Only:**
```powershell
.\BUILD_INSTALLER.bat
```

## Running Development Server

```powershell
cd web_app
python web_app.py
```

Opens browser to `http://localhost:5000`

## Features

### Screen Recording
- **Multi-monitor support** - Select specific monitor via picker
- **Fullscreen or windowed** - Capture entire screen or specific windows
- **Audio recording** - System + microphone audio
- **Screenshot mode** - Capture individual screenshots with auto-logging

### Guide Generation
- **AI-powered transcription** - Gemini AI analyzes screenshots
- **Interactive HTML editor** - Drag-drop steps, annotate screenshots
- **Annotation tools** - Pen, highlighter (5% opacity), arrows, rectangles, circles, text
- **Undo/redo support** - Full annotation history

### Narration
- **Text-to-speech** - edge-tts (primary) + gTTS (fallback)
- **Video merging** - Combines recording + narration audio
- **Batch processing** - Narrate all steps at once

### Screenshot Annotations
- **Path-based highlighter** - Prevents opacity compounding
- **Cache-busting refresh** - Shows updated images immediately
- **Visual feedback** - Toast notifications + step container flash

## Build Artifacts

### Web Application Folder
`web_app\dist\HallmarkScribble_Web\`
- `HallmarkScribble_Web.exe` - Main executable
- `_internal\` - Dependencies and resources
- `shared\` - FFmpeg binaries and modules

### Installer
`HallmarkScribble_Installer.exe` (~400 MB)
- Bundles complete web application
- Installs to `C:\Program Files\Hallmark Scribble\`
- Creates desktop shortcut
- Includes updater

### Updater
`HallmarkScribble_Updater.exe`
- Checks GitHub for new versions
- Downloads and installs updates
- Compares `version.json`

## Path Resolution

All modules use this pattern for dev + frozen builds:

```python
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_shared_path():
    base_path = get_base_path()
    if getattr(sys, 'frozen', False):
        for p in [os.path.join(base_path, 'shared'),
                  os.path.join(os.path.dirname(base_path), 'shared'),
                  os.path.join(base_path, '_internal', 'shared')]:
            if os.path.exists(p): return p
    return os.path.join(os.path.dirname(base_path), 'shared')
```

## Version Management

Edit `version.json`:
```json
{
  "version": "1.0.9",
  "release_date": "2025-12-11",
  "download_url": "https://github.com/agough77/hallmark-scribble/releases/latest/download/HallmarkScribble_Installer.exe",
  "changelog": [
    "Fixed highlighter opacity compounding",
    "Added annotation save fix",
    "Localhost default URL"
  ]
}
```

Then:
1. Build with `BUILD_COMPLETE.bat`
2. Commit: `git add -A; git commit -m "Release v1.0.9"`
3. Push: `git push origin main`
4. Create GitHub release with installer

## Troubleshooting

### Browser doesn't open
- Check if port 5000 is available
- Manually navigate to `http://localhost:5000`

### Annotations not saving
- Check browser console (F12) for errors
- Verify `shared/guide/html_editor.py` path resolution

### FFmpeg errors
- Ensure `shared/ffmpeg/bin/ffmpeg.exe` exists
- Check console window hiding (`CREATE_NO_WINDOW`)

### Multi-monitor issues
- MSS library handles negative coordinates automatically
- FFmpeg crop filter extracts monitor region

## Development Notes

### No Desktop Application
Previous PyQt5 desktop app removed. Web-only architecture is simpler and more maintainable.

### Shared Modules
All recorder, guide, transcription, and utility modules in `shared/` directory. Imported by web app using path resolution pattern.

### Frontend Cache-Busting
Always append `?t=<timestamp>` to image/video URLs after server-side modifications to force browser refresh.

### Highlighter Rendering
Uses path-based rendering with `skipHighlighter` parameter during active drawing to prevent opacity compounding at 5%.

## License

See LICENSE file for details.
