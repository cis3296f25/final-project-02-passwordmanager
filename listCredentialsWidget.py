from PyQt6.QtWidgets import (
    QApplication, QPushButton, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QScrollArea, QLineEdit
)
from PyQt6.QtGui import QFont, QClipboard, QIcon, QPixmap, QCursor
from PyQt6.QtCore import Qt 
import sys
import apiCallerMethods
from resources.colors import Colors
from resources.strings import Strings
from editCredentialsDialog import EditCredentialsDialog

class ListCredentialsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
    
        # outer layout
        layout = QVBoxLayout(self)

        # search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by site or username")
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.LIGHT_GREY};
                color: {Colors.WHITE};
                border-radius: 10px;
                padding: 6px;
                font-size: 12px;
            }}
        """)
        self.search_bar.textChanged.connect(self.filter_credentials)
        layout.addWidget(self.search_bar)

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

        self.search_bar.clear() # clear search

    # create a rectangular card for one credential
    def add_credential_card(self, cred):
        card = QWidget()
        card.setFixedHeight(45)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 5, 10, 5)

        # display for website, username, •••••••• (password)
        site = QLabel(f"{cred['site']}")
        site.setObjectName("site_label") # set obj name for searching
        username = QLabel(f"{cred['username']}")
        username.setObjectName("username_label") # set obj name for searching
        password = QLabel("••••••••")

        # font
        for label in (site, username, password):
            label.setStyleSheet(f"color: {Colors.WHITE}; font-size: 12px;")

        # buttons (really should refactor this later) ##########################################
        copy_button = QPushButton()
        edit_button = QPushButton()
        delete_button = QPushButton()

        # button icons
        copy_icon = QIcon(QPixmap(Strings.COPY_ICON_PATH)) 
        edit_icon = QIcon(QPixmap(Strings.EDIT_ICON_PATH)) 
        delete_icon = QIcon(QPixmap(Strings.DELETE_ICON_PATH)) 

        copy_button.setIcon(copy_icon)
        edit_button.setIcon(edit_icon)
        delete_button.setIcon(delete_icon)

        # styles
        copy_button.setStyleSheet(Strings.SMALL_BUTTON_STYLE)
        edit_button.setStyleSheet(Strings.SMALL_BUTTON_STYLE)
        delete_button.setStyleSheet(Strings.DELETE_BUTTON_STYLE)

        copy_button.clicked.connect(lambda _, p=cred['password']: self.copy_to_clipboard(p))
        edit_button.clicked.connect(lambda _, id=cred['id']: self.edit_credential(id))
        delete_button.clicked.connect(lambda _, id=cred['id']: self.delete_credential(id))

        button_layout = QHBoxLayout()
        button_layout.addWidget(copy_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        ###########################################################################################

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

    def copy_to_clipboard(self, password):
        QApplication.clipboard().setText(password)

    def delete_credential(self, id):
        apiCallerMethods.delete_credential(id)
        self.load_credentials()

    def edit_credential(self, id):
        overlay = QWidget(self)
        overlay.setGeometry(self.rect())
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

    def filter_credentials(self):
        search_text = self.search_bar.text().lower()

        # loop thru all widgets in layout
        for i in range(self.credentials_layout.count()):
            item = self.credentials_layout.itemAt(i)
            card = item.widget()

            if not card:
                continue

            # labels from above
            site_label = card.findChild(QLabel, "site_label")
            username_label = card.findChild(QLabel, "username_label")

            # this handles scenario where theres no credentials (i.e. no children)
            if not site_label or not username_label:
                if isinstance(card, QLabel):
                    card.setHidden(bool(search_text))
                continue

            # check for match in either field
            site_match = search_text in site_label.text().lower()
            username_match = search_text in username_label.text().lower()

            if site_match or username_match:
                card.show()
            else:
                card.hide()


