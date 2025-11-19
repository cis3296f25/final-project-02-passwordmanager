from PyQt6.QtWidgets import (
    QApplication, QPushButton, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QScrollArea
)
from PyQt6.QtGui import QFont, QClipboard, QIcon, QPixmap, QCursor
from PyQt6.QtCore import Qt 
import sys
from passwordmanager.api import apiCallerMethods
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings
from passwordmanager.gui.widgets.editCredentialsDialog import EditCredentialsDialog

class ListCredentialsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        theme_manager.register_window(self)
    
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

        self.parentWidget = parent
        
        theme_manager.apply_theme_to_window(self, theme_manager.current_theme)

    def load_credentials(self):
        # clear all previous cards
        for i in reversed(range(self.credentials_layout.count())):
            widget = self.credentials_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        try:
            credentials = apiCallerMethods.get_all_credentials()
            if not credentials:
                colors = theme_manager.get_theme_colors()
                label = QLabel("No credentials stored yet.")
                label.setStyleSheet(f"color: {colors['text']};")
                self.credentials_layout.addWidget(label)
                return

            for cred in credentials:
                self.add_credential_card(cred)

        except Exception as e:
            colors = theme_manager.get_theme_colors()
            error_label = QLabel(f"Error loading credentials: {e}")
            error_label.setStyleSheet(f"color: {colors['text']};")
            self.credentials_layout.addWidget(error_label)

    # create a rectangular card for one credential
    def add_credential_card(self, cred):
        colors = theme_manager.get_theme_colors()
        
        card = QWidget()
        card.setFixedHeight(45)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 5, 10, 5)

        # actual password text
        password_text = cred.get("password", "")

        # display for website, username, ••••••••
        site = QLabel(f"{cred['site']}")
        username = QLabel(f"{cred['username']}")
        # show 12 bullets by default to hide password length
        password_label = QLabel("•" * 12)

        site.setStyleSheet(f"color: {colors['text']}; font-size: 12px;")
        username.setStyleSheet(f"color: {colors['text']}; font-size: 12px;")
        password_label.setStyleSheet(f"color: {colors['text']}; font-size: 16px;")

        # buttons (really should refactor this later) ##########################################
        copy_button = QPushButton()
        edit_button = QPushButton()
        delete_button = QPushButton()
        show_button = QPushButton("👁")  # show/hide password toggle

        # button icons
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
        
        # Set fixed height for all buttons to ensure consistency
        button_height = 32
        copy_button.setFixedHeight(button_height)
        edit_button.setFixedHeight(button_height)
        delete_button.setFixedHeight(button_height)
        show_button.setFixedHeight(button_height)

        # copy password to clipboard
        copy_button.clicked.connect(
            lambda _, p=password_text: self.copy_to_clipboard(p, copy_button)
        )
        edit_button.clicked.connect(lambda _, id=cred['id']: self.edit_credential(id))
        delete_button.clicked.connect(lambda _, id=cred['id']: self.delete_credential(id))

        # per-row visibility state
        is_visible = {"value": False}

        def toggle_password():
            if is_visible["value"]:
                # hide password - always show 12 dots to hide length
                password_label.setText("•" * 12)
                show_button.setText("👁")
                is_visible["value"] = False
            else:
                # show password
                password_label.setText(password_text)
                show_button.setText("🙈")
                is_visible["value"] = True

        show_button.clicked.connect(toggle_password)

        button_layout = QHBoxLayout()
        # put the eye next to the password, before the other action buttons
        button_layout.addWidget(show_button)
        button_layout.addWidget(copy_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        ###########################################################################################

        card_layout.addWidget(site)
        card_layout.addWidget(username)
        card_layout.addWidget(password_label)
        card_layout.addLayout(button_layout)

        card.setStyleSheet(f"""
            background-color: {colors['card_bg']};
            border-radius: 10px;
            padding: 6px;
        """)

        self.credentials_layout.addWidget(card)

    def copy_to_clipboard(self, password, copy_button):
        QApplication.clipboard().setText(password)

    def delete_credential(self, id):
        apiCallerMethods.delete_credential(id)
        self.load_credentials()

    def edit_credential(self, id):
        overlay = QWidget(self.parentWidget)
        overlay.setGeometry(self.parentWidget.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        overlay.show()

        dialog = EditCredentialsDialog(id, parent=self.parentWidget)
        dialog.setWindowFlag(Qt.WindowType.Window, True)
        dialog.adjustSize()

        # centering editCredentialsDialog
        parent_rect = self.parentWidget.frameGeometry()
        dialog_rect = dialog.frameGeometry()
        dialog_rect.moveCenter(parent_rect.center())
        dialog.move(dialog_rect.topLeft())

        dialog.exec()

        overlay.deleteLater()
        self.load_credentials()

