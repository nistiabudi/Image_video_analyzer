# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_all

datas = [('D:\\MyCode\\Image_video_analyzer\\assets', 'assets')]
binaries = [('D:\\MyCode\\Image_video_analyzer\\assets', 'assets')]
hiddenimports = ['PIL._tkinter', 'google.generativeai']
datas += collect_data_files('google.generativeai')
tmp_ret = collect_all('PIL')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['D:\\MyCode\\Image_video_analyzer\\src\\main.py'],
    pathex=['D:\\MyCode\\Image_video_analyzer\\src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='AnalyzerAppUpdated',
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
    icon=['D:\\MyCode\\Image_video_analyzer\\assets\\icon.ico'],
)
