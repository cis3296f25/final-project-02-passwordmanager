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

        # status
        self.status = QLabel("")
        self.status.setWordWrap(True)
        form_layout.addWidget(self.status)

        # Submit button
        button_layout = QHBoxLayout()

        self.check_button = QPushButton("Submit")
        self.check_button.clicked.connect(self.set_master_password)
        self.check_button.setStyleSheet(theme_manager.get_large_button_style())

        button_layout.addWidget(self.check_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Apply theme with current mode
        theme_manager.apply_theme_to_window(self, theme_manager.current_mode)
    
    def set_master_password(self):
        oldPassword = self.old_password_input.text()
        newPassword = self.new_password_input.text()

        response = apiCallerMethods.set_master_password(newPassword, oldPassword)

        if response.status_code == 200:
            self.status.setText("Changed master password!")
            self.status.setStyleSheet("color: green;")
            self.accept()
        else:
            self.status.setText("Incorrect old password")
            self.status.setStyleSheet("color: red;")
    
    def closeEvent(self, event):
        theme_manager.unregister_window(self)
        super().closeEvent(event)
