from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel
)
from PyQt6.QtGui import QFont
import sys
import apiCallerMethods
from colors import Colors


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
        self.label = QLabel("Offline Password Manager\nlets come up with a more fun name for this :)", self)
        self.label.setFont(QFont("Segoe UI", 14))
        self.label.setStyleSheet(f"color: {Colors.WHITE};")
        layout.addWidget(self.label)

        # buttons
        test_button = QPushButton("Test Button")
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
        test_button.setStyleSheet(button_style)
        exit_button.setStyleSheet(button_style)

        # add buttons to layout
        layout.addWidget(test_button)
        layout.addWidget(exit_button)

        # connect buttons to actions
        test_button.clicked.connect(self.test_button_clicked)
        exit_button.clicked.connect(self.close)

    def test_button_clicked(self):
        test_site = "example.com"
        test_user = "alice"
        test_pass = apiCallerMethods.get_new_generated_password()
        test_pass = test_pass["password"]

        apiCallerMethods.add_credential(test_site, test_user, test_pass)

        credentials = apiCallerMethods.get_credential(test_site)
        credentials = f"User: {credentials["username"]}\nPassword: {credentials["password"]}"
        self.label.setText(credentials)

    def run():
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        app.exec()
