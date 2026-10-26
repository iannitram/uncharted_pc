"""run.py hands patches.py the collection's executable name of the game being run."""
from paths import ROOT
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('bbrun', ROOT / 'run.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class PatchArguments(unittest.TestCase):
    def test_a_game_dumped_on_its_own_keeps_its_collection_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            u2 = root / 'u2'; u2.mkdir(); (u2 / 'eboot.bin').write_bytes(b'')
            patches = root / 'patches'; patches.mkdir()
            env = {'BB_GAME_DIR_U2': str(u2), 'BB_PATCHES_DIR': str(patches)}
            exe = run.EXECUTABLES['u2']
            game, file = run.locate(env, exe)
            self.assertEqual(file, 'eboot.bin')  # the per-game dump's own executable file
            args = run.patch_arguments(env, exe, game, root / 'out')
            self.assertEqual(args[args.index('--app-elf') + 1], 'big2-ps4_Shipping.elf')

    def test_no_patch_folder_means_no_patches(self):
        self.assertEqual(run.patch_arguments({}, 'eboot.bin', Path('.'), Path('.')), [])
        self.assertEqual(run.patch_arguments({'BB_PATCHES_DIR': '/nonexistent'}, 'eboot.bin', Path('.'), Path('.')), [])


class PatchFiles(unittest.TestCase):
    """run.py gives bb-probe every patch source, not one of them: third-party patches (patches.py),
    cheats (cheats.py) and the Steam Deck's 720p video settings (render_720p.py)."""

    def setUp(self):
        self.calls = []
        self.saved = (run.run_script, run.cheats.build, run.subprocess.run)
        run.run_script = lambda name, *args: self.calls.append(('script', name))
        self.cheat_file = None

        def build(path, out, enabled):
            self.calls.append(('cheats', list(enabled)))
            return self.cheat_file
        run.cheats.build = build

        class Done:
            returncode = 0
        run.subprocess.run = lambda command, **kwargs: self.calls.append(('render', Path(command[-1]).name)) or Done()

    def tearDown(self):
        run.run_script, run.cheats.build, run.subprocess.run = self.saved

    def files(self, env, root):
        patches = root / 'patches'
        patches.mkdir(exist_ok=True)
        env = {**env, 'BB_PATCHES_DIR': str(patches)}
        return run.patch_files_for(env, 'eboot.bin', root, root / 'out')

    def test_third_party_cheats_and_720p_patches_all_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.cheat_file = root / 'out' / 'cheats.bin'
            files = self.files({'BB_CHEATS': 'health,ammo', 'BB_RENDER_720P': '1'}, root)
            # in the order bb-probe applies them
            self.assertEqual(files, [root / 'out' / 'patches.bin', root / 'out' / 'cheats.bin',
                                     root / 'out' / 'render-720p.bin'])
            self.assertEqual(self.calls, [('script', 'patches.py'), ('cheats', ['health', 'ammo']),
                                          ('render', 'render-720p.bin')])

    def test_each_source_only_when_it_applies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(run.patch_files_for({}, 'eboot.bin', root, root / 'out'), [])
            self.assertEqual(run.patch_files_for({'BB_RENDER_720P': '1'}, 'eboot.bin', root, root / 'out'),
                             [root / 'out' / 'render-720p.bin'])
            self.cheat_file = root / 'out' / 'cheats.bin'
            self.assertEqual(self.files({'BB_CHEATS': 'ammo'}, root), [root / 'out' / 'patches.bin',
                                                                       root / 'out' / 'cheats.bin'])
            self.assertEqual(run.patch_files_for({'BB_CHEATS': 'ammo'}, 'eboot.bin', root, root / 'out'),
                             [root / 'out' / 'cheats.bin'])  # no patches folder: no third-party patches

    def test_an_explicit_game_resolution_replaces_the_720p_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = self.files({'BB_RENDER_720P': '1', 'BB_GAME_RES': '2560x1440'}, root)
            self.assertEqual(files, [root / 'out' / 'patches.bin'])
            self.assertNotIn(('render', 'render-720p.bin'), self.calls)

    def test_a_720p_patch_that_cannot_be_made_is_skipped(self):
        class Failed:
            returncode = 1
        run.subprocess.run = lambda command, **kwargs: Failed()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.files({'BB_RENDER_720P': '1'}, root), [root / 'out' / 'patches.bin'])


if __name__ == '__main__':
    unittest.main()
