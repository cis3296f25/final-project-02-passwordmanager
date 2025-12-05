from PyQt6.QtWidgets import (
    QApplication, QPushButton, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QScrollArea, QLineEdit, QComboBox, QMenu,
    QMessageBox, QSizePolicy
)
from PyQt6.QtGui import QFont, QClipboard, QIcon, QPixmap, QCursor, QTransform
from PyQt6.QtCore import Qt, QSettings, QPropertyAnimation, QEasingCurve, QSize
import sys
from passwordmanager.api import apiCallerMethods
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings
from passwordmanager.gui.widgets.editCredentialsDialog import EditCredentialsDialog
from passwordmanager.gui.settingsDialog import settingsDialog
from passwordmanager.utils.apiPasswordStrength import get_password_strength
from datetime import datetime

# Base sizes before applying display scale
BASE_CARD_HEIGHT = 45
BASE_BUTTON_HEIGHT = 32
BASE_BUTTON_WIDTH = 30


class ListCredentialsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        theme_manager.register_window(self)

        # Keep a copy of all credentials for sorting/filtering
        self.all_credentials = []
        
        # Track password visibility states for "show all" feature
        self.password_buttons = []  # List of dicts: {button, password_text, password_copy_button, is_visible}

        # outer layout
        layout = QVBoxLayout(self)

        # Top row icons: search bar + filter button
        top_row = QHBoxLayout()
        
        # search bar (shortened to make room for show all button)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self.filter_credentials)
        top_row.addWidget(self.search_bar, 2)  # take 2/3 of remaining space
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
        # NOTE: we do NOT add self.sort_dropdown to any layout

        # filter button that opens a dropdown menu
        self.filter_button = QPushButton("")
        self.filter_button.setToolTip("Sort Options")
        filter_icon = QIcon(QPixmap(Strings.FILTER_ICON_PATH))
        self.filter_button.setIcon(filter_icon)
        self.filter_button.setFixedSize(40, 40)
        self.filter_button.setStyleSheet(theme_manager.get_small_button_style())

        self.filter_menu = QMenu(self)
        for index, label in enumerate(sort_options):
            action = self.filter_menu.addAction(label)
            action.triggered.connect(
                lambda _, i=index: self.sort_dropdown.setCurrentIndex(i)
            )
        self.filter_button.clicked.connect(self.show_filter_menu)

        # show password icons
        self.show_icon = QIcon(QPixmap(Strings.VIEW_PASSWORD_ICON_PATH))
        self.hide_icon = QIcon(QPixmap(Strings.HIDE_PASSWORD_ICON_PATH))

        # Show all passwords button
        self.show_all_button = QPushButton()
        self.show_all_button.setIcon(self.show_icon)
        self.show_all_button.setToolTip("Show all passwords")
        self.show_all_button.setFixedSize(40, 40)
        self.show_all_button.setStyleSheet(theme_manager.get_small_button_style())
        self.show_all_button.clicked.connect(self.toggle_show_all_passwords)
        self.all_passwords_visible = False

        # Settings button - store as instance variable for theme updates
        self.settings_button = QPushButton("")
        self.settings_button.setToolTip("Settings")
        self.settings_button.setStyleSheet(theme_manager.get_small_button_style())
        settings_icon = QIcon(QPixmap(Strings.SETTINGS_ICON_PATH))
        self.settings_button.setIcon(settings_icon)
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.clicked.connect(self.open_settings_dialog)

        # Add buttons to top row
        top_row.addWidget(self.filter_button)
        top_row.addWidget(self.show_all_button)
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
        self.credentials_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.credentials_layout = QVBoxLayout(self.credentials_container)
        self.credentials_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.credentials_layout.setContentsMargins(10, 0, 10, 0)  # Left and right margins
        self.scroll_area.setWidget(self.credentials_container)

        self.parentWidget = parent

        # Apply theme with current mode (not theme parameter)
        theme_manager.apply_theme_to_window(self, theme_manager.current_mode)

    def load_credentials(self):
        """Fetch all credentials from the API and rebuild the list with current filters/sort."""
        # reset stored credentials
        self.all_credentials = []
        self.password_buttons = []

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
        self.password_buttons = []
        
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
        
        # 4) Update show all button state based on stored visibility
        self.update_show_all_button_state()

    # create a rectangular card for one credential
    def add_credential_card(self, cred):
        colors = theme_manager.get_theme_colors()
        
        # Prefer global display_scale set by settingsDialog / main_window
        scale = getattr(theme_manager, "display_scale", None)
        if scale is None:
            # Fallback to persisted setting if global not set for some reason
            settings = QSettings("OfflinePasswordManager", "OfflinePasswordManager")
            scale = settings.value("display_scale", 1.0, type=float)

        # Clamp to reasonable range
        scale = max(0.85, min(scale, 1.4))

        # Compute scaled sizes
        card_height = int(BASE_CARD_HEIGHT * scale)
        btn_height = int(BASE_BUTTON_HEIGHT * scale)
        btn_width = int(BASE_BUTTON_WIDTH * scale)

        # font sizes for password bullets (site/username will use global font scale)
        base_password_size = 14
        password_size = int(base_password_size * scale)

        # Main card container (vertical: top row + expand area)
        card_container = QWidget()
        card_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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
        top_row_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top_row = QHBoxLayout(top_row_widget)
        top_row.setContentsMargins(12, 6, 12, 6)
        top_row.setSpacing(10)
        
        # Site label 
        site = QLabel(f"{cred.get('site','')}")
        site.setObjectName("site_label")
        site.setStyleSheet(f"color: {colors['text']}; font-size: {password_size}px;")
        site.setFixedWidth(160)
        site.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        site.setWordWrap(False)
        
        # Username label
        username_copy_button = QPushButton(f"{cred.get('username','')}")
        username_copy_button.setObjectName("username_label")
        username_copy_button.setToolTip("Click to copy username")
        username_copy_button.setFixedWidth(160)
        username_copy_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        username_copy_button.setFixedHeight(btn_height)

        username_copy_button.setStyleSheet(f"""
            QPushButton {{
                color: {colors['text']};
                font-size: {password_size}px;
                text-align: left;
                padding-left: 8px;
                border: none;
                background-color: transparent;
            }}
            QPushButton:hover {{
                background-color: {colors['pressed_card_bg']};
                color: {colors['text']};
            }}
            QPushButton:pressed {{
                border: 2px solid {colors['card_bg']};
            }}
        """)

        # Connect username button click to copy
        username_text = cred.get('username', '')
        username_copy_button.clicked.connect(
            lambda _, u=username_text: self.copy_to_clipboard(u, username_copy_button)
        )
        
        # Password text (needed for both top row and dropdown)
        password_text = cred.get("password", "")
        
        # Password display button for top row 
        password_copy_button = QPushButton("••••••••••••")
        password_copy_button.setToolTip("Click to copy password")
        password_copy_button.setFixedWidth(180)
        password_copy_button.setFixedHeight(btn_height)
        password_copy_button.setStyleSheet(f"""
            QPushButton {{
                color: {colors['text']};
                font-size: {password_size}px;
            }}
            QPushButton:hover {{
                background-color: {colors['pressed_card_bg']};
                color: {colors['text']};
            }}
            QPushButton:pressed {{
                border: 2px solid {colors['card_bg']};
            }}
        """)
        
        # Dropdown arrow button - choose icon based on theme
        from resources.strings import get_resource_path
        if theme_manager.current_mode == "dark":
            ARROW_ICON_PATH = "resources/images/downArrowButtonWhiteIcon.png"
        else:
            ARROW_ICON_PATH = "resources/images/downArrowButtonIcon.png"
        arrow_pix = QPixmap(get_resource_path(ARROW_ICON_PATH))
        dropdown_btn = QPushButton()
        dropdown_btn.setIcon(QIcon(arrow_pix))
        dropdown_btn.setFixedSize(24, 24)
        dropdown_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {colors['pressed_card_bg']};
                border-radius: 4px;
            }}
        """)
        
        def rotate_arrow(pixmap, degrees):
            transform = QTransform().rotate(degrees)
            return pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        
        # Add widgets to top row: site | username | password | arrow
        top_row.addWidget(site)
        top_row.addWidget(username_copy_button)
        top_row.addWidget(password_copy_button)
        top_row.addWidget(dropdown_btn)
        
        # EXPANDABLE AREA
        expand_area = QWidget()
        expand_area.setMaximumHeight(0)  # collapsed initially
        expand_area.setMinimumHeight(0)
        expand_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Include tooltip styling in expand_area so buttons inside inherit it
        expand_area.setStyleSheet(f"""
            background-color: transparent;
            QToolTip {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['accent']};
                padding: 4px;
            }}
        """)
        
        expand_layout = QHBoxLayout(expand_area)
        expand_layout.setContentsMargins(10, 8, 10, 12)
        expand_layout.setSpacing(8)
        
        # Password strength label
        strength_label = QLabel()
        strength = get_password_strength(password_text)
        if strength == "weak":
            strength_label.setText("Password strength: Weak")
            strength_label.setStyleSheet("color: red; font-size: 13px;")
        elif strength == "medium":
            strength_label.setText("Password strength: Medium")
            strength_label.setStyleSheet("color: orange; font-size: 13px;")
        else:
            strength_label.setText("Password strength: Strong")
            strength_label.setStyleSheet("color: green; font-size: 13px;")
        strength_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        
        # Edit button
        edit_button = QPushButton()
        edit_icon = QIcon(QPixmap(Strings.EDIT_ICON_PATH))
        edit_button.setIcon(edit_icon)
        edit_button.setStyleSheet(theme_manager.get_small_button_style())
        edit_button.setFixedHeight(btn_height)
        edit_button.setFixedWidth(btn_width)
        edit_button.clicked.connect(lambda _, id=cred['id']: self.edit_credential(id))
        
        # Delete button
        delete_button = QPushButton()
        delete_icon = QIcon(QPixmap(Strings.DELETE_ICON_PATH))
        delete_button.setIcon(delete_icon)
        delete_button.setStyleSheet(theme_manager.get_delete_button_style())
        delete_button.setFixedHeight(btn_height)
        delete_button.setFixedWidth(btn_width)
        delete_button.clicked.connect(lambda _, id=cred['id']: self.delete_credential(id))
        
        # Date label
        raw_date = cred.get("created_at")
        formatted_date = ""
        if raw_date:
            try:
                parsed = datetime.fromisoformat(str(raw_date).replace("Z", "").replace("T", " "))
                formatted_date = parsed.strftime("%m-%d-%Y")
            except:
                formatted_date = str(raw_date) if raw_date else ""
        
        date_label = QLabel(f"Added: {formatted_date}")
        date_label.setStyleSheet(f"color: {colors['text']}; font-size: 13px;")
        date_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        date_label.setWordWrap(False)
        
        # Visual button to show/hide password (controls the password button in top row)
        visual_button = QPushButton(self)
        visual_button.setIcon(self.show_icon)
        visual_button.setFixedSize(btn_width, btn_height)
        visual_button.setText("")
        visual_button.setToolTip("Show password")
        visual_button.setStyleSheet(theme_manager.get_small_button_style())
        # Force tooltip styling directly on button - brute force fix for black rectangle
        button_style = theme_manager.get_small_button_style()
        tooltip_style = f"""
            QToolTip {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['accent']};
                padding: 4px;
            }}
        """
        visual_button.setStyleSheet(button_style + tooltip_style)
        
        # Use global show all state to set initial visibility
        is_visible = {"state": self.all_passwords_visible}
        
        # Set initial state based on global state
        if self.all_passwords_visible:
            password_copy_button.setText(password_text)
            visual_button.setIcon(self.hide_icon)
            visual_button.setToolTip("Hide password")
        else:
            password_copy_button.setText("••••••••••••")
            visual_button.setIcon(self.show_icon)
            visual_button.setToolTip("Show password")
        
        def toggle_visual():
            if is_visible["state"]:
                password_copy_button.setText("••••••••••••")
                visual_button.setIcon(self.show_icon)
                visual_button.setToolTip("Show password")
                is_visible["state"] = False
            else:
                password_copy_button.setText(password_text)
                visual_button.setIcon(self.hide_icon)
                visual_button.setToolTip("Hide password")
                is_visible["state"] = True
            self.update_show_all_button_state()
        
        visual_button.clicked.connect(toggle_visual)
        
        # Store reference for "show all" feature
        password_info = {
            "button": visual_button,
            "password_text": password_text,
            "password_copy_button": password_copy_button,
            "is_visible": is_visible
        }
        self.password_buttons.append(password_info)
        
        # Connect password button click to copy (now that it's in top row)
        password_copy_button.clicked.connect(
            lambda _, p=password_text: self.copy_to_clipboard(p, password_copy_button)
        )
        
        # Add widgets to expand layout (password button removed, now in top row)
        # Labels aligned to the left
        expand_layout.addWidget(strength_label)
        expand_layout.addSpacing(15)  # Spacing between strength and date
        expand_layout.addWidget(date_label)
        expand_layout.addStretch()
        # Buttons aligned to the right
        expand_layout.addWidget(visual_button)
        visual_button.setToolTip("Show password")
        expand_layout.addWidget(edit_button)
        expand_layout.addWidget(delete_button)
        
        # Animation for expand/collapse
        animation = QPropertyAnimation(expand_area, b"maximumHeight")
        animation.setDuration(180)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        is_expanded = {"state": False}
        
        def toggle_expand():
            if not is_expanded["state"]:
                is_expanded["state"] = True
                expand_area.adjustSize()
                full_height = expand_area.sizeHint().height()
                animation.setStartValue(0)
                animation.setEndValue(full_height)
                animation.start()
                dropdown_btn.setIcon(QIcon(rotate_arrow(arrow_pix, 180)))
            else:
                is_expanded["state"] = False
                animation.setStartValue(expand_area.maximumHeight())
                animation.setEndValue(0)
                animation.start()
                dropdown_btn.setIcon(QIcon(rotate_arrow(arrow_pix, 0)))
        
        dropdown_btn.clicked.connect(toggle_expand)
        top_row_widget.mousePressEvent = lambda e: toggle_expand() if e.button() == Qt.MouseButton.LeftButton else None
        
        # Add top row and expand area to card layout
        card_layout.addWidget(top_row_widget)
        card_layout.addWidget(expand_area)
        
        # Add the card to the list
        self.credentials_layout.addWidget(card_container)       

    def copy_to_clipboard(self, password, copy_button):
        QApplication.clipboard().setText(password)

    def delete_credential(self, id):
        colors = theme_manager.get_theme_colors()

        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Deletion")
        msg.setText("Are you sure you want to delete this credential?\nThis cannot be undone.")
        msg.setIcon(QMessageBox.Icon.Question)

        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {colors['background']};
            }}
            QLabel {{
                color: {colors['text']};
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {colors['accent']};
                color: {colors['text']};
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_hover']}; 
            }}
            QPushButton:pressed {{
                background-color: {colors['accent_pressed']};
            }}
        """)

        reply = msg.exec()

        if reply == QMessageBox.StandardButton.Yes:
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
    
    def toggle_show_all_passwords(self):
        # Toggle global state
        self.all_passwords_visible = not self.all_passwords_visible
        new_state = self.all_passwords_visible
        
        if not self.password_buttons:
            self.update_show_all_button_state()
            return
        
        valid_buttons = []
        for p in self.password_buttons:
            try:
                _ = p["button"].isVisible()
                _ = p["password_copy_button"].isVisible()
                valid_buttons.append(p)
            except RuntimeError:
                continue
        
        if not valid_buttons:
            self.password_buttons = []
            self.update_show_all_button_state()
            return
        
        # Update all visible passwords to match global state
        for p in valid_buttons:
            try:
                p["is_visible"]["state"] = new_state
                if new_state:
                    # Show password
                    p["password_copy_button"].setText(p["password_text"])
                    p["button"].setIcon(self.hide_icon)
                    p["button"].setToolTip("Hide password")
                else:
                    # Hide password
                    p["password_copy_button"].setText("••••••••••••")
                    p["button"].setIcon(self.show_icon)
                    p["button"].setToolTip("Show password")
            except RuntimeError:
                continue
        
        self.password_buttons = valid_buttons
        
        self.update_show_all_button_state()
    
    def update_show_all_button_state(self):
        """Update the show all button icon and tooltip based on global visibility state."""
        # Just reflect the global state - this is the source of truth
        if self.all_passwords_visible:
            self.show_all_button.setIcon(self.hide_icon)
            self.show_all_button.setToolTip("Hide all passwords")
        else:
            self.show_all_button.setIcon(self.show_icon)
            self.show_all_button.setToolTip("Show all passwords")
