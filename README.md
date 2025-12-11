# 🎬 Hallmark Scribble

A comprehensive AI-powered screen recording and documentation tool with a modern web-based interface.

## 📁 Project Structure

```
Hallmark Scribble/
├── web_app/              # Web application (Flask)
│   ├── web_app.py        # Web server entry point
│   ├── templates/        # HTML templates
│   ├── requirements.txt  # All dependencies
│   └── WEB_README.md
│
├── shared/               # Shared modules
│   ├── recorder/         # Audio & screen recording
│   ├── transcription/    # AI transcription (Gemini)
│   ├── utils/            # Utility functions
│   ├── guide/            # AI guide generation & HTML editor
│   └── ffmpeg/           # FFmpeg binaries (bundled)
│
├── outputs/              # Generated recordings and guides
├── BUILD_COMPLETE.bat    # Build all components
├── version.json          # Version metadata
└── .env                  # Environment variables (GEMINI_API_KEY)
```

## 🚀 Quick Start

### Development Mode
```bash
cd web_app
pip install -r requirements.txt
python web_app.py
```

Then open your browser to `http://localhost:5000`

### Production (Standalone Installer)
Run `BUILD_COMPLETE.bat` to build the installer, or download the latest release from GitHub.

## ✨ Features

- **🎥 Screen Recording**: Record full screen or select a specific region at 30fps
- **🎤 Audio Recording**: Capture microphone audio during recording
- **🖱️ Input Logging**: Track mouse clicks with automatic screenshots
- **🤖 AI Vision Analysis**: Google Gemini AI analyzes your actions and writes natural narration scripts
- **🎙️ AI Narration**: Text-to-speech narration with edge-tts or gTTS fallback
- **✏️ Interactive HTML Editor**: Drag-and-drop editor to reorder, delete, and customize your guides
## ✨ Features

- **🎥 Multi-Monitor Recording**: Select specific monitor or capture all screens
- **🎤 Audio Recording**: System audio + microphone with automatic mixing
- **📸 Screenshot Mode**: Capture individual screenshots with auto-input logging
- **🤖 AI-Powered Transcription**: Gemini AI analyzes screenshots and generates step-by-step guides
- **🎨 Interactive HTML Editor**: Drag-drop steps, annotate screenshots, rich text formatting
- **✏️ Annotation Tools**: Pen, highlighter (5% opacity), arrows, rectangles, circles, text
- **🗣️ AI Narration**: Text-to-speech with edge-tts (primary) + gTTS (fallback)
- **🎬 Video Merging**: Combines recording + narration audio automatically
- **📄 Export Options**: Generate self-contained HTML guides
- **🌐 Web-Based**: Access via browser at localhost:5000
- **🔄 Auto-Update**: Built-in updater checks for new versions

## 📋 Requirements

- Python 3.11+
- FFmpeg (bundled in `shared/ffmpeg/`)
- Google Gemini API key (for AI transcription)
- Windows 10/11 (for standalone installer)

## 🚀 Installation

### Option 1: Standalone Installer (Recommended)
1. Download `HallmarkScribble_Installer.exe` from [Releases](https://github.com/agough77/hallmark-scribble/releases)
2. Right-click → Run as administrator
3. Installer will extract web app, updater, and create shortcuts
4. Launch from desktop shortcut or Start menu

### Option 2: Development Mode
1. Clone this repository
2. Create a `.env` file with your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
3. Run the web server:
   ```bash
   cd web_app
   pip install -r requirements.txt
   python web_app.py
   ```
4. Open browser to `http://localhost:5000`

## 🎯 Usage

### Recording Workflow:
1. **Select Capture Mode** - Choose fullscreen, window, or screenshot mode
2. **Choose Monitor** - If multiple monitors, select which to capture
3. **Start Recording** - Click "Start Recording" (or "Start Screenshot Mode")
4. **Perform Actions** - Do the task you want to document
5. **Stop Recording** - Click "Stop" button
6. **Open HTML Editor** - View and edit your guide

### Guide Editor Features:
- **Drag-Drop Steps** - Reorder steps by dragging
- **Edit & Annotate** - Click "Edit & Annotate" to mark up screenshots
- **Generate AI Instructions** - Let AI analyze and write step descriptions
- **Add Narration** - Create narrated video with AI voice-over
- **Rich Text Formatting** - Bold, italic, lists, colors, links
- **Export HTML** - Save as self-contained HTML file

## 📁 Output Structure

Recordings are organized by date in `~/Downloads/Hallmark Scribble Outputs/`:
```
Hallmark Scribble Outputs/
└── 2025-12-11/
    ├── Scribble 1/
    │   ├── recording.mp4          # Original screen recording
    │   ├── audio.wav               # Microphone audio
    │   ├── narrated_video.mp4      # Video with AI narration
    │   ├── narration.mp3           # AI voice-over audio
    │   ├── transcript.txt          # AI-generated script
    │   ├── actions.log             # Input event log
    │   ├── screenshot_*.png        # Screenshots on each click
    │   ├── editor.html             # Interactive guide editor
    │   └── notes.json              # Step metadata
    ├── Scribble 2/
    └── ...
```

## 🛠️ Building from Source

Run the complete build:
```bash
.\BUILD_COMPLETE.bat
```

This creates:
- `web_app\dist\HallmarkScribble_Web\` - Web application folder
- `HallmarkScribble_Updater.exe` - Update checker
- `HallmarkScribble_Installer.exe` - Complete installer (~400 MB)

## 🔧 Technical Details

### Core Technologies:
- **Flask 3.0** - Web framework
- **FFmpeg** - Screen and audio recording
- **Google Gemini 2.5 Flash** - AI vision analysis
- **edge-tts / gTTS** - Text-to-speech narration
- **MSS 9.0+** - Multi-monitor screenshot library
- **Pillow** - Image processing
- **PyInstaller** - Executable bundling

### AI Features:
- Vision-based analysis (Gemini AI analyzes screenshots, not just text)
- Conversational narration scripts with natural speech patterns
- Optimized speech rate (+20% for edge-tts, 1.15x for gTTS)
- Automatic audio mixing and volume normalization

## 🔄 Version Management

The application includes auto-update functionality:
1. On launch, checks GitHub for newer versions
2. Compares local `version.json` with GitHub's latest
3. Downloads and installs updates automatically
4. Seamless upgrade without losing settings

## 📝 License

See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please open an issue or pull request.

## 📧 Support

For issues or questions, please use the GitHub Issues page.
│   ├── screen.py              # FFmpeg screen recording
│   ├── audio.py               # Audio device management
│   └── input_logger.py        # Input tracking
├── transcription/
│   └── whisper_transcribe.py  # Gemini AI analysis
├── guide/
│   ├── narration.py           # Text-to-speech
│   ├── html_editor.py         # Interactive editor
│   └── generate_guide.py      # Markdown export
├── utils/
│   └── screenshot.py          # Screenshot utilities
├── ffmpeg/                    # FFmpeg binaries
└── outputs/                   # Generated recordings
```

## 📝 License

This project is for internal use at Hallmark.

## 🙏 Credits

- Google Gemini AI for vision analysis
- Microsoft Edge TTS for natural voice synthesis
- FFmpeg team for multimedia processing
- PyQt5 for the beautiful UI framework
