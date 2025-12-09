# Hallmark Scribble - Desktop Application

Windows desktop application with PyQt5 UI for screen recording and AI-powered documentation.

## Features

- 🎥 Full screen or region recording
- 🎤 Audio recording with device selection
- 🖱️ Input logging with automatic screenshots
- 🤖 AI guide generation with Google Gemini
- 🎙️ AI narration with text-to-speech
- ✏️ Interactive HTML editor
- 🗑️ Built-in cleanup manager
- ⌨️ Global hotkey support (Ctrl+Shift+S)

## Installation

```bash
cd desktop_app
pip install -r requirements.txt
python main.py
```

## Configuration

Create `.env` file in the parent directory:
```
GEMINI_API_KEY=your_api_key_here
```

Or use `config.txt` in the parent directory:
```
GEMINI_API_KEY=your_api_key_here
```

## Building Executable

See `BUILD_INSTRUCTIONS.md` for detailed build instructions.

Quick build:
```bash
build_exe_fast.bat
```

## Documentation

- `USER_GUIDE.md` - End user guide
- `BUILD_INSTRUCTIONS.md` - Build process
- `DISTRIBUTION_GUIDE.md` - Distribution instructions
