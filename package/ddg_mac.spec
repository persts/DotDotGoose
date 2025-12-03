# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# 1. Dynamic Root Path (Allows building on any machine)
# Since this spec is in 'package/', the root is one level up.
root_path = os.path.abspath('..')

# 2. Collect Hidden Imports
# We explicitly collect PyQt6. 
# We also ensure torch and cv2 are found since we are now IMPORTING them.
hidden_imports = collect_submodules("PyQt6")
hidden_imports += ['torch', 'torchvision', 'cv2', 'numpy', 'PIL', 'cell_detector_wrapper']

a = Analysis(
    [os.path.join(root_path, 'main.py')],
    pathex=[root_path],
    binaries=[],
    datas=[
        # --- UI files ---
        (os.path.join(root_path, "ddg/about_dialog.ui"), "ddg/"),
        (os.path.join(root_path, "ddg/chip_dialog.ui"), "ddg/"),
        (os.path.join(root_path, "ddg/point_widget.ui"), "ddg/"),
        (os.path.join(root_path, "ddg/central_widget.ui"), "ddg/"),
        (os.path.join(root_path, "ddg/central_graphics_view.py"), "ddg/"),

        # --- Icons ---
        (os.path.join(root_path, "icons/add.svg"), "icons/"),
        (os.path.join(root_path, "icons/cancel.svg"), "icons/"),
        (os.path.join(root_path, "icons/ddg.png"), "icons/"),
        (os.path.join(root_path, "icons/delete.svg"), "icons/"),
        (os.path.join(root_path, "icons/export.svg"), "icons/"),
        (os.path.join(root_path, "icons/folder.svg"), "icons/"),
        (os.path.join(root_path, "icons/import.svg"), "icons/"),
        (os.path.join(root_path, "icons/load.svg"), "icons/"),
        (os.path.join(root_path, "icons/reset.svg"), "icons/"),
        (os.path.join(root_path, "icons/save.svg"), "icons/"),
        (os.path.join(root_path, "icons/zoom_in.svg"), "icons/"),
        (os.path.join(root_path, "icons/zoom_out.svg"), "icons/"),
        # IMPORTANT: Mac apps need an .icns file for the Dock icon. 

        # --- Translations ---
        (os.path.join(root_path, "i18n/ddg_es.qm"), "i18n/"),
        (os.path.join(root_path, "i18n/ddg_fr.qm"), "i18n/"),
        (os.path.join(root_path, "i18n/ddg_vi.qm"), "i18n/"),
        (os.path.join(root_path, "i18n/ddg_zh_hans_cn.qm"), "i18n/"),

        # --- AI Model Files ---
        (os.path.join(root_path, "ai_model/infer_single_overlay_improved.py"), "ai_model/"),
        (os.path.join(root_path, "ai_model/cell_classifier_best.pth"), "ai_model/"),
    ],
    hiddenimports=hidden_imports,
    hooksconfig={},
    runtime_hooks=[],
    # CRITICAL: We DO NOT exclude torch/cv2 on Mac. 
    # The App Bundle must contain these libraries to work standalone.
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
    [],
    exclude_binaries=True,
    name='ddg',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, 
    console=False, # Disable console for Mac GUI apps
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ddg',
)

# This creates the actual "DotDotGoose.app"
app = BUNDLE(
    coll,
    name='DotDotGoose.app',
    bundle_identifier='com.uab.cellcounter',
)