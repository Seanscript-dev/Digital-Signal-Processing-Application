# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_dynamic_libs

HERE = Path('.')

cv2_binaries = collect_dynamic_libs('cv2')

datas = [
    (str(HERE / 'icons'), 'icons'),
    (str(HERE / 'filtered_audio'), 'filtered_audio'),
    (str(HERE / 'filtered_images'), 'filtered_images'),
    (str(HERE / 'labs'), 'labs'),
    (str(HERE / 'ui'), 'ui'),
    (str(HERE / 'controller'), 'controller'),
    (str(HERE / 'core'), 'core'),
    (str(HERE / 'requirements.txt'), '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=cv2_binaries,
    datas=datas,
    hiddenimports=['cv2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='DSPulse Studio',
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
    icon=['icons\\logoo.png'],
)
