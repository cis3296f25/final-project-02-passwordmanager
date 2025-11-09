from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QFont, QIcon
import sys
import apiCallerMethods
from colors import Colors
from credentialListWidget import CredentialsListWidget
from addCredentialsDialog import AddCredentialsDialog

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
        self.setWindowIcon(QIcon("resources\windowIcon.png"))
        self.setGeometry(200, 200, 475, 400)  # x, y, width, height
        self.setMinimumWidth(475)
        self.setMinimumHeight(400)

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
        # credentials list widget
        self.credentials_list = CredentialsListWidget()
        layout.addWidget(self.credentials_list)

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
        self.refresh_credentials()

    def refresh_credentials(self):
        self.credentials_list.load_credentials()

    def open_list_dialog(self):
        dialog = ListCredentialsDialog()
        dialog.exec()

    # Run the app
    @staticmethod
    def run():
        app = QApplication.instance() or QApplication(sys.argv)
        window = MainWindow()
        window.show()
        window.refresh_credentials()
        app.exec()
