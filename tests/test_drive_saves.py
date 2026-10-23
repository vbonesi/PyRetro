import itertools
import unittest
from pathlib import Path
from core import drive_saves as ds, mobile_sync

A, B, C = ('a' * 64, 'b' * 64, 'c' * 64)


class DriveSavesTests(unittest.TestCase):
    def row(self, digest=A, remote=False):
        return {'path': 'SFC/Game.srm', 'sha256': digest, 'size': 4,
                **({'id': 'drive-file', 'version': '8'} if remote else {})}

    def test_layout_agrees_with_default_mobile_sync(self):
        cfg = {'pc': {'saves_root': '/tmp/Jogos/Saves/saves', 'states_root': '/tmp/Jogos/Saves/states'}}
        self.assertEqual(set(ds.GROUP_PATHS), set(mobile_sync.GROUPS))
        for group, path in ds.GROUP_PATHS.items():
            self.assertEqual(mobile_sync.root(cfg, group), Path('/tmp/Jogos/Saves') / path)

    def test_entire_three_way_table_matches_android_rule(self):
        # 64 combinations including absence. No timestamp participates.
        for left, right, base in itertools.product((None, A, B, C), repeat=3):
            want = ('same' if left == right else
                    ('download' if base is None else 'conflict') if left is None else
                    ('upload' if base is None else 'conflict') if right is None else
                    'conflict' if base is None else 'download' if left == base else
                    'upload' if right == base else 'conflict')
            self.assertEqual(ds.direction(left, right, base), want, (left, right, base))

    def test_scope_changes_on_account_folder_group_or_local_tree(self):
        parts = ['account', 'folder-id', 'retro-saves', 'local-tree']
        first = ds.identity(*parts)
        for i in range(4):
            changed = parts.copy(); changed[i] = 'retro-states' if i == 2 else changed[i] + '-new'
            self.assertNotEqual(first, ds.identity(*changed))

    def test_duplicates_history_and_malicious_paths_are_not_silent(self):
        for path in ('../Game.srm', '.pyretro-history/Game.srm', 'a//Game.srm'):
            with self.assertRaises(ValueError): ds.index('retro-saves', [{**self.row(), 'path': path}])
        with self.assertRaises(mobile_sync.Conflict): ds.index('retro-saves', [self.row(), self.row()])
        with self.assertRaises(ValueError): ds.index('retro-saves', [{**self.row(), 'size': True}])

    def test_conflict_choice_revalidates_version_and_requires_history(self):
        scope = ds.identity('account', 'folder', 'retro-saves', 'tree')
        row = ds.analyze('retro-saves', [self.row(B)], [self.row(C, True)], {'SFC/Game.srm': A}, scope)['rows'][0]
        self.assertEqual(row['direction'], 'conflict')
        transfer = ds.prepare(row, 'upload', row['local'], row['remote'])
        with self.assertRaises(mobile_sync.Conflict):
            ds.prepare(row, 'upload', row['local'], {**row['remote'], 'version': '9'})
        after = {**row['remote'], 'sha256': B, 'version': '9'}
        with self.assertRaises(mobile_sync.Conflict): ds.confirm(transfer, row['local'], after, published=True)
        with self.assertRaises(mobile_sync.Conflict): ds.confirm(transfer, row['local'], after, C)
        self.assertEqual(ds.confirm(transfer, row['local'], after, C, published=True), B)

    def test_missing_side_never_means_delete_and_skip_does_not_advance(self):
        scope = ds.identity('account', 'folder', 'retro-saves', 'tree')
        row = ds.analyze('retro-saves', [], [self.row(A, True)], {'SFC/Game.srm': A}, scope)['rows'][0]
        self.assertEqual(row['direction'], 'conflict')
        with self.assertRaises(ValueError): ds.prepare(row, 'upload', None, row['remote'])
        self.assertEqual(ds.prepare(row, 'skip', None, row['remote']), {'action': 'skip'})

    def test_fbneo_files_are_accepted_on_both_ends(self):
        self.assertTrue(mobile_sync.accepted('retro-saves', 'ARCADE/game.fs'))
