# SPDX-License-Identifier: GPL-2.0-or-later
"""Font files for the artwork the launcher draws with Pillow: Windows' own Segoe UI.

The launcher bundles no font. A plain system font keeps the artwork from imitating the game's
logo; where Segoe UI is missing (another OS), Pillow's default font is used.
"""
import os
from pathlib import Path

_FILES = {'bold': ('segoeuib.ttf', 'seguisb.ttf'), 'regular': ('segoeui.ttf',)}


def font_path(weight):
    """Path of Segoe UI in the given weight ('bold' or 'regular'), or None."""
    fonts = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts'
    for name in _FILES[weight]:
        path = fonts / name
        if path.is_file():
            return path
    return None
