from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QFont
import sys
import apiCallerMethods
from colors import Colors


class AddCredentialsDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowTitle("Add New Credential")
        self.setStyleSheet(f"background-color: {Colors.DARK_GREY}; color: {Colors.WHITE};")
        self.setMinimumWidth(300)

        # Main layout
        layout = QVBoxLayout()

        # Input form fields
        form_layout = QFormLayout()
        self.site_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()

        form_layout.addRow("Site:", self.site_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate Password")
        self.save_button = QPushButton("Save Credential")

        button_style = f"""
            QPushButton {{
                background-color: {Colors.BRAT_GREEN};
                color: {Colors.WHITE};
                border-radius: 10px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            }}
        """
        self.generate_button.setStyleSheet(button_style)
        self.save_button.setStyleSheet(button_style)

        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Connect buttons
        self.generate_button.clicked.connect(self.generate_password)
        self.save_button.clicked.connect(self.save_credential)

    # Generate password via API
    def generate_password(self):
        try:
            new_pass = apiCallerMethods.get_new_generated_password()
            self.password_input.setText(new_pass["password"])
            self.status_label.setText("Generated new password.")
        except Exception as e:
            self.status_label.setText(f"Error generating password: {e}")

    # Save credential to database
    def save_credential(self):
        try:
            site = self.site_input.text()
            username = self.username_input.text()
            password = self.password_input.text()

            response = apiCallerMethods.add_credential(site, username, password)
            if "status" in response and response["status"] == "added":
                self.status_label.setText("Credential added successfully.")
            else:
                self.status_label.setText(f"Error: {response.get('error', 'Unknown')}")
        except Exception as e:
            self.status_label.setText(f"Error saving credential: {e}")

class ListCredentialsDialog(QDialog):
    def __init__(self):
        super().__init__()

        # window setup
        self.setWindowTitle("Stored Credentials")
        self.setStyleSheet(f"background-color: {Colors.DARK_GREY}; color: {Colors.WHITE};")
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout()

        # create the table
        self.table = QTableWidget()
        self.table.setStyleSheet(f"background-color: #4a4a4a; gridline-color: {Colors.BRAT_GREEN};") # little bit lighter gray
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Site", "Username", "Password"])

        # stretch columns to fill window
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)
        self.setLayout(layout)

        # load data from api
        self.load_data()
    
    def load_data(self):
        try:
            credentials = apiCallerMethods.get_all_credentials()

            # handles api errors (i.e. vault locked)
            if isinstance(credentials, dict) and "error" in credentials:
                self.table.setRowCount(1)
                self.table.setColumnCount(1)
                error_item = QTableWidgetItem(f"Error: {credentials['error']}")
                self.table.setItem(0, 0, error_item)
                return
            
            # populate table
            self.table.setRowCount(len(credentials))
            for i, cred in enumerate(credentials):
                self.table.setItem(i, 0, QTableWidgetItem(cred.get("site")))
                self.table.setItem(i, 1, QTableWidgetItem(cred.get("username")))
                self.table.setItem(i, 2, QTableWidgetItem(cred.get("password")))

        except Exception as e:
            # handles connection errors
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(f"Error loading data: {e}"))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # set window
        self.setWindowTitle("Offline Password Manager")
        self.setGeometry(200, 200, 400, 300)  # x, y, width, height
        self.setStyleSheet(f"background-color: {Colors.DARK_GREY};")

        # set central widget (similar to panels in jpanel)
        central = QWidget()
        self.setCentralWidget(central)

        # layout for central widget
        layout = QVBoxLayout()
        central.setLayout(layout)

        # label
        self.label = QLabel("Welcome to Offline Password Manager!\nlets come up with a more fun name for this :)", self)
        self.label.setFont(QFont("Segoe UI", 14))
        self.label.setStyleSheet(f"color: {Colors.WHITE};")
        layout.addWidget(self.label)

        # buttons
        add_button = QPushButton("Add New Credential")
        list_button = QPushButton("List All Credentials")
        exit_button = QPushButton("Exit")

        # button styling
        button_style = f"""
            QPushButton {{
                background-color: {Colors.BRAT_GREEN};
                color: {Colors.WHITE};
                border-radius: 10px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            }}
        """
        add_button.setStyleSheet(button_style)
        list_button.setStyleSheet(button_style)
        exit_button.setStyleSheet(button_style)

        layout.addWidget(add_button)
        layout.addWidget(list_button)
        layout.addWidget(exit_button)

        # Connect buttons
        add_button.clicked.connect(self.open_add_dialog)
        list_button.clicked.connect(self.open_list_dialog)
        exit_button.clicked.connect(self.close)

    # Open the Add Credentials dialog
    def open_add_dialog(self):
        dialog = AddCredentialsDialog()
        dialog.exec()

    def open_list_dialog(self):
        dialog = ListCredentialsDialog()
        dialog.exec()

    # Run the app
    @staticmethod
    def run():
        app = QApplication.instance() or QApplication(sys.argv)
        window = MainWindow()
        window.show()
        app.exec()
