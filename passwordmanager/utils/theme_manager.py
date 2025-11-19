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
                if hasattr(window, 'apply_theme'):
                    window.apply_theme(theme)
            except RuntimeError:
                # Window was deleted, remove from list
                self.windows.remove(window)
    
    def get_theme_colors(self, theme=None):
        if theme is None:
            theme = self.current_theme
            
        if theme == 'light':
            return {
                'background': Colors.OFF_WHITE,
                'text': Colors.BLACK,
                'input_bg': Colors.WHITE,
                'input_text': Colors.BLACK,
                'background-button': Colors.SUPER_LIGHT_GREY,
            }
        else: 
            return {
                'background': Colors.DARK_GREY,
                'background-button': Colors.LIGHT_GREY,
                'text': Colors.WHITE,
                'input_bg': Colors.LIGHT_GREY,
                'input_text': Colors.WHITE
            }

theme_manager = ThemeManager()