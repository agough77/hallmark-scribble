# Project Structure Update

## Overview

The Hallmark Scribble project has been reorganized to separate the desktop and web applications while sharing common modules.

## New Directory Structure

```
Hallmark Scribble/
│
├── desktop_app/                    # Desktop Application (PyQt5)
│   ├── main.py                     # Main desktop app entry point
│   ├── splash.py                   # Splash screen
│   ├── requirements.txt            # Desktop dependencies
│   ├── HallmarkScribe.spec         # PyInstaller spec file
│   ├── build_exe_fast.bat          # Fast build script
│   ├── installer.iss               # Inno Setup installer
│   ├── USER_GUIDE.md               # User documentation
│   ├── BUILD_INSTRUCTIONS.md       # Build documentation
│   ├── DISTRIBUTION_GUIDE.md       # Distribution documentation
│   └── README.md                   # Desktop app README
│
├── web_app/                        # Web Application (Flask)
│   ├── web_app.py                  # Flask server entry point
│   ├── templates/                  # HTML templates
│   │   └── index.html              # Main web interface
│   ├── web_requirements.txt        # Web dependencies
│   ├── START_WEB_SERVER.bat        # Server launch script
│   ├── WEB_README.md               # Web app documentation
│   └── README.md                   # (to be created)
│
├── shared/                         # Shared Modules
│   ├── recorder/                   # Recording modules
│   │   ├── screen.py               # Screen recording with FFmpeg
│   │   ├── audio.py                # Audio device management
│   │   └── input_logger.py         # Input event tracking
│   ├── transcription/              # AI transcription
│   │   └── whisper_transcribe.py   # Gemini AI integration
│   ├── utils/                      # Utility functions
│   │   └── screenshot.py           # Screenshot utilities
│   ├── guide/                      # Guide generation
│   │   ├── narration.py            # TTS narration
│   │   ├── html_editor.py          # HTML editor creation
│   │   ├── generate_guide.py       # Markdown guide generation
│   │   └── editor_server.py        # Editor server
│   └── ffmpeg/                     # FFmpeg binaries
│       ├── bin/                    # Executables
│       └── doc/                    # Documentation
│
├── outputs/                        # Generated recordings (shared)
│   └── [date]/
│       └── Scribble [n]/
│
├── .env                            # Environment variables (shared)
├── config.txt                      # Configuration file (shared)
├── README.md                       # Main project README
└── .gitignore                      # Git ignore rules

```

## Key Changes

### 1. Separated Applications
- **Desktop App**: All PyQt5 UI and desktop-specific code in `desktop_app/`
- **Web App**: All Flask server and web UI code in `web_app/`

### 2. Shared Modules
- Common functionality extracted to `shared/` directory
- Both apps import from `shared.*` modules
- No code duplication

### 3. Updated Import Paths
- **Desktop**: `from shared.recorder.screen import ...`
- **Web**: `from shared.recorder.screen import ...`
- Both apps add parent directory to `sys.path`

### 4. Build Scripts Updated
- `build_exe_fast.bat` updated to reference `../shared/ffmpeg`
- `HallmarkScribe.spec` updated to reference `../shared/ffmpeg`

## Running the Applications

### Desktop Application
```bash
cd desktop_app
pip install -r requirements.txt
python main.py
```

### Web Application
```bash
cd web_app
pip install -r web_requirements.txt
python web_app.py
# OR
START_WEB_SERVER.bat
```

## Shared Configuration

Both applications use the same configuration files in the root directory:
- `.env` - Environment variables (API keys)
- `config.txt` - Application configuration
- `outputs/` - Shared output directory

## Benefits

1. **Clear Separation**: Easy to understand which files belong to which app
2. **No Duplication**: Shared modules prevent code duplication
3. **Independent Development**: Each app can be developed separately
4. **Shared Outputs**: Both apps use the same output directory
5. **Easier Maintenance**: Changes to shared modules benefit both apps
6. **Better Organization**: Clear project structure for new developers

## Migration Notes

### Import Path Updates
All imports have been updated from:
```python
from recorder.screen import ...
```

To:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.recorder.screen import ...
```

### Build Process
Desktop builds now reference shared modules via relative paths:
```
--add-data="../shared/ffmpeg;ffmpeg"
```

## Future Enhancements

- Add `web_app/README.md` with detailed web app documentation
- Consider adding automated tests in separate `tests/` directory
- Add GitHub Actions workflow for automated builds
- Create Docker container for web app deployment
