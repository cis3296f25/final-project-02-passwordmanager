from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont, QIcon
import sys
import apiCallerMethods
from colors import Colors
from credentialListWidget import CredentialsListWidget
from addCredentialsDialog import AddCredentialsDialog

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

        # credentials list widget
        self.credentials_list = CredentialsListWidget()
        layout.addWidget(self.credentials_list)

        # buttons
        add_button = QPushButton("Add New Credential")
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
        exit_button.setStyleSheet(button_style)

        layout.addWidget(add_button)
        layout.addWidget(exit_button)

        # Connect buttons
        add_button.clicked.connect(self.open_add_dialog)
        exit_button.clicked.connect(self.close)

    # Open the Add Credentials dialog
    def open_add_dialog(self):
        dialog = AddCredentialsDialog()
        dialog.exec()
        self.refresh_credentials()

    def refresh_credentials(self):
        self.credentials_list.load_credentials()

    @staticmethod
    def run():
        app = QApplication.instance() or QApplication(sys.argv)
        window = MainWindow()
        window.show()
        window.refresh_credentials()
        app.exec()
