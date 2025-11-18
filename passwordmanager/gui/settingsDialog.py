from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont, QIcon
from passwordmanager.api import apiCallerMethods
from resources.colors import Colors
from resources.strings import Strings


class settingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Window setup
        self.setWindowTitle("Settings")
        self.setStyleSheet(f"background-color: {Colors.DARK_GREY}; color: {Colors.WHITE};")
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
        button_style = Strings.button_style if hasattr(Strings, 'button_style') else Strings.SMALL_BUTTON_STYLE
        self.light_button.setStyleSheet(button_style)
        self.dark_button.setStyleSheet(button_style)

        # Connect theme button actions
        self.light_button.clicked.connect(self.set_light_theme)
        self.dark_button.clicked.connect(self.set_dark_theme)

        theme_layout.addWidget(self.light_button)
        theme_layout.addWidget(self.dark_button)

        form_layout.addRow("Theme:", theme_layout)

        # Master password section with input and check button on same row
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        check_button = QPushButton()
        check_icon = QIcon(Strings.CHECK_ICON_PATH)
        check_button.setIcon(check_icon)
        check_button.setStyleSheet(Strings.SMALL_BUTTON_STYLE)

        password_layout.addWidget(self.password_input)
        password_layout.addWidget(check_button)

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

    def set_light_theme(self):
        #Set the application to light theme
        pass

    def set_dark_theme(self):
       #Set the application to dark theme
        pass