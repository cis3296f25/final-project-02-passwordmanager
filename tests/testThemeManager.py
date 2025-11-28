import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from passwordmanager.utils.theme_manager import ThemeManager
from resources.colors import Colors


class TestThemeManager(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_path = Path(self.temp_dir) / "test_config.json"
        
    def tearDown(self):
        if self.temp_config_path.exists():
            self.temp_config_path.unlink()
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    @patch('passwordmanager.utils.theme_manager.Path.home')
    def test_init(self, mock_home):
        mock_home.return_value = Path(self.temp_dir)
        m = ThemeManager()
        self.assertEqual(m.current_mode, 'dark')
        self.assertEqual(m.current_theme, 'default')
        self.assertEqual(m.windows, [])
    
    @patch('passwordmanager.utils.theme_manager.Path.home')
    def test_init_loads_theme(self, mock_home):
        mock_home.return_value = Path(self.temp_dir)
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps({'mode': 'light', 'theme': 'default'}))):
                m = ThemeManager()
                m.config_file = self.temp_config_path
                mode, theme = m.load_config()
                m.current_mode = mode
                m.current_theme = theme
        self.assertEqual(m.current_mode, 'light')
        self.assertEqual(m.current_theme, 'default')
    
    @patch('passwordmanager.utils.theme_manager.Path.home')
    def test_init_handles_errors(self, mock_home):
        mock_home.return_value = Path(self.temp_dir)
        with patch.object(Path, 'exists', side_effect=OSError()):
            m = ThemeManager()
            m.config_file = self.temp_config_path
            mode, theme = m.load_config()
            self.assertEqual(mode, 'dark')
            self.assertEqual(theme, 'default')
    
    def test_register_unregister(self):
        m = ThemeManager()
        w = Mock()
        m.register_window(w)
        self.assertIn(w, m.windows)
        m.unregister_window(w)
        self.assertNotIn(w, m.windows)
    
    def test_register_duplicate(self):
        m = ThemeManager()
        w = Mock()
        m.register_window(w)
        m.register_window(w)
        self.assertEqual(len(m.windows), 1)
    
    def test_unregister_not_registered(self):
        m = ThemeManager()
        m.unregister_window(Mock())
        self.assertEqual(len(m.windows), 0)
    
    @patch.object(Path, 'exists')
    def test_load_theme(self, mock_exists):
        mock_exists.return_value = False
        m = ThemeManager()
        m.config_file = self.temp_config_path
        self.assertEqual(m.load_mode(), 'dark')
    
    @patch.object(Path, 'exists')
    def test_load_theme_method(self, mock_exists):
        mock_exists.return_value = False
        m = ThemeManager()
        m.config_file = self.temp_config_path
        self.assertEqual(m.load_theme(), 'default')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_load_theme_from_file(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        # Use mock_open to ensure json.load is called (lines 82-83)
        mock_file_obj = mock_open(read_data=json.dumps({'theme': 'red'}))
        with patch('builtins.open', mock_file_obj):
            result = m.load_theme()
            self.assertEqual(result, 'red')
            # Verify file was opened and json.load was called
            mock_file_obj.assert_called()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_load_theme_from_file_with_theme_key(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        # Test that config.get('theme', 'default') is called (line 83)
        config_data = {'theme': 'green', 'mode': 'light'}
        mock_file_obj = mock_open(read_data=json.dumps(config_data))
        with patch('builtins.open', mock_file_obj):
            result = m.load_theme()
            self.assertEqual(result, 'green')
            # Verify the file was opened
            mock_file_obj.assert_called()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_load_theme_bad_json(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        with patch('builtins.open', mock_open(read_data="bad json")):
            self.assertEqual(m.load_theme(), 'default')
    
    @patch.object(Path, 'exists')
    def test_load_theme_oserror(self, mock_exists):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        with patch('builtins.open', side_effect=OSError()):
            self.assertEqual(m.load_theme(), 'default')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_load_theme_from_file(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        with patch('builtins.open', mock_open(read_data=json.dumps({'mode': 'light'}))):
            self.assertEqual(m.load_mode(), 'light')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_load_theme_bad_json(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        with patch('builtins.open', mock_open(read_data="bad json")):
            self.assertEqual(m.load_mode(), 'dark')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_save_theme(self, mock_exists, mock_file):
        mock_exists.return_value = False
        m = ThemeManager()
        m.config_file = self.temp_config_path
        m.current_mode = 'light'
        with patch('builtins.open', mock_open()) as mo:
            m.save_theme_config()
            mo.assert_called()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_save_theme_existing(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        m.current_mode = 'dark'
        m.current_theme = 'default'
        with patch('builtins.open', mock_open(read_data=json.dumps({'other': 'value'}))):
            with patch('json.dump') as mock_dump:
                m.save_theme_config()
                mock_dump.assert_called()
    
    @patch.object(Path, 'exists')
    def test_save_theme_oserror(self, mock_exists):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        m.current_mode = 'light'
        m.current_theme = 'default'
        with patch('builtins.open', side_effect=OSError()):
            m.save_theme_config()
    
    def test_set_theme(self):
        m = ThemeManager()
        m.save_theme_config = Mock()
        m.apply_theme_to_window = Mock()
        m.set_mode('light')
        self.assertEqual(m.current_mode, 'light')
        m.save_theme_config.assert_called_once()
    
    def test_set_theme_method(self):
        m = ThemeManager()
        m.save_theme_config = Mock()
        m.apply_theme_to_window = Mock()
        m.set_theme('red')
        self.assertEqual(m.current_theme, 'red')
        m.save_theme_config.assert_called_once()
    
    def test_set_theme_invalid(self):
        m = ThemeManager()
        m.save_theme_config = Mock()
        original_theme = m.current_theme
        m.set_theme('invalid')
        self.assertEqual(m.current_theme, original_theme)
        m.save_theme_config.assert_not_called()
    
    def test_set_theme_valid_themes(self):
        m = ThemeManager()
        m.save_theme_config = Mock()
        m.apply_theme_to_window = Mock()
        for theme in ['default', 'red', 'green', 'blue', 'purple']:
            m.set_theme(theme)
            self.assertEqual(m.current_theme, theme)
    
    def test_set_theme_applies_to_windows(self):
        m = ThemeManager()
        m.save_theme_config = Mock()
        m.apply_theme_to_window = Mock()
        w1, w2 = Mock(), Mock()
        m.register_window(w1)
        m.register_window(w2)
        m.set_theme('red')
        self.assertEqual(m.apply_theme_to_window.call_count, 2)
    
    def test_set_theme_handles_runtime_error(self):
        m = ThemeManager()
        m.save_theme_config = Mock()
        w1, w2 = Mock(), Mock()
        m.register_window(w1)
        m.register_window(w2)
        def side_effect(window, mode=None):
            if window == w1:
                raise RuntimeError()
        m.apply_theme_to_window = Mock(side_effect=side_effect)
        m.set_theme('green')
        self.assertNotIn(w1, m.windows)
    
    def test_set_mode_applies_to_windows(self):
        m = ThemeManager()
        m.save_theme_config = Mock()
        m.apply_theme_to_window = Mock()
        w1, w2 = Mock(), Mock()
        m.register_window(w1)
        m.register_window(w2)
        m.set_mode('light')
        self.assertEqual(m.apply_theme_to_window.call_count, 2)
    
    def test_set_mode_handles_runtime_error(self):
        m = ThemeManager()
        m.save_theme_config = Mock()
        w1, w2 = Mock(), Mock()
        m.register_window(w1)
        m.register_window(w2)
        def side_effect(window, mode=None):
            if window == w1:
                raise RuntimeError()
        m.apply_theme_to_window = Mock(side_effect=side_effect)
        m.set_mode('light')
        self.assertNotIn(w1, m.windows)
    
    def test_get_theme_colors(self):
        m = ThemeManager()
        # Test dark mode - should return colors from theme file as-is
        dark_colors = m.get_theme_colors('dark', 'default')
        self.assertEqual(dark_colors['background'], '#1e1e2f')  # From default.json
        # Test light mode - should return inverted colors
        light_colors = m.get_theme_colors('light', 'default')
        self.assertNotEqual(light_colors['background'], dark_colors['background'])
        self.assertTrue(light_colors['background'].startswith('#'))
        # Test invalid mode - defaults to dark
        other_colors = m.get_theme_colors('other', 'default')
        self.assertEqual(other_colors['background'], '#1e1e2f')
    
    def test_get_theme_colors_uses_current(self):
        m = ThemeManager()
        m.current_mode = 'light'
        m.current_theme = 'default'
        # Light mode should return inverted colors from theme file
        colors = m.get_theme_colors()
        self.assertIn('background', colors)
        self.assertTrue(colors['background'].startswith('#'))
        # Should be different from dark mode
        dark_colors = m.get_theme_colors('dark', 'default')
        self.assertNotEqual(colors['background'], dark_colors['background'])
    
    def test_get_theme_colors_light_mode_non_hex_value(self):
        m = ThemeManager()
        # Mock load_theme_file to return theme data with non-hex values
        theme_data = {
            'name': 'test',
            'background': '#1e1e2f',
            'text': '#ffffff',
            'non_hex_string': 'some_value',
            'non_string_value': 123
        }
        with patch.object(m, 'load_theme_file', return_value=theme_data):
            colors = m.get_theme_colors('light', 'default')
            # 'name' should be preserved as-is
            self.assertEqual(colors['name'], 'test')
            # Hex colors should be inverted
            self.assertNotEqual(colors['background'], theme_data['background'])
            # Non-hex strings should be preserved as-is
            self.assertEqual(colors['non_hex_string'], 'some_value')
            # Non-string values should be preserved as-is
            self.assertEqual(colors['non_string_value'], 123)
    
    def test_get_theme_button_styles(self):
        m = ThemeManager()
        with patch.object(m, 'get_theme_colors', return_value={
            'background-button': '#31314d',
            'text': '#ffffff',
            'accent': '#8ACE00',
            'accent_hover': '#6DA400'
        }):
            base, selected = m.get_theme_button_styles('light', 'default')
            self.assertIn('QPushButton', base)
            self.assertIn('#8ACE00', selected)  # accent color
            self.assertIn('#6DA400', selected)  # accent_hover color
    
    def test_get_theme_button_styles_uses_current(self):
        m = ThemeManager()
        m.current_mode = 'dark'
        m.current_theme = 'default'
        base, selected = m.get_theme_button_styles()
        self.assertIn('QPushButton', base)
    
    def test_get_theme_button_styles_with_normalize(self):
        m = ThemeManager()
        m.current_mode = 'light'
        m.current_theme = 'red'
        # Call with None to trigger _normalize_mode_theme
        base, selected = m.get_theme_button_styles(mode=None, theme=None)
        self.assertIn('QPushButton', base)
        self.assertIn('QPushButton', selected)
    
    def test_get_large_button_style_with_normalize(self):
        m = ThemeManager()
        m.current_mode = 'light'
        m.current_theme = 'blue'
        # Call with None to trigger _normalize_mode_theme
        style = m.get_large_button_style(mode=None, theme=None)
        self.assertIn('QPushButton', style)
        self.assertIn('background-color', style)
    
    def test_get_small_button_style_with_normalize(self):
        m = ThemeManager()
        m.current_mode = 'dark'
        m.current_theme = 'green'
        # Call with None to trigger _normalize_mode_theme
        style = m.get_small_button_style(mode=None, theme=None)
        self.assertIn('QPushButton', style)
        self.assertIn('background-color', style)
    
    def test_get_eye_button_style_with_normalize(self):
        m = ThemeManager()
        m.current_mode = 'light'
        m.current_theme = 'purple'
        # Call with None to trigger _normalize_mode_theme
        style = m.get_eye_button_style(mode=None, theme=None)
        self.assertIn('QPushButton', style)
        self.assertIn('border', style)
    
    def test_get_settings_button_style_with_normalize(self):
        m = ThemeManager()
        m.current_mode = 'dark'
        m.current_theme = 'default'
        # Call with None to trigger _normalize_mode_theme
        style = m.get_settings_button_style(mode=None, theme=None)
        self.assertIn('QPushButton', style)
        self.assertIn('background-color', style)
    
    def test_get_delete_button_style(self):
        m = ThemeManager()
        # get_delete_button_style just returns a static style string
        style = m.get_delete_button_style()
        self.assertIsInstance(style, str)
        self.assertIn('QPushButton', style)
        self.assertIn('background-color', style)
        self.assertIn(Colors.RED, style)
        # Test with parameters (they're ignored but should still work)
        style2 = m.get_delete_button_style(mode='light', theme='red')
        self.assertEqual(style, style2)
    
    def test_apply_mainwindow(self):
        m = ThemeManager()
        w = Mock()
        w.__class__.__name__ = 'MainWindow'
        w.setStyleSheet = Mock()
        m.apply_theme_to_window(w, 'light')
        w.setStyleSheet.assert_called_once()
    
    def test_apply_settings_dialog(self):
        m = ThemeManager()
        w = Mock()
        w.__class__.__name__ = 'settingsDialog'
        w.setStyleSheet = Mock()
        w.update_theme_buttons = Mock()
        w.current_mode = None
        m.apply_theme_to_window(w, 'dark')
        w.setStyleSheet.assert_called_once()
        self.assertEqual(w.current_mode, 'dark')
    
    def test_apply_settings_no_update(self):
        m = ThemeManager()
        w = Mock()
        w.__class__.__name__ = 'settingsDialog'
        w.setStyleSheet = Mock()
        m.apply_theme_to_window(w, 'light')
        w.setStyleSheet.assert_called_once()
    
    def test_apply_dialogs(self):
        m = ThemeManager()
        for name in ['AddCredentialsDialog', 'EditCredentialsDialog', 'LoginDialog']:
            w = Mock()
            w.__class__.__name__ = name
            w.setStyleSheet = Mock()
            m.apply_theme_to_window(w, 'dark')
            w.setStyleSheet.assert_called_once()
    
    def test_apply_login_with_button(self):
        m = ThemeManager()
        w = Mock()
        w.__class__.__name__ = 'LoginDialog'
        w.setStyleSheet = Mock()
        w.show_password_button = Mock()
        w.show_password_button.setStyleSheet = Mock()
        m.apply_theme_to_window(w, 'dark')
        w.show_password_button.setStyleSheet.assert_called_once()
    
    def test_apply_list_widget(self):
        m = ThemeManager()
        w = Mock()
        w.__class__.__name__ = 'ListCredentialsWidget'
        w.setStyleSheet = Mock()
        w.scroll_area = Mock()
        w.scroll_area.setStyleSheet = Mock()
        w.credentials_container = Mock()
        w.credentials_container.setStyleSheet = Mock()
        w.load_credentials = Mock()
        m.apply_theme_to_window(w, 'dark')
        w.setStyleSheet.assert_called_once()
        w.load_credentials.assert_called_once()
    
    def test_apply_list_widget_no_load(self):
        m = ThemeManager()
        w = Mock()
        w.__class__.__name__ = 'ListCredentialsWidget'
        w.setStyleSheet = Mock()
        w.scroll_area = Mock()
        w.scroll_area.setStyleSheet = Mock()
        w.credentials_container = Mock()
        w.credentials_container.setStyleSheet = Mock()
        m.apply_theme_to_window(w, 'light')
        w.setStyleSheet.assert_called_once()
    
    def test_apply_unknown(self):
        m = ThemeManager()
        w = Mock()
        w.__class__.__name__ = 'UnknownWindow'
        m.apply_theme_to_window(w, 'dark')
    
    def test_apply_uses_current(self):
        m = ThemeManager()
        m.current_theme = 'light'
        w = Mock()
        w.__class__.__name__ = 'MainWindow'
        w.setStyleSheet = Mock()
        m.apply_theme_to_window(w)
        w.setStyleSheet.assert_called_once()
    
    def test_load_theme_file_success(self):
        m = ThemeManager()
        theme_data = m.load_theme_file('default')
        self.assertIsInstance(theme_data, dict)
        self.assertIn('background', theme_data)
    
    def test_load_theme_file_not_found_fallback(self):
        m = ThemeManager()
        # Load a non-existent theme, should fallback to default
        theme_data = m.load_theme_file('nonexistent')
        # Should return default theme data
        self.assertIsInstance(theme_data, dict)
        self.assertIn('background', theme_data)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_load_theme_file_json_error(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.themes_dir = Path(self.temp_dir)
        with patch('builtins.open', mock_open(read_data="bad json")):
            # Should fallback to default
            theme_data = m.load_theme_file('red')
            # Should return default theme data
            self.assertIsInstance(theme_data, dict)
    
    @patch.object(Path, 'exists')
    def test_load_theme_file_oserror(self, mock_exists):
        mock_exists.return_value = True
        m = ThemeManager()
        m.themes_dir = Path(self.temp_dir)
        with patch('builtins.open', side_effect=OSError()):
            # Should fallback to default
            theme_data = m.load_theme_file('red')
            # Should return default theme data
            self.assertIsInstance(theme_data, dict)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_load_theme_file_default_fails_returns_empty(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.themes_dir = Path(self.temp_dir)
        # Mock open to raise OSError when trying to read default.json
        with patch('builtins.open', side_effect=OSError()):
            # When default theme file fails to load, should return {}
            theme_data = m.load_theme_file('default')
            self.assertEqual(theme_data, {})
