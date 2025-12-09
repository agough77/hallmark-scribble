# Hallmark Scribble - Web Version

## Overview
This is the web-based version of Hallmark Scribble that runs on a server and can be accessed through any web browser.

## Features
- ✅ Upload screenshots via drag-and-drop or file browser
- ✅ AI-powered guide generation using Google Gemini
- ✅ View and manage all recordings
- ✅ Configure settings through web interface
- ✅ Access from any device on your network
- ✅ No desktop installation required

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r web_requirements.txt
   ```

2. **Configure API Key**
   - Open `config.txt`
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

3. **Start the Server**
   - Windows: Double-click `START_WEB_SERVER.bat`
   - Manual: `python web_app.py`

## Usage

### Starting the Server
Run `START_WEB_SERVER.bat` or execute:
```bash
python web_app.py
```

The server will start on `http://localhost:5000`

### Accessing from Other Devices
To access from other devices on your network:
1. Find your server's IP address
2. Access from any browser: `http://YOUR_IP:5000`

### Creating a Screenshot Guide
1. Click "Start New Guide"
2. Drag and drop screenshots or click to browse
3. Upload all relevant screenshots
4. Click "Generate AI Guide"
5. View the generated how-to guide

### Managing Recordings
- Click the "My Recordings" tab to view all guides
- Each recording shows date, name, and file count

### Settings
- Configure output folder location
- View server information and logs

## Server Deployment

### Running on a Network
To make the server accessible on your network:
```python
# Already configured in web_app.py
socketio.run(app, host='0.0.0.0', port=5000)
```

### Running as a Service (Windows)
1. Install NSSM: https://nssm.cc/
2. Create service:
   ```bash
   nssm install HallmarkScribbleWeb "C:\Python\python.exe" "C:\path\to\web_app.py"
   nssm start HallmarkScribbleWeb
   ```

### Running as a Service (Linux)
Create systemd service file `/etc/systemd/system/hallmark-scribble.service`:
```ini
[Unit]
Description=Hallmark Scribble Web Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/Hallmark Scribble
ExecStart=/usr/bin/python3 web_app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hallmark-scribble
sudo systemctl start hallmark-scribble
```

## API Endpoints

### POST /api/start_recording
Start a new recording session
- Returns: `session_id`, `output_dir`

### POST /api/upload_screenshot
Upload a screenshot file
- Form data: `file`, `output_dir`
- Returns: `filename`, `path`

### POST /api/generate_guide
Generate AI guide from screenshots
- Body: `{output_dir: string}`
- Returns: `guide` text

### GET /api/list_recordings
List all recordings
- Returns: Array of recordings with date, name, path, file_count

### GET/POST /api/config
Get or update configuration
- GET: Returns current config
- POST: Updates config values

## Troubleshooting

### Port Already in Use
Change the port in `web_app.py`:
```python
socketio.run(app, host='0.0.0.0', port=5001)  # Changed from 5000
```

### Can't Access from Other Devices
1. Check firewall settings - allow port 5000
2. Verify server is running on `0.0.0.0` not `localhost`
3. Use your actual IP address, not localhost

### Missing Dependencies
Install all requirements:
```bash
pip install -r web_requirements.txt
```

## Logs
Server logs are saved to:
`~/Downloads/Hallmark Scribble Outputs/hallmark_scribble_web.log`

## Security Notes
- This server is designed for internal network use
- For internet-facing deployment, add:
  - HTTPS/SSL certificates
  - Authentication system
  - Rate limiting
  - Input validation
  - CSRF protection

## Comparison: Desktop vs Web

| Feature | Desktop Version | Web Version |
|---------|----------------|-------------|
| Screen Recording | ✅ Yes | ❌ No (upload only) |
| Audio Recording | ✅ Yes | ❌ No |
| Screenshot Upload | ❌ No | ✅ Yes |
| AI Guide Generation | ✅ Yes | ✅ Yes |
| Multi-user | ❌ No | ✅ Yes |
| Remote Access | ❌ No | ✅ Yes |
| Installation Required | ✅ Yes | ❌ No (server only) |

## Future Enhancements
- [ ] Real-time screen recording via browser
- [ ] Audio transcription
- [ ] User authentication
- [ ] Team collaboration features
- [ ] Cloud storage integration
- [ ] Mobile app support
