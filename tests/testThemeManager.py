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
        self.assertEqual(m.current_theme, 'dark')
        self.assertEqual(m.windows, [])
    
    @patch('passwordmanager.utils.theme_manager.Path.home')
    def test_init_loads_theme(self, mock_home):
        mock_home.return_value = Path(self.temp_dir)
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps({'theme': 'light'}))):
                m = ThemeManager()
                m.config_file = self.temp_config_path
                m.current_theme = m.load_theme()
        self.assertEqual(m.current_theme, 'light')
    
    @patch('passwordmanager.utils.theme_manager.Path.home')
    def test_init_handles_errors(self, mock_home):
        mock_home.return_value = Path(self.temp_dir)
        with patch.object(Path, 'exists', side_effect=OSError()):
            m = ThemeManager()
            m.config_file = self.temp_config_path
            self.assertEqual(m.load_theme(), 'dark')
    
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
        self.assertEqual(m.load_theme(), 'dark')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_load_theme_from_file(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        with patch('builtins.open', mock_open(read_data=json.dumps({'theme': 'light'}))):
            self.assertEqual(m.load_theme(), 'light')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_load_theme_bad_json(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        with patch('builtins.open', mock_open(read_data="bad json")):
            self.assertEqual(m.load_theme(), 'dark')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_save_theme(self, mock_exists, mock_file):
        mock_exists.return_value = False
        m = ThemeManager()
        m.config_file = self.temp_config_path
        with patch('builtins.open', mock_open()) as mo:
            m.save_theme('light')
            mo.assert_called()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(Path, 'exists')
    def test_save_theme_existing(self, mock_exists, mock_file):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        with patch('builtins.open', mock_open(read_data=json.dumps({'other': 'value'}))):
            with patch('json.dump') as mock_dump:
                m.save_theme('dark')
                mock_dump.assert_called()
    
    @patch.object(Path, 'exists')
    def test_save_theme_oserror(self, mock_exists):
        mock_exists.return_value = True
        m = ThemeManager()
        m.config_file = self.temp_config_path
        with patch('builtins.open', side_effect=OSError()):
            m.save_theme('light')
    
    def test_set_theme(self):
        m = ThemeManager()
        m.save_theme = Mock()
        m.apply_theme_to_window = Mock()
        m.set_theme('light')
        self.assertEqual(m.current_theme, 'light')
        m.save_theme.assert_called_once_with('light')
    
    def test_set_theme_invalid(self):
        m = ThemeManager()
        m.save_theme = Mock()
        m.set_theme('invalid')
        m.save_theme.assert_not_called()
    
    def test_set_theme_applies_to_windows(self):
        m = ThemeManager()
        m.save_theme = Mock()
        m.apply_theme_to_window = Mock()
        w1, w2 = Mock(), Mock()
        m.register_window(w1)
        m.register_window(w2)
        m.set_theme('light')
        self.assertEqual(m.apply_theme_to_window.call_count, 2)
    
    def test_set_theme_handles_runtime_error(self):
        m = ThemeManager()
        m.save_theme = Mock()
        w1, w2 = Mock(), Mock()
        m.register_window(w1)
        m.register_window(w2)
        def side_effect(window, theme=None):
            if window == w1:
                raise RuntimeError()
        m.apply_theme_to_window = Mock(side_effect=side_effect)
        m.set_theme('light')
        self.assertNotIn(w1, m.windows)
    
    def test_get_theme_colors(self):
        m = ThemeManager()
        self.assertEqual(m.get_theme_colors('light')['background'], Colors.OFF_WHITE)
        self.assertEqual(m.get_theme_colors('dark')['background'], Colors.DARK_GREY)
        self.assertEqual(m.get_theme_colors('other')['background'], Colors.DARK_GREY)
    
    def test_get_theme_colors_uses_current(self):
        m = ThemeManager()
        m.current_theme = 'light'
        self.assertEqual(m.get_theme_colors()['background'], Colors.OFF_WHITE)
    
    def test_get_theme_button_styles(self):
        m = ThemeManager()
        with patch.object(m, 'get_theme_colors', return_value={'button_bg': Colors.LIGHT_GREY, 'text': Colors.WHITE}):
            base, selected = m.get_theme_button_styles('light')
            self.assertIn('QPushButton', base)
            self.assertIn(Colors.BRAT_GREEN, selected)
    
    def test_get_theme_button_styles_uses_current(self):
        m = ThemeManager()
        m.current_theme = 'dark'
        base, selected = m.get_theme_button_styles()
        self.assertIn('QPushButton', base)
    
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
        w.current_theme = None
        m.apply_theme_to_window(w, 'dark')
        w.setStyleSheet.assert_called_once()
        self.assertEqual(w.current_theme, 'dark')
    
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
