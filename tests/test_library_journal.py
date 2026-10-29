"""Diário de mudanças da Biblioteca: diff/aplicação, publicação incremental e junção entre dispositivos."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core import cloud, library_journal as lj


def lib(*games, **extra):
    return {'games': [dict(g) for g in games], **extra}


G1 = {'id': 'a', 'nome': 'Jogo A', 'nota': 8, 'iniciado': True}
G2 = {'id': 'b', 'nome': 'Jogo B', 'nota': None}


class TestDiffApply(unittest.TestCase):
    def test_roundtrip_add_remove_set_unset_and_meta(self):
        old = lib(G1, G2, versao=1)
        new = lib({**G1, 'nota': 9, 'comentario': 'bom'}, {'id': 'c', 'nome': 'Jogo C'}, versao=2)
        new['games'][0].pop('iniciado')
        changes = lj.diff(old, new)
        self.assertEqual({c['op'] for c in changes}, {'add', 'remove', 'set', 'unset', 'meta'})
        result = lj.apply(old, changes)
        self.assertEqual({g['id']: g for g in result['games']}, {g['id']: g for g in new['games']})
        self.assertEqual(result['versao'], 2)
        self.assertEqual(lj.diff(new, new), [])
        self.assertEqual(old['games'][0]['nota'], 8, 'apply não altera o original')

    def test_game_order_is_not_a_change(self):
        self.assertEqual(lj.diff(lib(G1, G2), lib(G2, G1)), [])


class TestJournal(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp)
        self.store = cloud.MemoryStorage()
        self.clock = [1000.0]
        self.now = lambda: self.clock[0]
        self.pc = lj.Journal(self.tmp / 'pc.db', 'pc', now=self.now)
        self.phone = lj.Journal(self.tmp / 'celular.db', 'celular', now=self.now)

    def tick(self, n=10):
        self.clock[0] += n

    def test_publish_sends_only_new_changes_as_immutable_segments(self):
        base = lib(G1)
        self.assertEqual(self.pc.record(None, base), 1)
        self.assertEqual(self.pc.publish(self.store), 1)
        self.assertEqual(self.pc.publish(self.store), 0)
        self.tick(); edited = lib({**G1, 'nota': 10})
        self.pc.record(base, edited)
        self.assertEqual(self.pc.publish(self.store), 1)
        segments = sorted(self.store.files)
        self.assertEqual(len(segments), 2)
        self.assertTrue(all(p.startswith('journal/pc/') for p in segments))
        size_edit = len(self.store.files[segments[1]])
        self.assertLess(size_edit, 300, 'uma edição de nota sobe poucos bytes, não a Biblioteca inteira')

    def test_pull_applies_the_other_device_once_and_does_not_echo_it_back(self):
        base = lib(G1, G2)
        self.pc.record(None, base); self.pc.publish(self.store)
        self.tick(); self.phone.record(base, lib({**G1, 'nota': 5}, G2))
        self.phone.publish(self.store)
        merged, n = self.pc.pull(self.store, base)
        self.assertEqual((n, merged['games'][0]['nota']), (1, 5))
        self.assertEqual(self.pc.pull(self.store, merged)[1], 0)  # já visto
        self.assertEqual(self.pc.publish(self.store), 0)           # origem remota nunca é reenviada

    def test_last_write_wins_per_field_and_a_newer_local_edit_beats_an_older_remote(self):
        base = lib(G1)
        self.pc.record(None, base); self.pc.publish(self.store)
        self.tick(10); self.phone.record(base, lib({**G1, 'nota': 5, 'observacoes': 'celular'}))
        self.phone.publish(self.store)
        self.tick(10); local = lib({**G1, 'nota': 9})
        self.pc.record(base, local)  # edição local MAIS RECENTE do mesmo campo
        merged, _ = self.pc.pull(self.store, local)
        game = merged['games'][0]
        self.assertEqual(game['nota'], 9)               # a do PC vence (mais recente)
        self.assertEqual(game['observacoes'], 'celular')  # campo diferente do celular entra

    def test_removal_loses_to_a_newer_local_edit_and_unknown_ops_are_ignored(self):
        base = lib(G1, G2)
        self.pc.record(None, base)
        self.tick(5); self.phone.record(base, lib(G1))  # celular removeu B
        self.phone.publish(self.store)
        self.tick(5); edited = lib(G1, {**G2, 'nota': 7}); self.pc.record(base, edited)
        merged, _ = self.pc.pull(self.store, edited)
        self.assertEqual(sorted(g['id'] for g in merged['games']), ['a', 'b'])
        self.store.put('journal/outro/000000000001-000000000001.json', json.dumps(
            {'device': 'outro', 'from': 1, 'to': 1, 'changes': [{'seq': 1, 'at': 1, 'op': 'apagar-tudo'}]}).encode())
        self.assertEqual(self.pc.pull(self.store, merged)[1], 0)

    def test_snapshot_plus_replay_rebuilds_the_current_library(self):
        v0 = lib(G1); self.pc.record(None, v0)
        snapshot_seq = self.pc.rows()[-1]['seq']
        v1 = lib({**G1, 'nota': 3}, G2); self.tick(); self.pc.record(v0, v1)
        later = [self.pc._export(r) for r in self.pc.rows(since=snapshot_seq)]
        rebuilt = lj.apply(v0, later)
        self.assertEqual({g['id']: g for g in rebuilt['games']}, {g['id']: g for g in v1['games']})


if __name__ == '__main__':
    unittest.main()
