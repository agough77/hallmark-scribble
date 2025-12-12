import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QRect, QPoint, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen
import win32gui
import win32con
import ctypes
import ctypes.wintypes

class RegionSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Region")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)
        
        # Get all screens
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            self.setGeometry(screen_geometry)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.selecting = False
        self.selected_rect = None
        
        self.setCursor(Qt.CrossCursor)
        
    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw dark overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        if not self.selecting and not self.selected_rect:
            # Draw instruction text
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            text = "Click and drag to select region (ESC to cancel)"
            font = painter.font()
            font.setPointSize(16)
            painter.setFont(font)
            text_rect = painter.fontMetrics().boundingRect(text)
            text_x = (self.width() - text_rect.width()) // 2
            text_y = (self.height() - text_rect.height()) // 2
            painter.drawText(text_x, text_y, text)
        
        if self.selecting or self.selected_rect:
            if self.selected_rect:
                rect = self.selected_rect
            else:
                rect = QRect(self.begin, self.end).normalized()
            
            # Clear selected area (make it transparent)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, QColor(0, 0, 0, 0))
            
            # Draw green border
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(0, 255, 0), 3, Qt.SolidLine))
            painter.drawRect(rect)
            
            # Draw dimensions
            if rect.width() > 0 and rect.height() > 0:
                painter.setPen(QPen(QColor(255, 255, 0), 2))
                font = painter.font()
                font.setPointSize(12)
                font.setBold(True)
                painter.setFont(font)
                text = f"{rect.width()} x {rect.height()}"
                painter.fillRect(rect.x(), rect.y() - 25, 150, 25, QColor(0, 0, 0, 180))
                painter.drawText(rect.x() + 5, rect.y() - 8, text)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.begin = event.pos()
            self.end = event.pos()
            self.selecting = True
            self.selected_rect = None
            self.update()
    
    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            self.selected_rect = QRect(self.begin, self.end).normalized()
            if self.selected_rect.width() > 10 and self.selected_rect.height() > 10:
                QTimer.singleShot(100, self.accept_selection)
            else:
                self.selected_rect = None
                self.update()
    
    def accept_selection(self):
        self.close()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.selected_rect = None
            self.close()
    
    def get_region(self):
        if self.selected_rect:
            return (
                self.selected_rect.x(),
                self.selected_rect.y(),
                self.selected_rect.width(),
                self.selected_rect.height()
            )
        return None

class WindowSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Window")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)
        
        # Get all screens
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            self.setGeometry(screen_geometry)
        
        self.selected_window = None
        self.highlighted_hwnd = None
        self.is_closed = False
        
        # Set up timer for mouse tracking
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_highlight)
        self.timer.start(50)  # Update every 50ms
        
        self.setCursor(Qt.CrossCursor)
        
        # Info label
        self.info_label = QLabel("Click on any window to select it (ESC to cancel)", self)
        self.info_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 200);
            color: white;
            padding: 15px 30px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
        """)
        self.info_label.adjustSize()
        self.info_label.move(
            (self.width() - self.info_label.width()) // 2,
            30
        )
    
    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        # Reposition label
        self.info_label.move(
            (self.width() - self.info_label.width()) // 2,
            30
        )
    
    def update_highlight(self):
        # Get window under cursor
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        point = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        hwnd = ctypes.windll.user32.WindowFromPoint(point)
        
        # Get the root window (not child controls)
        while hwnd:
            parent = win32gui.GetParent(hwnd)
            if parent == 0:
                break
            hwnd = parent
        
        if hwnd and hwnd != self.winId() and win32gui.IsWindowVisible(hwnd):
            if hwnd != self.highlighted_hwnd:
                self.highlighted_hwnd = hwnd
                self.update()
        else:
            if self.highlighted_hwnd is not None:
                self.highlighted_hwnd = None
                self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw semi-transparent overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
        
        # Highlight the window under cursor
        if self.highlighted_hwnd:
            try:
                rect = win32gui.GetWindowRect(self.highlighted_hwnd)
                highlight_rect = QRect(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])
                
                # Clear the highlighted area
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.fillRect(highlight_rect, QColor(0, 0, 0, 0))
                
                # Draw yellow border
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.setPen(QPen(QColor(255, 255, 0), 4, Qt.SolidLine))
                painter.drawRect(highlight_rect)
                
                # Draw window title
                try:
                    title = win32gui.GetWindowText(self.highlighted_hwnd)
                    if title:
                        painter.setPen(QPen(QColor(255, 255, 0), 2))
                        font = painter.font()
                        font.setPointSize(12)
                        font.setBold(True)
                        painter.setFont(font)
                        
                        # Background for text
                        text_rect = painter.fontMetrics().boundingRect(title[:50])
                        painter.fillRect(
                            highlight_rect.x(),
                            highlight_rect.y() - 30,
                            text_rect.width() + 20,
                            30,
                            QColor(0, 0, 0, 200)
                        )
                        painter.drawText(highlight_rect.x() + 10, highlight_rect.y() - 10, title[:50])
                except:
                    pass
            except:
                pass
    
    def mousePressEvent(self, event):
        print(f"DEBUG: mousePressEvent called at {event.pos()}")  # Debug
        if event.button() == Qt.LeftButton:
            # Get window under the mouse position (not under overlay)
            pos = self.mapToGlobal(event.pos())
            point = ctypes.wintypes.POINT()
            point.x = pos.x()
            point.y = pos.y()
            
            # Get the window at this point
            hwnd = ctypes.windll.user32.WindowFromPoint(point)
            print(f"DEBUG: WindowFromPoint returned: {hwnd}")  # Debug
            
            # Get the root window
            while hwnd:
                parent = win32gui.GetParent(hwnd)
                if parent == 0:
                    break
                hwnd = parent
            
            print(f"DEBUG: Root window: {hwnd}")  # Debug
            
            # Make sure it's not our own window
            if hwnd and hwnd != self.winId():
                print(f"DEBUG: Valid window found, getting rect...")  # Debug
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    print(f"DEBUG: Got window rect: {rect}")  # Debug
                    self.selected_window = {
                        'hwnd': hwnd,
                        'x': rect[0],
                        'y': rect[1],
                        'width': rect[2] - rect[0],
                        'height': rect[3] - rect[1]
                    }
                    print(f"DEBUG: Stored selected_window: {self.selected_window}")  # Debug
                    self.cleanup_and_close()
                except Exception as e:
                    print(f"DEBUG: Error getting window rect: {e}")  # Debug
            else:
                print(f"DEBUG: Invalid window (our own or none)")  # Debug
        else:
            print(f"DEBUG: Not left button: {event.button()}")  # Debug
    
    def cleanup_and_close(self):
        """Stop timer and close window"""
        self.is_closed = True
        if self.timer.isActive():
            self.timer.stop()
        self.hide()  # Hide instead of close to preserve data
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.selected_window = None
            self.cleanup_and_close()
    
    def closeEvent(self, event):
        """Ensure timer stops when window closes"""
        if self.timer.isActive():
            self.timer.stop()
        super().closeEvent(event)
    
    def get_window_region(self):
        return self.selected_window

def select_region():
    """Show region selector overlay"""
    from PyQt5.QtCore import QEventLoop
    
    selector = RegionSelector()
    selector.show()
    selector.raise_()
    selector.activateWindow()
    
    # Run event loop until selector closes
    loop = QEventLoop()
    selector.destroyed.connect(loop.quit)
    
    # Process events while selector is visible
    while selector.isVisible():
        QApplication.processEvents()
    
    return selector.get_region()

def select_window():
    """Show simple window list dialog"""
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel
    from PyQt5.QtCore import QEventLoop
    
    dialog = QDialog()
    dialog.setWindowTitle("Select Window")
    dialog.setModal(True)
    dialog.resize(500, 400)
    
    layout = QVBoxLayout()
    
    label = QLabel("Select a window to record:")
    layout.addWidget(label)
    
    list_widget = QListWidget()
    
    # Enumerate windows
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            title = win32gui.GetWindowText(hwnd)
            windows.append((hwnd, title))
    
    windows = []
    win32gui.EnumWindows(callback, windows)
    
    # Add to list
    for hwnd, title in windows:
        list_widget.addItem(title)
        list_widget.item(list_widget.count() - 1).setData(Qt.UserRole, hwnd)
    
    layout.addWidget(list_widget)
    
    selected_hwnd = [None]
    
    def on_select():
        current = list_widget.currentItem()
        if current:
            selected_hwnd[0] = current.data(Qt.UserRole)
            dialog.accept()
    
    def on_double_click(item):
        selected_hwnd[0] = item.data(Qt.UserRole)
        dialog.accept()
    
    list_widget.itemDoubleClicked.connect(on_double_click)
    
    btn_select = QPushButton("Select")
    btn_select.clicked.connect(on_select)
    layout.addWidget(btn_select)
    
    btn_cancel = QPushButton("Cancel")
    btn_cancel.clicked.connect(dialog.reject)
    layout.addWidget(btn_cancel)
    
    dialog.setLayout(layout)
    
    result = dialog.exec_()
    
    if result == QDialog.Accepted and selected_hwnd[0]:
        try:
            hwnd = selected_hwnd[0]
            
            # Check if window is minimized and restore it
            if win32gui.IsIconic(hwnd):
                print(f"DEBUG: Window is minimized, restoring...")
                win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
                import time
                time.sleep(0.3)  # Give window time to restore
            
            # Bring window to foreground
            try:
                win32gui.SetForegroundWindow(hwnd)
                import time
                time.sleep(0.2)  # Brief pause to ensure window is focused
            except Exception as e:
                print(f"DEBUG: Could not bring window to foreground: {e}")
            
            rect = win32gui.GetWindowRect(hwnd)
            x, y = rect[0], rect[1]
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            print(f"DEBUG: Selected window rect: {rect}")
            print(f"DEBUG: Calculated dimensions: x={x}, y={y}, w={width}, h={height}")
            
            # Validate dimensions immediately
            if width <= 0 or height <= 0:
                print(f"DEBUG: Invalid dimensions (w={width}, h={height})")
                return None
            
            # Check if window is still too small
            if width < 10 or height < 10:
                print(f"DEBUG: Window appears too small (w={width}, h={height})")
                return None
            
            return x, y, width, height
        except Exception as e:
            print(f"DEBUG: Error getting rect: {e}")
            import traceback
            traceback.print_exc()
    
    return None
