import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout, QScrollArea
)
from PyQt6.QtGui import QFont, QClipboard
from PyQt6.QtCore import Qt, QTimer
import sys
import apiCallerMethods
from colors import Colors

class CredentialsListWidget(QWidget):
    def __init__(self):
        super().__init__()

        # outer layout
        layout = QVBoxLayout(self)

        # scrollable area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")
        layout.addWidget(self.scroll_area)

        # inner rectangular container for credentials cards
        self.credentials_container = QWidget()
        self.credentials_layout = QVBoxLayout(self.credentials_container)
        self.credentials_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.credentials_container)

    def load_credentials(self):
        # clear all previous cards
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

    # create a rectangular card for one credential
    def add_credential_card(self, cred):
        card = QWidget()
        card.setFixedHeight(50)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)

        # display for website, username, ••••••••
        site = QLabel(f"{cred['site']}")
        username = QLabel(f"{cred['username']}")
        password = QLabel("••••••••")

        # font
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
        copy_button.clicked.connect(lambda _, p=cred['password']: self.copy_to_clipboard(p, copy_button))

        button_layout = QHBoxLayout()
        button_layout.addWidget(copy_button)

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

    def copy_to_clipboard(self, password, copy_button):
        QApplication.clipboard().setText(password)

        # flash "Copied!" for 1/2 second after clicking
        copy_button.setText("Copied!")
        QTimer.singleShot(500, lambda: copy_button.setText("Copy Password"))

        print("Copied password")