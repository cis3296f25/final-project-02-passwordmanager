from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont, QIcon
from passwordmanager.api import apiCallerMethods
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings


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

        # Style the theme buttons
        self.update_theme_buttons()

        # Connect theme button actions
        self.light_button.clicked.connect(self.set_light_theme)
        self.dark_button.clicked.connect(self.set_dark_theme)

        theme_layout.addWidget(self.light_button)
        theme_layout.addWidget(self.dark_button)

        form_layout.addRow("Theme:", theme_layout)

        # Master password section with input and check button on same row
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.check_button = QPushButton()
        check_icon = QIcon(Strings.CHECK_ICON_PATH)
        self.check_button.setIcon(check_icon)
        self.check_button.setStyleSheet(Strings.SMALL_BUTTON_STYLE)

        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.check_button)

        form_layout.addRow("Change Master Password:", password_layout)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)

        button_style = Strings.button_style if hasattr(Strings, 'button_style') else Strings.SMALL_BUTTON_STYLE
        self.close_button.setStyleSheet(button_style)

        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.apply_theme(self.current_theme)

    def apply_theme(self, theme):
        """Apply theme colors to this dialog"""
        self.current_theme = theme
        colors = theme_manager.get_theme_colors(theme) 
        
        self.setStyleSheet(f"""
        QDialog {{ 
            background-color: {colors['background']}; 
            color: {colors['text']}; 
        }}
        QLabel {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        QLineEdit {{
            background-color: {colors['background-button']};
            color: {colors['input_text']};
            padding: 5px;
            border-radius: 4px;
        }}
        """)
        
        self.update_theme_buttons()

    def update_theme_buttons(self):
        colors = theme_manager.get_theme_colors(self.current_theme)
        
        base_theme_button_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            color: {colors['input_text']};
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
            color: {colors['input_text']};
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
  
    def set_light_theme(self):
        theme_manager.set_theme("light")

    def set_dark_theme(self):
        theme_manager.set_theme("dark")
        
    def closeEvent(self, event):
        theme_manager.unregister_window(self)
        super().closeEvent(event)