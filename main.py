from gui import MainWindow
import requests
import threading
import time
from passwordManager import app

#####
# Main entry point for PasswordManager GUI application
#####
threading.Thread(target=app.run, kwargs={'port': 5000}, daemon=True).start()
time.sleep(1)

if __name__ == "__main__":
    MainWindow = MainWindow()
