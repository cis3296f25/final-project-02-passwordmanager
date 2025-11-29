import json
import os
import colorsys
from pathlib import Path
from resources.colors import Colors


def invert_color_hsv(hex_color):
    # Remove '#'
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Convert RGB (0-255) to normalized RGB (0.0-1.0)
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0
    
    # Convert RGB to HSV
    # colorsys.rgb_to_hsv returns (H: 0-1, S: 0-1, V: 0-1)
    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    
    # Apply inversion: Keep hue the same, invert saturation and value (brightness)
    h_light = h
    s_light = 1.0 -s
    v_light = 1.0 - v
    
    # Convert HSV back to RGB (0.0-1.0)
    r_norm_light, g_norm_light, b_norm_light = colorsys.hsv_to_rgb(h_light, s_light, v_light)
    
    # Convert normalized RGB (0.0-1.0) back to RGB (0-255)
    r_light = int(round(r_norm_light * 255))
    g_light = int(round(g_norm_light * 255))
    b_light = int(round(b_norm_light * 255))
    
    # Ensure values are in valid range
    r_light = max(0, min(255, r_light))
    g_light = max(0, min(255, g_light))
    b_light = max(0, min(255, b_light))
    
    # Convert RGB to hex
    hex_light = f"#{r_light:02x}{g_light:02x}{b_light:02x}"
    
    return hex_light


