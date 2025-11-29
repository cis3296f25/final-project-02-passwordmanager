# Frontend Quick Reference

## Creating a New Dialog

**Before:**
```python
class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        # ... widgets ...
```

**Now:**
```python
from passwordmanager.utils.theme_manager import theme_manager
from resources.strings import Strings
from PyQt6.QtGui import QIcon

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        theme_manager.register_window(self)
        self.setWindowIcon(QIcon(Strings.WINDOW_ICON_PATH))
        # ... create widgets ...
        theme_manager.apply_theme_to_window(self, theme_manager.current_mode)
```

## Creating Buttons

**Before:**
```python
button = QPushButton("Click")
button.setStyleSheet(Strings.LARGE_BUTTON_STYLE)
```

**Now:**
```python
button = QPushButton("Click")
button.setStyleSheet(theme_manager.get_large_button_style())
```

Button types: `get_large_button_style()`, `get_small_button_style()`, `get_delete_button_style()`, `get_settings_button_style()`

## Storing Buttons

**Before:**
```python
button = QPushButton("Save")
layout.addWidget(button)
```

**Now:**
```python
self.button = QPushButton("Save")  # Store as instance variable
self.button.setStyleSheet(theme_manager.get_large_button_style())
layout.addWidget(self.button)
```

## Window Cleanup

**Before:**
```python
def closeEvent(self, event):
    super().closeEvent(event)
```

**Now:**
```python
def closeEvent(self, event):
    theme_manager.unregister_window(self)
    super().closeEvent(event)
```

## Theme Colors

**Before:**
```python
from resources.colors import Colors
color = Colors.BRAT_GREEN
```

**Now:**
```python
colors = theme_manager.get_theme_colors()
color = colors['accent']
```
