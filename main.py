from gui import MainWindow
import requests
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

    MainWindow.run()

    
