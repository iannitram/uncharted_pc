"""The scene render size of the Uncharted games: which size is chosen, and the patch that sets it."""
from paths import ROOT
import importlib.util
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(ROOT / 'launcher'))
import render_size as rs  # noqa: E402
import uncharted_linux as linux  # noqa: E402

spec = importlib.util.spec_from_file_location('bbrun', ROOT / 'run.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


def setup_code(width=1920, height=1080):
    """The bytes of the games' default video setup: movl $imm, disp8(%rax) for the size fields."""
    def movl(field, value):
        return b'\xc7\x40' + bytes([field]) + struct.pack('<I', value)
    return (movl(0x08, width) + movl(0x0c, height) + movl(0x14, 0) + movl(0x18, width) + movl(0x1c, height)
            + movl(0x24, width) + movl(0x28, height) + movl(0x30, 2560) + movl(0x34, 1216)
            + movl(0x38, width) + movl(0x3c, height) + movl(0x40, width // 8) + movl(0x44, height // 4))


def fake_elf(code):
    """A minimal 64-bit ELF: one PT_LOAD at vaddr 0 holding `code` after a 0x200 byte header."""
    header = bytearray(0x200)
    header[:4] = b'\x7fELF'
    struct.pack_into('<Q', header, 0x20, 0x40)       # e_phoff
    struct.pack_into('<HH', header, 0x36, 56, 1)     # e_phentsize, e_phnum
    struct.pack_into('<IIQQQQQQ', header, 0x40, 1, 5, 0x200, 0, 0, len(code), len(code), 0x1000)
    return bytes(header) + b'\x90' * 16 + code + b'\x90' * 16


def patched(blob, elf):
    """Apply a BBPATCH2 blob to the ELF image and return the new bytes."""
    magic, base, count = struct.unpack_from('<8sQQ', blob)
    assert magic == b'BBPATCH2'
    out, at = bytearray(elf), 24
    for _ in range(count):
        offset, size = struct.unpack_from('<QQ', blob, at)
        at += 16
        out[0x200 + offset:0x200 + offset + size] = blob[at:at + size]
        at += size
    return bytes(out)


class Decision(unittest.TestCase):
    def test_nothing_set_keeps_the_games_1080p(self):
        self.assertIsNone(rs.decide({}))
        self.assertIsNone(rs.decide({'BB_RENDER_720P': '0'}))

    def test_deck_flag_is_720p(self):
        self.assertEqual(rs.decide({'BB_RENDER_720P': '1'}), (1280, 720))

    def test_explicit_size_wins_and_native_16_10_is_allowed(self):
        self.assertEqual(rs.decide({'BB_RENDER_SIZE': '1280x800'}), (1280, 800))
        self.assertEqual(rs.decide({'BB_RENDER_SIZE': '1280X800', 'BB_RENDER_720P': '1'}), (1280, 800))

    def test_unusable_sizes_are_ignored(self):
        for bad in ('', 'abc', '1280', '1281x800', '1280x801', '0x0', '3840x2160', '1920x1200', '100x100'):
            self.assertIsNone(rs.decide({'BB_RENDER_SIZE': bad}), bad)

    def test_1080p_itself_is_no_patch(self):
        self.assertIsNone(rs.decide({'BB_RENDER_SIZE': '1920x1080'}))


class Deck(unittest.TestCase):
    def test_deck_mode_asks_for_the_deck_size(self):
        env = {}
        linux.deck_environment({'steam_deck': True}, env)
        self.assertEqual(rs.decide(env), (1280, 720))
        self.assertEqual(env['BB_WINDOW_SIZE'], '1280x800')

    def test_off_leaves_1080p(self):
        env = {}
        linux.deck_environment({'steam_deck': False}, env)
        self.assertIsNone(rs.decide(env))


class Patch(unittest.TestCase):
    def test_every_1080p_field_becomes_the_size(self):
        elf = fake_elf(setup_code())
        for size, small in (((1280, 720), (160, 180)), ((1280, 800), (160, 200))):
            blob = rs.patch_bytes(elf, size)
            new = patched(blob, elf)
            for field, value in ((0x08, size[0]), (0x0c, size[1]), (0x18, size[0]), (0x1c, size[1]),
                                 (0x24, size[0]), (0x28, size[1]), (0x38, size[0]), (0x3c, size[1]),
                                 (0x40, small[0]), (0x44, small[1])):
                at = new.index(b'\xc7\x40' + bytes([field])) + 3
                self.assertEqual(struct.unpack_from('<I', new, at)[0], value, hex(field))
            # the 2560x1216 pair is not a scene size: untouched
            self.assertIn(b'\xc7\x40\x30' + struct.pack('<I', 2560), new)

    def test_no_video_setup_is_an_error_not_a_silent_1080p(self):
        with self.assertRaises(ValueError):
            rs.patch_bytes(fake_elf(b'\x90' * 64), (1280, 720))

    def test_one_setup_is_enough(self):
        # The games of this collection have one default setup, not three.
        self.assertEqual(len(rs.find_sites(fake_elf(setup_code()))), 1)

    def test_merge_keeps_the_other_patches(self):
        elf = fake_elf(setup_code())
        other = struct.pack('<8sQQ', b'BBPATCH2', 0x400000, 1) + struct.pack('<QQ', 4, 2) + b'ab'
        merged = rs.merge(other, rs.patch_bytes(elf, (1280, 720)))
        magic, base, count = struct.unpack_from('<8sQQ', merged)
        self.assertEqual((magic, base), (b'BBPATCH2', 0x400000))
        self.assertGreater(count, 1)
        self.assertIn(struct.pack('<QQ', 4, 2) + b'ab', merged)


class RunPy(unittest.TestCase):
    def test_run_makes_the_patch_file_for_the_chosen_size(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            (out / 'eboot.elf').write_bytes(fake_elf(setup_code()))
            args = run.render_size_arguments({'BB_RENDER_720P': '1'}, out)
            self.assertEqual(args[0], str(out / 'eboot.elf'))
            self.assertIn('1280x720', args)
            self.assertEqual(run.render_size_arguments({}, out), [])


if __name__ == '__main__':
    unittest.main()
