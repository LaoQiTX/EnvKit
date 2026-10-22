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
a.binaries = [
    x for x in a.binaries
    if not x[0].lower().startswith('msvcp140')
    and not x[0].lower().startswith('vcruntime140')
]
pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EnvKit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
