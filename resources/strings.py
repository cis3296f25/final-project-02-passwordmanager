import os
import sys

from resources.colors import Colors

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class Strings:
    APP_NAME = "Offline Password Manager"

    # image paths
    WINDOW_ICON_PATH = get_resource_path("resources/images/windowIcon.png")
    DELETE_ICON_PATH = get_resource_path("resources/images/deleteButtonIcon.png")
    EDIT_ICON_PATH = get_resource_path("resources/images/editButtonIcon.png")
    COPY_ICON_PATH = get_resource_path("resources/images/copyButtonIcon.png")
    CHECK_ICON_PATH = get_resource_path("resources/images/checkButtonIcon.png")
    
    # style sheets:
    LARGE_BUTTON_STYLE = f"""
            QPushButton {{
                background-color: {Colors.BRAT_GREEN};
                color: {Colors.BLACK};
                font-weight: 600;
                border-radius: 10px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            }}
            QPushButton:pressed {{
                border: 2px solid {Colors.BRAT_GREEN_BUTTON_PRESSED};
            }}
        """
    button_style = f"""
        QPushButton {{
            background-color: {Colors.BRAT_GREEN};
            color: {Colors.WHITE};
            border-radius: 10px;
            padding: 6px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
        }}
    """
    SMALL_BUTTON_STYLE = f"""
            QPushButton {{
                background-color: {Colors.BRAT_GREEN};
                color: {Colors.BLACK};
                font-weight: 600;
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            }}
            QPushButton:pressed {{
                border: 2px solid {Colors.BRAT_GREEN_BUTTON_PRESSED};
            }}
        """
    DELETE_BUTTON_STYLE = f"""
            QPushButton {{
                background-color: {Colors.RED};
                color: {Colors.BLACK};
                font-weight: 600;
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.RED_BUTTON_HOVER};
            }}
            QPushButton:pressed {{
                border: 2px solid {Colors.RED_BUTTON_PRESSED};
            }}
        """
    EYE_BUTTON_STYLE = f"""
            QPushButton {{
                border: 1px solid {Colors.BRAT_GREEN};
                padding: 5px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            }}
            """