class ThemeManager:
    
    def __init__(self):
        self.config_file = Path.home() / ".password_manager_config.json"
        self.themes_dir = Path(__file__).parent.parent / "themes"
        mode, theme = self.load_config()  # Load both at once for efficiency
        self.current_mode = mode  # light or dark
        self.current_theme = theme  # default, red, green, blue, purple
        self.windows = []  # track all windows that need theme updates
        
    def register_window(self, window):
        if window not in self.windows:
            self.windows.append(window)
            
    def unregister_window(self, window):
        if window in self.windows:
            self.windows.remove(window)
    
    def load_mode(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('mode', 'dark')
        except (json.JSONDecodeError, OSError):
            pass
        return 'dark'  # Default to dark mode
    
    def load_theme(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('theme', 'default')
        except (json.JSONDecodeError, OSError):
            pass
        return 'default'  # Default to default theme
    
    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    mode = config.get('mode', 'dark')
                    theme = config.get('theme', 'default')
                    return (mode, theme)
        except (json.JSONDecodeError, OSError):
            pass
        return ('dark', 'default')  # Default values
    
    def load_theme_file(self, theme_name):
        theme_file = self.themes_dir / f"{theme_name}.json"
        
        try:
            if theme_file.exists():
                with open(theme_file, 'r') as f:
                    theme_data = json.load(f)
                    return theme_data
        except (json.JSONDecodeError, OSError):
            pass
        
        if theme_name != 'default':
            return self.load_theme_file('default')
        
        return {}
    
    def save_theme_config(self):
        try:
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            config['mode'] = self.current_mode
            config['theme'] = self.current_theme
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except OSError:
            pass  
    
    def set_mode(self, mode):
        self.current_mode = mode
        self.save_theme_config()
        
        # Apply theme to all registered windows
        for window in self.windows[:]:  
            try:
                self.apply_theme_to_window(window, mode)
            except RuntimeError:
                # Window was deleted, remove from list
                self.windows.remove(window)
    
    def set_theme(self, theme):
        if theme not in ['default', 'red', 'green', 'blue', 'purple']:
            return
            
        self.current_theme = theme
        self.save_theme_config()
        
        # Apply theme to all registered windows
        for window in self.windows[:]:  
            try:
                self.apply_theme_to_window(window, self.current_mode)
            except RuntimeError:
                # Window was deleted, remove from list
                self.windows.remove(window)
    
    def _normalize_mode_theme(self, mode=None, theme=None):
        # Helper to normalize mode and theme parameters to current values
        if mode is None:
            mode = self.current_mode
        if theme is None:
            theme = self.current_theme
        return mode, theme
    
    def get_theme_colors(self, mode=None, theme=None):
        mode, theme = self._normalize_mode_theme(mode, theme)
        
        # Load theme file
        theme_data = self.load_theme_file(theme)
        
        # If mode is light, apply color inversion
        if mode == 'light':
            colors = {}
            # First pass: process all colors except accent_hover
            for key, value in theme_data.items():
                if key == 'name':
                    colors[key] = value
                elif key == 'accent_hover':
                    # Skip for now, process after accent
                    continue
                elif isinstance(value, str) and value.startswith('#'):
                    # Special handling for default theme - white background with unchanged brat green
                    if theme == 'default':
                        if key in ['background', 'background-button', 'input_bg', 'card_bg', 'pressed_card_bg']:
                            # Make backgrounds white/light
                            if key == 'background':
                                colors[key] = '#ffffff'
                            elif key == 'background-button':
                                colors[key] = '#f0f0f0'
                            elif key == 'input_bg':
                                colors[key] = '#f0f0f0'
                            elif key == 'card_bg':
                                colors[key] = '#f0f0f0'
                            elif key == 'pressed_card_bg':
                                colors[key] = '#e0e0e0'
                        elif key == 'text' or key == 'input_text':
                            # Make text dark
                            colors[key] = '#000000'
                        else:
                            # Keep accent colors unchanged (brat green stays brat green)
                            colors[key] = value
                    else:
                        # For other themes, use HSV inversion for backgrounds/text
                        # But keep accent colors unchanged so buttons remain visible
                        if key in ['accent', 'accent_hover', 'accent_pressed']:
                            # Keep original bright accent colors for buttons in light mode
                            colors[key] = value
                        else:
                            # Invert backgrounds, text, inputs, etc.
                            colors[key] = invert_color_hsv(value)
                else:
                    colors[key] = value
            
            # Second pass: process accent_hover for non-default themes
            if theme != 'default' and 'accent' in colors and 'accent_hover' in theme_data:
                accent_hex = colors['accent'].lstrip('#')
                accent_r = int(accent_hex[0:2], 16)
                accent_g = int(accent_hex[2:4], 16)
                accent_b = int(accent_hex[4:6], 16)
                # Darken by 15% for hover effect
                new_r = max(0, min(255, int(accent_r * 0.85)))
                new_g = max(0, min(255, int(accent_g * 0.85)))
                new_b = max(0, min(255, int(accent_b * 0.85)))
                colors['accent_hover'] = f"#{new_r:02x}{new_g:02x}{new_b:02x}"
            elif theme == 'default' and 'accent_hover' in theme_data:
                # For default theme, keep accent_hover unchanged
                colors['accent_hover'] = theme_data['accent_hover']
            
            # Post-process for purple theme to fix bright pink issue
            if theme == 'purple':
                # Adjust purple colors to be less pink/more purple in light mode
                for bg_key in ['background', 'background-button', 'input_bg', 'card_bg', 'pressed_card_bg']:
                    if bg_key in colors:
                        bg_hex = colors[bg_key].lstrip('#')
                        bg_r = int(bg_hex[0:2], 16)
                        bg_g = int(bg_hex[2:4], 16)
                        bg_b = int(bg_hex[4:6], 16)
                        # Reduce red component significantly, keep green/blue more balanced
                        new_r = max(0, min(255, int(bg_r * 0.6)))
                        new_g = max(0, min(255, int(bg_g * 0.95)))
                        new_b = max(0, min(255, int(bg_b * 1.05)))
                        colors[bg_key] = f"#{new_r:02x}{new_g:02x}{new_b:02x}"
            
            return colors
        else:
            # Return dark mode colors as-is from theme file
            return theme_data

    def get_theme_button_styles(self, mode=None, theme=None):
        mode, theme = self._normalize_mode_theme(mode, theme)
        colors = self.get_theme_colors(mode, theme)
        
        base_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            color: {colors['text']};
            border: 2px solid {colors['background-button']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
        }}
        """
        
        selected_style = f"""
        QPushButton {{
            background-color: {colors['background-button']};
            color: {colors['text']};
            border: 2px solid {colors['accent']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
        }}
        """
        
        return base_style, selected_style
    
    def get_large_button_style(self, mode=None, theme=None):
        # Generate large button style using current theme colors
        mode, theme = self._normalize_mode_theme(mode, theme)
        colors = self.get_theme_colors(mode, theme)
        
        # Use dark text on bright accent buttons for readability
        # Check if accent is bright (sum > 400) to determine text color
        accent_hex = colors['accent'].lstrip('#')
        accent_r = int(accent_hex[0:2], 16)
        accent_g = int(accent_hex[2:4], 16)
        accent_b = int(accent_hex[4:6], 16)
        accent_brightness = accent_r + accent_g + accent_b
        text_color = '#000000' if accent_brightness > 400 else colors['text']
        
        return f"""
        QPushButton {{
            background-color: {colors['accent']};
            color: {text_color};
            font-weight: 600;
            border-radius: 10px;
            padding: 8px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
        }}
        QPushButton:pressed {{
            border: 2px solid {colors['accent_pressed']};
        }}
        """
    
    def get_small_button_style(self, mode=None, theme=None):
        # Generate small button style using current theme colors
        mode, theme = self._normalize_mode_theme(mode, theme)
        colors = self.get_theme_colors(mode, theme)
        
        # Use dark text on bright accent buttons for readability
        # Check if accent is bright (sum > 400) to determine text color
        accent_hex = colors['accent'].lstrip('#')
        accent_r = int(accent_hex[0:2], 16)
        accent_g = int(accent_hex[2:4], 16)
        accent_b = int(accent_hex[4:6], 16)
        accent_brightness = accent_r + accent_g + accent_b
        text_color = '#000000' if accent_brightness > 400 else colors['text']
        
        return f"""
        QPushButton {{
            background-color: {colors['accent']};
            color: {text_color};
            font-weight: 600;
            border-radius: 6px;
            padding: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
        }}
        QPushButton:pressed {{
            border: 2px solid {colors['accent_pressed']};
        }}
        """
    
    def get_delete_button_style(self, mode=None, theme=None): # always uses red, not theme colors
        return f"""
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
    
    def get_eye_button_style(self, mode=None, theme=None):
        # Generate eye button style using current theme colors
        mode, theme = self._normalize_mode_theme(mode, theme)
        colors = self.get_theme_colors(mode, theme)
        
        return f"""
        QPushButton {{
            border: 1px solid {colors['accent']};
            padding: 5px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
        }}
        """
    
    def get_settings_button_style(self, mode=None, theme=None):
        # Generate settings button style using current theme colors
        mode, theme = self._normalize_mode_theme(mode, theme)
        colors = self.get_theme_colors(mode, theme)
        
        return f"""
        QPushButton {{
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
            color: {colors['text']};
        }}
        """

    def apply_theme_to_window(self, window, mode=None, theme=None):
        if mode is None:
            mode = self.current_mode
        if theme is None:
            theme = self.current_theme
            
        colors = self.get_theme_colors(mode, theme)
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
            # Update large buttons when theme changes
            if hasattr(window, 'add_button'):
                window.add_button.setStyleSheet(self.get_large_button_style(mode, theme))
            if hasattr(window, 'logout_button'):
                window.logout_button.setStyleSheet(self.get_large_button_style(mode, theme))
            
        elif window_class_name == "settingsDialog":
            window.setStyleSheet(f"""
            QDialog {{ {base_style} }}
            {label_style}
            {input_style}
            """)
            # Update close button when theme changes
            if hasattr(window, 'close_button'):
                window.close_button.setStyleSheet(self.get_large_button_style(mode, theme))
            if hasattr(window, 'update_theme_buttons'):
                window.current_mode = mode
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
            
            # Update filter and settings buttons when theme changes
            if hasattr(window, 'filter_button'):
                window.filter_button.setStyleSheet(self.get_small_button_style(mode, theme))
            if hasattr(window, 'settings_button'):
                window.settings_button.setStyleSheet(self.get_small_button_style(mode, theme))
            
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
                    border: 2px solid {colors['accent']};
                    padding: 7px;
                }}
                QLineEdit:hover {{
                    background-color: {colors['input_bg']};
                    border: 1px solid {colors['accent_hover']};
                }}
                QLineEdit:hover:focus {{
                    border: 2px solid {colors['accent']};
                    padding: 7px;
                }}
                """)
            
            if hasattr(window, 'load_credentials'):
                window.load_credentials()

theme_manager = ThemeManager()