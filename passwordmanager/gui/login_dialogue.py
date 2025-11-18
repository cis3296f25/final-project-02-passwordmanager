from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout
)
from PyQt6.QtGui import QFont, QIcon
from resources.colors import Colors
from resources.strings import Strings
from passwordmanager.api import apiCallerMethods


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setWindowIcon(QIcon(Strings.WINDOW_ICON_PATH))
        self.setStyleSheet(f"background-color: {Colors.DARK_GREY}; color: {Colors.WHITE};")
        self.setMinimumWidth(320)

        layout = QVBoxLayout()

        title = QLabel("Offline Password Manager")
        title.setFont(QFont("Segoe UI", 16))
        layout.addWidget(title)

        form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Username:", self.username)
        form.addRow("Master Password:", self.password)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.create_btn = QPushButton("Create Account")
        button_style = Strings.SMALL_BUTTON_STYLE
        self.login_btn.setStyleSheet(button_style)
        self.create_btn.setStyleSheet(button_style)
        buttons.addWidget(self.login_btn)
        buttons.addWidget(self.create_btn)
        layout.addLayout(buttons)

        self.status = QLabel("")
        layout.addWidget(self.status)

        self.setLayout(layout)

        self.login_btn.clicked.connect(self.handle_login)
        self.create_btn.clicked.connect(self.handle_create)

    def handle_login(self):
        try:
            resp = apiCallerMethods.account_login(self.username.text(), self.password.text())
            if resp.get("status") == "logged in":
                self.accept()
            else:
                self.status.setText(resp.get("error", "Login failed"))
        except Exception as e:
            self.status.setText(f"Error: {e}")

    def handle_create(self):
        try:
            resp = apiCallerMethods.account_create(self.username.text(), self.password.text())
            if resp.get("status") == "account created":
                self.status.setText("Account created. Logging in…")
                self.handle_login()
            else:
                self.status.setText(resp.get("error", "Create failed"))
        except Exception as e:
            self.status.setText(f"Error: {e}")


