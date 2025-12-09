# Hallmark Scribe - Build Instructions

## Prerequisites

1. **Python 3.11** must be installed
2. **FFmpeg** must be downloaded and placed in the project

## Step 1: Download FFmpeg

1. Download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/
2. Download the "release essentials" build (smaller)
3. Extract the downloaded zip file
4. Copy the contents so you have this structure:
   ```
   Hallmark Scribe/
   ├── ffmpeg/
   │   └── bin/
   │       ├── ffmpeg.exe
   │       └── ffprobe.exe
   ├── main.py
   ├── build_exe.bat
   └── HallmarkScribe.spec
   ```

## Step 2: Install Dependencies

Run in PowerShell or CMD:
```bash
python3.11.exe -m pip install -r requirements.txt
```

## Step 3: Build the EXE

Simply double-click `build_exe.bat` or run:
```bash
build_exe.bat
```

This will:
- Install PyInstaller
- Clean previous builds
- Build the executable with all dependencies
- Include FFmpeg binaries
- Create `HallmarkScribe.exe`

## Step 4: Distribute

After building, you'll have `HallmarkScribe.exe` which can be distributed to other Windows machines.

**Important:** The EXE is self-contained and includes:
- All Python libraries
- FFmpeg binaries
- All application code

Users just need to:
1. Copy `HallmarkScribe.exe` to their machine
2. Run it (no installation needed!)
3. Have a Google Gemini API key (they'll need to add it in settings)

## Troubleshooting

### Error: FFmpeg not found
Make sure the FFmpeg folder structure is correct before building.

### Error: Missing module
Add the module to `hiddenimports` in `HallmarkScribe.spec`

### Executable too large
The EXE will be 80-150 MB because it includes:
- Python runtime
- PyQt5 GUI framework
- FFmpeg binaries
- All dependencies

This is normal for PyInstaller builds.

## Creating an Installer (Optional)

To create a proper installer, you can use:
- **Inno Setup** (free, recommended)
- **NSIS** (free)
- **Advanced Installer** (commercial)

Example Inno Setup script can be created to:
- Install the EXE to Program Files
- Create desktop shortcuts
- Add to Start Menu
- Set up file associations
