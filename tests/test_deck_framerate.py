"""Steam Deck mode's frame rate: a 30/60 choice, 60 by default on every handheld."""
from paths import ROOT
import sys
import unittest

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_linux as linux  # noqa: E402


class DeckFrameRate(unittest.TestCase):
    def test_default_is_60_on_every_handheld(self):
        # Owner's decision, 2026-10-18: 60 always, Steam Deck and Legion Go alike; no device lookup.
        self.assertEqual(linux.deck_frame_rate(), '60')
        self.assertEqual(linux.DECK_SETTINGS['frame_rate'], '60')

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
