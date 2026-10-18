"""The launcher's update download: which asset it takes and how it is verified."""
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'launcher'))
import update_check  # noqa: E402

DATA = b'package bytes'
DIGEST = 'sha256:' + hashlib.sha256(DATA).hexdigest()


def release(*assets, tag='v0.4.1'):
    return {'tag_name': tag, 'assets': list(assets)}


def asset(name='ndc-native-windows.zip', digest=DIGEST, size=len(DATA)):
    return {'name': name, 'browser_download_url': f'https://example.invalid/{name}', 'size': size,
            'digest': digest}


class PackageAsset(unittest.TestCase):
    def test_takes_the_package_by_exact_name(self):
        picked = update_check.package_asset(release(asset('other.zip'), asset()))
        self.assertEqual(picked['name'], 'ndc-native-windows.zip')
        self.assertEqual(picked['sha256'], DIGEST[7:])

    def test_old_package_name_still_found(self):
        self.assertEqual(update_check.package_asset(release(asset('uncharted-windows.zip')))['name'],
                         'uncharted-windows.zip')

    def test_no_package_or_no_digest_is_not_installed(self):
        self.assertIsNone(update_check.package_asset(release(asset('source.zip'))))
        self.assertIsNone(update_check.package_asset(release(asset(digest=None))))
        self.assertIsNone(update_check.package_asset(release(asset(digest='md5:abc'))))

    def test_version_from_tag(self):
        self.assertEqual(update_check.release_version(release(tag='v0.4.1')), '0.4.1')


class Hasher(unittest.TestCase):
    def check(self, data, **kwargs):
        hasher = update_check.Hasher(update_check.package_asset(release(asset(**kwargs))))
        for i in range(0, len(data), 4):
            hasher.update(data[i:i + 4])
        hasher.check()

    def test_matching_download_passes(self):
        self.check(DATA)

    def test_changed_or_truncated_download_fails(self):
        with self.assertRaises(update_check.VerificationError):
            self.check(DATA[:-1] + b'X')
        with self.assertRaises(update_check.VerificationError):
            self.check(DATA[:-2])


if __name__ == '__main__':
    unittest.main()
