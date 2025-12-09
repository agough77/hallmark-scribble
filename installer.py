"""
Hallmark Scribble - Installer GUI
Builds both applications and installs them with shortcuts
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import ctypes

def is_admin():
    """Check if running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Re-run the script with admin privileges"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hallmark Scribble Installer")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Get script directory (or exe directory if frozen)
        if getattr(sys, 'frozen', False):
            # Running as compiled executable - PyInstaller creates a temp folder and stores path in _MEIPASS
            self.script_dir = Path(sys._MEIPASS)
        else:
            # Running as script
            self.script_dir = Path(__file__).parent
        
        # Installation options
        self.install_desktop = tk.BooleanVar(value=True)
        self.install_web = tk.BooleanVar(value=True)
        
        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(main_frame, text="Hallmark Scribble Installer", 
                         font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Installation options
        options_frame = ttk.LabelFrame(main_frame, text="Select Components to Install", padding="10")
        options_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        desktop_check = ttk.Checkbutton(options_frame, text="Desktop Application (PyQt5 GUI)", 
                                       variable=self.install_desktop)
        desktop_check.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        web_check = ttk.Checkbutton(options_frame, text="Web Application (Browser-based)", 
                                    variable=self.install_web)
        web_check.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Info label
        info_label = ttk.Label(options_frame, 
                              text="Tip: Install only what you need to speed up installation", 
                              font=("Arial", 8), foreground="gray")
        info_label.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to install", 
                                     font=("Arial", 10))
        self.status_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=2, pady=(0, 20))
        
        # Log text area
        self.log_text = tk.Text(main_frame, height=10, width=70, wrap=tk.WORD)
        self.log_text.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        # Scrollbar for log
        scrollbar = ttk.Scrollbar(main_frame, command=self.log_text.yview)
        scrollbar.grid(row=4, column=2, sticky=(tk.N, tk.S))
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        self.install_btn = ttk.Button(button_frame, text="Build & Install", 
                                      command=self.start_install, width=20)
        self.install_btn.grid(row=0, column=0, padx=5)
        
        self.close_btn = ttk.Button(button_frame, text="Close", 
                                    command=self.root.quit, width=20)
        self.close_btn.grid(row=0, column=1, padx=5)
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def update_status(self, message, progress=None):
        """Update status label and progress bar"""
        self.status_label.config(text=message)
        if progress is not None:
            self.progress['value'] = progress
        self.root.update()
        
    def run_command(self, cmd, cwd=None):
        """Run a command and capture output"""
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=cwd,
                shell=True,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                self.log(line.rstrip())
                
            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.log(f"Error: {str(e)}")
            return False
            
    def build_desktop_app(self):
        """Build desktop application"""
        if not self.install_desktop.get():
            self.log("Skipping desktop app (not selected)")
            return True
            
        self.update_status("Verifying Desktop Application...", 20)
        self.log("\n=== Checking Desktop App ===")
        
        desktop_dir = self.script_dir / "desktop_app" / "dist" / "HallmarkScribble_Desktop"
        if not desktop_dir.exists():
            self.log("ERROR: Desktop app not found. Please build it first with BUILD_ALL.bat")
            return False
        
        self.log(f"Found desktop app at: {desktop_dir}")
        return True
    
    def build_web_app(self):
        """Build web application"""
        if not self.install_web.get():
            self.log("Skipping web app (not selected)")
            return True
            
        self.update_status("Verifying Web Application...", 40)
        self.log("\n=== Checking Web App ===")
        
        web_dir = self.script_dir / "web_app" / "dist" / "HallmarkScribble_Web"
        if not web_dir.exists():
            self.log("ERROR: Web app not found. Please build it first with BUILD_ALL.bat")
            return False
            
        self.log(f"Found web app at: {web_dir}")
        return True
        
    def install_applications(self):
        """Install applications to Program Files"""
        self.update_status("Installing Applications...", 70)
        self.log("\n=== Installing Applications ===")
        
        install_dir = Path("C:/Program Files/HallmarkScribble")
        
        # Create installation directory
        try:
            install_dir.mkdir(parents=True, exist_ok=True)
            self.log(f"Created installation directory: {install_dir}")
        except Exception as e:
            self.log(f"ERROR creating installation directory: {e}")
            return False
        
        # Copy web app (if selected)
        if self.install_web.get():
            web_build = self.script_dir / "web_app" / "dist" / "HallmarkScribble_Web"
            if web_build.exists():
                try:
                    web_dest = install_dir / "Web"
                    if web_dest.exists():
                        shutil.rmtree(web_dest)
                    shutil.copytree(web_build, web_dest)
                    self.log(f"Copied web app to {web_dest}")
                except Exception as e:
                    self.log(f"ERROR copying web app: {e}")
                    return False
            else:
                self.log("WARNING: Web app build not found at web_app\\dist\\HallmarkScribble_Web")
                return False
        else:
            self.log("Skipped web app installation (not selected)")
            
        # Copy desktop app (if selected)
        if self.install_desktop.get():
            desktop_build = self.script_dir / "desktop_app" / "dist" / "HallmarkScribble_Desktop"
            if desktop_build.exists():
                try:
                    desktop_dest = install_dir / "Desktop"
                    if desktop_dest.exists():
                        shutil.rmtree(desktop_dest)
                    shutil.copytree(desktop_build, desktop_dest)
                    self.log(f"Copied desktop app to {desktop_dest}")
                except Exception as e:
                    self.log(f"ERROR copying desktop app: {e}")
                    return False
            else:
                self.log("WARNING: Desktop app build not found")
        else:
            self.log("Skipped desktop app installation (not selected)")
            
        # Copy shared folder
        shared_dir = self.script_dir / "shared"
        if shared_dir.exists():
            try:
                shared_dest = install_dir / "shared"
                self.log(f"Copying shared resources to {shared_dest}")
                
                # If shared exists, try to remove it first
                if shared_dest.exists():
                    self.log("Removing existing shared folder...")
                    try:
                        # Try to remove readonly attribute recursively
                        for root, dirs, files in os.walk(str(shared_dest), topdown=False):
                            for name in files:
                                filepath = os.path.join(root, name)
                                os.chmod(filepath, 0o777)
                            for name in dirs:
                                dirpath = os.path.join(root, name)
                                os.chmod(dirpath, 0o777)
                        shutil.rmtree(shared_dest)
                    except Exception as e:
                        self.log(f"WARNING: Could not remove existing shared folder: {e}")
                        self.log("If installation fails, please run the uninstaller first.")
                
                shutil.copytree(shared_dir, shared_dest)
                self.log(f"Copied shared resources to {shared_dest}")
            except Exception as e:
                self.log(f"ERROR copying shared resources: {e}")
                messagebox.showerror("Installation Error",
                                   f"Failed to copy shared resources.\n\n"
                                   f"Error: {e}\n\n"
                                   f"If Hallmark Scribble is already installed, "
                                   f"please run the uninstaller first from Start Menu.")
                return False
        
        # Copy updater if it exists
        updater_exe = self.script_dir / "HallmarkScribble_Updater.exe"
        if updater_exe.exists():
            try:
                updater_dest = install_dir / "HallmarkScribble_Updater.exe"
                shutil.copy2(updater_exe, updater_dest)
                self.log(f"Copied updater to {updater_dest}")
            except Exception as e:
                self.log(f"WARNING: Could not copy updater: {e}")
        
        # Copy restart tool if it exists
        restart_exe = self.script_dir / "HallmarkScribble_RestartService.exe"
        if restart_exe.exists():
            try:
                restart_dest = install_dir / "HallmarkScribble_RestartService.exe"
                shutil.copy2(restart_exe, restart_dest)
                self.log(f"Copied restart tool to {restart_dest}")
            except Exception as e:
                self.log(f"WARNING: Could not copy restart tool: {e}")
        
        # Copy config.txt if it exists
        config_file = self.script_dir / "config.txt"
        if config_file.exists():
            try:
                config_dest = install_dir / "config.txt"
                shutil.copy2(config_file, config_dest)
                self.log(f"Copied config.txt to {config_dest}")
            except Exception as e:
                self.log(f"WARNING: Could not copy config.txt: {e}")
        
        # Copy version.json
        version_file = self.script_dir / "version.json"
        if version_file.exists():
            try:
                version_dest = install_dir / "version.json"
                shutil.copy2(version_file, version_dest)
                self.log(f"Copied version info to {version_dest}")
            except Exception as e:
                self.log(f"WARNING: Could not copy version info: {e}")
        
        # Copy config.txt if it exists
        config_file = self.script_dir / "config.txt"
        if config_file.exists():
            try:
                config_dest = install_dir / "config.txt"
                shutil.copy2(config_file, config_dest)
                self.log(f"Copied configuration to {config_dest}")
            except Exception as e:
                self.log(f"WARNING: Could not copy config.txt: {e}")
                
        return True
        
    def create_shortcuts(self):
        """Create desktop and start menu shortcuts"""
        self.update_status("Creating Shortcuts...", 90)
        self.log("\n=== Creating Shortcuts ===")
        
        install_dir = Path("C:/Program Files/HallmarkScribble")
        desktop = Path.home() / "Desktop"
        start_menu = Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs/Hallmark Scribble")
        
        # Create start menu folder
        try:
            start_menu.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log(f"ERROR creating start menu folder: {e}")
            return False
            
        # Create shortcuts using PowerShell
        shortcuts = [
            {
                'name': 'Hallmark Scribble Web',
                'target': str(install_dir / "Web" / "HallmarkScribble_Web.exe"),
                'desktop': desktop / "Hallmark Scribble Web.lnk",
                'startmenu': start_menu / "Hallmark Scribble Web.lnk"
            },
            {
                'name': 'Hallmark Scribble Desktop',
                'target': str(install_dir / "Desktop" / "HallmarkScribble_Desktop.exe"),
                'desktop': desktop / "Hallmark Scribble Desktop.lnk",
                'startmenu': start_menu / "Hallmark Scribble Desktop.lnk"
            },
            {
                'name': 'Check for Updates',
                'target': str(install_dir / "HallmarkScribble_Updater.exe"),
                'desktop': None,  # Don't create desktop shortcut for updater
                'startmenu': start_menu / "Check for Updates.lnk"
            },
            {
                'name': 'Restart Services',
                'target': str(install_dir / "HallmarkScribble_RestartService.exe"),
                'desktop': None,  # Don't create desktop shortcut for restart tool
                'startmenu': start_menu / "Restart Services.lnk"
            },
            {
                'name': 'Uninstall Hallmark Scribble',
                'target': str(install_dir / "Uninstall.bat"),
                'desktop': None,  # Don't create desktop shortcut for uninstaller
                'startmenu': start_menu / "Uninstall.lnk"
            }
        ]
        
        for shortcut in shortcuts:
            if not Path(shortcut['target']).exists():
                self.log(f"Skipping {shortcut['name']} - executable not found")
                continue
                
            # Desktop shortcut (if specified)
            if shortcut['desktop']:
                ps_cmd = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{shortcut['desktop']}')
