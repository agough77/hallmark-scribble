"""
Robust Log Monitor with Auto-Recovery
Watches logs in real-time, categorizes issues, and automatically restarts server when needed
"""
import time
import os
import re
import subprocess
import sys
import requests
from datetime import datetime
from collections import deque
from pathlib import Path

class LogMonitor:
    def __init__(self, log_file_path):
        self.log_file = log_file_path
        self.last_position = 0
        self.error_buffer = deque(maxlen=10)  # Keep last 10 lines for context
        self.error_count = 0
        self.warning_count = 0
        self.screenshot_count = 0
        self.session_active = False
        self.server_process = None
        self.last_health_check = datetime.now()
        self.server_restarts = 0
        self.web_app_dir = Path(__file__).parent
        
        # Error patterns and their fixes
        self.error_patterns = {
            r"QApplication.*main.*thread": {
                "severity": "ERROR",
                "description": "PyQt threading issue - QApplication created in wrong thread",
                "fix": "Use HTML dialog instead of PyQt for web version"
            },
            r"No module named": {
                "severity": "ERROR",
                "description": "Missing Python module",
                "fix": "Install missing module with pip"
            },
            r"Permission denied": {
                "severity": "ERROR",
                "description": "File permission issue",
                "fix": "Check file/directory permissions"
            },
            r"Connection refused": {
                "severity": "ERROR",
                "description": "Server not running or port blocked",
                "fix": "Restart server or check firewall"
            },
            r"Traceback": {
                "severity": "ERROR",
                "description": "Python exception occurred",
                "fix": "Check full traceback for details"
            },
            r"404.*Not Found": {
                "severity": "WARNING",
                "description": "Endpoint or resource not found",
                "fix": "Check route definitions and URL paths"
            },
            r"500.*Internal Server Error": {
                "severity": "ERROR",
                "description": "Server-side error",
                "fix": "Check server logs for exception details"
            }
        }
        
        # Initialize position
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)
                self.last_position = f.tell()
    
    def analyze_line(self, line):
        """Analyze a log line and categorize it"""
        # Check for errors
        for pattern, info in self.error_patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                return {
                    'type': 'ERROR',
                    'line': line,
                    'severity': info['severity'],
                    'description': info['description'],
                    'fix': info['fix']
                }
        
        # Check for specific events
        if 'Started recording' in line:
            self.session_active = True
            return {'type': 'EVENT', 'event': 'SESSION_START', 'line': line}
        elif 'Stopped recording' in line:
            self.session_active = False
            return {'type': 'EVENT', 'event': 'SESSION_STOP', 'line': line}
        elif 'Screenshot captured' in line:
            self.screenshot_count += 1
            return {'type': 'EVENT', 'event': 'SCREENSHOT', 'line': line, 'count': self.screenshot_count}
        elif 'Guide generated' in line:
            return {'type': 'EVENT', 'event': 'GUIDE_COMPLETE', 'line': line}
        elif 'ERROR' in line or 'Error' in line:
            return {'type': 'ERROR', 'line': line, 'severity': 'ERROR', 'description': 'Generic error', 'fix': 'Check log details'}
        elif 'WARNING' in line or 'Warning' in line:
            return {'type': 'WARNING', 'line': line}
        elif 'CRITICAL' in line:
            return {'type': 'CRITICAL', 'line': line}
        
        return {'type': 'INFO', 'line': line}
    
    def format_output(self, analysis):
        """Format the analysis for display"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if analysis['type'] == 'ERROR':
            self.error_count += 1
            print(f"\n{'='*60}")
            print(f"🔴 ERROR #{self.error_count} at {timestamp}")
            print(f"{'='*60}")
            print(f"Severity: {analysis['severity']}")
            print(f"Issue: {analysis['description']}")
            print(f"Fix: {analysis['fix']}")
            print(f"\nLog: {analysis['line'].strip()}")
            print(f"{'='*60}\n")
            
        elif analysis['type'] == 'WARNING':
            self.warning_count += 1
            print(f"\n⚠️  WARNING at {timestamp}: {analysis['line'].strip()}")
            
        elif analysis['type'] == 'CRITICAL':
            print(f"\n🚨 CRITICAL at {timestamp}: {analysis['line'].strip()}")
            
        elif analysis['type'] == 'EVENT':
            if analysis['event'] == 'SESSION_START':
                self.screenshot_count = 0
                session_id = analysis['line'].split('session ')[-1].split(' ')[0]
                print(f"\n✅ Session Started at {timestamp}")
                print(f"   ID: {session_id}")
                
            elif analysis['event'] == 'SESSION_STOP':
                print(f"\n🛑 Session Stopped at {timestamp}")
                print(f"   Total screenshots: {self.screenshot_count}")
                
            elif analysis['event'] == 'SCREENSHOT':
                filename = analysis['line'].split('screenshot_')[-1].strip()
                print(f"  📸 Screenshot #{analysis['count']}: {filename}")
                
            elif analysis['event'] == 'GUIDE_COMPLETE':
                print(f"\n🎉 AI Guide Generated at {timestamp}")
    
    def check_server_health(self):
        """Check if the server is responding"""
        try:
            response = requests.get('http://127.0.0.1:5000/', timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def restart_server(self):
        """Restart the web server"""
        print("\n" + "=" * 60)
        print("🔄 SERVER CRASH DETECTED - AUTO-RESTARTING")
        print("=" * 60)
        
        # Kill any existing Python processes running web_app.py
        try:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/FI', 'WINDOWTITLE eq web_app.py*'], 
                             capture_output=True, timeout=5)
                time.sleep(2)
        except Exception as e:
            print(f"Warning: Could not kill existing process: {e}")
        
        # Start new server process
        try:
            print("🚀 Starting web server...")
            if sys.platform == 'win32':
                # Use PowerShell to start in new window
                cmd = f'Start-Process python -ArgumentList "web_app.py" -WorkingDirectory "{self.web_app_dir}"'
                subprocess.Popen(['powershell', '-Command', cmd], cwd=self.web_app_dir)
            else:
                # Linux/Mac
                subprocess.Popen([sys.executable, 'web_app.py'], 
                               cwd=self.web_app_dir,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            
            # Wait for server to start
            print("⏳ Waiting for server to start...")
            for i in range(15):
                time.sleep(1)
                if self.check_server_health():
                    self.server_restarts += 1
                    print(f"✅ Server restarted successfully (restart #{self.server_restarts})")
                    print(f"🌐 Access at: http://127.0.0.1:5000")
                    print("=" * 60 + "\n")
                    return True
            
            print("⚠️ Server started but not responding yet...")
            print("=" * 60 + "\n")
            return False
            
        except Exception as e:
            print(f"❌ Failed to restart server: {e}")
            print("=" * 60 + "\n")
            return False
    
    def monitor(self):
        """Main monitoring loop with auto-restart capability"""
        print("=" * 60)
        print("🔍 HALLMARK SCRIBBLE - LOG MONITOR WITH AUTO-RESTART")
        print("=" * 60)
        print(f"Log file: {self.log_file}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Server health checks: Every 30 seconds")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        print("\n⏳ Monitoring for events...\n")
        
        health_check_interval = 30  # Check every 30 seconds
        last_health_check = time.time()
        
        try:
            while True:
                # Check server health periodically
                current_time = time.time()
                if current_time - last_health_check >= health_check_interval:
                    if not self.check_server_health():
                        print(f"\n⚠️ Server not responding at {datetime.now().strftime('%H:%M:%S')}")
                        self.restart_server()
                    last_health_check = current_time
                
                if os.path.exists(self.log_file):
                    with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(self.last_position)
                        new_lines = f.readlines()
                        self.last_position = f.tell()
                        
                        for line in new_lines:
                            self.error_buffer.append(line)
                            analysis = self.analyze_line(line)
                            
                            # Only show relevant events, not all INFO lines
                            if analysis['type'] in ['ERROR', 'WARNING', 'CRITICAL', 'EVENT']:
                                self.format_output(analysis)
                            
                            # Check for critical errors that might crash the server
                            if analysis['type'] in ['ERROR', 'CRITICAL']:
                                # Give it a moment, then check health
                                time.sleep(2)
                                if not self.check_server_health():
                                    print(f"\n⚠️ Server crashed after error at {datetime.now().strftime('%H:%M:%S')}")
                                    self.restart_server()
                                    last_health_check = time.time()
                
                time.sleep(0.3)  # Check 3 times per second
                
        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("MONITORING SUMMARY")
            print("=" * 60)
            print(f"Errors: {self.error_count}")
            print(f"Warnings: {self.warning_count}")
            print(f"Screenshots captured: {self.screenshot_count}")
            print(f"Session active: {self.session_active}")
            print(f"Server restarts: {self.server_restarts}")
            print("=" * 60)
            print("\n✅ Monitoring stopped.\n")
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")

if __name__ == "__main__":
    log_path = os.path.join(
        os.path.expanduser("~"), 
        "Downloads", 
        "Hallmark Scribble Outputs", 
        "hallmark_scribble_web.log"
    )
    
    if not os.path.exists(log_path):
        print(f"❌ Log file not found: {log_path}")
        print("Make sure the web server is running!")
        exit(1)
    
    monitor = LogMonitor(log_path)
    monitor.monitor()

