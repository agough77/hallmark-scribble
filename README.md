# 🎬 Hallmark Scribble

A comprehensive AI-powered screen recording and documentation tool available in two versions: a desktop application and a web application.

## 📁 Project Structure

```
Hallmark Scribble/
├── desktop_app/          # Desktop application (PyQt5)
│   ├── main.py           # Desktop app entry point
│   ├── splash.py         # Splash screen
│   ├── requirements.txt  # Desktop dependencies
│   └── ...               # Build scripts and docs
│
├── web_app/              # Web application (Flask)
│   ├── web_app.py        # Web server entry point
│   ├── templates/        # HTML templates
│   ├── web_requirements.txt
│   └── WEB_README.md
│
├── shared/               # Shared modules (used by both apps)
│   ├── recorder/         # Audio & screen recording
│   ├── transcription/    # Whisper transcription
│   ├── utils/            # Utility functions
│   ├── guide/            # AI guide generation
│   └── ffmpeg/           # FFmpeg binaries
│
├── outputs/              # Generated recordings and guides
├── config.txt            # Shared configuration
└── .env                  # Environment variables
```

## 🚀 Quick Start

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
```

Then open your browser to `http://localhost:5000`

## ✨ Features

- **🎥 Screen Recording**: Record full screen or select a specific region at 30fps
- **🎤 Audio Recording**: Capture microphone audio during recording
- **🖱️ Input Logging**: Track mouse clicks with automatic screenshots
- **🤖 AI Vision Analysis**: Google Gemini AI analyzes your actions and writes natural narration scripts
- **🎙️ AI Narration**: Text-to-speech narration with edge-tts or gTTS fallback
- **✏️ Interactive HTML Editor**: Drag-and-drop editor to reorder, delete, and customize your guides
- **📄 Export Options**: Generate markdown guides and self-contained HTML files
- **🗑️ Cleanup Manager**: Select and delete old recordings to free up space
- **⌨️ Global Hotkey**: Stop recording with Ctrl+Shift+S without showing the app
- **🎨 Windows Metro UI**: Modern, flat design with intuitive icons and colors

## 📋 Requirements

- Python 3.11+
- FFmpeg (included in `ffmpeg/` folder)
- Google Gemini API key
- Required Python packages (auto-installed)

## 🚀 Installation

1. Clone or download this repository
2. Create a `.env` file with your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
3. Run the application:
   ```
   python main.py
   ```

Dependencies will be auto-installed as needed.

## 🎯 Usage

### Quick Start:
1. **Start Recording** - Click the green "Start Recording" button (window minimizes)
2. **Perform Actions** - Do the task you want to document
3. **Stop Recording** - Press `Ctrl+Shift+S` or click "Stop Recording"
4. **Generate Transcript** - AI analyzes screenshots and writes narration
5. **Add AI Narration** - Creates narrated video with voice-over
6. **Preview** - Watch the final narrated video
7. **Open HTML Editor** - Customize and export your guide

### Advanced Features:
- **Region Recording**: Select specific screen area instead of full screen
- **Settings**: Choose your audio input device
- **Cleanup Library**: Manage and delete old recordings
- **Export Guide**: Create markdown or HTML documentation

## 📁 Output Structure

Recordings are organized by date in `outputs/`:
```
outputs/
└── 2025-11-25/
    ├── Scribble 1/
    │   ├── recording.mp4          # Original screen recording
    │   ├── audio.wav               # Microphone audio
    │   ├── narrated_video.mp4      # Video with AI narration
    │   ├── narration.mp3           # AI voice-over audio
    │   ├── transcript.txt          # AI-generated script
    │   ├── actions.log             # Input event log
    │   ├── screenshot_*.png        # Screenshots on each click
    │   ├── editor.html             # Interactive guide editor
    │   └── guide.md                # Markdown guide
    ├── Scribble 2/
    └── ...
```

## 🔑 Keyboard Shortcuts

- **Ctrl+Shift+S** - Stop recording (global hotkey)

## 🛠️ Technical Details

### Dependencies:
- **PyQt5** - Modern Metro UI interface
- **FFmpeg** - Screen and audio recording
- **Google Gemini 2.5 Flash** - AI vision analysis
- **edge-tts / gTTS** - Text-to-speech narration
- **keyboard** - Global hotkey support
- **pynput** - Input event tracking
- **pyautogui** - Screenshot automation

### AI Features:
- Vision-based analysis (analyzes what you do, not just what you say)
- Conversational narration scripts with natural speech patterns
- Optimized speech rate (+20% for edge-tts, 1.15x for gTTS)
- 2x volume boost for clear audio

## 📂 Project Structure

```
Hallmark Scribble/
├── main.py                     # Main application with Metro UI
├── recorder/
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
