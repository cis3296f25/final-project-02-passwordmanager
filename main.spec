# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_all

# Collect all dependencies (binaries, datas, hiddenimports)
argon2_datas, argon2_binaries, argon2_hiddenimports = collect_all('argon2')
cffi_datas, cffi_binaries, cffi_hiddenimports = collect_all('cffi')
pyqt6_datas, pyqt6_binaries, pyqt6_hiddenimports = collect_all('PyQt6')
cryptography_datas, cryptography_binaries, cryptography_hiddenimports = collect_all('cryptography')
flask_datas, flask_binaries, flask_hiddenimports = collect_all('flask')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=argon2_binaries + cffi_binaries + pyqt6_binaries + cryptography_binaries + flask_binaries,
    datas=[
        ('resources/images', 'resources/images'),
        ('passwordmanager/themes', 'passwordmanager/themes'),
    ] + argon2_datas + cffi_datas + pyqt6_datas + cryptography_datas + flask_datas,
    hiddenimports=[
        'argon2',
        'argon2.low_level',
        'argon2._ffi',
        'argon2_cffi_bindings',
        '_argon2_cffi_bindings',
        'cffi',
        'cffi._cffi_backend',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'cryptography',
        'cryptography.fernet',
        'flask',
        'requests',
    ] + argon2_hiddenimports + cffi_hiddenimports + pyqt6_hiddenimports + cryptography_hiddenimports + flask_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['imp', 'PyQt5', 'PySide2', 'PySide6'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="resources\\images\\appIcon.ico"
)
