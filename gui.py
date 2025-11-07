from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont
import sys
import apiCallerMethods
from colors import Colors
from credentialListWidget import CredentialsListWidget


class AddCredentialsDialog(QDialog):
    def __init__(self):
        super().__init__()

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # set window
        self.setWindowTitle("Offline Password Manager")
        self.setGeometry(200, 200, 475, 400)  # x, y, width, height
        self.setMinimumWidth(475)
        self.setMinimumHeight(400)

        self.setStyleSheet(f"background-color: {Colors.DARK_GREY};")

        # set central widget (similar to panels in jpanel)
        central = QWidget()
        self.setCentralWidget(central)

        # layout for central widget
        layout = QVBoxLayout()
        central.setLayout(layout)

        # Credentials list widget
        self.credentials_list = CredentialsListWidget()
        layout.addWidget(self.credentials_list)

        # buttons
        add_button = QPushButton("Add New Credential")
        exit_button = QPushButton("Exit")

        # button styling
        button_style = f"""
            QPushButton {{
                background-color: {Colors.BRAT_GREEN};
                color: {Colors.WHITE};
                border-radius: 10px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            }}
        """
        add_button.setStyleSheet(button_style)
        exit_button.setStyleSheet(button_style)

        layout.addWidget(add_button)
        layout.addWidget(exit_button)

        # Connect buttons
        add_button.clicked.connect(self.open_add_dialog)
        exit_button.clicked.connect(self.close)

    # Open the Add Credentials dialog
    def open_add_dialog(self):
        dialog = AddCredentialsDialog()
        dialog.exec()
        self.refresh_credentials()

    def refresh_credentials(self):
        self.credentials_list.load_credentials()

    # Run the app
    @staticmethod
    def run():
        app = QApplication.instance() or QApplication(sys.argv)
        window = MainWindow()
        window.show()
        window.refresh_credentials()
        app.exec()
