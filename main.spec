# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# --- Zbieranie wszystkich niezbędnych plików danych ---
datas = []
datas += collect_data_files('sv_ttk')
datas += collect_data_files('matplotlib')
datas += collect_data_files('pandas')
datas += collect_data_files('pytz')
datas += collect_data_files('tzdata')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    # --- Uwzględnienie wszystkich potencjalnie ukrytych importów ---
    hiddenimports=[
        'pandas', 'matplotlib.backends.backend_tkagg',
        'pytz', 'babel.numbers', 'sv_ttk', 'yfinance', 'instruments'
    ],
    hookspath=[],
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
    name='PortfolioManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # --- Kluczowa zmiana: tworzymy jeden plik, nie katalog ---
    runtime_tmpdir=None,
    # --- Wyłączamy konsolę dla finalnej wersji ---
    console=False,
    icon=None, # Tutaj można dodać ścieżkę do własnej ikony .ico
)