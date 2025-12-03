from PyQt6.QtWidgets import (
    QApplication, QPushButton, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QScrollArea, QLineEdit, QComboBox, QMenu, QSizePolicy
)
from PyQt6.QtGui import QFont, QClipboard, QIcon, QPixmap, QCursor, QTransform
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
import sys
from passwordmanager.api import apiCallerMethods
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings
from passwordmanager.gui.widgets.editCredentialsDialog import EditCredentialsDialog
from passwordmanager.gui.settingsDialog import settingsDialog
from passwordmanager.utils.apiPasswordStrength import get_password_strength
from datetime import datetime

button_height = 32

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

        # search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self.filter_credentials)
        top_row.addWidget(self.search_bar, 1)  # take remaining space
        top_row.addSpacing(10)

        # hidden sort combobox (used only for logic)
        self.sort_dropdown = QComboBox()
        sort_options = [
            "Sort: Date Added (Newest First)",  # keep API order
            "Sort: Site (A–Z)",
            "Sort: Site (Z–A)",
        ]
        self.sort_dropdown.addItems(sort_options)
        self.sort_dropdown.currentIndexChanged.connect(self.apply_filters)

        # filter button that opens a dropdown menu
        self.filter_button = QPushButton("")
        self.filter_button.setToolTip("Sort Options")
        filter_icon = QIcon(QPixmap(Strings.FILTER_ICON_PATH))
        self.filter_button.setIcon(filter_icon)
        self.filter_button.setFixedWidth(40)
        self.filter_button.setStyleSheet(theme_manager.get_small_button_style())

        self.filter_menu = QMenu(self)
        for index, label in enumerate(sort_options):
            action = self.filter_menu.addAction(label)
            action.triggered.connect(
                lambda _, i=index: self.sort_dropdown.setCurrentIndex(i)
            )
        self.filter_button.clicked.connect(self.show_filter_menu)

        # Settings button - store as instance variable for theme updates
        self.settings_button = QPushButton("")
        self.settings_button.setToolTip("Settings")
        self.settings_button.setStyleSheet(theme_manager.get_small_button_style())
        settings_icon = QIcon(QPixmap(Strings.SETTINGS_ICON_PATH))
        self.settings_button.setIcon(settings_icon)
        self.settings_button.setFixedWidth(40)
        self.settings_button.clicked.connect(self.open_settings_dialog)

        # Add buttons to top row
        top_row.addWidget(self.filter_button)
        top_row.addWidget(self.settings_button)

        # Set margins to match credential cards layout
        top_row.setContentsMargins(10, 0, 10, 0)

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

        # Apply theme with current mode (not theme parameter)
        theme_manager.apply_theme_to_window(self, theme_manager.current_mode)

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

        # Main card container (vertical: top row + expand area)
        card_container = QWidget()
        card_layout = QVBoxLayout(card_container)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(6)

        
        # TOP ROW
        top_row_widget = QWidget()
        top_row_widget.setStyleSheet(f"""
            background-color: {colors['card_bg']};
            border-radius: 10px;
            padding: 6px;
        """)
        top_row_widget.setFixedHeight(50)

        top_row = QHBoxLayout(top_row_widget)
        top_row.setContentsMargins(12, 6, 12, 6)
        top_row.setSpacing(10)

        # site label
        site = QLabel(f"{cred.get('site','')}")
        site.setObjectName("site_label")
        site.setStyleSheet(f"color: {colors['text']}; font-size: 13px;")
        site.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # username label
        username = QLabel(f"{cred.get('username','')}")
        username.setObjectName("username_label")
        username.setStyleSheet(f"color: {colors['text']}; font-size: 13px;")
        username.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # password copy button 
        password_text = cred.get("password", "")
        password_copy_button = QPushButton("••••••••••••")
        password_copy_button.setToolTip("Copy password")
        password_copy_button.clicked.connect(
            lambda _, p=password_text: self.copy_to_clipboard(p, password_copy_button)
        )
        # ensure password button keeps a reasonable min width so arrow isn't pushed off
        password_copy_button.setMinimumWidth(130)
        password_copy_button.setFixedHeight(button_height)
        password_copy_button.setStyleSheet(f"""
            QPushButton {{
                color: {colors['text']};
            }}
            QPushButton:hover {{
                background-color: {colors['pressed_card_bg']};
                color: {colors['text']};
            }}
            QPushButton:pressed {{
                border: 2px solid {colors['card_bg']};
            }}
        """)

        # Password strength label 
        strength_label = QLabel()
        strength_label.setStyleSheet(f"color: {colors['text']}; font-size: 13px;")

        # DATE ADDED label
        raw_date = cred.get("created_at")

        # Format as MM-DD-YYYY if possible
        formatted_date = ""
        if raw_date:
            try:
                parsed = datetime.fromisoformat(raw_date.replace("Z", "").replace("T", " "))
                formatted_date = parsed.strftime("%m-%d-%Y")
            except:
                formatted_date = raw_date

        date_label = QLabel(f"Added: {formatted_date}")
        date_label.setStyleSheet(f"color: {colors['text']}; font-size: 13px;")


        # determine strength color
        strength = get_password_strength(password_text)
        if strength == "weak":
            strength_label.setText("Strength: Weak")
            strength_label.setStyleSheet("color: red; font-size: 13px;")
        elif strength == "medium":
            strength_label.setText("Strength: Medium")
            strength_label.setStyleSheet("color: orange; font-size: 13px;")
        else:
            strength_label.setText("Strength: Strong")
            strength_label.setStyleSheet("color: lightgreen; font-size: 13px;")

        if theme_manager.current_mode == "dark":
            ARROW_ICON_PATH = "resources/images/downArrowButtonWhiteIcon.png"
        else:
            ARROW_ICON_PATH = "resources/images/downArrowButtonIcon.png"

        # Dropdown button 
        arrow_pix = QPixmap(ARROW_ICON_PATH)

        dropdown_btn = QPushButton()
        dropdown_btn.setIcon(QIcon(arrow_pix))
        dropdown_btn.setIconSize(QSize(20, 20))
        dropdown_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        dropdown_btn.setFixedSize(32, 32)

        dropdown_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: transparent;
            }
            QPushButton:pressed {
                background-color: transparent;
            }
        """)

        # Add widgets to top row
        top_row.addWidget(site)
        top_row.addWidget(username)
        top_row.addWidget(password_copy_button)
        top_row.addWidget(dropdown_btn, 0, Qt.AlignmentFlag.AlignRight)

        # Expandable section
        expand_area = QWidget()
        expand_area.setMaximumHeight(0)  # collapsed initially
        expand_area.setMinimumHeight(0)
        expand_area.setStyleSheet(f"background-color: transparent;")

        expand_layout = QHBoxLayout(expand_area)
        expand_layout.setContentsMargins(14, 8, 14, 12)
        expand_layout.setSpacing(12)

        # EDIT BUTTON 
        edit_button = QPushButton()
        edit_button.setIcon(QIcon(QPixmap(Strings.EDIT_ICON_PATH)))
        edit_button.setIconSize(QSize(20, 20))
        edit_button.setFixedSize(40, 40)
        edit_button.setStyleSheet(theme_manager.get_small_button_style())
        edit_button.clicked.connect(lambda _, id=cred['id']: self.edit_credential(id))


        # VISUAL BUTTON 
        visual_button = QPushButton("👁️")
        visual_button.setIconSize(QSize(20, 20))
        visual_button.setFixedSize(40, 40)
        visual_button.setStyleSheet(theme_manager.get_small_button_style())

        # Track visibility 
        is_visible = {"state": False}

        def toggle_visual():
            if is_visible["state"]:
                # Hide password
                password_copy_button.setText("••••••••••••")
                visual_button.setText("👁️")   
                is_visible["state"] = False
            else:
                # Show password
                password_copy_button.setText(password_text)
                visual_button.setText("🙈")  
                is_visible["state"] = True

        visual_button.clicked.connect(toggle_visual)


        # DELETE BUTTON 
        delete_button = QPushButton()
        delete_button.setIcon(QIcon(QPixmap(Strings.DELETE_ICON_PATH)))
        delete_button.setIconSize(QSize(20, 20))
        delete_button.setFixedSize(40, 40)
        delete_button.setStyleSheet(theme_manager.get_delete_button_style())
        delete_button.clicked.connect(lambda _, id=cred['id']: self.delete_credential(id))

        # Equal size for buttons
        edit_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        visual_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        delete_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        expand_layout.addWidget(strength_label)
        expand_layout.addSpacing(20)
        expand_layout.addWidget(date_label)

        expand_layout.addStretch()

        expand_layout.addWidget(visual_button)
        expand_layout.addWidget(edit_button)
        expand_layout.addWidget(delete_button)

        # animation and toggle
        animation = QPropertyAnimation(expand_area, b"maximumHeight")
        animation.setDuration(180)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        is_expanded = {"state": False}

        def rotate_arrow(pixmap, degrees):
            """Rotate a QPixmap and return the rotated pixmap."""
            transform = QTransform()
            transform.rotate(degrees)
            rotated = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            return rotated

        def toggle_dropdown():
            if is_expanded["state"]:
                # collapse
                animation.stop()
                animation.setStartValue(expand_area.maximumHeight())
                animation.setEndValue(0)
                animation.start()

                # rotate arrow back to 0
                dropdown_btn.setIcon(QIcon(rotate_arrow(arrow_pix, 0)))
                is_expanded["state"] = False
            else:
                # expand to contents height
                animation.stop()
                expand_area.adjustSize()
                full_height = expand_area.sizeHint().height()
                animation.setStartValue(0)
                animation.setEndValue(full_height)
                animation.start()

                # rotate arrow 180
                dropdown_btn.setIcon(QIcon(rotate_arrow(arrow_pix, 180)))
                is_expanded["state"] = True

        dropdown_btn.clicked.connect(toggle_dropdown)

        # Add everything to the card container
        card_layout.addWidget(top_row_widget)
        card_layout.addWidget(expand_area)

        # add the card to the list
        self.credentials_layout.addWidget(card_container)

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

    def open_settings_dialog(self):
        overlay = QWidget(self.parentWidget)
        overlay.setGeometry(self.parentWidget.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")  # translucent overlay
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        overlay.show()

        dialog = settingsDialog(self.parentWidget)  # Pass parentWidget as parent
        dialog.adjustSize()

        # Center dialog relative to main window
        parent_rect = self.parentWidget.frameGeometry()
        dialog_rect = dialog.frameGeometry()

        dialog_rect.moveCenter(parent_rect.center())
        dialog.move(dialog_rect.topLeft())
        dialog.exec()

        overlay.deleteLater()

    def closeEvent(self, event):
        """Clean up when widget is closed"""
        theme_manager.unregister_window(self)
        super().closeEvent(event)

    def show_filter_menu(self):
        """This just shows the already-created menu at the right position (I didn't like the automatic small arrow)."""
        button_rect = self.filter_button.rect()
        button_global_pos = self.filter_button.mapToGlobal(button_rect.bottomLeft())

        # Show the menu at the calculated position
        self.filter_menu.exec(button_global_pos)