$Shortcut.TargetPath = '{shortcut['target']}'
$Shortcut.WorkingDirectory = '{Path(shortcut['target']).parent}'
$Shortcut.Description = '{shortcut['name']}'
$Shortcut.Save()
"""
                subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
                self.log(f"Created desktop shortcut: {shortcut['name']}")
            
            # Start menu shortcut
            ps_cmd = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{shortcut['startmenu']}')
$Shortcut.TargetPath = '{shortcut['target']}'
$Shortcut.WorkingDirectory = '{Path(shortcut['target']).parent}'
$Shortcut.Description = '{shortcut['name']}'
$Shortcut.Save()
"""
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
            self.log(f"Created start menu shortcut: {shortcut['name']}")
            
        # Create uninstaller
        uninstaller = install_dir / "Uninstall.bat"
        try:
            with open(uninstaller, 'w') as f:
                f.write(f"""@echo off
echo ========================================
echo Hallmark Scribble - Uninstaller
echo ========================================
echo.
echo WARNING: This will remove all Hallmark Scribble files and shortcuts.
echo.
pause

echo.
echo Stopping any running processes...
taskkill /F /IM HallmarkScribble_Web.exe 2>nul
taskkill /F /IM HallmarkScribble_Desktop.exe 2>nul
taskkill /F /IM HallmarkScribble.exe 2>nul
taskkill /F /IM main.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Removing desktop shortcuts...
del "{desktop}\\Hallmark Scribble Web.lnk" 2>nul
del "{desktop}\\Hallmark Scribble Desktop.lnk" 2>nul
del "{desktop}\\Hallmark Scribble.lnk" 2>nul

echo Removing Start Menu shortcuts...
rmdir /S /Q "{start_menu}" 2>nul
rmdir /S /Q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Hallmark Scribble" 2>nul
rmdir /S /Q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\HallmarkScribble" 2>nul

echo Removing old installation locations...
if exist "%LOCALAPPDATA%\\HallmarkScribble" (
    echo Found old installation in LocalAppData...
    rmdir /S /Q "%LOCALAPPDATA%\\HallmarkScribble" 2>nul
)
if exist "%USERPROFILE%\\HallmarkScribble" (
    echo Found old installation in UserProfile...
    rmdir /S /Q "%USERPROFILE%\\HallmarkScribble" 2>nul
)

echo Removing current installation directory...
cd /d "%TEMP%"
rmdir /S /Q "{install_dir}" 2>nul

echo.
echo ========================================
echo Hallmark Scribble has been uninstalled.
echo ========================================
pause
""")
            self.log(f"Created uninstaller: {uninstaller}")
        except Exception as e:
            self.log(f"WARNING: Could not create uninstaller: {e}")
            
        return True
        
    def clean_old_installations(self):
        """Remove old/broken installations before installing"""
        self.update_status("Checking for old installations...", 5)
        self.log("\n=== Cleaning Old Installations ===")
        
        install_dir = Path("C:/Program Files/HallmarkScribble")
        cleaned_something = False
        
        # Kill any running processes
        processes_to_kill = [
            "HallmarkScribble_Web.exe",
            "HallmarkScribble_Desktop.exe", 
            "HallmarkScribble.exe",
            "main.exe"
        ]
        
        for proc_name in processes_to_kill:
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", proc_name],
                    capture_output=True,
                    text=True
                )
                if "SUCCESS" in result.stdout:
                    self.log(f"Stopped running process: {proc_name}")
                    cleaned_something = True
            except:
                pass
        
        # Remove installation directory if it exists
        if install_dir.exists():
            self.log(f"Found existing installation at {install_dir}")
            try:
                # Remove readonly attributes recursively
                for root, dirs, files in os.walk(str(install_dir), topdown=False):
                    for name in files:
                        try:
                            filepath = os.path.join(root, name)
                            os.chmod(filepath, 0o777)
                        except:
                            pass
                    for name in dirs:
                        try:
                            dirpath = os.path.join(root, name)
                            os.chmod(dirpath, 0o777)
                        except:
                            pass
                
                shutil.rmtree(install_dir)
                self.log(f"Removed old installation directory")
                cleaned_something = True
            except Exception as e:
                self.log(f"WARNING: Could not fully remove old installation: {e}")
        
        # Check for old installation locations
        old_locations = [
            Path(os.environ.get('LOCALAPPDATA', '')) / "HallmarkScribble",
            Path(os.environ.get('USERPROFILE', '')) / "HallmarkScribble"
        ]
        
        for old_path in old_locations:
            if old_path.exists():
                self.log(f"Found old installation at {old_path}")
                try:
                    shutil.rmtree(old_path)
                    self.log(f"Removed old installation: {old_path}")
                    cleaned_something = True
                except Exception as e:
                    self.log(f"WARNING: Could not remove {old_path}: {e}")
        
        # Remove old shortcuts
        desktop = Path.home() / "Desktop"
        old_shortcuts = [
            desktop / "Hallmark Scribble Web.lnk",
            desktop / "Hallmark Scribble Desktop.lnk",
            desktop / "Hallmark Scribble.lnk"
        ]
        
        for shortcut in old_shortcuts:
            if shortcut.exists():
                try:
                    shortcut.unlink()
                    self.log(f"Removed old shortcut: {shortcut.name}")
                    cleaned_something = True
                except:
                    pass
        
        # Remove old Start Menu folders
        old_start_menu_locations = [
            Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs/Hallmark Scribble"),
            Path(os.environ.get('APPDATA', '')) / "Microsoft/Windows/Start Menu/Programs/Hallmark Scribble",
            Path(os.environ.get('APPDATA', '')) / "Microsoft/Windows/Start Menu/Programs/HallmarkScribble"
        ]
        
        for old_menu in old_start_menu_locations:
            if old_menu.exists():
                try:
                    shutil.rmtree(old_menu)
                    self.log(f"Removed old Start Menu folder: {old_menu}")
                    cleaned_something = True
                except:
                    pass
        
        if cleaned_something:
            self.log("Old installations cleaned successfully")
        else:
            self.log("No old installations found")
        
        return True
        
    def start_install(self):
        """Main installation process"""
        # Check if at least one component is selected
        if not self.install_desktop.get() and not self.install_web.get():
            messagebox.showwarning("No Selection", 
                                 "Please select at least one component to install.")
            return
        
        # Disable buttons during install
        self.install_btn.config(state='disabled')
        self.close_btn.config(state='disabled')
        
        try:
            # Step 0: Clean old installations
            if not self.clean_old_installations():
                messagebox.showerror("Error", "Failed to clean old installations")
                return
            
            # Step 1: Build desktop app
            if not self.build_desktop_app():
                messagebox.showerror("Error", "Desktop app build failed")
                return
                
            # Step 2: Build web app
            if not self.build_web_app():
                messagebox.showerror("Error", "Web app build failed")
                return
                
            # Step 3: Install applications
            if not self.install_applications():
                messagebox.showerror("Error", "Installation failed")
                return
                
            # Step 4: Create shortcuts
            if not self.create_shortcuts():
                messagebox.showerror("Error", "Shortcut creation failed")
                return
                
            # Success
            self.update_status("Installation Complete!", 100)
            self.log("\n=== Installation Successful! ===")
            self.log("\nYou can now find Hallmark Scribble in:")
            self.log("- Desktop shortcuts")
            self.log("- Start Menu > Hallmark Scribble")
            self.log(f"- Installed to: C:\\Program Files\\HallmarkScribble\\")
            
            messagebox.showinfo("Success", 
                              "Hallmark Scribble installed successfully!\n\n"
                              "Check your desktop and start menu for shortcuts.")
                              
        except Exception as e:
            self.log(f"\nERROR: {str(e)}")
            messagebox.showerror("Error", f"Installation failed: {str(e)}")
            
        finally:
            # Re-enable buttons
            self.install_btn.config(state='normal')
            self.close_btn.config(state='normal')

def main():
    # Check for admin privileges
    if not is_admin():
        messagebox.showerror("Admin Required", 
                           "This installer requires administrator privileges.\n"
                           "Please run as administrator.")
        run_as_admin()
        return
        
    # Create and run GUI
    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
