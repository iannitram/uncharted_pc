"""Steam Deck mode's frame rate: a 30/60 choice, 60 by default only on measured handhelds."""
from paths import ROOT
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_linux as linux  # noqa: E402


def dmi(name, version):
    files = {'product_name': name, 'product_version': version}
    return lambda self: files[self.name] + '\n'


class DeckFrameRate(unittest.TestCase):
    def default_for(self, name, version):
        with patch.object(Path, 'read_text', dmi(name, version)):
            return linux.deck_frame_rate()

    def test_default_follows_the_device(self):
        self.assertEqual(self.default_for('83E1', 'Legion Go 8APU1'), '60')
        self.assertEqual(self.default_for('ROG Flow Z13 GZ302EA_GZ302EA', '1.0'), '60')
        self.assertEqual(self.default_for('Jupiter', '1'), '30')       # Steam Deck LCD
        self.assertEqual(self.default_for('Galileo', '1'), '30')       # Steam Deck OLED

    def test_unreadable_dmi_means_30(self):
        with patch.object(Path, 'read_text', side_effect=OSError):
            self.assertEqual(linux.deck_frame_rate(), '30')

    def test_environment_takes_the_choice_and_caps_it(self):
        for chosen, expected in (('30', '30'), ('60', '60'), ('120', '60'), ('144', '60'),
                                 ('', linux.DECK_SETTINGS['frame_rate'])):
            env = {}
            linux.deck_environment({'steam_deck': True, 'frame_rate': chosen}, env)
            self.assertEqual(env['BB_VBLANK_HZ'], expected, chosen)

    def test_frame_rate_is_not_locked_in_deck_mode(self):
        self.assertNotIn('frame_rate', linux.DECK_LOCKED)
        self.assertIn('window_size', linux.DECK_LOCKED)

    def test_off_changes_nothing(self):
        env = {}
        linux.deck_environment({'steam_deck': False, 'frame_rate': '60'}, env)
        self.assertEqual(env, {})


if __name__ == '__main__':
    unittest.main()
