from PyQt5.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 200)
        
        # Create widget for splash
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Hallmark Scribble")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #4A90E2;")
        layout.addWidget(title)
        
        # Loading message
        loading = QLabel("Loading...")
        loading.setAlignment(Qt.AlignCenter)
        loading.setFont(QFont("Arial", 12))
        loading.setStyleSheet("color: #666;")
        layout.addWidget(loading)
        
        # Version
        version = QLabel("How-To Creator v1.0")
        version.setAlignment(Qt.AlignCenter)
        version.setFont(QFont("Arial", 9))
        version.setStyleSheet("color: #999;")
        layout.addWidget(version)
        
        widget.setLayout(layout)
        
        # Set background
        widget.setAutoFillBackground(True)
        palette = widget.palette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255))
        widget.setPalette(palette)
        
        # Center on screen
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
    def showMessage(self, message):
        """Show a message on the splash screen"""
        pass  # Using static text for simplicity
