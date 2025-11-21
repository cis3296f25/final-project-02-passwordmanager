import json
import os
from pathlib import Path
from resources.colors import Colors

class ThemeManager:
    
    def __init__(self):
        self.config_file = Path.home() / ".password_manager_config.json"
        self.current_theme = self.load_theme()
        self.windows = []  # track all windows that need theme updates
        
    def register_window(self, window):
        if window not in self.windows:
            self.windows.append(window)
            
    def unregister_window(self, window):
        if window in self.windows:
            self.windows.remove(window)
    
    def load_theme(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('theme', 'dark')
        except (json.JSONDecodeError, OSError):
            pass
        return 'dark'  # Default to dark theme
    
    def save_theme(self, theme):
        try:
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            config['theme'] = theme
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except OSError:
            pass  
    
    def set_theme(self, theme):
        if theme not in ['light', 'dark']:
            return
            
        self.current_theme = theme
        self.save_theme(theme)
        
        # Apply theme to all registered windows
        for window in self.windows[:]:  
            try:
                self.apply_theme_to_window(window, theme)
            except RuntimeError:
                # Window was deleted, remove from list
                self.windows.remove(window)
    
    def get_theme_colors(self, theme=None):
        if theme is None:
            theme = self.current_theme
            
        if theme == 'light':
            return {
                'background': Colors.OFF_WHITE,
                'background-button': Colors.SUPER_LIGHT_GREY,
                'text': Colors.BLACK,
                'input_bg': Colors.WHITE,
                'input_text': Colors.BLACK,
                'card_bg': Colors.SUPER_LIGHT_GREY,
            }
        else: 
            return {
                'background': Colors.DARK_GREY,
                'background-button': Colors.LIGHT_GREY,
                'text': Colors.WHITE,
                'input_bg': Colors.LIGHT_GREY,
                'input_text': Colors.WHITE,
                'card_bg': Colors.LIGHT_GREY,
            }

    def get_theme_button_styles(self, theme=None):
        if theme is None:
            theme = self.current_theme
        
        colors = self.get_theme_colors(theme)
        
        base_style = f"""
        QPushButton {{
            background-color: {colors['button_bg']};
            color: {colors['text']};
            border: 2px solid {colors['button_bg']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
        }}
        """
        
        selected_style = f"""
        QPushButton {{
            background-color: {colors['button_bg']};
            color: {colors['text']};
            border: 2px solid {Colors.BRAT_GREEN};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {Colors.BRAT_GREEN_BUTTON_HOVER};
        }}
        """
        
        return base_style, selected_style

    def apply_theme_to_window(self, window, theme=None):
        if theme is None:
            theme = self.current_theme
            
        colors = self.get_theme_colors(theme)
        window_class_name = window.__class__.__name__
        
        base_style = f"""
        background-color: {colors['background']};
        color: {colors['text']};
        """
        
        input_style = f"""
        QLineEdit {{
            background-color: {colors['input_bg']};
            color: {colors['input_text']};
            padding: 5px;
            border-radius: 4px;
        }}
        QLineEdit:hover {{
            background-color: {colors['input_bg']};
        }}
        """
        
        label_style = f"""
        QLabel {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        """
        
        if window_class_name == "MainWindow":
            window.setStyleSheet(base_style)
            
        elif window_class_name == "settingsDialog":
            window.setStyleSheet(f"""
            QDialog {{ {base_style} }}
            {label_style}
            {input_style}
            """)
            if hasattr(window, 'update_theme_buttons'):
                window.current_theme = theme
                window.update_theme_buttons()
                window.update_button_theme()
                
        elif window_class_name in ["AddCredentialsDialog", "EditCredentialsDialog", "LoginDialog", "ChangePasswordWindow"]:
            window.setStyleSheet(f"""
            QDialog {{ {base_style} }}
            {label_style}
            {input_style}
            """)
            
            if hasattr(window, 'show_password_button'):
                window.show_password_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {colors['text']};
                        border: none;
                        padding: 0;
                        font-size: 14px;
                    }}
                """)
                
        elif window_class_name == "ListCredentialsWidget":
            window.setStyleSheet(f"""
            QWidget {{ {base_style} }}
            """)
            
            window.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors['background']};
                border: none;
            }}
            """)
            
            window.credentials_container.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['background']};
            }}
            """)
            
            if hasattr(window, 'search_bar'):
                window.search_bar.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {colors['input_bg']};
                    color: {colors['input_text']};
                    padding: 8px;
                    border-radius: 6px;
                    font-size: 14px;
                }}
                QLineEdit:focus {{
                    background-color: {colors['input_bg']};
                    color: {colors['input_text']};
                    border: 2px solid {Colors.BRAT_GREEN};
                    padding: 7px;
                }}
                QLineEdit:hover {{
                    background-color: {colors['input_bg']};
                    border: 1px solid {Colors.BRAT_GREEN_BUTTON_HOVER};
                }}
                QLineEdit:hover:focus {{
                    border: 2px solid {Colors.BRAT_GREEN};
                    padding: 7px;
                }}
                """)
            
            if hasattr(window, 'load_credentials'):
                window.load_credentials()

theme_manager = ThemeManager()