from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QIcon
import sys
import apiCallerMethods
from resources.colors import Colors
from resources.strings import Strings
from listCredentialsWidget import ListCredentialsWidget
from addCredentialsDialog import AddCredentialsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # set window
        self.setWindowTitle(Strings.APP_NAME)
        self.setWindowIcon(QIcon(Strings.WINDOW_ICON_PATH))
        self.setGeometry(200, 200, 475, 400)  # x, y, width, height
        self.setMinimumWidth(525)
        self.setMinimumHeight(600)

        self.setStyleSheet(f"background-color: {Colors.DARK_GREY};")

        # set central widget (similar to panels in jpanel)
        central = QWidget()
        self.setCentralWidget(central)

        # layout for central widget
        layout = QVBoxLayout()
        central.setLayout(layout)

        # credentials list widget
        self.credentials_list = ListCredentialsWidget(self)
        layout.addWidget(self.credentials_list)

        # buttons
        add_button = QPushButton("Add New Credential")
        exit_button = QPushButton("Exit")

        # button styling
        add_button.setStyleSheet(Strings.LARGE_BUTTON_STYLE)
        exit_button.setStyleSheet(Strings.LARGE_BUTTON_STYLE)

        layout.addWidget(add_button)
        layout.addWidget(exit_button)

        # Connect buttons
        add_button.clicked.connect(self.open_add_dialog)
        exit_button.clicked.connect(self.close)

    # Open the Add Credentials dialog
    def open_add_dialog(self):
        overlay = QWidget(self)
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")  # translucent overlay
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        overlay.show()
        
        dialog = AddCredentialsDialog(self)  # Pass self as parent so it stays centered
        dialog.adjustSize() 

        #Center dialog relative to main window
        parent_rect = self.frameGeometry()
        dialog_rect = dialog.frameGeometry()

        dialog_rect.moveCenter(parent_rect.center())
        dialog.move(dialog_rect.topLeft())
        dialog.exec()

        overlay.deleteLater()
        self.refresh_credentials()

    def refresh_credentials(self):
        self.credentials_list.load_credentials()
    
    def center(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        screen_center = screen.availableGeometry().center()
        frame_geom = self.frameGeometry()
        frame_geom.moveCenter(screen_center)
        self.move(frame_geom.topLeft())

    # Run the app
    @staticmethod
    def run():
        app = QApplication.instance() or QApplication(sys.argv)
        window = MainWindow()
        window.center()
        window.show()
        window.show()
        window.refresh_credentials()
        app.exec()