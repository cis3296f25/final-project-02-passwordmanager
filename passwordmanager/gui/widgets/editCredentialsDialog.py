from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont
from passwordmanager.api import apiCallerMethods
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings

class EditCredentialsDialog(QDialog):
    def __init__(self, credId, parent=None):
        super().__init__(parent) 
        
        theme_manager.register_window(self)
        
        self.credId = credId

        # Window setup
        self.setWindowTitle("Edit Credential")
        self.setMinimumWidth(300)

        # Main layout
        layout = QVBoxLayout()

        # Input form fields
        form_layout = QFormLayout()
        self.site_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()

        credential = apiCallerMethods.get_credential(credId)

        self.site_input.setText(credential["site"])
        self.username_input.setText(credential["username"])
        self.password_input.setText(credential["password"])

        form_layout.addRow("Site:", self.site_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.generate_button = QPushButton("Generate Password")
        self.save_button = QPushButton("Save")

        button_style = Strings.LARGE_BUTTON_STYLE
        self.cancel_button.setStyleSheet(button_style)
        self.generate_button.setStyleSheet(button_style)
        self.save_button.setStyleSheet(button_style)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Connect buttons
        self.cancel_button.clicked.connect(self.close_dialog)
        self.generate_button.clicked.connect(self.generate_password)
        self.save_button.clicked.connect(self.edit_credential)
        
        # Apply current theme
        theme_manager.apply_theme_to_window(self, theme_manager.current_theme)

    def close_dialog(self):
        self.close()

    def generate_password(self):
        try:
            new_pass = apiCallerMethods.get_new_generated_password()
            self.password_input.setText(new_pass["password"])
            self.status_label.setText("Generated new password.")
        except Exception as e:
            self.status_label.setText(f"Error generating password: {e}")

    def edit_credential(self):
        try:
            site = self.site_input.text()
            username = self.username_input.text()
            password = self.password_input.text()

            response = apiCallerMethods.update_credential(self.credId, site, username, password)
            if "status" in response and response["status"] == "updated":
                self.status_label.setText("Credential updated successfully.")
                self.close()
            else:
                self.status_label.setText(f"Error: {response.get('error', 'Unknown')}")
        except Exception as e:
            self.status_label.setText(f"Error saving credential: {e}")
    
    def closeEvent(self, event):
        theme_manager.unregister_window(self)
        super().closeEvent(event)