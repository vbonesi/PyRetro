import itertools
import json
import tempfile
import unittest
from pathlib import Path

from core import cloud, journal_rules as rules, library_journal as lj


class TestConvergence(unittest.TestCase):
    def test_shared_python_kotlin_fixture(self):
        fixture=json.loads((Path(__file__).resolve().parents[1]/'android/app/src/test/resources/journal-parity.json').read_text())
        for order in itertools.permutations(fixture['changes']):
            data,state=fixture['base'],None
            for change in order:data,_,state=rules.merge(data,[change],state)
            self.assertEqual(data,fixture['expected'])
    def test_remote_order_and_equal_time_have_the_same_winner(self):
        base = {'games': [{'id': 'a', 'nome': 'A', 'nota': 0}]}
        changes = [dict(op='set', id='a', field='nota', value=n, at=t, device=d, seq=1)
                   for n, t, d in [(3, 10, 'a'), (8, 20, 'b'), (9, 20, 'c')]]
        for order in itertools.permutations(changes):
            library, state = base, None
            for change in order:
                library, _, state = rules.merge(library, [change], state)
            self.assertEqual(library['games'][0]['nota'], 9)

    def test_partial_add_and_field_edits_converge_without_erasing_other_fields(self):
        changes = [dict(op='add', id='a', value={'id': 'a', 'nome': 'A'}, at=20, device='pc', seq=1),
                   dict(op='set', id='a', field='nota', value=8, at=10, device='phone', seq=1)]
        base = {'games': [{'id': 'a', 'nome': 'Antigo'}]}
        for order in itertools.permutations(changes):
            result, _, _ = rules.merge(base, list(order))
            self.assertEqual(result['games'][0], {'id': 'a', 'nome': 'A', 'nota': 8})

    def test_sessions_merge_once_and_do_not_replace_historical_time(self):
        base = {'games': [{'id': 'a', 'tempo': '10:00:00'}]}
        events = [dict(op='session', id='a', value={'event': d, 'seconds': 60}, at=10, device=d, seq=1) for d in ('pc', 'phone')]
        result, _, state = rules.merge(base, events)
        again, applied, _ = rules.merge(result, events, state)
        self.assertEqual(applied, 0)
        self.assertEqual(sum(again['games'][0]['_play_sessions'].values()), 120)
        self.assertEqual(again['games'][0]['tempo'], '10:00:00')

    def test_unknown_game_edits_wait_for_its_registration_and_survive_an_older_removal(self):
        events = [dict(op='add', id='a', value={'id': 'a', 'nome': 'A'}, at=10, device='pc', seq=1),
                  dict(op='remove', id='a', at=20, device='pc', seq=2),
                  dict(op='set', id='a', field='nota', value=8, at=30, device='phone', seq=1)]
        for order in itertools.permutations(events):
            library, state = {'games': []}, None
            for event in order:
                library, _, state = rules.merge(library, [event], state)
            self.assertEqual(library['games'], [{'id': 'a', 'nome': 'A', 'nota': 8}], order)

    def test_receipt_waits_for_a_successful_local_save_and_clock_never_goes_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = cloud.MemoryStorage();now = [1000.0]
            pc = lj.Journal(Path(tmp)/'pc.db', 'pc', now=lambda: now[0])
            phone = lj.Journal(Path(tmp)/'phone.db', 'phone', now=lambda: now[0])
            base = {'games': [{'id': 'a', 'nota': 5}]}
            phone.record(base, {'games': [{'id': 'a', 'nota': 8}]});phone.publish(store)
            with self.assertRaises(OSError):
                pc.pull(store, base, save=lambda _: (_ for _ in ()).throw(OSError('disco cheio')))
            merged, count = pc.pull(store, base)
            self.assertEqual((count, merged['games'][0]['nota']), (1, 8))
            now[0] = 1
            pc.record(merged, {'games': [{'id': 'a', 'nota': 9}]})
            self.assertGreater(pc.rows(origin='local')[0]['at'], 1000)

    def test_existing_segment_with_different_content_is_not_acknowledged(self):
        with tempfile.TemporaryDirectory() as tmp:
            diary = lj.Journal(Path(tmp)/'pc.db', 'pc')
            diary.record(None, {'games': [{'id': 'a'}]})
            store = cloud.MemoryStorage()
            store.put('journal/pc/000000000001-000000000001.json', b'{}')
            with self.assertRaises(ValueError):diary.publish(store)
            with diary._db() as db:self.assertEqual(diary._meta(db, 'published_seq'), 0)


if __name__ == '__main__':unittest.main()
