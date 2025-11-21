from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout, QWidget
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt
from passwordmanager.api import apiCallerMethods
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings
from passwordmanager.gui.changePasswordWindow import ChangePasswordWindow


class settingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Register with theme manager
        theme_manager.register_window(self)
        
        # Store parent reference for theme propagation
        self.parent_window = parent
        
        # Current theme state from theme manager
        self.current_theme = theme_manager.current_theme

        # Window setup
        self.setWindowTitle("Settings")
       
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)

        # Main layout
        layout = QVBoxLayout()

        # Input form fields
        form_layout = QFormLayout()

        # Theme section with Light/Dark buttons
        theme_layout = QHBoxLayout()
        self.light_button = QPushButton("Light")
        self.dark_button = QPushButton("Dark")

        # Connect theme button actions
        self.light_button.clicked.connect(self.set_light_theme)
        self.dark_button.clicked.connect(self.set_dark_theme)

        theme_layout.addWidget(self.light_button)
        theme_layout.addWidget(self.dark_button)
        
        form_layout.addRow("Theme:", theme_layout)
        
        # Change password section
        self.change_password_button = QPushButton("Change Password")
        self.change_password_button.setStyleSheet(Strings.SETTINGS_BUTTON_STYLE)
        self.change_password_button.clicked.connect(self.open_change_password_window)
        
        form_layout.addRow("Password:", self.change_password_button)

        # Add form layout to main layout
        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet(Strings.LARGE_BUTTON_STYLE)

        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        
        # Let the theme manager handle initial theming
        theme_manager.apply_theme_to_window(self, theme_manager.current_theme)

    def update_theme_buttons(self):
        colors = theme_manager.get_theme_colors(self.current_theme)
        
        base_theme_button_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
        }}
        """
        
        selected_theme_button_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            border: 2px solid {Colors.BRAT_GREEN};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
        }}
        """
        
        if self.current_theme == "light":
            self.light_button.setStyleSheet(selected_theme_button_style)
            self.dark_button.setStyleSheet(base_theme_button_style)
        else:
            # Dark theme selected
            self.dark_button.setStyleSheet(selected_theme_button_style)
            self.light_button.setStyleSheet(base_theme_button_style)

    def update_button_theme(self):
        """Update the Change Password button styling based on current theme"""
        colors = theme_manager.get_theme_colors(self.current_theme)
        
        button_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            color: {colors['text']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            color: {Colors.BLACK};
        }}
        """
        self.change_password_button.setStyleSheet(button_style)
  
    def set_light_theme(self):
        theme_manager.set_theme("light")

    def set_dark_theme(self):
        theme_manager.set_theme("dark")
        
    def closeEvent(self, event):
        theme_manager.unregister_window(self)
        super().closeEvent(event)
        
    def open_change_password_window(self):
        overlay = QWidget(self)
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")  # translucent overlay
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        overlay.show()
        
        change_password_window = ChangePasswordWindow(self)
        change_password_window.exec()
        overlay.deleteLater()
