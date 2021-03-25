# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Users\\GeorgStockinger\\OneDrive - A2MAC1\\Dokumente\\python\\DotDotIC'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['pandas', 'scipy', 'matplotlib', 'xlwings', 'beautifulsoup4', 'sklearn', 'tornado', 'hook', 'setuptools', 'site', 'tensorflow', 'flask', 'cx_freeze', 'flake8', 'hdf5', 'h5py', 'ipython', 'ipython', 'jupyter', 'selenium', 'requests', 'pyinstaller'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='DotDotIC',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
