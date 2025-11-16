from PyQt6.QtWidgets import (
    QApplication, QPushButton, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QScrollArea
)
from PyQt6.QtGui import QFont, QClipboard, QIcon, QPixmap
from PyQt6.QtCore import Qt, QTimer
import sys
import apiCallerMethods
from resources.colors import Colors
from resources.strings import Strings


class ListCredentialsWidget(QWidget):
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
        card.setFixedHeight(45)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 5, 10, 5)

        # actual password text
        password_text = cred.get("password", "")

        # display for website, username, ••••••••
        site = QLabel(f"{cred['site']}")
        username = QLabel(f"{cred['username']}")
        # show bullets by default, one per character (or 8 if empty)
        bullet_count = len(password_text) if password_text else 8
        password_label = QLabel("•" * bullet_count)

        # font / color
        for label in (site, username, password_label):
            label.setStyleSheet(f"color: {Colors.WHITE}; font-size: 12px;")

        # buttons
        copy_button = QPushButton()
        edit_button = QPushButton()
        delete_button = QPushButton()
        show_button = QPushButton("👁")  # show/hide password toggle

        copy_icon = QIcon(QPixmap(Strings.COPY_ICON_PATH))
        edit_icon = QIcon(QPixmap(Strings.EDIT_ICON_PATH))
        delete_icon = QIcon(QPixmap(Strings.DELETE_ICON_PATH))

        copy_button.setIcon(copy_icon)
        edit_button.setIcon(edit_icon)
        delete_button.setIcon(delete_icon)

        # styling
        copy_button.setStyleSheet(Strings.SMALL_BUTTON_STYLE)
        edit_button.setStyleSheet(Strings.SMALL_BUTTON_STYLE)
        delete_button.setStyleSheet(Strings.DELETE_BUTTON_STYLE)
        show_button.setStyleSheet(Strings.SMALL_BUTTON_STYLE)

        # copy password to clipboard
        copy_button.clicked.connect(
            lambda _, p=password_text: self.copy_to_clipboard(p, copy_button)
        )

        # per-row visibility state
        is_visible = {"value": False}

        def toggle_password():
            if is_visible["value"]:
                # hide password
                password_label.setText("•" * bullet_count)
                show_button.setText("👁")
                is_visible["value"] = False
            else:
                # show password
                password_label.setText(password_text)
                show_button.setText("🙈")
                is_visible["value"] = True

        show_button.clicked.connect(toggle_password)

        # lay out widgets
        card_layout.addWidget(site)
        card_layout.addWidget(username)
        card_layout.addWidget(password_label)

        button_layout = QHBoxLayout()
        # put the eye next to the password, before the other action buttons
        button_layout.addWidget(show_button)
        button_layout.addWidget(copy_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)

        card_layout.addLayout(button_layout)

        card.setStyleSheet(
            f"""
            background-color: {Colors.LIGHT_GREY};
            border-radius: 10px;
            padding: 6px;
        """
        )

        self.credentials_layout.addWidget(card)

    def copy_to_clipboard(self, password, copy_button):
        QApplication.clipboard().setText(password)
        print("Copied password")