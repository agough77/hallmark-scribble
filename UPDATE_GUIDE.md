# Hallmark Scribble - Update System

## Overview
The update system allows you to push bug fixes and new features to installed applications.

## Files
- **`updater.py`** - Update checker GUI application
- **`version.json`** - Version information and changelog
- **`BUILD_UPDATER.bat`** - Builds the updater executable

## Workflow

### For End Users
1. Launch **"Check for Updates"** from Start Menu
2. Updater automatically checks for new versions
3. If update available, click "Yes" to download and install
4. Restart the application after update

### For Developers (Releasing Updates)

#### 1. Update Version Number
Edit `version.json`:
```json
{
  "version": "1.0.1",
  "release_date": "2025-12-09",
  "download_url": "https://github.com/YOUR_ORG/hallmark-scribble/releases/download/v1.0.1/HallmarkScribble_v1.0.1.zip",
  "sha256": "HASH_HERE",
  "changelog": [
    "Fixed screenshot bug",
    "Improved title persistence"
  ],
  "minimum_version": "1.0.0",
  "critical_update": false
}
```

#### 2. Build Updated Applications
```batch
cd desktop_app
call build_exe_fast.bat

cd ../web_app
call build_exe_web.bat
```

#### 3. Package the Update
Create a ZIP file containing:
```
HallmarkScribble_v1.0.1.zip
├── Web/
│   └── (contents of web_app/HallmarkScribble_Web/)
├── Desktop/
│   └── (contents of desktop_app/dist/HallmarkScribble_Desktop/)
├── shared/
│   └── (contents of shared/)
└── version.json
```

#### 4. Generate SHA256 Hash
```powershell
Get-FileHash "HallmarkScribble_v1.0.1.zip" -Algorithm SHA256
```
Copy the hash to `version.json`

#### 5. Publish Release

**Option A: GitHub Releases (Recommended)**
1. Create GitHub repository
2. Go to Releases → Create new release
3. Tag: `v1.0.1`
4. Upload `HallmarkScribble_v1.0.1.zip`
5. Publish release
6. Update `version.json` with the download URL

**Option B: SharePoint/Network Drive**
1. Upload ZIP to SharePoint
2. Get sharing link
3. Update `version.json` with SharePoint URL
4. Update `updater.py` to use SharePoint URL

**Option C: Local Network (Testing)**
1. Place `version.json` on shared network drive
2. Update `VERSION_URL` in `updater.py` to point to network path
3. Place ZIP file in same location

#### 6. Deploy version.json
Upload the updated `version.json` to:
- GitHub: `https://raw.githubusercontent.com/YOUR_ORG/hallmark-scribble/main/version.json`
- SharePoint: Your SharePoint URL
- Network: Shared network location

Users will automatically be notified on next update check.

## Update Configuration

### Current Setup (Local Testing)
- `updater.py` checks for `version.json` in same directory first
- Falls back to GitHub URL if configured
- Useful for testing updates locally

### Production Setup
1. Create GitHub repository or SharePoint location
2. Update `VERSION_URL` in `updater.py`:
   ```python
   VERSION_URL = "https://raw.githubusercontent.com/YOUR_ORG/hallmark-scribble/main/version.json"
   ```
3. Rebuild updater: `BUILD_UPDATER.bat`
4. Rebuild installer with new updater: `BUILD_INSTALLER.bat`

## Building the Updater

```batch
cd "C:\Users\AGough\Hallmark University\IT Services - Documents\Scripts + Tools\Hallmark Scribble"
BUILD_UPDATER.bat
```

This creates `HallmarkScribble_Updater.exe` (~5MB)

## Rebuilding Installer with Updater

After building the updater, rebuild the installer to include it:
```batch
BUILD_INSTALLER.bat
```

The installer will now include:
- Web application
- Desktop application
- Updater
- Start menu shortcut for "Check for Updates"

## Update Process Flow

```
User launches "Check for Updates"
    ↓
Updater fetches version.json
    ↓
Compares current version with latest
    ↓
If update available → Show dialog
    ↓
User clicks "Yes"
    ↓
Download update ZIP
    ↓
Verify SHA256 hash
    ↓
Create backup of current installation
    ↓
Extract and replace files
    ↓
Show completion message
    ↓
User restarts application
```

## Security Features

1. **SHA256 Verification** - Ensures downloaded file is not corrupted or tampered
2. **Automatic Backup** - Creates timestamped backup before updating
3. **Rollback Support** - If update fails, previous version remains intact

## Testing Updates Locally

1. Create test `version.json`:
   ```json
   {
     "version": "1.0.1",
     "release_date": "2025-12-08",
     "download_url": "file:///C:/Users/YourName/Downloads/test_update.zip",
     "sha256": "actual_hash_here",
     "changelog": ["Test update"],
     "minimum_version": "1.0.0",
     "critical_update": false
   }
   ```

2. Place `version.json` in same directory as `updater.py`

3. Run `python updater.py`

4. Updater will detect local version file and use it for testing

## Troubleshooting

**Update Check Fails**
- Check internet connection
- Verify `VERSION_URL` is accessible
- Check firewall settings

**Download Fails**
- Verify download URL in `version.json`
- Check available disk space
- Ensure proper permissions

**Installation Fails**
- Check if application is running (must be closed)
- Verify admin permissions
- Check backup was created

**Checksum Mismatch**
- Re-download the update
- Verify SHA256 in `version.json` matches actual file
- Check for file corruption

## Future Enhancements

- [ ] Auto-update on startup (optional setting)
- [ ] Delta updates (only changed files)
- [ ] Rollback button in updater
- [ ] Update notifications in main apps
- [ ] Silent update mode for critical fixes
- [ ] Update history viewer
