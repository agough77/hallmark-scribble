# Hallmark Scribe - Distribution Guide

## 📦 What You Have

After building, you have a **standalone Windows executable**: `HallmarkScribe.exe`

This is approximately **120-150 MB** and includes:
- ✅ Python runtime
- ✅ All Python libraries (PyQt5, Google AI, etc.)
- ✅ FFmpeg for video recording
- ✅ All application code

## 🚀 Quick Distribution (Simplest)

**For quick sharing or personal use:**

1. Copy `HallmarkScribe.exe` to any Windows machine
2. Double-click to run - **no installation needed!**
3. Users will need to add their Google Gemini API key in the app

That's it! The EXE is fully self-contained.

## 💾 Professional Installer (Recommended for Distribution)

**For professional deployment:**

### Using Inno Setup (Free)

1. **Download Inno Setup:** https://jrsoftware.org/isdl.php
2. **Install Inno Setup**
3. **Open `installer.iss`** (included in this project)
4. **Compile the installer** (Build → Compile in Inno Setup)
5. This creates `HallmarkScribe_Setup.exe` in the `installer` folder

The installer will:
- ✅ Install to Program Files
- ✅ Create Start Menu shortcuts
- ✅ Create Desktop shortcut (optional)
- ✅ Include uninstaller
- ✅ Look professional

## 📝 What Users Need

**System Requirements:**
- Windows 10/11 (64-bit)
- ~200 MB disk space
- Internet connection (for AI features)

**Setup:**
1. Run the application
2. Go to Tools → Settings
3. Enter Google Gemini API key
4. Start creating how-to guides!

## 🔑 Google Gemini API Key

Users need their own API key:
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key
5. Paste into Hallmark Scribe Settings

**Free tier includes:**
- 60 requests per minute
- Plenty for most users!

## 📋 Distribution Checklist

Before sharing:

- [x] EXE built successfully (`HallmarkScribe.exe`)
- [ ] Test the EXE on a clean Windows machine
- [ ] Create installer with Inno Setup (optional)
- [ ] Create README for users
- [ ] Include API key instructions
- [ ] Test all features (Screenshot mode, Video mode, Editor)

## 🎯 Distribution Options

### Option 1: Direct EXE (Fastest)
- Email the EXE file
- Share via USB drive
- Host on cloud storage (Dropbox, Google Drive)

### Option 2: Installer (Professional)
- Create `HallmarkScribe_Setup.exe` with Inno Setup
- Distribute the installer
- Users get proper installation experience

### Option 3: Portable Package
Create a ZIP file with:
```
HallmarkScribe_Portable.zip
├── HallmarkScribe.exe
├── README.txt
└── API_KEY_INSTRUCTIONS.txt
```

## 🔒 Code Signing (Optional - For Enterprise)

For enterprise distribution, consider code signing:
1. Purchase code signing certificate
2. Sign the EXE: `signtool sign /f cert.pfx /p password HallmarkScribe.exe`
3. Windows won't show "Unknown Publisher" warning

## 📱 Updates

When you make changes:
1. Make code changes
2. Run `build_exe.bat` again
3. Distribute new EXE
4. Consider version numbers in filename: `HallmarkScribe_v1.1.exe`

## 🛠️ Troubleshooting

**"Windows protected your PC":**
- Click "More info" → "Run anyway"
- This is normal for unsigned executables
- Code signing eliminates this warning

**"Missing DLL errors":**
- Rebuild the EXE with `build_exe.bat`
- Make sure all dependencies in `requirements.txt`

**EXE won't start:**
- Check Windows Event Viewer for errors
- Run from command line to see error messages:
  ```
  cmd
  HallmarkScribe.exe
  ```

## ✨ Success!

You now have a distributable Windows application that anyone can run without Python or dependencies!

**Next steps:**
1. Test the EXE thoroughly
2. Create user documentation
3. Share with users
4. Collect feedback
5. Iterate and improve!
