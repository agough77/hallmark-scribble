"""
Hallmark Scribble - Service Restart Tool
Restarts the Hallmark Scribble services if they fail
"""
import os
import sys
import subprocess
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import psutil

class ServiceRestartGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hallmark Scribble - Service Restart")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Installation directory
        self.install_dir = Path("C:/Program Files/HallmarkScribble")
        
        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(main_frame, text="Service Restart Tool", 
                         font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Service Status", padding="10")
        status_frame.grid(row=1, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        self.web_status_label = ttk.Label(status_frame, text="Web App: Checking...", 
                                          font=("Arial", 10))
        self.web_status_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.desktop_status_label = ttk.Label(status_frame, text="Desktop App: Checking...", 
                                             font=("Arial", 10))
        self.desktop_status_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Log text area
        self.log_text = tk.Text(main_frame, height=12, width=60, wrap=tk.WORD)
        self.log_text.grid(row=2, column=0, pady=(10, 10))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, command=self.log_text.yview)
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=(10, 0))
        
        self.check_btn = ttk.Button(button_frame, text="Check Status", 
                                    command=self.check_services, width=15)
        self.check_btn.grid(row=0, column=0, padx=5)
        
        self.restart_web_btn = ttk.Button(button_frame, text="Restart Web", 
                                         command=self.restart_web, width=15)
        self.restart_web_btn.grid(row=0, column=1, padx=5)
        
        self.restart_desktop_btn = ttk.Button(button_frame, text="Restart Desktop", 
                                             command=self.restart_desktop, width=15)
        self.restart_desktop_btn.grid(row=0, column=2, padx=5)
        
        self.close_btn = ttk.Button(button_frame, text="Close", 
                                    command=self.root.quit, width=15)
        self.close_btn.grid(row=1, column=1, padx=5, pady=(5, 0))
        
        # Configure grid
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Auto-check on startup
        self.root.after(500, self.check_services)
        
    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def is_process_running(self, process_name):
        """Check if a process is running"""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
        
    def kill_process(self, process_name):
        """Kill a process by name"""
        killed = False
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    self.log(f"Killed process: {proc.info['name']} (PID: {proc.info['pid']})")
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return killed
        
    def check_services(self):
        """Check status of services"""
        self.log("\n=== Checking Service Status ===")
        
        # Check web app
        web_running = self.is_process_running("HallmarkScribble_Web.exe")
        if web_running:
            self.web_status_label.config(text="Web App: ✓ Running", foreground="green")
            self.log("Web App: Running")
        else:
            self.web_status_label.config(text="Web App: ✗ Not Running", foreground="red")
            self.log("Web App: Not Running")
            
        # Check desktop app
        desktop_running = self.is_process_running("HallmarkScribble_Desktop.exe")
        if desktop_running:
            self.desktop_status_label.config(text="Desktop App: ✓ Running", foreground="green")
            self.log("Desktop App: Running")
        else:
            self.desktop_status_label.config(text="Desktop App: ✗ Not Running", foreground="red")
            self.log("Desktop App: Not Running")
            
    def restart_web(self):
        """Restart web application"""
        self.log("\n=== Restarting Web Application ===")
        
        # Kill existing process
        if self.is_process_running("HallmarkScribble_Web.exe"):
            self.log("Stopping existing web app...")
            self.kill_process("HallmarkScribble_Web.exe")
            time.sleep(2)
        
        # Start new process
        web_exe = self.install_dir / "Web" / "HallmarkScribble_Web.exe"
        if web_exe.exists():
            try:
                self.log(f"Starting web app: {web_exe}")
                subprocess.Popen([str(web_exe)], 
                               cwd=str(web_exe.parent),
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                time.sleep(2)
                
                if self.is_process_running("HallmarkScribble_Web.exe"):
                    self.log("✓ Web app started successfully")
                    self.web_status_label.config(text="Web App: ✓ Running", foreground="green")
                    messagebox.showinfo("Success", "Web application restarted successfully!")
                else:
                    self.log("✗ Web app failed to start")
                    messagebox.showerror("Error", "Web application failed to start")
                    
            except Exception as e:
                self.log(f"Error starting web app: {e}")
                messagebox.showerror("Error", f"Failed to start web app: {e}")
        else:
            self.log(f"ERROR: Web app not found at {web_exe}")
            messagebox.showerror("Not Found", 
                               f"Web application not found.\nExpected at: {web_exe}\n\n"
                               "Please reinstall Hallmark Scribble.")
            
    def restart_desktop(self):
        """Restart desktop application"""
        self.log("\n=== Restarting Desktop Application ===")
        
        # Kill existing process
        if self.is_process_running("HallmarkScribble_Desktop.exe"):
            self.log("Stopping existing desktop app...")
            self.kill_process("HallmarkScribble_Desktop.exe")
            time.sleep(2)
        
        # Start new process
        desktop_exe = self.install_dir / "Desktop" / "HallmarkScribble_Desktop.exe"
        if desktop_exe.exists():
            try:
                self.log(f"Starting desktop app: {desktop_exe}")
                subprocess.Popen([str(desktop_exe)], 
                               cwd=str(desktop_exe.parent))
                time.sleep(2)
                
                if self.is_process_running("HallmarkScribble_Desktop.exe"):
                    self.log("✓ Desktop app started successfully")
                    self.desktop_status_label.config(text="Desktop App: ✓ Running", foreground="green")
                    messagebox.showinfo("Success", "Desktop application restarted successfully!")
                else:
                    self.log("✗ Desktop app failed to start")
                    messagebox.showerror("Error", "Desktop application failed to start")
                    
            except Exception as e:
                self.log(f"Error starting desktop app: {e}")
                messagebox.showerror("Error", f"Failed to start desktop app: {e}")
        else:
            self.log(f"ERROR: Desktop app not found at {desktop_exe}")
            messagebox.showerror("Not Found", 
                               f"Desktop application not found.\nExpected at: {desktop_exe}\n\n"
                               "Please reinstall Hallmark Scribble.")

def main():
    root = tk.Tk()
    app = ServiceRestartGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
