from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon
import time
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
        self.setMinimumSize(375, 225)
        self.resize(375, 225)

        layout = QVBoxLayout()

        title = QLabel("Offline Password Manager")
        title.setFont(QFont("Segoe UI", 16))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)

        form = QFormLayout()
        self.username = QLineEdit()
        self.username.setMinimumHeight(30)
        self.password = QLineEdit()
        self.password.setMinimumHeight(30)
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
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.setLayout(layout)

        self.login_btn.clicked.connect(self.handle_login)
        self.create_btn.clicked.connect(self.handle_create)

        self.lockout_timer = QTimer()
        self.lockout_timer.timeout.connect(self.update_lockout_countdown)
        self.lockout_timer.setInterval(1000)
        
        self.lockout_until_timestamp = None

        theme_manager.apply_theme_to_window(self, theme_manager.current_mode)
        self.center()
        
        QTimer.singleShot(100, self.check_lockout_status)
    
    def _format_time_remaining(self, seconds):
        if seconds <= 0:
            return "0s"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    def _adjust_dialog_size(self, text):
        font_metrics = self.status.fontMetrics()
        text_width = font_metrics.horizontalAdvance(text)
        padding = 40
        min_width = 375
        new_width = max(min_width, text_width + padding)
        self.resize(new_width, self.height())

    def handle_login(self):
        username = self.username.text()
        if not username:
            self.status.setText("Please enter a username")
            return
        
        try:
            lockout_status = apiCallerMethods.account_lockout_status()
            if lockout_status.get("locked"):
                lockout_seconds = lockout_status.get("lockout_seconds", 0)
                self.lockout_until_timestamp = time.time() + lockout_seconds
                time_str = self._format_time_remaining(lockout_seconds)
                message = f"Login locked. Please wait {time_str}"
                self.status.setText(message)
                self._adjust_dialog_size(message)
                self._update_lockout_display(lockout_seconds)
                return
        except Exception:
            pass
        
        try:
            resp = apiCallerMethods.account_login(username, self.password.text())
            if resp.get("status") == "logged in":
                self.accept()
            else:
                error_msg = resp.get("error", "Login failed")
                if "lockout_seconds" in resp:
                    lockout_seconds = resp.get("lockout_seconds", 0)
                    self.lockout_until_timestamp = time.time() + lockout_seconds
                    time_str = self._format_time_remaining(lockout_seconds)
                    error_msg = f"Login locked. Please wait {time_str}"
                    self._adjust_dialog_size(error_msg)
                    self._update_lockout_display(lockout_seconds)
                elif error_msg == "incorrect credentials":
                    error_msg = "Incorrect credentials"
                    self._adjust_dialog_size(error_msg)
                self.status.setText(error_msg)
                if "lockout_seconds" not in resp:
                    self.check_lockout_status()
        except Exception as e:
            self.status.setText(f"Error: {e}")
            self.check_lockout_status()

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

    def check_lockout_status(self):
        try:
            lockout_status = apiCallerMethods.account_lockout_status()
            if lockout_status.get("locked"):
                lockout_seconds = lockout_status.get("lockout_seconds", 0)
                self.lockout_until_timestamp = time.time() + lockout_seconds
                time_str = self._format_time_remaining(lockout_seconds)
                message = f"Login locked. Please wait {time_str}"
                self.status.setText(message)
                self._adjust_dialog_size(message)
                self._update_lockout_display(lockout_seconds)
            else:
                self.lockout_until_timestamp = None
                self.lockout_timer.stop()
                self.login_btn.setEnabled(True)
                if self.status.text() and "Login locked" in self.status.text():
                    self.status.setText("")
                    self.resize(375, self.height())
        except Exception:
            self.lockout_until_timestamp = None
            self.lockout_timer.stop()
            self.login_btn.setEnabled(True)

    def _update_lockout_display(self, lockout_seconds):
        if lockout_seconds > 0:
            time_str = self._format_time_remaining(lockout_seconds)
            message = f"Login locked. Please wait {time_str}"
            self.status.setText(message)
            self._adjust_dialog_size(message)
            self.login_btn.setEnabled(False)
            if not self.lockout_timer.isActive():
                self.lockout_timer.start()
        else:
            self.lockout_until_timestamp = None
            self.lockout_timer.stop()
            self.login_btn.setEnabled(True)

    def update_lockout_countdown(self):
        if self.lockout_until_timestamp is None:
            self.lockout_timer.stop()
            self.login_btn.setEnabled(True)
            return
        
        current_time = time.time()
        remaining_seconds = int(self.lockout_until_timestamp - current_time)
        
        if remaining_seconds > 0:
            time_str = self._format_time_remaining(remaining_seconds)
            message = f"Login locked. Please wait {time_str}"
            self.status.setText(message)
            self._adjust_dialog_size(message)
            self.login_btn.setEnabled(False)
        else:
            self.lockout_until_timestamp = None
            self.lockout_timer.stop()
            self.login_btn.setEnabled(True)
            self.status.setText("")
            self.resize(375, self.height())

    def center(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        screen_center = screen.availableGeometry().center()
        frame_geom = self.frameGeometry()
        frame_geom.moveCenter(screen_center)
        self.move(frame_geom.topLeft())


