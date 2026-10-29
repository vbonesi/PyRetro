"""Snapshots da Biblioteca e cópias dos Backups pela camada de nuvem."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core import cloud, cloud_snapshots as snap


class TestSnapshots(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp)
        self.store = cloud.MemoryStorage()
        self.lib = self.tmp / "library.json"
        self.clock = iter(range(1_700_000_000, 1_800_000_000, 100))
        self.now = lambda: next(self.clock)

    def write(self, data):
        self.lib.write_text(json.dumps(data))

    def test_publish_sends_new_content_once_and_updates_the_pointer(self):
        self.write({"games": [1]})
        first = snap.publish(self.store, "library", self.lib, now=self.now)
        self.assertEqual(first["state"], "enviado")
        self.assertEqual(snap.publish(self.store, "library", self.lib, now=self.now)["state"], "igual")
        self.write({"games": [1, 2]})
        second = snap.publish(self.store, "library", self.lib, now=self.now)
        self.assertEqual(second["state"], "enviado")
        self.assertEqual(len(snap.versions(self.store, "library")), 2)
        self.assertEqual(snap.latest(self.store, "library")["file"], second["file"])

    def test_invalid_json_is_never_published(self):
        self.lib.write_text('{"games": [')
        with self.assertRaises(ValueError):
            snap.publish(self.store, "library", self.lib, now=self.now)
        self.assertEqual(self.store.files, {})

    def test_retention_trashes_only_the_oldest_versions(self):
        for n in range(5):
            self.write({"n": n}); snap.publish(self.store, "library", self.lib, keep=3, now=self.now)
        self.assertEqual(len(snap.versions(self.store, "library")), 3)
        self.assertEqual(len(self.store.trashed), 2)
        newest = snap.versions(self.store, "library")[0]
        self.assertEqual(json.loads(self.store.files[newest["path"]]), {"n": 4})

    def test_restore_verifies_hash_keeps_the_local_copy_and_refuses_tampering(self):
        self.write({"v": 1}); snap.publish(self.store, "library", self.lib, now=self.now)
        self.write({"v": 2})
        out = snap.restore(self.store, "library", self.lib)
        self.assertEqual(json.loads(self.lib.read_text()), {"v": 1})
        self.assertEqual(len(list(self.tmp.glob("library.json.antes-*"))), 1)
        path = snap.versions(self.store, "library")[0]["path"]
        self.store.files[path] = b'{"adulterado": true}'
        with self.assertRaises(ValueError):
            snap.restore(self.store, "library", self.lib)
        self.assertEqual(json.loads(self.lib.read_text()), {"v": 1})
        with self.assertRaises(cloud.NotFound):
            snap.restore(cloud.MemoryStorage(), "library", self.lib)

    def test_publish_tree_sends_only_new_files_and_never_deletes(self):
        root = self.tmp / "Backups"; (root / "a").mkdir(parents=True)
        (root / "a/um.ini").write_text("1"); (root / "dois.txt").write_text("2"); (root / "x.tmp").write_text("t")
        self.assertEqual(snap.publish_tree(self.store, root), {"sent": 2, "skipped": 0, "present": 0})
        (root / "tres.txt").write_text("3")
        self.assertEqual(snap.publish_tree(self.store, root), {"sent": 1, "skipped": 0, "present": 2})
        (root / "dois.txt").unlink()
        snap.publish_tree(self.store, root)
        self.assertIn("backups/dois.txt", self.store.files)  # remoto nunca é apagado por esta rotina
        self.assertEqual(snap.publish_tree(self.store, root / "nao-existe"), {"sent": 0, "skipped": 0, "present": 0})


class TestLibraryHook(unittest.TestCase):
    def test_save_library_calls_hooks_and_a_failing_hook_never_breaks_the_save(self):
        from core import library as lm
        tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, tmp)
        calls = []
        def boom(_path):
            raise RuntimeError("rede caiu")
        lm.AFTER_SAVE.extend([boom, calls.append]); self.addCleanup(lambda: [lm.AFTER_SAVE.remove(h) for h in (boom, calls.append) if h in lm.AFTER_SAVE])
        path = tmp / "library.json"
        lm.save_library(path, {"games": []})
        self.assertEqual(json.loads(path.read_text()), {"games": []})
        self.assertEqual(calls, [path])


class TestLibraryJournalFlow(unittest.TestCase):
    """Gravar a Biblioteca registra no diário; publicar envia só as mudanças e compacta com snapshot."""

    def setUp(self):
        from core import cloud_sync as cs, library as lm
        self.cs, self.lm = cs, lm
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / "Biblioteca").mkdir(); (self.tmp / "Backups").mkdir()
        self.cfg = {"pc": {"library_root": str(self.tmp / "Biblioteca"), "backups_root": str(self.tmp / "Backups")},
                    "cloud": {"remote": "x", "device": "pc"}}
        self.store = cloud.MemoryStorage()
        hook = lambda path, before, after: cs.record_library_change(self.cfg, before, after)
        lm.AFTER_SAVE_DIFF.append(hook); self.addCleanup(lm.AFTER_SAVE_DIFF.remove, hook)
        self.path = cs.library_file(self.cfg)

    def test_saving_records_publishes_increments_and_compacts_with_a_snapshot(self):
        game = {"id": "a", "nome": "A", "nota": 5}
        self.lm.save_library(self.path, {"games": [game]})
        first = self.cs.publish_snapshots(self.cfg, self.store)
        self.assertEqual(first["journal"], 1); self.assertEqual(first["library"]["state"], "enviado")  # 1º snapshot
        self.lm.save_library(self.path, {"games": [{**game, "nota": 9}]})
        second = self.cs.publish_snapshots(self.cfg, self.store)
        self.assertEqual(second["journal"], 1)
        self.assertNotIn("library", second)                      # sem compactar de novo: só o diário subiu
        self.assertEqual(len(snap.versions(self.store, "library")), 1)
        self.assertEqual(len([p for p in self.store.files if p.startswith("journal/pc/")]), 2)

    def test_pull_merges_another_device_without_echoing_it_back(self):
        from core import library_journal as lj
        game = {"id": "a", "nome": "A", "nota": 5}
        self.lm.save_library(self.path, {"games": [game]})
        self.cs.publish_snapshots(self.cfg, self.store)
        phone = lj.Journal(self.tmp / "celular.db", "celular")
        phone.record({"games": [game]}, {"games": [{**game, "nota": 7}, {"id": "b", "nome": "B"}]}, at=9e12)
        phone.publish(self.store)
        self.assertEqual(self.cs.pull_library(self.cfg, self.store)["applied"], 2)
        merged = json.loads(self.path.read_text())
        self.assertEqual({g["id"]: g.get("nota") for g in merged["games"]}, {"a": 7, "b": None})
        self.assertEqual(self.cs.publish_snapshots(self.cfg, self.store)["journal"], 0)  # nada de eco


if __name__ == "__main__":
    unittest.main()
