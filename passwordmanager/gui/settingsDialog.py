from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout, QWidget,
    QFileDialog, QMessageBox, QRadioButton, QButtonGroup, QComboBox, QSlider
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt
from passwordmanager.api import apiCallerMethods
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings
from passwordmanager.gui.changePasswordWindow import ChangePasswordWindow
import csv


class settingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Register with theme manager
        theme_manager.register_window(self)

        # Store parent reference for theme propagation & font scaling
        self.parent_window = parent

        # Base font size for "100%" display scale
        base_widget = self.parent_window if self.parent_window is not None else self
        self.base_point_size = base_widget.font().pointSizeF() or 11.0

        # Current mode and theme state from theme manager
        self.current_mode = theme_manager.current_mode
        self.current_theme = theme_manager.current_theme

        # Window setup
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)

        # Main layout
        layout = QVBoxLayout()

        # Input form fields
        form_layout = QFormLayout()

        # Themes section with dropdown
        themes_layout = QVBoxLayout()

        # Theme color palette dropdown
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Red", "Green", "Blue", "Purple"])
        self.theme_combo.currentIndexChanged.connect(self.on_color_theme_changed)

        # Set view to show all items without scrolling (5 items) - add extra padding
        view = self.theme_combo.view()
        row_height = view.sizeHintForRow(0)
        view.setMinimumHeight(row_height * 5 + 10)  # Add 10px padding

        # Set current selection based on theme_manager
        theme_index_map = {"default": 0, "red": 1, "green": 2, "blue": 3, "purple": 4}
        current_theme_lower = self.current_theme.lower()
        if current_theme_lower in theme_index_map:
            self.theme_combo.setCurrentIndex(theme_index_map[current_theme_lower])

        themes_layout.addWidget(self.theme_combo)

        # Light/Dark mode buttons
        mode_layout = QHBoxLayout()
        self.light_button = QPushButton("Light")
        self.dark_button = QPushButton("Dark")

        # Connect mode button actions
        self.light_button.clicked.connect(self.set_light_mode)
        self.dark_button.clicked.connect(self.set_dark_mode)

        mode_layout.addWidget(self.light_button)
        mode_layout.addWidget(self.dark_button)

        themes_layout.addLayout(mode_layout)

        form_layout.addRow("Themes:", themes_layout)

        # Display Size Section
        display_layout = QHBoxLayout()

        # Small "A" label
        self.display_small_label = QLabel("A")
        small_font = QFont(self.display_small_label.font())
        small_font.setPointSizeF(self.base_point_size * 0.8)
        self.display_small_label.setFont(small_font)

        # Slider: 80% – 140% of base size
        self.display_slider = QSlider(Qt.Orientation.Horizontal)
        self.display_slider.setMinimum(80)
        self.display_slider.setMaximum(140)
        self.display_slider.setSingleStep(5)
        self.display_slider.setPageStep(10)
        self.display_slider.setValue(100)  # 100% default
        self.display_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.display_slider.valueChanged.connect(self.on_display_size_changed)

        # Large "A" label
        self.display_large_label = QLabel("A")
        large_font = QFont(self.display_large_label.font())
        large_font.setPointSizeF(self.base_point_size * 1.3)
        self.display_large_label.setFont(large_font)

        display_layout.addWidget(self.display_small_label)
        display_layout.addWidget(self.display_slider)
        display_layout.addWidget(self.display_large_label)

        form_layout.addRow("Display size:", display_layout)

        # Password Section
        self.change_password_button = QPushButton("Change Password")
        self.change_password_button.setStyleSheet(
            theme_manager.get_settings_button_style()
        )
        self.change_password_button.clicked.connect(self.open_change_password_window)

        form_layout.addRow("Password:", self.change_password_button)

        # Export Section
        export_layout = QHBoxLayout()
        self.export_json_radio = QRadioButton("JSON")
        self.export_csv_radio = QRadioButton("CSV")
        self.export_json_radio.setChecked(True)
        self.export_format_group = QButtonGroup(self)
        self.export_format_group.addButton(self.export_json_radio)
        self.export_format_group.addButton(self.export_csv_radio)
        export_layout.addWidget(self.export_json_radio)
        export_layout.addWidget(self.export_csv_radio)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.handle_export)
        export_layout.addWidget(self.export_button)
        form_layout.addRow("Export:", export_layout)

        # Import Section
        import_layout = QHBoxLayout()
        self.import_button = QPushButton("Import CSV")
        self.import_button.clicked.connect(self.handle_import_csv)
        import_layout.addWidget(self.import_button)
        form_layout.addRow("Import:", import_layout)

        # Add form layout to main layout
        layout.addLayout(form_layout)

        # Close button
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet(theme_manager.get_large_button_style())
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Initial theming
        theme_manager.apply_theme_to_window(self, theme_manager.current_mode)
        self.update_theme_buttons()
        self.update_button_theme()

    # Theme + Mode Buttons
    def update_theme_buttons(self):
        # Sync current theme and mode from theme_manager
        self.current_mode = theme_manager.current_mode
        self.current_theme = theme_manager.current_theme

        colors = theme_manager.get_theme_colors(self.current_mode)

        # Update dropdown to reflect current color theme selection (only if it exists)
        if hasattr(self, "theme_combo"):
            theme_index_map = {"default": 0, "red": 1, "green": 2, "blue": 3, "purple": 4}
            current_theme_lower = self.current_theme.lower()
            if current_theme_lower in theme_index_map:
                # Block signals temporarily to avoid triggering on_color_theme_changed
                self.theme_combo.blockSignals(True)
                self.theme_combo.setCurrentIndex(theme_index_map[current_theme_lower])
                self.theme_combo.blockSignals(False)

            # Style the dropdown with theme colors
            combo_style = f"""
        QComboBox {{
            background-color: {colors['input_bg']};
            color: {colors['text']};
            padding: 5px;
            border-radius: 4px;
            border: 1px solid {colors['accent']};
        }}
        QComboBox:hover {{
            border: 2px solid {colors['accent']};
            padding: 4px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 25px;
            background-color: {colors['input_bg']};
        }}
        QComboBox::drop-down:hover {{
            background-color: {colors['accent_hover']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {colors['input_bg']};
            color: {colors['text']};
            selection-background-color: {colors['accent']};
            selection-color: {colors['background']};
            border: 1px solid {colors['accent']};
        }}
        QComboBox QAbstractItemView::item {{
            padding: 4px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {colors['accent_hover']};
            color: {colors['background']};
        }}
        """
            self.theme_combo.setStyleSheet(combo_style)

        base_theme_button_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
        }}
        """

        selected_theme_button_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            border: 2px solid {colors['accent']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
        }}
        """
            # Only update buttons if they exist (check for attribute)
        if hasattr(self, "light_button") and hasattr(self, "dark_button"):
            if self.current_mode == "light":
                self.light_button.setStyleSheet(selected_theme_button_style)
                self.dark_button.setStyleSheet(base_theme_button_style)
            else:
                self.dark_button.setStyleSheet(selected_theme_button_style)
                self.light_button.setStyleSheet(base_theme_button_style)

    def update_button_theme(self):
        colors = theme_manager.get_theme_colors(self.current_mode)

        button_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            color: {colors['text']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
            color: {colors['text']};
        }}
        """

        # Only update buttons if they exist (check for attribute)
        if hasattr(self, "change_password_button"):
            self.change_password_button.setStyleSheet(button_style)
         # also style export/import buttons
        if hasattr(self, "export_button"):
            self.export_button.setStyleSheet(button_style)
        if hasattr(self, "import_button"):
            self.import_button.setStyleSheet(button_style)
       
        # Improve radio button contrast (indicator ring more visible on dark backgrounds)
        radio_style = f"""
        QRadioButton {{
            color: {colors['text']};
            spacing: 6px;
        }}
        QRadioButton::indicator {{
            width: 14px;
            height: 14px;
            border-radius: 7px;
            border: 2px solid {colors['accent']};   /* high-contrast ring */
            background: transparent;
        }}
        QRadioButton::indicator:hover {{
            border-color: {colors['accent_hover']};
        }}
        QRadioButton::indicator:checked {{
            background-color: {colors['accent']}; /* filled when selected */
            border-color: {colors['accent']};
        }}
        """
        if hasattr(self, "export_json_radio"):
            self.export_json_radio.setStyleSheet(radio_style)
        if hasattr(self, "export_csv_radio"):
            self.export_csv_radio.setStyleSheet(radio_style)

    # Display Size Handling
    def on_display_size_changed(self, value: int):
        """
        Slider is 80–140. Treat as percentage of base_point_size.
        Apply new font size immediately to the main window and settings dialog.
        """
        scale = value / 100.0
        target_size = max(8.0, self.base_point_size * scale)
        self.apply_font_size(target_size)

    def apply_font_size(self, point_size: float):
        def _apply_to_widget(widget: QWidget):
            f = QFont(widget.font())
            f.setPointSizeF(point_size)
            widget.setFont(f)

        # Apply to main window + its children
        if self.parent_window is not None:
            _apply_to_widget(self.parent_window)
            for child in self.parent_window.findChildren(QWidget):
                _apply_to_widget(child)

        # Apply to settings dialog itself
        _apply_to_widget(self)
        for child in self.findChildren(QWidget):
            _apply_to_widget(child)

    # Mode + Theme Changers
    def on_color_theme_changed(self, index):
        theme_map = {0: "default", 1: "red", 2: "green", 3: "blue", 4: "purple"}
        if index in theme_map:
            theme_manager.set_theme(theme_map[index])
            self.current_theme = theme_map[index]

    def set_light_mode(self):
        theme_manager.set_mode("light")
        self.current_mode = "light"

    def set_dark_mode(self):
        theme_manager.set_mode("dark")
        self.current_mode = "dark"

    def closeEvent(self, event):
        theme_manager.unregister_window(self)
        super().closeEvent(event)

    # Password Change
    def open_change_password_window(self):
        overlay = QWidget(self)
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        overlay.show()

        change_password_window = ChangePasswordWindow(self)
        change_password_window.exec()
        overlay.deleteLater()

    # Export/Import Support
    def is_vault_unlocked(self) -> bool:
        try:
            status = apiCallerMethods.get_status()
            return isinstance(status, dict) and not status.get("vault_locked", True)
        except Exception:
            return False

    def handle_export(self):
        if not self.is_vault_unlocked():
            QMessageBox.information(
                self, "Vault Locked", "Please unlock and log in to export."
            )
            return

        confirm = QMessageBox.question(
            self,
            "Export Passwords",
            "Exported files contain plaintext passwords. Proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        fmt = "json" if self.export_json_radio.isChecked() else "csv"
        filter_str = "JSON Files (*.json)" if fmt == "json" else "CSV Files (*.csv)"
        default_name = "passwords.json" if fmt == "json" else "passwords.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Export", default_name, filter_str
        )
        if not path:
            return
        try:
            data = apiCallerMethods.export_credentials(fmt)
            if fmt == "json":
                import json

                text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            else:
                text = data if isinstance(data, str) else ""
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            QMessageBox.information(
                self, "Export Complete", f"Passwords exported to:\n{path}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Failed to export: {e}")

    def handle_import_csv(self):
        if not self.is_vault_unlocked():
            QMessageBox.information(
                self, "Vault Locked", "Please unlock and log in to import."
            )
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                csv_text = f.read()

            inserted = 0
            skipped = 0
            errors = 0
            parse_errors = 0

            # Parse header
            lines = csv_text.splitlines()
            if not lines:
                QMessageBox.warning(self, "Import Failed", "CSV is empty.")
                return
            reader = csv.reader(lines)
            try:
                headers = next(reader)
            except StopIteration:
                QMessageBox.warning(
                    self, "Import Failed", "CSV is missing a header row."
                )
                return
            normalized = [
                h.strip().lower().replace("_", "").replace("-", "") for h in headers
            ]

            def find_col(name: str) -> int:
                key = name.replace("_", "").replace("-", "").lower()
                return normalized.index(key) if key in normalized else -1

            site_idx = find_col("site")
            user_idx = find_col("username")
            pass_idx = find_col("password")
            if site_idx < 0 or user_idx < 0 or pass_idx < 0:
                QMessageBox.warning(
                    self,
                    "Import Failed",
                    "CSV must include headers: site, username, password.",
                )
                return

            # Iterate each row and import with per-duplicate prompt
            for row in csv.reader(lines[1:]):
                try:
                    site = (row[site_idx] if site_idx < len(row) else "").strip()
                    username = (row[user_idx] if user_idx < len(row) else "").strip()
                    password = (row[pass_idx] if pass_idx < len(row) else "").strip()
                    if not site or not username or not password:
                        parse_errors += 1
                        continue

                    dup_resp = apiCallerMethods.check_duplicate_credential(
                        site, username
                    )
                    is_dup = (
                        bool(dup_resp.get("exists"))
                        if isinstance(dup_resp, dict)
                        else False
                    )
                    if is_dup:
                        choice = QMessageBox.question(
                            self,
                            "Duplicate Found",
                            f"Credential exists for:\n\nSite: {site}\nUser: {username}\n\nImport anyway?",
                            QMessageBox.StandardButton.Yes
                            | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No,
                        )
                        if choice != QMessageBox.StandardButton.Yes:
                            skipped += 1
                            continue

                    add_resp = apiCallerMethods.add_credential(
                        site, username, password
                    )
                    if isinstance(add_resp, dict) and add_resp.get("status") == "added":
                        inserted += 1
                    else:
                        errors += 1
                except Exception:
                    errors += 1

            QMessageBox.information(
                self,
                "Import Complete",
                f"Inserted: {inserted}\nSkipped (duplicates): {skipped}\nErrors: {errors}\nParse errors: {parse_errors}",
            )
            # Refresh main list to show newly imported credentials
            self.parent_window.refresh_credentials()
        except Exception as e:
            QMessageBox.warning(self, "Import Failed", f"Failed to import: {e}")
