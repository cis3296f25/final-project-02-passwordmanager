from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout,
    QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from passwordmanager.api import apiCallerMethods
from passwordmanager.utils.apiPasswordStrength import get_password_strength
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings  


class AddCredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Register with theme manager
        theme_manager.register_window(self)

        # Window setup
        self.setWindowTitle("Add New Credential")
        self.setMinimumWidth(300)

        # Main layout
        layout = QVBoxLayout()

        # Input form fields
        form_layout = QFormLayout()
        self.site_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()

        # password hidden by default
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # show password eye
        password_row = QHBoxLayout()
        password_row.addWidget(self.password_input)
        
        button_style = theme_manager.get_small_button_style()

        self.show_password_button = QPushButton("👁")
        self.show_password_button.setCheckable(True)
        self.show_password_button.setFixedWidth(32)
        self.show_password_button.setStyleSheet(theme_manager.get_eye_button_style())
        self.show_password_button.toggled.connect(self.toggle_password_visibility)
        password_row.addWidget(self.show_password_button)

        form_layout.addRow("Site:", self.site_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", password_row)

        layout.addLayout(form_layout)

        # Password strength label
        self.strength_label = QLabel("Password strength: ")
        layout.addWidget(self.strength_label)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_button = QPushButton("Generate Password")
        self.generate_button.setStyleSheet(button_style)
        self.save_button = QPushButton("Save Credential")
        self.save_button.setStyleSheet(button_style)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(button_style)
        self.cancel_button.clicked.connect(self.close)

        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Connect buttons
        self.generate_button.clicked.connect(self.generate_password)
        self.save_button.clicked.connect(self.save_credential)

        # Connect password input to strength checker
        self.password_input.textChanged.connect(self.update_strength_label)
        # Apply current theme
        theme_manager.apply_theme_to_window(self, theme_manager.current_mode)

    def toggle_password_visibility(self, checked: bool):
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_button.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_button.setText("👁")
        self.password_input.setFocus()

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
            site = self.site_input.text().strip()
            username = self.username_input.text().strip()
            password = self.password_input.text()
            
            if not site or not username or not password:
                self.status_label.setText("Please fill in all fields before saving.")
                return
            
            try:
                dup_response = apiCallerMethods.check_duplicate_credential(site, username)
                if dup_response.get("exists"):
                    # trigger warning pop-up
                    reply = QMessageBox.question(
                        self,
                        "Duplicate credential!",
                        f"An entry for '{username}' on '{site}' already exists.\nDo you want to save this duplicate?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )

                    # if no is clocked, stop save process
                    if reply == QMessageBox.StandardButton.No:
                        self.status_label.setText("Save cancelled.")
                        return
            except Exception as e:
                print(f"Warning: couldn't check for duplicates: {e}")
            # ========================================================

            # call API
            response = apiCallerMethods.add_credential(site, username, password)
            if "status" in response and response["status"] == "added":
                self.status_label.setText("Credential added successfully.")
                self.accept() # close dialog after successful save
            else:
                err = None
                
                if isinstance(response, dict):
                    err = response.get("error", "Unknown")
                else:
                    err = "Unknown (unexpected response type)"
                self.status_label.setText(f"Error: {err}")
        except Exception as e:
            self.status_label.setText(f"Error saving credential: {e}")

    # Password strength checker
    def update_strength_label(self):
        password = self.password_input.text()
        strength = get_password_strength(password)

        if strength == "weak":
            self.strength_label.setText("Password strength: Weak")
            self.strength_label.setStyleSheet("color: red;")
        elif strength == "medium":
            self.strength_label.setText("Password strength: Medium")
            self.strength_label.setStyleSheet("color: orange;")
        else:
            self.strength_label.setText("Password strength: Strong")
            self.strength_label.setStyleSheet("color: lightgreen;")
        
    def closeEvent(self, event):
        theme_manager.unregister_window(self)
        super().closeEvent(event)