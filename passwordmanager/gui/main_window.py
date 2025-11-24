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

        # Apply initial theme
        self.apply_theme(theme_manager.current_theme)

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
        logout_button = QPushButton("Logout")

        # button styling
        add_button.setStyleSheet(Strings.LARGE_BUTTON_STYLE)
        logout_button.setStyleSheet(Strings.LARGE_BUTTON_STYLE)

        layout.addWidget(add_button)
        layout.addWidget(logout_button)

        # Connect buttons
        add_button.clicked.connect(self.open_add_dialog)
        logout_button.clicked.connect(self.handle_logout)

    def apply_theme(self, theme):
        """Apply theme colors to this window"""
        colors = theme_manager.get_theme_colors(theme)
        self.setStyleSheet(f"background-color: {colors['background']}; color: {colors['text']};")
        
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
        window.show()
        window.refresh_credentials()
        app.exec()