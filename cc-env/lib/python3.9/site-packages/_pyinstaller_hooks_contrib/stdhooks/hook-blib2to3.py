# ------------------------------------------------------------------
# Copyright (c) 2025 PyInstaller Development Team.
#
# This file is distributed under the terms of the GNU General Public
# License (version 2.0 or later).
#
# The full license is available in LICENSE, distributed with
# this software.
#
# SPDX-License-Identifier: GPL-2.0-or-later
# ------------------------------------------------------------------
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from _pyinstaller_hooks_contrib.compat import importlib_metadata


# Find the mypyc extension module for `black`, which is called something like `30fcd23745efe32ce681__mypyc`. The prefix
# changes with each `black` version, so we need to obtain the name by looking at distribution's list of files.
def _find_mypyc_module():
    try:
        dist = importlib_metadata.distribution("black")
    except importlib_metadata.PackageNotFoundError:
        return []
    return [entry.name.split('.')[0] for entry in (dist.files or []) if '__mypyc' in entry.name]


hiddenimports = [
    *_find_mypyc_module(),
    'dataclasses',
    'pkgutil',
    'tempfile',
    *collect_submodules('blib2to3')
]

# Ensure that data files, such as `PatternGrammar.txt` and `Grammar.txt`, are collected.
datas = collect_data_files('blib2to3')
