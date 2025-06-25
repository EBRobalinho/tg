# stcad.spec
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['src/stcad.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules("back"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtMultimedia',
        'PySide6.QtWebEngine',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.QtQuick',
        'PySide6.QtQml',
        'tkinter',
	'scypy'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='stcad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # sem UPX como solicitado
    console=False,  # mude para True se quiser ver terminal
    icon='assets/imagem_icon/icon_stcad.ico',

)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='stcad'
)
