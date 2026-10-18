# SPDX-License-Identifier: GPL-2.0-or-later
"""Picking and verifying the launcher's update download (no Tk, no Windows: unit-tested).

The launcher only installs a release zip whose SHA-256 matches the digest GitHub publishes for
that asset. A release without the package, or an asset without a digest, is never installed
automatically: the launcher opens the releases page instead.
"""
import hashlib
import re

# The package package.sh builds; older packages were named uncharted-windows.zip.
PACKAGE_NAMES = ('ndc-native-windows.zip', 'uncharted-windows.zip')


class VerificationError(OSError):
    """The download is not the file the release describes."""


def release_version(release):
    """'v0.4.0' -> '0.4.0' (the digits of the tag, as the launcher compares them)."""
    return '.'.join(re.findall(r'\d+', release['tag_name']))


def package_asset(release):
    """The release's package as {name, url, size, sha256}, or None when it has none we can verify."""
    assets = {asset.get('name', ''): asset for asset in release.get('assets', [])}
    for name in PACKAGE_NAMES:
        asset = assets.get(name)
        if not asset:
            continue
        digest = asset.get('digest') or ''
        if not digest.startswith('sha256:') or not re.fullmatch(r'[0-9a-f]{64}', digest[7:]):
            return None
        return {'name': name, 'url': asset['browser_download_url'], 'size': int(asset.get('size') or 0),
                'sha256': digest[7:]}
    return None


class Hasher:
    """Hashes a download as it is written and checks it at the end."""

    def __init__(self, asset):
        self.asset = asset
        self.sha256 = hashlib.sha256()
        self.size = 0

    def update(self, chunk):
        self.sha256.update(chunk)
        self.size += len(chunk)

    def check(self):
        if self.asset['size'] and self.size != self.asset['size']:
            raise VerificationError(f"the download is {self.size} bytes, the release says {self.asset['size']}")
        if self.sha256.hexdigest() != self.asset['sha256']:
            raise VerificationError("the download does not match the release's SHA-256 checksum")
