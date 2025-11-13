import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from listCredentialsWidget import ListCredentialsWidget

app = QApplication([])

class TestListCredentialsWidget(unittest.TestCase):

    # mocks a get all response containing one credential, confirms credentials are loaded into
    # the ListCredentialsWidget
    @patch("apiCallerMethods.get_all_credentials", return_value=[
        {"id": 1, "site": "example.com", "username": "user", "password": "123"}
    ])
    def test_load_credentials_adds_card(self, mock_get):
        widget = ListCredentialsWidget()
        widget.load_credentials()
        self.assertGreater(widget.credentials_layout.count(), 0)

    # mocks a get all response containing no credentials, confirms no credentials are loaded into
    # the ListCredentialsWidget
    @patch("apiCallerMethods.get_all_credentials", return_value=[])
    def test_load_credentials_no_credentials(self, mock_get):
        widget = ListCredentialsWidget()
        widget.load_credentials()
        self.assertEqual(widget.credentials_layout.count(), 1)
        label = widget.credentials_layout.itemAt(0).widget()
        self.assertIn("No credentials", label.text())

    # confirms a generic string is copied to keyboard with the copy_to_keyboard function
    def test_copy_to_clipboard(self):
        widget = ListCredentialsWidget()
        widget.copy_to_clipboard("test")
        self.assertEqual(app.clipboard().text(), "test")


if __name__ == "__main__":
    unittest.main()
