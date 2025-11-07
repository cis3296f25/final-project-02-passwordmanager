from gui import MainWindow
from login import LoginDialog
from PyQt6.QtWidgets import QApplication, QDialog
import sys
import threading
import time
from passwordManager import app

#####
# Main entry point for PasswordManager GUI application
#####

if __name__ == "__main__":
    server = threading.Thread(target=app.run, daemon=True, kwargs={'port': 5000})
    server.start()

    time.sleep(1)

    qt_app = QApplication(sys.argv)
    login = LoginDialog()
    result = login.exec()
    if result == QDialog.DialogCode.Accepted:
        MainWindow.run()
    else:
        sys.exit(0)
