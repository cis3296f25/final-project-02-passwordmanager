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
        self.base_height = 225
        self.setMinimumSize(375, self.base_height)
        self.resize(375, self.base_height)

        layout = QVBoxLayout()

        title = QLabel("Offline Password Manager")
        title.setFont(QFont("Segoe UI", 16))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)
        self.username = QLineEdit()
        self.username.setMinimumHeight(30)
        self.password = QLineEdit()
        self.password.setMinimumHeight(30)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password = QLineEdit()
        self.confirm_password.setMinimumHeight(30)
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_label.setVisible(False)
        self.confirm_password.setVisible(False)
        
        form.addRow("Username:", self.username)
        form.addRow("Master Password:", self.password)
        form.addRow(self.confirm_password_label, self.confirm_password)
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
        
        self.password.textChanged.connect(self._on_password_changed)
        self.confirm_password.textChanged.connect(self._on_confirm_password_changed)
        self.confirm_password.returnPressed.connect(self.handle_create)

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
    
    def _adjust_dialog_height(self):
        current_height = self.height()
        if self.confirm_password.isVisible():
            if current_height < self.base_height + 50:
                self.resize(self.width(), self.base_height + 50)
        else:
            if current_height > self.base_height:
                self.resize(self.width(), self.base_height)
    
    def show_create_mode(self):
        if not self.confirm_password.isVisible():
            self.confirm_password_label.setVisible(True)
            self.confirm_password.setVisible(True)
            self._adjust_dialog_height()
            self.confirm_password.setFocus()
    
    def hide_create_mode(self):
        if self.confirm_password.isVisible():
            self.confirm_password_label.setVisible(False)
            self.confirm_password.setVisible(False)
            self.confirm_password.clear()
            self._adjust_dialog_height()
    
    def _on_password_changed(self):
        if self.confirm_password.isVisible() and self.confirm_password.text():
            self._validate_password_match()
    
    def _on_confirm_password_changed(self):
        if self.confirm_password.isVisible():
            self._validate_password_match()
    
    def _validate_password_match(self):
        password = self.password.text()
        confirm = self.confirm_password.text()
        if confirm and password != confirm:
            self.status.setText("Passwords do not match")
            self.status.setStyleSheet("color: red;")
        elif confirm and password == confirm:
            self.status.setText("Passwords match")
            self.status.setStyleSheet("color: green;")
        else:
            self.status.setText("")
            self.status.setStyleSheet("")

    def handle_login(self):
        self.hide_create_mode()
        username = self.username.text()
        if not username:
            self.status.setText("Please enter a username")
            self.status.setStyleSheet("")
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
                self.status.setStyleSheet("")
                if "lockout_seconds" not in resp:
                    self.check_lockout_status()
        except Exception as e:
            self.status.setText(f"Error: {e}")
            self.status.setStyleSheet("")
            self.check_lockout_status()

    def handle_create(self):
        username = self.username.text()
        password = self.password.text()
        confirm = self.confirm_password.text()
        
        if not self.confirm_password.isVisible():
            self.show_create_mode()
            if not username:
                self.status.setText("Please enter a username")
                self.status.setStyleSheet("color: red;")
            elif not password:
                self.status.setText("Please enter a password")
                self.status.setStyleSheet("color: red;")
            else:
                self.status.setText("Please confirm your password")
                self.status.setStyleSheet("")
            return
        
        if not username:
            self.status.setText("Please enter a username")
            self.status.setStyleSheet("color: red;")
            return
        
        if not password:
            self.status.setText("Please enter a password")
            self.status.setStyleSheet("color: red;")
            return
        
        if not confirm:
            self.status.setText("Please confirm your password")
            self.status.setStyleSheet("color: red;")
            return
        
        if password != confirm:
            self.status.setText("Passwords do not match")
            self.status.setStyleSheet("color: red;")
            return
        
        try:
            resp = apiCallerMethods.account_create(username, password)
            if resp.get("status") == "account created":
                self.status.setText("Account created successfully! Logging in…")
                self.status.setStyleSheet("color: green;")
                QTimer.singleShot(1500, self.handle_login)
            else:
                error_msg = resp.get("error", "Create failed")
                self.status.setText(error_msg)
                self.status.setStyleSheet("color: red;")
        except Exception as e:
            self.status.setText(f"Error: {e}")
            self.status.setStyleSheet("color: red;")

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
                    self.status.setStyleSheet("")
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
            self.status.setStyleSheet("")
            self.resize(375, self.height())

    def center(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        screen_center = screen.availableGeometry().center()
        frame_geom = self.frameGeometry()
        frame_geom.moveCenter(screen_center)
        self.move(frame_geom.topLeft())


