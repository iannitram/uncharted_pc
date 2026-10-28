"""A 45 FPS choice in the Linux launcher and in Steam Deck mode."""
from paths import ROOT
import sys
import unittest

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_linux as linux  # noqa: E402


def rate_env(rate, deck=True):
    env = {}
    linux.deck_environment({'steam_deck': deck, 'frame_rate': rate}, env)
    return env


class FortyFive(unittest.TestCase):
    def test_deck_mode_allows_30_45_60_in_order(self):
        self.assertEqual(tuple(linux.DECK_FRAME_RATES), ('30', '45', '60'))
        self.assertTrue(linux.deck_allows('frame_rate', '45'))

    def test_45_reaches_the_game(self):
        self.assertEqual(rate_env('45')['BB_VBLANK_HZ'], '45')

    def test_the_default_and_the_cap_do_not_move(self):
        self.assertEqual(linux.DECK_SETTINGS['frame_rate'], '60')
        for chosen in ('120', '144', ''):
            self.assertEqual(rate_env(chosen)['BB_VBLANK_HZ'], '60', chosen)
        self.assertFalse(linux.deck_allows('frame_rate', '90'))

    def test_the_list_offers_45_once_between_30_and_60(self):
        ns = {'APP_DEFAULTS': {}, 'WINDOW_SIZES': [('1920x1080', '1920 × 1080')],
              'ANTI_ALIASING': [], 'FRAME_RATES': [('60', '60 FPS (as on PS4)'), ('120', '120 FPS')]}
        linux.apply_defaults(ns)
        values = [value for value, _text in ns['FRAME_RATES']]
        self.assertEqual(values.count('45'), 1)
        self.assertLess(values.index('30'), values.index('45'))
        self.assertLess(values.index('45'), values.index('60'))
        linux.apply_defaults(ns)  # a second call adds nothing
        self.assertEqual([v for v, _t in ns['FRAME_RATES']].count('45'), 1)

    def test_off_changes_nothing(self):
        self.assertEqual(rate_env('45', deck=False), {})


if __name__ == '__main__':
    unittest.main()
