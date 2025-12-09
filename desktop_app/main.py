import sys
import os
from datetime import datetime
import keyboard
import shutil
import logging
import traceback
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, 
                             QRadioButton, QHBoxLayout, QDialog, QComboBox, QDialogButtonBox,
                             QFrame, QGridLayout, QListWidget, QListWidgetItem, QMessageBox,
                             QCheckBox, QScrollArea, QButtonGroup, QLineEdit, QSplashScreen)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# Add parent directory to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.recorder.screen import start_screen_recording, stop_screen_recording, set_region
from shared.recorder.audio import start_audio_recording, stop_audio_recording, list_audio_devices, set_audio_device
from shared.recorder.input_logger import start_logging, stop_logging
from shared.utils.screenshot import select_region, select_window

def setup_logging():
    """Setup comprehensive error logging"""
    log_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "hallmark_scribble_errors.log")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("="*50)
    logging.info("Hallmark Scribble Started")
    logging.info(f"Log file: {log_file}")
    logging.info("="*50)
    return log_file

def load_config_to_env():
    """Load API key from config.txt into environment variables"""
    # Determine config path
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(__file__)
    
    config_path = os.path.join(app_dir, "config.txt")
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    if api_key:
                        os.environ['GEMINI_API_KEY'] = api_key
                    break

# Load config at startup
load_config_to_env()

class CleanupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("🗑️ Cleanup Manager")
        self.setGeometry(250, 250, 650, 500)
        self.selected_items = []
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Info label
        info_label = QLabel("📁 Select recordings to delete from your library")
        layout.addWidget(info_label)
        
        # List of recordings
        self.recording_list = QListWidget()
        self.recording_list.setSelectionMode(QListWidget.MultiSelection)
        self.load_recordings()
        layout.addWidget(self.recording_list)
        
        # Size info
        self.size_label = QLabel()
        self.update_size_info()
        layout.addWidget(self.size_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("✓ Select All")
        select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("✗ Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(deselect_all_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def load_recordings(self):
        """Load all recordings from configured output folder"""
        # Use parent's output folder if available, otherwise fall back to Downloads
        # Always add "Hallmark Scribble Outputs" subfolder
        if hasattr(self.parent, 'base_output_folder') and self.parent.base_output_folder:
            outputs_dir = os.path.join(self.parent.base_output_folder, "Hallmark Scribble Outputs")
            logging.info(f"Cleanup using configured output folder: {outputs_dir}")
        else:
            # Fallback to Downloads
            outputs_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs")
            logging.info(f"Cleanup using fallback output folder: {outputs_dir}")
        
        if not os.path.exists(outputs_dir):
            logging.warning(f"Output directory does not exist: {outputs_dir}")
            return
        
        self.recordings = []
        
        # Walk through date folders
        for date_folder in sorted(os.listdir(outputs_dir), reverse=True):
            date_path = os.path.join(outputs_dir, date_folder)
            if not os.path.isdir(date_path):
                continue
            
            # Walk through scribble folders
            for scribble_folder in sorted(os.listdir(date_path)):
                scribble_path = os.path.join(date_path, scribble_folder)
                if not os.path.isdir(scribble_path):
                    continue
                
                # Calculate folder size
                total_size = 0
                file_count = 0
                for dirpath, dirnames, filenames in os.walk(scribble_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                        file_count += 1
                
                size_mb = total_size / (1024 * 1024)
                
                # Add to list
                display_text = f"📁 {date_folder} / {scribble_folder}  —  {file_count} files  —  {size_mb:.1f} MB"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, scribble_path)
                self.recording_list.addItem(item)
                self.recordings.append({'path': scribble_path, 'size': total_size})
    
    def update_size_info(self):
        """Update total size information"""
        selected = self.recording_list.selectedItems()
        if selected:
            total_size = sum(os.path.getsize(os.path.join(root, f))
                           for item in selected
                           for root, _, files in os.walk(item.data(Qt.UserRole))
                           for f in files)
            size_mb = total_size / (1024 * 1024)
            self.size_label.setText(f"💾 Selected: {len(selected)} recording(s)  —  {size_mb:.1f} MB")
        else:
            total_recordings = self.recording_list.count()
            self.size_label.setText(f"💾 Total: {total_recordings} recording(s) in library")
    
    def select_all(self):
        """Select all items"""
        self.recording_list.selectAll()
        self.update_size_info()
    
    def deselect_all(self):
        """Deselect all items"""
        self.recording_list.clearSelection()
        self.update_size_info()
    
    def delete_selected(self):
        """Delete selected recordings"""
        selected = self.recording_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select recordings to delete.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete {len(selected)} recording(s)?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted_count = 0
            for item in selected:
                folder_path = item.data(Qt.UserRole)
                try:
                    shutil.rmtree(folder_path)
                    deleted_count += 1
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to delete: {os.path.basename(folder_path)}\n{str(e)}")
            
            # Reload list
            self.recording_list.clear()
            self.load_recordings()
            self.update_size_info()
            
            QMessageBox.information(self, "Success", f"Deleted {deleted_count} recording(s) successfully!")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setWindowTitle("⚙️ Settings")
        self.setGeometry(300, 300, 550, 350)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Output Folder section
        output_label = QLabel("📁 Output Folder:")
        layout.addWidget(output_label)
        
        output_layout = QHBoxLayout()
        self.output_folder_input = QLineEdit()
        self.output_folder_input.setReadOnly(True)
        
        # Load existing output folder if available
        if parent:
            config_path = parent.get_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    for line in f:
                        if line.startswith('OUTPUT_FOLDER='):
                            existing_folder = line.split('=', 1)[1].strip()
                            self.output_folder_input.setText(existing_folder)
                            break
        
        output_layout.addWidget(self.output_folder_input)
        
        from PyQt5.QtWidgets import QFileDialog
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(browse_btn)
        
        layout.addLayout(output_layout)
        
        output_help = QLabel("All recordings and screenshots will be saved to this folder")
        output_help.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(output_help)
        
        # Add separator
        from PyQt5.QtWidgets import QFrame
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        layout.addWidget(separator)
        
        # API Key section
        api_label = QLabel("🔑 Google Gemini API Key:")
        layout.addWidget(api_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key here...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        
        # Load existing API key if available
        if parent:
            config_path = parent.get_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    for line in f:
                        if line.startswith('GEMINI_API_KEY='):
                            existing_key = line.split('=', 1)[1].strip()
                            self.api_key_input.setText(existing_key)
                            break
        
        layout.addWidget(self.api_key_input)
        
        api_help = QLabel('<a href="https://makersuite.google.com/app/apikey">Get your free API key here</a>')
        api_help.setOpenExternalLinks(True)
        api_help.setStyleSheet("font-size: 10px; color: #4A90E2;")
        layout.addWidget(api_help)
        
        # Add separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        layout.addWidget(separator2)
        
        # Audio device selection
        audio_label = QLabel("🎤 Select Audio Device:")
        layout.addWidget(audio_label)
        
        self.audio_combo = QComboBox()
        devices = list_audio_devices()
        if devices:
            self.audio_combo.addItems(devices)
        else:
            self.audio_combo.addItem("No devices found")
        layout.addWidget(self.audio_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def browse_output_folder(self):
        """Browse for output folder"""
        from PyQt5.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            self.output_folder_input.text() or os.path.expanduser("~/Documents"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder:
            self.output_folder_input.setText(folder)
    
    def save_settings(self):
        """Save API key, output folder, and accept dialog"""
        # Save to config.txt
        if self.parent_app:
            config_path = self.parent_app.get_config_path()
            api_key = self.api_key_input.text().strip()
            output_folder = self.output_folder_input.text().strip()
            
            # Read existing config
            lines = []
            api_key_found = False
            output_folder_found = False
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    for line in f:
                        if line.startswith('GEMINI_API_KEY='):
                            if api_key:
                                lines.append(f'GEMINI_API_KEY={api_key}\n')
                            else:
                                lines.append(line)
                            api_key_found = True
                        elif line.startswith('OUTPUT_FOLDER='):
                            if output_folder:
                                lines.append(f'OUTPUT_FOLDER={output_folder}\n')
                            else:
                                lines.append(line)
                            output_folder_found = True
                        else:
                            lines.append(line)
            
            # Add new entries if not found
            if api_key and not api_key_found:
                lines.append(f'GEMINI_API_KEY={api_key}\n')
            if output_folder and not output_folder_found:
                lines.append(f'OUTPUT_FOLDER={output_folder}\n')
            
            # Write config
            with open(config_path, 'w') as f:
                f.writelines(lines)
            
            # Update environment variable and parent app settings immediately
            if api_key:
                os.environ['GEMINI_API_KEY'] = api_key
            if output_folder:
                self.parent_app.base_output_folder = output_folder
        
        self.accept()
    
    def get_selected_device(self):
        return self.audio_combo.currentText()

class RecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hallmark Scribble - How-To Creator")
        self.setGeometry(200, 200, 320, 420)
        self.current_output_dir = None
        self.is_recording = False
        self.is_screenshot_mode = False
        self.screenshot_count = 0
        self.base_output_folder = None
        
        # Load output folder from config if available
        self.load_output_folder_from_config()
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

        # === SCREENSHOT MODE SECTION ===
        screenshot_label = QLabel("📸 Screenshot How-To")
        screenshot_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(screenshot_label)
        
        # Hotkey info
        hotkey_info = QLabel("Hotkey: Shift+Alt+H | Click mouse to capture")
        hotkey_info.setStyleSheet("font-size: 10px; color: #4A90E2;")
        main_layout.addWidget(hotkey_info)
        
        self.screenshot_fullscreen_radio = QRadioButton("Full Screen")
        self.screenshot_fullscreen_radio.setChecked(True)
        self.screenshot_window_radio = QRadioButton("Window")
        
        # Create button group for screenshot mode radio buttons
        self.screenshot_button_group = QButtonGroup()
        self.screenshot_button_group.addButton(self.screenshot_fullscreen_radio)
        self.screenshot_button_group.addButton(self.screenshot_window_radio)
        
        # Store selected window region
        self.selected_window_region = None
        
        # Connect window radio to show window selector
        self.screenshot_window_radio.toggled.connect(self.on_window_mode_toggled)

        screenshot_radio_layout = QHBoxLayout()
        screenshot_radio_layout.addWidget(self.screenshot_fullscreen_radio)
        screenshot_radio_layout.addWidget(self.screenshot_window_radio)
        main_layout.addLayout(screenshot_radio_layout)
        
        self.screenshot_counter_label = QLabel("Captures: 0")
        main_layout.addWidget(self.screenshot_counter_label)
        
        screenshot_grid = QGridLayout()
        screenshot_grid.setSpacing(3)
        
        self.screenshot_start_btn = QPushButton("Start")
        self.screenshot_start_btn.clicked.connect(self.start_screenshot_mode)
        screenshot_grid.addWidget(self.screenshot_start_btn, 0, 0)

        self.screenshot_stop_btn = QPushButton("Stop")
        self.screenshot_stop_btn.clicked.connect(self.stop_screenshot_mode)
        screenshot_grid.addWidget(self.screenshot_stop_btn, 0, 1)

        self.screenshot_editor_btn = QPushButton("Editor")
        self.screenshot_editor_btn.clicked.connect(self.open_html_editor)
        screenshot_grid.addWidget(self.screenshot_editor_btn, 0, 2)
        
        main_layout.addLayout(screenshot_grid)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator1)
        
        # === VIDEO MODE SECTION ===
        video_label = QLabel("🎥 Video How-To")
        video_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(video_label)
        
        self.full_screen_radio = QRadioButton("Full Screen")
        self.full_screen_radio.setChecked(True)
        self.window_radio = QRadioButton("Window")
        
        # Create button group for video mode radio buttons
        self.video_button_group = QButtonGroup()
        self.video_button_group.addButton(self.full_screen_radio)
        self.video_button_group.addButton(self.window_radio)
        
        # Connect window radio to show window selector
        self.window_radio.toggled.connect(self.on_video_window_mode_toggled)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.full_screen_radio)
        radio_layout.addWidget(self.window_radio)
        main_layout.addLayout(radio_layout)
        
        video_grid = QGridLayout()
        video_grid.setSpacing(3)
        
        self.video_start_btn = QPushButton("Start")
        self.video_start_btn.clicked.connect(self.start_video_recording)
        video_grid.addWidget(self.video_start_btn, 0, 0)

        self.video_stop_btn = QPushButton("Stop")
        self.video_stop_btn.clicked.connect(self.stop_video_recording)
        video_grid.addWidget(self.video_stop_btn, 0, 1)

        self.generate_guide_btn = QPushButton("Generate Guide")
        self.generate_guide_btn.clicked.connect(self.generate_video_guide)
        video_grid.addWidget(self.generate_guide_btn, 0, 2)

        self.add_narration_btn = QPushButton("Add Narration")
        self.add_narration_btn.clicked.connect(self.add_narration)
        video_grid.addWidget(self.add_narration_btn, 1, 0)

        self.video_editor_btn = QPushButton("Editor")
        self.video_editor_btn.clicked.connect(self.open_html_editor)
        video_grid.addWidget(self.video_editor_btn, 1, 1)

        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.show_preview)
        video_grid.addWidget(self.preview_btn, 1, 2)
        
        main_layout.addLayout(video_grid)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator2)
        
        # === SHARED TOOLS ===
        tools_label = QLabel("Tools")
        tools_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(tools_label)
        
        shared_grid = QGridLayout()
        shared_grid.setSpacing(3)
        
        self.open_folder_btn = QPushButton("Output")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        shared_grid.addWidget(self.open_folder_btn, 0, 0)
        
        self.cleanup_btn = QPushButton("Cleanup")
        self.cleanup_btn.clicked.connect(self.open_cleanup_manager)
        shared_grid.addWidget(self.cleanup_btn, 0, 1)
        
        self.logs_btn = QPushButton("Logs")
        self.logs_btn.clicked.connect(self.show_logs)
        shared_grid.addWidget(self.logs_btn, 0, 2)
        
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        shared_grid.addWidget(self.settings_btn, 1, 0)
        
        main_layout.addLayout(shared_grid)

        self.setLayout(main_layout)
        
        # Register global hotkeys
        try:
            keyboard.add_hotkey('ctrl+alt+r', self.hotkey_toggle_recording)
            keyboard.add_hotkey('shift+alt+h', self.hotkey_capture_screenshot)
        except:
            pass
    
    def get_config_path(self):
        """Get the path to config.txt in a persistent location"""
        # If running as EXE, store config next to the executable
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_dir = os.path.dirname(sys.executable)
            logging.info(f"Running as EXE - sys.executable: {sys.executable}")
            logging.info(f"EXE directory: {app_dir}")
            config_path = os.path.join(app_dir, "config.txt")
            logging.info(f"Config path for EXE: {config_path}")
            
            # If config doesn't exist next to exe, try to copy from bundled resources
            if not os.path.exists(config_path):
                logging.warning(f"Config not found at {config_path}, checking bundled resources")
                # PyInstaller extracts files to sys._MEIPASS
                bundled_config = os.path.join(sys._MEIPASS, "config.txt")
                logging.info(f"Bundled config path: {bundled_config}")
                if os.path.exists(bundled_config):
                    import shutil
                    logging.info(f"Copying bundled config to {config_path}")
                    shutil.copy(bundled_config, config_path)
                else:
                    logging.error(f"Bundled config not found at {bundled_config}")
            else:
                logging.info(f"Config found at {config_path}")
            
            return config_path
        else:
            # Running as script
            app_dir = os.path.dirname(__file__)
            logging.info(f"Running as script - __file__: {__file__}")
            logging.info(f"Script directory: {app_dir}")
            config_path = os.path.join(app_dir, "config.txt")
            logging.info(f"Config path for script: {config_path}")
            return config_path
    
    def load_output_folder_from_config(self):
        """Load output folder from config if available"""
        try:
            config_path = self.get_config_path()
            logging.info(f"Loading output folder from config: {config_path}")
            logging.info(f"Config file exists: {os.path.exists(config_path)}")
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    content = f.read()
                    logging.info(f"Config file content:\n{content}")
                    f.seek(0)
                    for line in f:
                        line = line.strip()
                        if line.startswith('OUTPUT_FOLDER='):
                            output_folder = line.split('=', 1)[1].strip()
                            # Normalize path separators
                            output_folder = output_folder.replace('/', os.sep).replace('\\', os.sep)
                            logging.info(f"Found OUTPUT_FOLDER in config: '{output_folder}'")
                            logging.info(f"Path exists check: {os.path.exists(output_folder)}")
                            if output_folder and os.path.exists(output_folder):
                                self.base_output_folder = output_folder
                                logging.info(f"Output folder set to: {output_folder}")
                                return
                            elif output_folder:
                                logging.warning(f"Output folder in config does not exist: {output_folder}")
                logging.info("No OUTPUT_FOLDER found in config file")
            else:
                logging.warning(f"Config file not found: {config_path}")
        except Exception as e:
            logging.error(f"Error loading output folder: {e}", exc_info=True)
    
    def start_screenshot_mode(self):
        """Start screenshot capture mode"""
        try:
            self.status_label.setText("Initializing screenshot mode...")
            # Create new output directory
            self.current_output_dir = self.create_output_directory()
            self.screenshot_count = 0
            self.is_screenshot_mode = True
            self.update_screenshot_counter()
            
            # Start mouse listener for click captures with callback
            actions_log = os.path.join(self.current_output_dir, "actions.log")
            start_logging(output=actions_log, screenshot_dir_path=self.current_output_dir, 
                         click_callback=self.on_mouse_click_capture)
            
            self.status_label.setText("Screenshot mode active - Press Shift+Alt+H to capture")
            
            # Minimize the window
            self.showMinimized()
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def on_mouse_click_capture(self, x, y):
        """Callback for mouse click during screenshot mode"""
        if self.is_screenshot_mode and self.current_output_dir:
            import pyautogui
            from datetime import datetime
            
            self.screenshot_count += 1
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"screenshot_{self.screenshot_count:03d}_{timestamp}.png"
            filepath = os.path.join(self.current_output_dir, filename)
            
            # Check capture mode
            if self.screenshot_window_radio.isChecked() and self.selected_window_region:
                # Window mode - use stored window region
                x, y, w, h = self.selected_window_region
                # Capture specific window region
                screenshot = pyautogui.screenshot(region=(x, y, w, h))
            else:
                # Full screen mode
                screenshot = pyautogui.screenshot()
            
            screenshot.save(filepath)
            
            self.update_screenshot_counter()
            self.status_label.setText(f"✓ Captured screenshot {self.screenshot_count} - Click or Shift+Alt+H for next")
    
    def on_window_mode_toggled(self, checked):
        """Handle window mode radio button toggle"""
        if checked:
            # Show window selector when Window mode is selected
            result = select_window()
            if result:
                x, y, w, h = result
                # Validate dimensions before storing
                if w > 0 and h > 0:
                    self.selected_window_region = result
                    self.status_label.setText(f"✓ Window selected ({w}x{h}) - Ready to capture")
                else:
                    # Invalid dimensions - switch back to fullscreen
                    self.screenshot_fullscreen_radio.setChecked(True)
                    self.selected_window_region = None
                    self.status_label.setText(f"Invalid window size ({w}x{h}) - using Full Screen")
            else:
                # User cancelled - switch back to fullscreen
                self.screenshot_fullscreen_radio.setChecked(True)
                self.selected_window_region = None
                self.status_label.setText("Window selection cancelled - using Full Screen")
        else:
            # Clear selection when switching away from window mode
            self.selected_window_region = None
    
    def on_video_window_mode_toggled(self, checked):
        """Handle video mode window radio button toggle"""
        if checked:
            # Show window selector when Window mode is selected
            result = select_window()
            if result:
                x, y, w, h = result
                print(f"Window selection returned: x={x}, y={y}, w={w}, h={h}")
                # Validate dimensions before storing (need minimum size and positive values)
                if w > 50 and h > 50:
                    # Ensure even dimensions for FFmpeg
                    if w % 2 != 0:
                        w -= 1
                    if h % 2 != 0:
                        h -= 1
                    self.selected_window_region = (x, y, w, h)
                    self.status_label.setText(f"✓ Window selected ({w}x{h}) - Ready to record")
                else:
                    # Invalid dimensions - switch back to fullscreen
                    self.full_screen_radio.setChecked(True)
                    self.selected_window_region = None
                    self.status_label.setText(f"❌ Window too small ({w}x{h}). Please select a larger window or use Full Screen.")
            else:
                # User cancelled or window invalid - switch back to fullscreen
                self.full_screen_radio.setChecked(True)
                self.selected_window_region = None
                self.status_label.setText("❌ Window selection failed. Please try again or use Full Screen.")
        else:
            # Clear selection when switching away from window mode
            self.selected_window_region = None
    
    def stop_screenshot_mode(self):
        """Stop screenshot capture mode"""
        self.status_label.setText("Stopping screenshot mode...")
        self.is_screenshot_mode = False
        
        # Stop mouse listener
        stop_logging()
        
        # Auto-generate transcript and verify files
        if self.screenshot_count > 0 and self.current_output_dir:
            self.status_label.setText("Generating AI-powered guide...")
            self.auto_generate_screenshot_transcript()
            
            # Verify screenshots were saved
            import glob
            screenshots = glob.glob(os.path.join(self.current_output_dir, "screenshot_*.png"))
            if len(screenshots) > 0:
                self.status_label.setText(f"✓ Complete! {len(screenshots)} screenshots with AI guide")
            else:
                self.status_label.setText(f"⚠️ Session ended - screenshots may not have saved")
        else:
            self.status_label.setText("Screenshot session ended (no captures)")
    
    def auto_generate_screenshot_transcript(self):
        """Automatically generate transcript file for screenshots with AI-generated steps"""
        if not self.current_output_dir:
            return
        
        try:
            transcript_path = os.path.join(self.current_output_dir, "transcript.txt")
            actions_path = os.path.join(self.current_output_dir, "actions.log")
            
            # Generate AI-powered step-by-step guide
            self.status_label.setText("AI analyzing screenshots and actions...")
            guide_content = self.generate_ai_screenshot_guide(self.current_output_dir, self.screenshot_count)
            
            self.status_label.setText("Writing guide to file...")
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(guide_content)
                
        except Exception as e:
            print(f"Error creating transcript: {e}")
            self.status_label.setText("Warning: AI generation failed, using basic template")
            # Fallback to basic transcript
            try:
                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write("Screenshot How-To Guide\n\n")
                    f.write(f"Total Screenshots: {self.screenshot_count}\n\n")
            except:
                pass
    
    def generate_ai_screenshot_guide(self, scribble_dir, screenshot_count):
        """Generate AI-powered step-by-step instructions for screenshots"""
        
        # Validate we have screenshots to analyze
        if screenshot_count == 0:
            print("No screenshots to analyze")
            return "Screenshot How-To Guide\n\nNo screenshots captured yet.\n"
        
        try:
            import google.generativeai as genai
            import glob
            
            # Get API key
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                config_path = self.get_config_path()
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        for line in f:
                            if line.startswith('GEMINI_API_KEY='):
                                api_key = line.split('=', 1)[1].strip()
                                break
            
            if not api_key:
                print("No API key found, using basic template")
                self.status_label.setText("No API key found - using basic template")
                return f"Screenshot How-To Guide\n\nTotal Screenshots: {screenshot_count}\n\nAdd step descriptions for each screenshot in the editor.\n"
            
            print("API key found, generating AI content...")
            self.status_label.setText("API key found - initializing AI...")
            QApplication.processEvents()
            # Read action logs if available
            actions_log = ""
            actions_path = os.path.join(scribble_dir, "actions.log")
            if os.path.exists(actions_path):
                with open(actions_path, 'r', encoding='utf-8') as f:
                    actions_log = f.read()
            
            print("Configuring AI model...")
            self.status_label.setText("Configuring AI model...")
            QApplication.processEvents()
            genai.configure(api_key=api_key)
            
            # Use Gemini 2.0 Flash which supports vision
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Get all screenshot files
            screenshots = sorted([f for f in os.listdir(scribble_dir) 
                                if f.startswith("screenshot_") and f.endswith(".png")])
            
            if len(screenshots) == 0:
                print("No screenshot files found in directory")
                return f"Screenshot How-To Guide\n\nTotal Screenshots: {screenshot_count}\n\nScreenshots will appear here once captured.\n"
            
            print(f"Found {len(screenshots)} screenshots to analyze")
            self.status_label.setText(f"Found {len(screenshots)} screenshots - loading images...")
            QApplication.processEvents()
            
            # Load images for AI analysis
            from PIL import Image
            images = []
            for idx, screenshot_file in enumerate(screenshots[:screenshot_count], 1):  # Only analyze actual screenshots
                img_path = os.path.join(scribble_dir, screenshot_file)
                if os.path.exists(img_path):
                    images.append(Image.open(img_path))
                    self.status_label.setText(f"Loading image {idx}/{screenshot_count}...")
                    QApplication.processEvents()
            
            actions_context = f"\n\nUser actions during capture:\n{actions_log}" if actions_log else ""
            
            prompt = f"""You are analyzing {screenshot_count} screenshots to create a professional step-by-step how-to guide.

{actions_context}

Carefully examine each screenshot image and create a detailed, educational guide with:

1. A clear, engaging title for the tutorial based on what you see
2. A brief introduction explaining what will be accomplished
3. Step-by-step instructions (one for each screenshot):
   - Start with "Step 1:", "Step 2:", etc.
   - Describe exactly what you SEE in each screenshot
   - Identify specific UI elements, buttons, menus, text fields visible
   - Explain what action should be taken ("Click on...", "Type in...", "Select...")
   - Explain WHY each step matters
   - Use professional but friendly language
4. A brief conclusion or next steps

Analyze the visual content of each screenshot carefully. Reference specific elements you can see like button labels, menu items, window titles, etc.

Write in a natural, human-like style - as if an expert is explaining this to a colleague while showing them the screenshots. Be clear, educational, and encouraging. Keep each step concise but informative (2-4 sentences per step).

IMPORTANT: Write ONLY the guide content. Do NOT include any meta-commentary."""

            print("Sending screenshots to AI for analysis...")
            self.status_label.setText("Sending to AI for analysis (this may take a moment)...")
            QApplication.processEvents()
            response = model.generate_content([prompt] + images)
            guide_text = response.text.strip()
            
            print(f"AI generated {len(guide_text)} characters of content")
            self.status_label.setText(f"AI analysis complete - {len(guide_text)} characters generated")
            QApplication.processEvents()
            return guide_text if guide_text else f"Screenshot How-To Guide\n\nTotal Screenshots: {screenshot_count}\n\n"
            
        except Exception as e:
            print(f"AI guide generation failed: {e}")
            self.status_label.setText(f"AI generation failed: {str(e)}")
            return f"Screenshot How-To Guide\n\nTotal Screenshots: {screenshot_count}\n\n"
    
    def hotkey_capture_screenshot(self):
        """Capture screenshot when Ctrl+Alt+S is pressed"""
        print(f"Screenshot hotkey pressed. Mode: {self.is_screenshot_mode}, Dir: {self.current_output_dir}")
        
        if not self.is_screenshot_mode or not self.current_output_dir:
            print("Screenshot mode not active or no output directory")
            return
        
        try:
            import pyautogui
            from datetime import datetime
            
            self.screenshot_count += 1
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"screenshot_{self.screenshot_count:03d}_{timestamp}.png"
            filepath = os.path.join(self.current_output_dir, filename)
            
            print(f"Capturing screenshot {self.screenshot_count} to {filepath}")
            
            # Check capture mode
            if self.screenshot_window_radio.isChecked() and self.selected_window_region:
                # Window mode - use stored window region
                x, y, w, h = self.selected_window_region
                # Capture specific window region
                screenshot = pyautogui.screenshot(region=(x, y, w, h))
            else:
                # Full screen mode
                screenshot = pyautogui.screenshot()
            
            screenshot.save(filepath)
            print(f"Screenshot saved: {filepath}")
            
            self.update_screenshot_counter()
            self.status_label.setText(f"✓ Captured screenshot {self.screenshot_count} - Press Shift+Alt+H for next")
            
            # Log the action
            actions_path = os.path.join(self.current_output_dir, "actions.log")
            with open(actions_path, "a", encoding="utf-8") as f:
                log_time = datetime.now().strftime("%H:%M:%S")
                f.write(f"[{log_time}] Screenshot {self.screenshot_count} captured\n")
            
            # Auto-generate transcript after each capture
            self.auto_generate_screenshot_transcript()
        except Exception as e:
            print(f"Screenshot error: {e}")
            self.status_label.setText(f"Screenshot error: {str(e)}")
    
    def update_screenshot_counter(self):
        """Update the screenshot counter display"""
        self.screenshot_counter_label.setText(f"Captures: {self.screenshot_count}")
    
    def start_video_recording(self):
        """Start video recording (existing functionality)"""
        self.start_recording()
    
    def stop_video_recording(self):
        """Stop video recording (existing functionality)"""
        self.stop_recording()
    
    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            device = dialog.get_selected_device()
            if device and device != "No devices found":
                set_audio_device(device)
                self.status_label.setText(f"Audio device set: {device}")
            else:
                self.status_label.setText("No audio device selected")

    def create_output_directory(self):
        """Create a new timestamped output directory with incremental naming"""
        # Use the configured base output folder and add "Hallmark Scribble Outputs" subfolder
        if self.base_output_folder and os.path.exists(self.base_output_folder):
            base_dir = os.path.join(self.base_output_folder, "Hallmark Scribble Outputs")
            os.makedirs(base_dir, exist_ok=True)
        else:
            # Fallback to Downloads if base folder not set or doesn't exist
            base_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs")
            os.makedirs(base_dir, exist_ok=True)
        
        # Get current date for folder organization
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_dir = os.path.join(base_dir, date_str)
        os.makedirs(date_dir, exist_ok=True)
        
        # Find next available Scribble number
        existing = [d for d in os.listdir(date_dir) if d.startswith("Scribble ")]
        if existing:
            numbers = []
            for name in existing:
                try:
                    num = int(name.replace("Scribble ", ""))
                    numbers.append(num)
                except:
                    pass
            next_num = max(numbers) + 1 if numbers else 1
        else:
            next_num = 1
        
        scribble_dir = os.path.join(date_dir, f"Scribble {next_num}")
        os.makedirs(scribble_dir, exist_ok=True)
        return scribble_dir
    
    def start_recording(self):
        try:
            logging.info("="*50)
            logging.info("START RECORDING INITIATED")
            logging.info("="*50)
            
            # Create new output directory
            self.current_output_dir = self.create_output_directory()
            logging.info(f"Output directory created: {self.current_output_dir}")
            self.status_label.setText(f"Recording (Ctrl+Alt+R to stop)...")
            self.is_recording = True
            
            # Set up file paths
            video_path = os.path.join(self.current_output_dir, "recording.mp4")
            audio_path = os.path.join(self.current_output_dir, "audio.wav")
            log_path = os.path.join(self.current_output_dir, "actions.log")
            logging.info(f"Video path: {video_path}")
            logging.info(f"Audio path: {audio_path}")
            
            if self.window_radio.isChecked():
                logging.info("Window mode selected")
                # Use stored window region if available
                if self.selected_window_region:
                    x, y, w, h = self.selected_window_region
                    logging.info(f"Using stored window region: x={x}, y={y}, w={w}, h={h}")
                else:
                    # Prompt for window selection
                    logging.info("Prompting for window selection...")
                    result = select_window()
                    logging.info(f"Window selection result: {result}")
                    if result:
                        x, y, w, h = result
                        logging.info(f"Window selected: x={x}, y={y}, w={w}, h={h}")
                    else:
                        logging.warning("Window selection was cancelled or returned None")
                        self.status_label.setText("❌ Window selection failed. Please try again or use Full Screen.")
                        self.is_recording = False
                        return
                
                # Validate dimensions before adjustments
                logging.info(f"Validating dimensions: w={w}, h={h}")
                if w <= 0 or h <= 0:
                    error_msg = f"Invalid window dimensions: w={w}, h={h} (window may be minimized)"
                    logging.error(error_msg)
                    self.status_label.setText(f"❌ {error_msg}. Please restore the window and try again.")
                    self.is_recording = False
                    self.window_radio.setChecked(False)
                    self.full_screen_radio.setChecked(True)
                    return
                
                # Clamp coordinates to screen bounds
                # Get screen dimensions
                import win32api
                screen_width = win32api.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN - total width of all monitors
                screen_height = win32api.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN - total height of all monitors
                logging.info(f"Virtual screen dimensions: {screen_width}x{screen_height}")
                
                # Check if window extends beyond screen bounds
                if x + w > screen_width:
                    old_w = w
                    w = screen_width - x
                    logging.warning(f"Window extends beyond right edge of screen. Adjusted width from {old_w} to {w}")
                
                if y + h > screen_height:
                    old_h = h
                    h = screen_height - y
                    logging.warning(f"Window extends beyond bottom edge of screen. Adjusted height from {old_h} to {h}")
                
                if x < 0:
                    logging.info(f"X coordinate negative ({x}), clamping to 0")
                    w += x
                    x = 0
                if y < 0:
                    logging.info(f"Y coordinate negative ({y}), clamping to 0")
                    h += y
                    y = 0
                
                # Ensure minimum dimensions
                if w < 100:
                    logging.info(f"Width too small ({w}), setting to 100")
                    w = 100
                if h < 100:
                    logging.info(f"Height too small ({h}), setting to 100")
                    h = 100
                
                # Round dimensions to even numbers (required by FFmpeg)
                if w % 2 != 0:
                    w -= 1
                    logging.info(f"Width adjusted to even number: {w}")
                if h % 2 != 0:
                    h -= 1
                    logging.info(f"Height adjusted to even number: {h}")
                
                logging.info(f"Final adjusted coordinates: x={x}, y={y}, w={w}, h={h}")
                
                # Final validation
                if w <= 0 or h <= 0:
                    error_msg = f"Unable to adjust window size to valid dimensions (w={w}, h={h})"
                    logging.error(error_msg)
                    self.status_label.setText(f"❌ {error_msg}. Using Full Screen instead.")
                    self.is_recording = False
                    self.window_radio.setChecked(False)
                    self.full_screen_radio.setChecked(True)
                    # Retry with full screen
                    self.start_recording()
                    return
                
                logging.info("Setting window region for FFmpeg...")
                set_region(x, y, w, h)
                logging.info("Starting screen recording with window region...")
                start_screen_recording(output=video_path, full_screen=False)
                logging.info(f"✓ Recording started successfully for window: {x},{y} {w}x{h}")
                self.selected_window_region = (x, y, w, h)  # Store validated region
            else:
                logging.info("Full screen mode selected")
                start_screen_recording(output=video_path, full_screen=True)
                logging.info("✓ Full screen recording started successfully")
            
            # Try audio recording but don't fail if it doesn't work
            try:
                logging.info("Starting audio recording...")
                start_audio_recording(output=audio_path)
                logging.info("✓ Audio recording started")
            except Exception as audio_err:
                logging.warning(f"Audio recording failed: {audio_err}")
            
            logging.info("Starting input logging...")
            start_logging(output=log_path, screenshot_dir_path=self.current_output_dir)
            logging.info("✓ Input logging started")
            
            # Minimize window after starting recording
            self.showMinimized()
            logging.info("✓ Recording fully started and window minimized")
            logging.info("="*50)
        except FileNotFoundError as e:
            error_msg = "FFmpeg not found. Please install FFmpeg."
            logging.error(f"{error_msg} - {e}", exc_info=True)
            self.status_label.setText(f"❌ Error: {error_msg}")
            self.is_recording = False
        except Exception as e:
            logging.error(f"RECORDING ERROR: {str(e)}", exc_info=True)
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.is_recording = False

    def hotkey_toggle_recording(self):
        """Called when Ctrl+Alt+R is pressed - toggles recording on/off"""
        if self.is_recording:
            # Stop recording
            try:
                self.status_label.setText("Finalizing recording...")
                QApplication.processEvents()
                
                stop_screen_recording()
                stop_audio_recording()
                stop_logging()
                
                self.is_recording = False
                self.status_label.setText("Recording finalized ✓")
            except Exception as e:
                self.status_label.setText(f"Error stopping: {str(e)}")
                self.is_recording = False
        else:
            # Start recording
            self.start_recording()

    def stop_recording(self):
        try:
            # Restore window
            self.showNormal()
            self.activateWindow()
            
            self.status_label.setText("Finalizing recording...")
            QApplication.processEvents()  # Update UI immediately
            
            stop_screen_recording()
            stop_audio_recording()
            stop_logging()
            
            self.is_recording = False
            
            # Verify files were created
            if self.current_output_dir:
                video_path = os.path.join(self.current_output_dir, "recording.mp4")
                audio_path = os.path.join(self.current_output_dir, "audio.wav")
                
                import time
                time.sleep(0.5)  # Give files time to finish writing
                
                video_exists = os.path.exists(video_path) and os.path.getsize(video_path) > 0
                audio_exists = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
                
                if video_exists and audio_exists:
                    self.status_label.setText("✅ Recording finalized successfully")
                elif video_exists:
                    self.status_label.setText("⚠️ Recording saved (audio may have failed)")
                else:
                    self.status_label.setText("⚠️ Recording may have failed - check output folder")
            else:
                self.status_label.setText("✅ Recording stopped")
        except Exception as e:
            self.status_label.setText(f"❌ Error stopping: {str(e)}")
            self.is_recording = False

    def generate_transcript(self):
        if not self.current_output_dir:
            self.status_label.setText("Error: No recording found. Record first.")
            return
        
        # Check if this is screenshot mode (no video/audio files)
        audio_path = os.path.join(self.current_output_dir, "audio.wav")
        video_path = os.path.join(self.current_output_dir, "recording.mp4")
        
        if not os.path.exists(audio_path) and not os.path.exists(video_path):
            # Screenshot mode - create a basic transcript from action logs
            output_path = os.path.join(self.current_output_dir, "transcript.txt")
            actions_path = os.path.join(self.current_output_dir, "actions.log")
            
            try:
                if os.path.exists(actions_path):
                    with open(actions_path, "r", encoding="utf-8") as f:
                        actions = f.read()
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write("Screenshot How-To Guide\n\n")
                        f.write(actions)
                else:
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write("Screenshot How-To Guide\n\nAdd your step descriptions in the editor.")
                
                self.status_label.setText("Transcript created for screenshots")
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
            return
        
        # Video mode - use audio transcription
        self.status_label.setText("Analyzing audio...")
        QApplication.processEvents()
        
        try:
            from shared.transcription.whisper_transcribe import transcribe_audio
            output_path = os.path.join(self.current_output_dir, "transcript.txt")
            
            self.status_label.setText("Calling AI model...")
            QApplication.processEvents()
            
            if os.path.exists(audio_path):
                transcribe_audio(audio_path=audio_path, output=output_path)
            elif os.path.exists(video_path):
                transcribe_audio(audio_path=video_path, output=output_path)
            else:
                raise FileNotFoundError("No audio or video file found")
            
            self.status_label.setText("Transcript generated")
        except (ImportError, OSError) as e:
            error_msg = str(e)
            if "DLL" in error_msg or "torch" in error_msg.lower():
                self.status_label.setText("Error: PyTorch DLL issue. Manual transcription mode.")
            else:
                self.status_label.setText(f"Import Error: {error_msg[:100]}")
        except Exception as e:
            self.status_label.setText(f"Transcription unavailable: Manual mode")

    def export_guide(self):
        if not self.current_output_dir:
            self.status_label.setText("Error: No recording found. Record first.")
            return
        
        try:
            from shared.guide.generate_guide import create_guide
            transcript_path = os.path.join(self.current_output_dir, "transcript.txt")
            actions_path = os.path.join(self.current_output_dir, "actions.log")
            guide_path = os.path.join(self.current_output_dir, "guide.md")
            create_guide(transcript_path=transcript_path, actions_path=actions_path, output=guide_path)
            self.status_label.setText(f"Guide exported to {os.path.basename(self.current_output_dir)}/guide.md")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def open_output_folder(self):
        import subprocess
        logging.info(f"open_output_folder called - current_output_dir: {self.current_output_dir}")
        logging.info(f"open_output_folder called - base_output_folder: {self.base_output_folder}")
        
        if self.current_output_dir and os.path.exists(self.current_output_dir):
            # Open the current recording's folder
            logging.info(f"Opening current output folder: {self.current_output_dir}")
            subprocess.run(["explorer", self.current_output_dir])
        else:
            # Open the configured base output folder with Hallmark Scribble Outputs subfolder
            if self.base_output_folder and os.path.exists(self.base_output_folder):
                output_path = os.path.join(self.base_output_folder, "Hallmark Scribble Outputs")
                logging.info(f"Using configured base folder: {self.base_output_folder}")
            else:
                # Fallback to Downloads
                output_path = os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs")
                logging.info(f"Using fallback Downloads folder (base_output_folder={'None' if not self.base_output_folder else 'path does not exist'})")
            
            os.makedirs(output_path, exist_ok=True)
            logging.info(f"Opening output path: {output_path}")
            subprocess.run(["explorer", output_path])
    
    def show_logs(self):
        """Open the error log file in default text editor"""
        import subprocess
        log_file = os.path.join(os.path.expanduser("~"), "Downloads", "Hallmark Scribble Outputs", "hallmark_scribble_errors.log")
        if os.path.exists(log_file):
            os.startfile(log_file)
            logging.info(f"Opened log file: {log_file}")
            self.status_label.setText(f"✓ Log file opened")
        else:
            self.status_label.setText(f"❌ Log file not found")
            logging.warning(f"Log file not found: {log_file}")
    
    def open_cleanup_manager(self):
        """Open cleanup manager dialog"""
        dialog = CleanupDialog(self)
        dialog.exec_()
    
    def show_preview(self):
        import subprocess
        if not self.current_output_dir:
            self.status_label.setText("No recording found. Record first!")
            return
        
        # Check for narrated video first, then fall back to original
        narrated_path = os.path.join(self.current_output_dir, "narrated_video.mp4")
        video_path = os.path.join(self.current_output_dir, "recording.mp4")
        
        if os.path.exists(narrated_path):
            os.startfile(narrated_path)
            self.status_label.setText("Opening narrated video in default player")
        elif os.path.exists(video_path):
            os.startfile(video_path)
            self.status_label.setText("Opening preview in default player")
        else:
            self.status_label.setText("Video file not found!")
            return
    
    def open_html_editor(self):
        if not self.current_output_dir:
            self.status_label.setText("Error: No recording found. Record first.")
            return
        
        try:
            # Start the editor server
            from shared.guide.editor_server import start_editor_server
            start_editor_server()
            print("Editor server started on port 8765")
            
            from shared.guide.html_editor import create_html_editor
            import webbrowser
            html_content = create_html_editor(self.current_output_dir)
            # The HTML file is still saved, open it from the saved location
            html_path = os.path.join(self.current_output_dir, "editor.html")
            webbrowser.open(f"file:///{html_path}")
            self.status_label.setText("HTML editor opened in browser (server running on port 8765)")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            print(f"Editor error: {e}")
    
    def generate_video_guide(self):
        """Generate AI guide directly from video file using Gemini vision"""
        if not self.current_output_dir:
            self.status_label.setText("Error: No recording found. Record first.")
            return
        
        video_path = os.path.join(self.current_output_dir, "recording.mp4")
        if not os.path.exists(video_path):
            self.status_label.setText("Error: No video file found.")
            return
        
        self.status_label.setText("Uploading video to AI for analysis...")
        QApplication.processEvents()
        
        try:
            import google.generativeai as genai
            
            # Get API key
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                config_path = self.get_config_path()
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        for line in f:
                            if line.startswith('GEMINI_API_KEY='):
                                api_key = line.split('=', 1)[1].strip()
                                break
            
            if not api_key:
                self.status_label.setText("Error: No API key found. Go to Tools → Settings to add your API key")
                return
            
            self.status_label.setText("Configuring AI model...")
            QApplication.processEvents()
            
            genai.configure(api_key=api_key)
            
            # Upload video file
            self.status_label.setText("Uploading video file to Gemini...")
            QApplication.processEvents()
            
            video_file = genai.upload_file(path=video_path)
            
            self.status_label.setText("Processing video with AI (this may take a minute)...")
            QApplication.processEvents()
            
            # Wait for file to be processed
            import time
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                raise ValueError("Video processing failed")
            
            # Use Gemini 2.0 Flash with video analysis
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = """You are analyzing this screen recording video to create a professional step-by-step how-to guide.

Watch the video carefully and create a detailed tutorial guide with:

1. A clear, engaging title for the tutorial based on what you see
2. A brief introduction explaining what will be accomplished
3. Step-by-step instructions describing:
   - What is happening visually in each major action
   - Specific UI elements, buttons, menus being interacted with
   - What the user should do ("Click on...", "Type in...", "Navigate to...")
   - Why each step matters
4. A brief conclusion or next steps

Write in a natural, professional but friendly style. Be clear and educational. Focus on WHAT you SEE happening in the video - describe the visual actions and UI interactions.

IMPORTANT: Write ONLY the guide content. Do NOT include any meta-commentary."""

            self.status_label.setText("Analyzing video with AI...")
            QApplication.processEvents()
            
            response = model.generate_content([video_file, prompt])
            guide_text = response.text.strip()
            
            # Save to transcript.txt
            transcript_path = os.path.join(self.current_output_dir, "transcript.txt")
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(guide_text)
            
            self.status_label.setText(f"✓ AI guide generated ({len(guide_text)} characters)")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            print(f"Video guide generation error: {e}")
    
    def add_narration(self):
        if not self.current_output_dir:
            self.status_label.setText("Error: No recording found. Record first.")
            return
        
        transcript_path = os.path.join(self.current_output_dir, "transcript.txt")
        if not os.path.exists(transcript_path):
            self.status_label.setText("Error: Generate transcript first.")
            return
        
        self.status_label.setText("Generating AI narration...")
        QApplication.processEvents()
        
        try:
            from shared.guide.narration import add_narration_to_video
            
            self.status_label.setText("Enhancing transcript with AI...")
            QApplication.processEvents()
            
            output_path = add_narration_to_video(self.current_output_dir)
            
            self.status_label.setText(f"Narrated video created: {os.path.basename(output_path)} ✓")
        except ImportError as e:
            if "edge_tts" in str(e):
                self.status_label.setText("Installing edge-tts... (one-time setup)")
                QApplication.processEvents()
                import subprocess
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"], 
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    self.status_label.setText("edge-tts installed! Click 'Add AI Narration' again.")
                except:
                    self.status_label.setText("Failed to install edge-tts. Run: pip install edge-tts")
            elif "gTTS" in str(e) or "gtts" in str(e):
                self.status_label.setText("Installing gTTS fallback...")
                QApplication.processEvents()
                import subprocess
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "gtts"], 
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    self.status_label.setText("gTTS installed! Click 'Add AI Narration' again.")
                except:
                    self.status_label.setText("Failed to install gTTS. Run: pip install gtts")
            else:
                self.status_label.setText(f"Error: {str(e)}")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)[:80]}")


