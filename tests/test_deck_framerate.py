"""Steam Deck mode's frame rate: a 30/60 choice, 30 by default (owner's ruling, 2026-10-28:
Steam Deck mode 30 FPS is fine; upstream's default and its saved-setting migration are kept)."""
from paths import ROOT
import sys
import unittest

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_linux as linux  # noqa: E402


class DeckFrameRate(unittest.TestCase):
    def test_default_is_30(self):
        self.assertEqual(linux.DECK_SETTINGS['frame_rate'], '30')
        self.assertEqual(linux.DECK_FRAME_RATES, ('30', '60'))

    def test_environment_takes_the_choice_and_caps_it(self):
        for chosen, expected in (('30', '30'), ('60', '60'), ('120', linux.DECK_SETTINGS['frame_rate']),
                                 ('144', linux.DECK_SETTINGS['frame_rate']),
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
