#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Licence texts of the Python side of the package (package.sh runs it with the packaging Python).

Copies into LICENSES_DIR/python/: CPython's licence (it covers the bundled python3x.dll and the
standard library), Tcl/Tk's (the launcher's window toolkit), and the licence files of the
installed distributions PyInstaller bundles (Pillow) or uses (PyInstaller's bootloader, under the
GPL with its bootloader exception). Prints what it copied; missing files are reported, not fatal.
"""
import importlib.metadata
from pathlib import Path
import shutil
import sys

DISTRIBUTIONS = ('pillow', 'pyinstaller')


def copy(source, target, copied):
    if source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied.append(target.name)
        return True
    return False


def main(out):
    out = Path(out) / 'python'
    copied, missing = [], []
    base = Path(sys.base_prefix)
    if not copy(base / 'LICENSE.txt', out / 'CPython-LICENSE.txt', copied):
        missing.append('CPython LICENSE.txt')
    tcl = sorted(base.glob('tcl/tcl8*/license.terms')) + sorted(base.glob('tcl/tk8*/license.terms'))
    for terms in tcl:
        copy(terms, out / f'{terms.parent.name}-license.terms.txt', copied)
    if not tcl:
        missing.append('Tcl/Tk license.terms')
    for name in DISTRIBUTIONS:
        try:
            dist = importlib.metadata.distribution(name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(name)
            continue
        files = [f for f in dist.files or () if 'licen' in f.name.lower() or 'copying' in f.name.lower()]
        for file in files:
            copy(Path(dist.locate_file(file)), out / f'{name}-{file.name}', copied)
        if not files:
            missing.append(f'{name} licence file')
    print('Python licences:', ', '.join(copied) or 'none')
    if missing:
        print('Python licences missing:', ', '.join(missing), file=sys.stderr)


if __name__ == '__main__':
    main(sys.argv[1])