if __name__ == "__main__":
    # Setup error logging first
    log_file = setup_logging()
    logging.info("Application starting...")
    
    # Load config into environment
    load_config_to_env()
    
    app = QApplication(sys.argv)
    logging.info("QApplication created")
    
    # Create and show splash screen
    splash = QSplashScreen()
    splash.setFixedSize(400, 200)
    
    # Create splash content
    splash_widget = QWidget()
    splash_layout = QVBoxLayout()
    splash_layout.setContentsMargins(30, 30, 30, 30)
    
    # Title
    title = QLabel("Hallmark Scribble")
    title.setAlignment(Qt.AlignCenter)
    title.setFont(QFont("Arial", 24, QFont.Bold))
    title.setStyleSheet("color: #4A90E2;")
    splash_layout.addWidget(title)
    
    # Loading message
    loading = QLabel("Loading...")
    loading.setAlignment(Qt.AlignCenter)
    loading.setFont(QFont("Arial", 12))
    loading.setStyleSheet("color: #666;")
    splash_layout.addWidget(loading)
    
    # Version
    version = QLabel("How-To Creator v1.0")
    version.setAlignment(Qt.AlignCenter)
    version.setFont(QFont("Arial", 9))
    version.setStyleSheet("color: #999;")
    splash_layout.addWidget(version)
    
    splash_widget.setLayout(splash_layout)
    splash_widget.setAutoFillBackground(True)
    palette = splash_widget.palette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    splash_widget.setPalette(palette)
    
    splash.setPixmap(splash_widget.grab())
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    splash.show()
    app.processEvents()
    
    # Create main window
    logging.info("Creating main application window...")
    window = RecorderApp()
    logging.info(f"Output folder configured: {window.base_output_folder}")
    logging.info(f"Error log location: {log_file}")
    
    # Close splash and show main window
    splash.finish(window)
    window.show()
    logging.info("Main window shown, application ready")
    
    sys.exit(app.exec_())
