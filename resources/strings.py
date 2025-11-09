from resources.colors import Colors

class Strings:
    APP_NAME = "Offline Password Manager"

    # image paths
    WINDOW_ICON_PATH = "resources/images/windowIcon.png"
    DELETE_ICON_PATH = "resources/images/deleteButtonIcon.png"
    EDIT_ICON_PATH = "resources/images/editButtonIcon.png"
    COPY_ICON_PATH = "resources/images/copyButtonIcon.png"
    

    # style sheets:
    LARGE_BUTTON_STYLE = f"""
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
    SMALL_BUTTON_STYLE = f"""
            QPushButton {{
                background-color: {Colors.BRAT_GREEN};
                color: {Colors.WHITE};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
            }}
        """
    DELETE_BUTTON_STYLE = f"""
            QPushButton {{
                background-color: {Colors.RED};
                color: {Colors.WHITE};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.RED_BUTTON_HOVER};
            }}
        """
