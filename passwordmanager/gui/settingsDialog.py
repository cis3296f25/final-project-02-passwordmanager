from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout, QWidget,
    QFileDialog, QMessageBox, QRadioButton, QButtonGroup
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
        
        # Store parent reference for theme propagation
        self.parent_window = parent
        
        # Current theme state from theme manager
        self.current_theme = theme_manager.current_theme

        # Window setup
        self.setWindowTitle("Settings")
       
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)

        # Main layout
        layout = QVBoxLayout()

        # Input form fields
        form_layout = QFormLayout()

        # Theme section with Light/Dark buttons
        theme_layout = QHBoxLayout()
        self.light_button = QPushButton("Light")
        self.dark_button = QPushButton("Dark")

        # Connect theme button actions
        self.light_button.clicked.connect(self.set_light_theme)
        self.dark_button.clicked.connect(self.set_dark_theme)

        theme_layout.addWidget(self.light_button)
        theme_layout.addWidget(self.dark_button)
        
        form_layout.addRow("Theme:", theme_layout)
        
        # Change password section
        self.change_password_button = QPushButton("Change Password")
        self.change_password_button.setStyleSheet(Strings.SETTINGS_BUTTON_STYLE)
        self.change_password_button.clicked.connect(self.open_change_password_window)
        
        form_layout.addRow("Password:", self.change_password_button)

        # Export section
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

        # Import section
        import_layout = QHBoxLayout()
        self.import_button = QPushButton("Import CSV")
        self.import_button.clicked.connect(self.handle_import_csv)
        import_layout.addWidget(self.import_button)
        form_layout.addRow("Import:", import_layout)

        # Add form layout to main layout
        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet(Strings.LARGE_BUTTON_STYLE)

        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        
        # Let the theme manager handle initial theming
        theme_manager.apply_theme_to_window(self, theme_manager.current_theme)

    def update_theme_buttons(self):
        colors = theme_manager.get_theme_colors(self.current_theme)
        
        base_theme_button_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
        }}
        """
        
        selected_theme_button_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            border: 2px solid {Colors.BRAT_GREEN};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
        }}
        """
        
        if self.current_theme == "light":
            self.light_button.setStyleSheet(selected_theme_button_style)
            self.dark_button.setStyleSheet(base_theme_button_style)
        else:
            # Dark theme selected
            self.dark_button.setStyleSheet(selected_theme_button_style)
            self.light_button.setStyleSheet(base_theme_button_style)

    def update_button_theme(self):
        """Update the Change Password button styling based on current theme"""
        colors = theme_manager.get_theme_colors(self.current_theme)
        
        button_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            color: {colors['text']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            color: {Colors.BLACK};
        }}
        """
        self.change_password_button.setStyleSheet(button_style)
        # also style export/import buttons
        self.export_button.setStyleSheet(button_style)
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
            border: 2px solid {Colors.BRAT_GREEN};  /* high-contrast ring */
            background: transparent;
        }}
        QRadioButton::indicator:hover {{
            border-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
        }}
        QRadioButton::indicator:checked {{
            background-color: {Colors.BRAT_GREEN};  /* filled when selected */
            border-color: {Colors.BRAT_GREEN};
        }}
        """
        self.export_json_radio.setStyleSheet(radio_style)
        self.export_csv_radio.setStyleSheet(radio_style)
  
    def set_light_theme(self):
        theme_manager.set_theme("light")

    def set_dark_theme(self):
        theme_manager.set_theme("dark")
        
    def closeEvent(self, event):
        theme_manager.unregister_window(self)
        super().closeEvent(event)
        
    def open_change_password_window(self):
        overlay = QWidget(self)
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")  # translucent overlay
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        overlay.show()
        
        change_password_window = ChangePasswordWindow(self)
        change_password_window.exec()
        overlay.deleteLater()

    def is_vault_unlocked(self) -> bool:
        try:
            status = apiCallerMethods.get_status()
            return isinstance(status, dict) and not status.get("vault_locked", True)
        except Exception:
            return False

    def handle_export(self):
        if not self.is_vault_unlocked():
            QMessageBox.information(self, "Vault Locked", "Please unlock and log in to export.")
            return
        # Confirm plaintext risk
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
        path, _ = QFileDialog.getSaveFileName(self, "Save Export", default_name, filter_str)
        if not path:
            return
        try:
            data = apiCallerMethods.export_credentials(fmt)
            # data is dict for json, string for csv
            if fmt == "json":
                import json
                text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            else:
                text = data if isinstance(data, str) else ""
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            QMessageBox.information(self, "Export Complete", f"Passwords exported to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Failed to export: {e}")

    def handle_import_csv(self):
        if not self.is_vault_unlocked():
            QMessageBox.information(self, "Vault Locked", "Please unlock and log in to import.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
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
                QMessageBox.warning(self, "Import Failed", "CSV is missing a header row.")
                return
            normalized = [h.strip().lower().replace("_", "").replace("-", "") for h in headers]
            def find_col(name: str) -> int:
                key = name.replace("_", "").replace("-", "").lower()
                return normalized.index(key) if key in normalized else -1
            site_idx = find_col("site")
            user_idx = find_col("username")
            pass_idx = find_col("password")
            if site_idx < 0 or user_idx < 0 or pass_idx < 0:
                QMessageBox.warning(self, "Import Failed", "CSV must include headers: site, username, password.")
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

                    dup_resp = apiCallerMethods.check_duplicate_credential(site, username)
                    is_dup = bool(dup_resp.get("exists")) if isinstance(dup_resp, dict) else False
                    if is_dup:
                        choice = QMessageBox.question(
                            self,
                            "Duplicate Found",
                            f"Credential exists for:\n\nSite: {site}\nUser: {username}\n\nImport anyway?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No,
                        )
                        if choice != QMessageBox.StandardButton.Yes:
                            skipped += 1
                            continue

                    add_resp = apiCallerMethods.add_credential(site, username, password)
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
