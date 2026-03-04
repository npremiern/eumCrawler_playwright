# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

block_cipher = None

# Find playwright driver
playwright_driver = None
try:
    import playwright
    playwright_path = Path(playwright.__file__).parent
    driver_path = playwright_path / 'driver'

    # Find the driver executable
    if sys.platform == 'win32':
        driver_files = list(driver_path.glob('**/*.exe'))
    else:
        driver_files = list(driver_path.glob('**/node'))

    if driver_files:
        playwright_driver = [(str(f), 'playwright/driver') for f in driver_files if f.is_file()]
except Exception as e:
    print(f"Warning: Could not locate playwright driver: {e}")

# Collect all playwright driver files
playwright_binaries = []
if playwright_driver:
    playwright_binaries.extend(playwright_driver)

a = Analysis(
    ['../src/crawler.py'],
    pathex=['../src'],
    binaries=playwright_binaries,
    datas=[],
    hiddenimports=[
        'playwright',
        'playwright.sync_api',
        'playwright._impl._driver',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.cell._writer',
        'click',
        'rich',
        'rich.console',
        'rich.progress',
        'rich.panel',
        'rich.table',
        'PIL',
        'PIL.Image',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='crawler',
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
)
