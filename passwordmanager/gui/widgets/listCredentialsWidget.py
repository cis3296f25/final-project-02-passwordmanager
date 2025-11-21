from PyQt6.QtWidgets import (
    QApplication, QPushButton, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QScrollArea, QLineEdit, QComboBox, QMenu
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
    
        # Keep a copy of all credentials for sorting/filtering
        self.all_credentials = []

        # outer layout
        layout = QVBoxLayout(self)

 # Top row icons: search bar + filter button
        top_row = QHBoxLayout()
        #search bar
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
        top_row.addWidget(self.search_bar, 1)  # take remaining space

        # hidden sort combobox (used only for logic)
        self.sort_dropdown = QComboBox()
        sort_options = [
            "Sort: Date Added (Newest First)",  # keep API order
            "Sort: Site (A–Z)",
            "Sort: Site (Z–A)",
        ]
        self.sort_dropdown.addItems(sort_options)
        self.sort_dropdown.currentIndexChanged.connect(self.apply_filters)
        # NOTE: we do NOT add self.sort_dropdown to any layout

        # filter button that opens a dropdown menu
        self.filter_button = QPushButton("▾")  # you can swap this text for an icon later
        self.filter_button.setFixedWidth(40)
        self.filter_button.setStyleSheet(Strings.SMALL_BUTTON_STYLE)

        self.filter_menu = QMenu(self)
        for index, label in enumerate(sort_options):
            action = self.filter_menu.addAction(label)
            action.triggered.connect(
                lambda _, i=index: self.sort_dropdown.setCurrentIndex(i)
            )
        self.filter_button.setMenu(self.filter_menu)

        top_row.addWidget(self.filter_button)
        layout.addLayout(top_row)
        # ---------- end top row ----------

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
        """Fetch all credentials from the API and rebuild the list with current filters/sort."""
        # reset stored credentials
        self.all_credentials = []

        # clear all previous cards
        for i in reversed(range(self.credentials_layout.count())):
            widget = self.credentials_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        try:
            credentials = apiCallerMethods.get_all_credentials()
            self.all_credentials = credentials or []

            if not self.all_credentials:
                colors = theme_manager.get_theme_colors()
                label = QLabel("No credentials stored yet.")
                label.setStyleSheet(f"color: {colors['text']};")
                self.credentials_layout.addWidget(label)
            else:
                # Apply current search + sort settings
                self.apply_filters()

        except Exception as e:
            colors = theme_manager.get_theme_colors()
            error_label = QLabel(f"Error loading credentials: {e}")
            error_label.setStyleSheet(f"color: {colors['text']};")
            self.credentials_layout.addWidget(error_label)

        # reset search bar when reloading data
        self.search_bar.clear()

    def apply_filters(self):
        """
        Apply current search text and sort selection to self.all_credentials,
        then rebuild the visible cards.
        """
        # clear current 
        for i in reversed(range(self.credentials_layout.count())):
            widget = self.credentials_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        colors = theme_manager.get_theme_colors()

        if not self.all_credentials:
            label = QLabel("No credentials stored yet.")
            label.setStyleSheet(f"color: {colors['text']};")
            self.credentials_layout.addWidget(label)
            return

        # start from all credentials
        creds = list(self.all_credentials)

        # 1) Sort
        sort_text = self.sort_dropdown.currentText()

        # Keep backend order as "Date Added (Newest First)"
        if "Site (A–Z)" in sort_text:
            creds.sort(key=lambda c: c.get("site", "").lower())
        elif "Site (Z–A)" in sort_text:
            creds.sort(key=lambda c: c.get("site", "").lower(), reverse=True)
        # else: leave `creds` in the order received from API

        # 2) Filter by search text
        search = self.search_bar.text().lower().strip()
        if search:
            creds = [
                c for c in creds
                if search in c.get("site", "").lower()
                or search in c.get("username", "").lower()
            ]

        if not creds:
            label = QLabel("No credentials match your search.")
            label.setStyleSheet(f"color: {colors['text']};")
            self.credentials_layout.addWidget(label)
            return

        # 3) Rebuild cards
        for cred in creds:
            self.add_credential_card(cred)

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
        site.setObjectName("site_label") # set obj name for searching
        username = QLabel(f"{cred['username']}")
        username.setObjectName("username_label") # set obj name for searching

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

    def filter_credentials(self):
        """Called when search text changes – just reapply filters."""
        self.apply_filters()
