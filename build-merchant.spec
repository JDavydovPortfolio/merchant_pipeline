# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Define the main script
main_script = 'main.py'

# Data files to include
added_files = [
    ('input', 'input'),
    ('samples', 'samples'),
]

# Hidden imports needed for the application
hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'pytesseract',
    'cv2',
    'PIL',
    'PIL.Image',
    'pdf2image',
    'requests',
    'numpy',
    'qtawesome',
    'qdarkstyle',
    'pyqtgraph',
]

# Analysis phase
a = Analysis(
    [main_script],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MerchantProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/app_icon.ico' if Path('resources/app_icon.ico').exists() else None,
    version='version_info.txt' if Path('version_info.txt').exists() else None,
)