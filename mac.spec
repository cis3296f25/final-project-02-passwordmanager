# -*- mode: python ; coding: utf-8 -*-

#FOR MAC EXECUTABLES
import os
from PyInstaller.utils.hooks import collect_all

# Collect all dependencies (binaries, datas, hiddenimports)
argon2_datas, argon2_binaries, argon2_hiddenimports = collect_all('argon2')
cffi_datas, cffi_binaries, cffi_hiddenimports = collect_all('cffi')
pyqt6_datas, pyqt6_binaries, pyqt6_hiddenimports = collect_all('PyQt6')
cryptography_datas, cryptography_binaries, cryptography_hiddenimports = collect_all('cryptography')
flask_datas, flask_binaries, flask_hiddenimports = collect_all('flask')

# Get absolute project root
project_root = os.path.abspath(os.getcwd())
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[os.getcwd()],
    binaries=[],   
    datas=[
    (os.path.join(os.getcwd(), 'resources/images'), 'resources/images'),
    (os.path.join(os.getcwd(), 'passwordmanager/themes'), 'passwordmanager/themes'),], 
    hiddenimports=[], 
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['imp', 'PyQt5', 'PySide2', 'PySide6'],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PasswordManager',
    debug=False,
    strip=False,
    upx=False,                  
    console=False,
    windowed=True,               
    runtime_tmpdir=None, 
)
app = BUNDLE(
    exe,
    name='PasswordManager.app',
    icon=os.path.join(os.getcwd(), "resources/images/appIcon.icns")
)
