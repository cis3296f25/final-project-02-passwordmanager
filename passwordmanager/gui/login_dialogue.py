from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings
from passwordmanager.api import apiCallerMethods


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        
        # Register with theme manager
        theme_manager.register_window(self)
        
        self.setWindowTitle("Login")
        self.setWindowIcon(QIcon(Strings.WINDOW_ICON_PATH))
        self.setFixedSize(375, 225)

        layout = QVBoxLayout()

        title = QLabel("Offline Password Manager")
        title.setFont(QFont("Segoe UI", 16))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(15)

        form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Username:", self.username)
        form.addRow("Master Password:", self.password)
        layout.addLayout(form)

        layout.addSpacing(20)

        buttons = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.create_btn = QPushButton("Create Account")
        button_style = theme_manager.get_small_button_style()
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

        theme_manager.apply_theme_to_window(self, theme_manager.current_mode)
        self.center()

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

    def center(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        screen_center = screen.availableGeometry().center()
        frame_geom = self.frameGeometry()
        frame_geom.moveCenter(screen_center)
        self.move(frame_geom.topLeft())


