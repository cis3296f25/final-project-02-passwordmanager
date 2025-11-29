from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel,
    QDialog, QLineEdit, QFormLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QIcon
import sys
from passwordmanager.api import apiCallerMethods
from passwordmanager.utils.theme_manager import theme_manager
from resources.colors import Colors
from resources.strings import Strings
from passwordmanager.gui.widgets.listCredentialsWidget import ListCredentialsWidget
from passwordmanager.gui.widgets.addCredentialsDialog import AddCredentialsDialog
from passwordmanager.gui.login_dialogue import LoginDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Register with theme manager
        theme_manager.register_window(self)

        # set window
        self.setWindowTitle(Strings.APP_NAME)
        self.setWindowIcon(QIcon(Strings.WINDOW_ICON_PATH))
        self.setGeometry(200, 200, 475, 400)  # x, y, width, height
        self.setMinimumWidth(520)
        self.setMinimumHeight(575)

        # set central widget (similar to panels in jpanel)
        central = QWidget()
        self.setCentralWidget(central)

        # layout for central widget
        layout = QVBoxLayout()
        central.setLayout(layout)

        # credentials list widget
        self.credentials_list = ListCredentialsWidget(self)
        layout.addWidget(self.credentials_list)

        # buttons - store as instance variables so we can update them when theme changes
        self.add_button = QPushButton("Add New Credential")
        self.logout_button = QPushButton("Logout")

        # button styling
        self.add_button.setStyleSheet(theme_manager.get_large_button_style())
        self.logout_button.setStyleSheet(theme_manager.get_large_button_style())

        layout.addWidget(self.add_button)
        layout.addWidget(self.logout_button)

        # Connect buttons
        self.add_button.clicked.connect(self.open_add_dialog)
        self.logout_button.clicked.connect(self.handle_logout)
        
        # Apply initial theme after all widgets are created
        theme_manager.apply_theme_to_window(self, theme_manager.current_mode)
        
    def closeEvent(self, event):
        """Clean up when window is closed"""
        theme_manager.unregister_window(self)
        super().closeEvent(event)
        
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
        result = dialog.exec()

        overlay.deleteLater()
        
        # Only refresh if dialog closed with accept() (i.e., successful save)
        if result == QDialog.DialogCode.Accepted:
            self.refresh_credentials()

    def refresh_credentials(self):
        self.credentials_list.load_credentials()
    
    def handle_logout(self):
        apiCallerMethods.account_logout()
        self.hide()
        login = LoginDialog()
        result = login.exec()
        if result == QDialog.DialogCode.Accepted:
            # Reapply theme when showing window after login to ensure correct mode
            theme_manager.apply_theme_to_window(self, theme_manager.current_mode)
            self.show()
            self.refresh_credentials()
        else:
            self.close()
    
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
        # Ensure theme is applied correctly when window is shown
        theme_manager.apply_theme_to_window(window, theme_manager.current_mode)
        window.show()
        window.refresh_credentials()
        app.exec()