from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont, QIcon
from passwordmanager.api import apiCallerMethods
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings

class ChangePasswordWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Register with theme manager
        theme_manager.register_window(self)
        # Store parent reference for theme propagation
        self.parent_window = parent
        
        # Current theme state from theme manager
        self.current_theme = theme_manager.current_theme
        
        self.setWindowTitle("Change Master Password")
        
        self.setMinimumWidth(300)
        self.setMinimumHeight(150)
        
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Old password field with input and check button on same row
        password_layout = QHBoxLayout()
        self.old_password_input = QLineEdit()
        self.old_password_input.setPlaceholderText("Old Password")

        password_layout.addWidget(self.old_password_input)

        form_layout.addRow("Enter Old Password:", password_layout)

        # New password field on separate row
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("New Password")
        form_layout.addRow("Enter New Password:", self.new_password_input)
        layout.addLayout(form_layout)

        # Submit button
        button_layout = QHBoxLayout()

        self.check_button = QPushButton("Submit")
        self.check_button.clicked.connect(self.set_master_password)
        self.check_button.setStyleSheet(Strings.LARGE_BUTTON_STYLE)

        button_layout.addWidget(self.check_button)
        
        layout.addLayout(button_layout)
        
        theme_manager.apply_theme_to_window(self, self.current_theme)
        self.setLayout(layout)
        
    
    def set_master_password(self):
        newPassword = self.new_password_input.text()
        apiCallerMethods.set_master_password(newPassword)
