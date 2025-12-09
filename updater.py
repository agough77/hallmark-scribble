"""
Hallmark Scribble - Update Checker and Installer
Checks for updates and installs them automatically
"""
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import hashlib
from datetime import datetime

# Version info
CURRENT_VERSION = "1.0.2"
LOCAL_DEV_PATH = Path(r"C:\Users\AGough\Hallmark University\IT Services - Documents\Scripts + Tools\Hallmark Scribble")
# GitHub repository for public version.json access (no authentication required)
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/agough77/hallmark-scribble/main/version.json"
GITHUB_REPO_URL = "https://github.com/agough77/hallmark-scribble"

class UpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hallmark Scribble Updater")
        self.root.geometry("500x300")
        self.root.resizable(False, False)
        
        # Installation directory
        self.install_dir = Path("C:/Program Files/HallmarkScribble")
        
        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(main_frame, text="Hallmark Scribble Updater", 
                         font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, pady=(0, 10))
        
        # Version info
        self.version_label = ttk.Label(main_frame, 
                                       text=f"Current Version: {CURRENT_VERSION}", 
                                       font=("Arial", 10))
        self.version_label.grid(row=1, column=0, pady=(0, 5))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to check for updates", 
                                     font=("Arial", 10))
        self.status_label.grid(row=2, column=0, pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress.grid(row=3, column=0, pady=(0, 20))
        
        # Log text area
        self.log_text = tk.Text(main_frame, height=8, width=60, wrap=tk.WORD)
        self.log_text.grid(row=4, column=0, pady=(0, 10))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, command=self.log_text.yview)
        scrollbar.grid(row=4, column=1, sticky=(tk.N, tk.S))
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, pady=(10, 0))
        
        self.check_btn = ttk.Button(button_frame, text="Check for Updates", 
                                    command=self.check_updates, width=20)
        self.check_btn.grid(row=0, column=0, padx=5)
        
        self.close_btn = ttk.Button(button_frame, text="Close", 
                                    command=self.root.quit, width=20)
        self.close_btn.grid(row=0, column=1, padx=5)
        
        # Configure grid
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Auto-check on startup
        self.root.after(500, self.check_updates)
        
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def update_status(self, message, progress=None):
        """Update status label and progress bar"""
        self.status_label.config(text=message)
        if progress is not None:
            self.progress['value'] = progress
        self.root.update()
        
    def get_version_info(self):
        """Get latest version info - Check GitHub, local dev, or installed directory"""
        try:
            # Try to fetch from GitHub first (public URL, no authentication)
            try:
                self.log("Checking GitHub for latest version...")
                request = urllib.request.Request(GITHUB_VERSION_URL)
                request.add_header('User-Agent', 'HallmarkScribble/1.0')
                with urllib.request.urlopen(request, timeout=10) as response:
                    version_data = json.loads(response.read().decode())
                    version_data['source'] = 'github'
                    self.log(f"Successfully fetched version {version_data.get('version')} from GitHub")
                    return version_data
            except Exception as gh_error:
                self.log(f"GitHub fetch failed: {gh_error}")
                self.log("Falling back to local checks...")
            
            # Check local development folder (only on dev machine)
            if LOCAL_DEV_PATH.exists():
                local_version_file = LOCAL_DEV_PATH / "version.json"
                if local_version_file.exists():
                    self.log("Found local development version.json")
                    with open(local_version_file, 'r') as f:
                        version_data = json.load(f)
                        version_data['source'] = 'local'
                        return version_data
            
            # Check installed application directory
            installed_version_file = self.install_dir / "version.json"
            if installed_version_file.exists():
                self.log("Found installed version.json")
                with open(installed_version_file, 'r') as f:
                    version_data = json.load(f)
                    version_data['source'] = 'installed'
                    return version_data
            
            # Fallback to updater's directory
            current_version_file = Path(__file__).parent / "version.json"
            if current_version_file.exists():
                self.log("Found updater directory version.json")
                with open(current_version_file, 'r') as f:
                    version_data = json.load(f)
                    version_data['source'] = 'updater'
                    return version_data
            
            return None
        except Exception as e:
            self.log(f"Could not fetch version info: {e}")
            return None
            
    def compare_versions(self, current, latest):
        """Compare version strings (e.g., '1.0.0' vs '1.0.1')"""
        current_parts = [int(x) for x in current.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]
        
        for i in range(max(len(current_parts), len(latest_parts))):
            c = current_parts[i] if i < len(current_parts) else 0
            l = latest_parts[i] if i < len(latest_parts) else 0
            if l > c:
                return True  # Update available
            elif l < c:
                return False
        return False  # Same version
        
    def download_file(self, url, dest_path):
        """Download a file with progress"""
        try:
            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, (downloaded / total_size) * 100)
                    self.update_status(f"Downloading: {percent:.1f}%", percent)
            
            urllib.request.urlretrieve(url, dest_path, reporthook=report_progress)
            return True
        except Exception as e:
            self.log(f"Download failed: {e}")
            return False
            
    def verify_checksum(self, file_path, expected_hash):
        """Verify file integrity"""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest() == expected_hash
        except Exception as e:
            self.log(f"Checksum verification failed: {e}")
            return False
            
    def backup_current_installation(self):
        """Create backup of current installation"""
        try:
            backup_dir = self.install_dir.parent / f"HallmarkScribble_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.log(f"Creating backup at {backup_dir}")
            shutil.copytree(self.install_dir, backup_dir)
            return backup_dir
        except Exception as e:
            self.log(f"Backup failed: {e}")
            return None
            
    def install_update(self, source_path):
        """Install the update from local development or download"""
        try:
            self.update_status("Installing update...", 70)
            
            # Stop any running instances
            self.log("Stopping running instances...")
            subprocess.run(['taskkill', '/F', '/IM', 'HallmarkScribble_Web.exe'], 
                          capture_output=True, check=False)
            subprocess.run(['taskkill', '/F', '/IM', 'HallmarkScribble_Desktop.exe'], 
                          capture_output=True, check=False)
            
            # Copy from source
            if source_path.is_dir():
                # Copy directory structure - only update installed apps
                apps_to_check = [
                    ('web_app/dist/HallmarkScribble_Web', 'Web'),
                    ('desktop_app/dist/HallmarkScribble_Desktop', 'Desktop')
                ]
                
                updated_count = 0
                for src_path, app_name in apps_to_check:
                    src = source_path / src_path
                    dest = self.install_dir / app_name
                    
                    # Only update if the app is currently installed
                    if dest.exists() and src.exists():
                        self.log(f"Updating {app_name}...")
                        shutil.rmtree(dest)
                        shutil.copytree(src, dest)
                        self.log(f"✓ {app_name} updated")
                        updated_count += 1
                    elif dest.exists() and not src.exists():
                        self.log(f"⚠ {app_name} is installed but source not found - skipping")
                    elif not dest.exists() and src.exists():
                        self.log(f"ℹ {app_name} not installed - skipping")
                
                if updated_count == 0:
                    self.log("No installed apps found to update")
                    return False
            else:
                # Extract zip file
                import zipfile
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    zip_ref.extractall(self.install_dir)
            
            self.log("Update installed successfully")
            return True
        except Exception as e:
            self.log(f"Installation failed: {e}")
            return False
            
    def check_updates(self):
        """Main update check process"""
        self.check_btn.config(state='disabled')
        
        try:
            self.update_status("Checking for updates...", 10)
            self.log("Checking for updates...")
            
            # Check if installation exists
            if not self.install_dir.exists():
                self.log("Hallmark Scribble is not installed")
                self.update_status("Not installed", 0)
                messagebox.showwarning("Not Installed", 
                                     "Hallmark Scribble is not installed.\n"
                                     "Please run the installer first.")
                return
            
            # Get version info
            version_info = self.get_version_info()
            
            if not version_info:
                self.log("Could not check for updates (no version.json file)")
                self.update_status("Update check unavailable", 0)
                messagebox.showinfo("Update Check", 
                                  "Could not retrieve version information.\n"
                                  "Please check your network connection or contact IT support.")
                return
            
            latest_version = version_info.get('version')
            self.log(f"Latest version: {latest_version}")
            
            # Compare versions
            if not self.compare_versions(CURRENT_VERSION, latest_version):
                self.log("You have the latest version")
                self.update_status("Up to date", 100)
                messagebox.showinfo("Up to Date", 
                                  f"You have the latest version ({CURRENT_VERSION})")
                return
            
            # Update available
            self.log(f"Update available: {latest_version}")
            source = version_info.get('source', 'unknown')
            result = messagebox.askyesno("Update Available", 
                                        f"A new version is available: {latest_version}\n"
                                        f"Current version: {CURRENT_VERSION}\n"
                                        f"Source: {source}\n\n"
                                        f"Do you want to update now?")
            
            if not result:
                self.log("Update cancelled by user")
                return
            
            # Check if local development update
            if source == 'local':
                self.update_status("Copying from local development...", 30)
                self.log("Using local development builds")
                
                if self.install_update(LOCAL_DEV_PATH):
                    self.update_status("Update complete!", 100)
                    messagebox.showinfo("Update Complete", 
                                      f"Successfully updated to version {latest_version}!\n\n"
                                      f"Updated from local development folder.")
                else:
                    messagebox.showerror("Update Failed", "Could not install the update")
                return
            
            # Download update from GitHub
            self.update_status("Downloading update from GitHub...", 30)
            
            # For now, show message that manual download is needed
            messagebox.showinfo("Update Available",
                              f"Version {latest_version} is available!\n\n"
                              f"Please download the latest installer from GitHub:\n"
                              f"{GITHUB_REPO_URL}\n\n"
                              f"Run the installer as administrator to update.")
            self.update_status("Manual update required", 100)
            return
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Update check failed: {str(e)}")
            
        finally:
            self.check_btn.config(state='normal')

def main():
    root = tk.Tk()
    app = UpdaterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
