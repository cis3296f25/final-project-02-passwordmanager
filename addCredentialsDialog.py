from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont
import apiCallerMethods
from resources.colors import Colors



class AddCredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent) 

        # Window setup
        self.setWindowTitle("Add New Credential")
        self.setStyleSheet(f"background-color: {Colors.DARK_GREY}; color: {Colors.WHITE};")
        self.setMinimumWidth(300)

        # Main layout
        layout = QVBoxLayout()

        # Input form fields
        form_layout = QFormLayout()
        self.site_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()

        form_layout.addRow("Site:", self.site_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate Password")
        self.save_button = QPushButton("Save Credential")

        button_style = f"""
            QPushButton {{
                background-color: {Colors.BRAT_GREEN};
                color: {Colors.WHITE};
                border-radius: 10px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            }}
        """
        self.generate_button.setStyleSheet(button_style)
        self.save_button.setStyleSheet(button_style)

        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Connect buttons
        self.generate_button.clicked.connect(self.generate_password)
        self.save_button.clicked.connect(self.save_credential)

    # Generate password via API
    def generate_password(self):
        try:
            new_pass = apiCallerMethods.get_new_generated_password()
            self.password_input.setText(new_pass["password"])
            self.status_label.setText("Generated new password.")
        except Exception as e:
            self.status_label.setText(f"Error generating password: {e}")

    # Save credential to database
    def save_credential(self):
        try:
            site = self.site_input.text()
            username = self.username_input.text()
            password = self.password_input.text()

            response = apiCallerMethods.add_credential(site, username, password)
            if "status" in response and response["status"] == "added":
                self.status_label.setText("Credential added successfully.")
            else:
                self.status_label.setText(f"Error: {response.get('error', 'Unknown')}")
        except Exception as e:
            self.status_label.setText(f"Error saving credential: {e}")