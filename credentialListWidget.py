from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout, QScrollArea
)
from PyQt6.QtGui import QFont, QClipboard
from PyQt6.QtCore import Qt
import sys
import apiCallerMethods
from colors import Colors

class CredentialsListWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Outer layout
        layout = QVBoxLayout(self)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")
        layout.addWidget(self.scroll_area)

        # Inner container inside scroll area
        self.credentials_container = QWidget()
        self.credentials_layout = QVBoxLayout(self.credentials_container)
        self.credentials_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.credentials_container)

    # Load all credentials
    def load_credentials(self):
        # Clear previous cards
        for i in reversed(range(self.credentials_layout.count())):
            widget = self.credentials_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        try:
            credentials = apiCallerMethods.get_all_credentials()
            if not credentials:
                label = QLabel("No credentials stored yet.")
                label.setStyleSheet(f"color: {Colors.WHITE};")
                self.credentials_layout.addWidget(label)
                return

            for cred in credentials:
                self.add_credential_card(cred)

        except Exception as e:
            error_label = QLabel(f"Error loading credentials: {e}")
            error_label.setStyleSheet(f"color: {Colors.WHITE};")
            self.credentials_layout.addWidget(error_label)

    # Create a visual card for one credential
    def add_credential_card(self, cred):
        card = QWidget()
        card.setFixedHeight(50)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)

        site = QLabel(f"{cred['site']}")
        username = QLabel(f"{cred['username']}")
        password = QLabel("••••••••")

        for label in (site, username, password):
            label.setStyleSheet(f"color: {Colors.WHITE}; font-size: 12px;")

        copy_button = QPushButton("Copy Password")
        copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BRAT_GREEN};
                color: {Colors.WHITE};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            }}
        """)
        copy_button.clicked.connect(lambda _, p=cred['password']: self.copy_to_clipboard(p))

        button_layout = QHBoxLayout()
        button_layout.addWidget(copy_button)
        # button_layout.addStretch()

        card_layout.addWidget(site)
        card_layout.addWidget(username)
        card_layout.addWidget(password)
        card_layout.addLayout(button_layout)

        card.setStyleSheet(f"""
            background-color: {Colors.LIGHT_GREY};
            border-radius: 10px;
            padding: 6px;
        """)

        self.credentials_layout.addWidget(card)

    # Copy password to clipboard
    def copy_to_clipboard(self, password):
        QApplication.clipboard().setText(password)
        print(f"Copied password")