# Build Options for Hallmark Scribble

There are two build scripts available, each with different trade-offs:

## Option 1: Single-File EXE (build_exe.bat)
**File:** `build_exe.bat`
**Output:** `HallmarkScribble.exe` (single file)

### Pros:
✅ Single executable file - easy to share
✅ Looks professional (one .exe file)
✅ No visible dependencies

### Cons:
❌ **Slow startup** (5-15 seconds on first run)
❌ Larger file size (~150 MB)
❌ Extracts to temp folder on every run

### Best For:
- Simple distribution to non-technical users
- When you want just one file to share

---

## Option 2: Folder Distribution (build_exe_fast.bat) ⚡ RECOMMENDED
**File:** `build_exe_fast.bat`
**Output:** `HallmarkScribble_Fast\` folder

### Pros:
✅ **INSTANT startup** (no extraction delay)
✅ Smaller total size
✅ Updates are easier (replace individual files)
✅ Professional software distribution method

### Cons:
❌ Multiple files in a folder
❌ User needs to keep entire folder together

### Best For:
- Frequent use (daily work)
- When startup speed matters
- Professional deployment

---

## How Startup Times Compare

| Build Type | First Startup | Subsequent Startups |
|-----------|--------------|---------------------|
| Single-File | 10-15 sec | 5-10 sec |
| Folder Mode | <1 sec | <1 sec |

---

## Why is Single-File Slow?

PyInstaller single-file EXEs work by:
1. Extracting ALL files to `C:\Users\[You]\AppData\Local\Temp\_MEI*`
2. Loading Python runtime
3. Loading all libraries
4. Starting the application

The **folder mode** skips step 1 entirely, making it much faster.

---

## Recommended Setup

For best user experience:

1. Use **`build_exe_fast.bat`** to create folder distribution
2. Compress `HallmarkScribble_Fast\` to a ZIP file
3. Share the ZIP with instructions:
   - "Extract the ZIP file"
   - "Run HallmarkScribble.exe inside the folder"
   - "Keep all files together"

This is how professional software is distributed (Chrome, VS Code, etc.)

---

## How to Use

### For Single-File:
```batch
.\build_exe.bat
```
Output: `HallmarkScribble.exe`

### For Folder (Fast):
```batch
.\build_exe_fast.bat
```
Output: `HallmarkScribble_Fast\` folder

---

## Distribution

### Single-File:
- Share: `HallmarkScribble.exe`
- User runs: Double-click the EXE

### Folder Mode:
- Compress `HallmarkScribble_Fast\` to ZIP
- Share: `HallmarkScribble_Fast.zip`
- User:
  1. Extracts ZIP
  2. Opens folder
  3. Runs `HallmarkScribble.exe`

---

## Technical Details

Both builds include:
- Python 3.11 runtime
- PyQt5 GUI framework
- FFmpeg for video processing
- All required libraries
- Google Gemini AI integration

The only difference is packaging method.
