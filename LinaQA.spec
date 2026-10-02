# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('PylinaQA')


a = Analysis(
    ['LinaQA\\LinaQA.pyw'],
    pathex=['LinaQA', 'LinaQA\\PylinaQA'],
    binaries=[],
    datas=[
		('html','html'),
		('readme.txt', '.'),
		('licence.txt', '.'),
		('credits.txt', '.'),
		('LinaQA\\Icons\\LinacToolkit.png', 'Icons')],
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
    name='LinaQA',
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
    icon=['LinaQA\\Icons\\LinacToolkit.png'],
)
