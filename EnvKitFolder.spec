# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

a = Analysis(
    ['EnvKit/main.py'],
    pathex=['EnvKit'],
    binaries=[],
    datas=[
        ('EnvKit/models/model_config.json', 'models'),
        ('EnvKit/skills', 'skills')
    ],
    hiddenimports=[
        'dearpygui',
        'dearpygui.dearpygui',
        'tkinter',
        'tkinter.filedialog',
        'ctypes',
        'ctypes.wintypes',
        'winreg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EnvKitFolder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EnvKitFolder',
)
