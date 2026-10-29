"""Camada de nuvem: contrato do armazenamento (memória e rclone local) e saves por manifestos."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core import cloud, cloud_saves
from core.cloud_saves import CloudSaves, decide


class StorageContract:
    """Mesmo comportamento em qualquer implementação."""

    def test_put_get_exists_list(self):
        s = self.storage
        self.assertFalse(s.exists("a/b.txt"))
        s.put("a/b.txt", b"um"); s.put("a/c/d.bin", b"tres")
        self.assertTrue(s.exists("a/b.txt"))
        self.assertEqual(s.get("a/b.txt"), b"um")
        self.assertEqual(sorted((i["path"], i["size"]) for i in s.list("a")), [("a/b.txt", 2), ("a/c/d.bin", 4)])
        self.assertEqual(s.list("nada/aqui"), [])

    def test_put_never_overwrites_unless_asked_and_missing_get_raises(self):
        s = self.storage
        s.put("x.txt", b"1")
        with self.assertRaises(cloud.Exists):
            s.put("x.txt", b"2")
        self.assertEqual(s.get("x.txt"), b"1")
        s.put("x.txt", b"3", overwrite=True)
        self.assertEqual(s.get("x.txt"), b"3")
        with self.assertRaises(cloud.NotFound):
            s.get("não/existe")

    def test_trash_removes_from_listing_and_bad_paths_are_refused(self):
        s = self.storage
        s.put("t/arquivo", b"z"); s.trash("t/arquivo")
        self.assertFalse(s.exists("t/arquivo"))
        for bad in ("../fora", "/abs", "a//b", "a/./b", ""):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                s.put(bad, b"x")


class TestMemory(StorageContract, unittest.TestCase):
    def setUp(self):
        self.storage = cloud.MemoryStorage()


@unittest.skipUnless(shutil.which("rclone"), "rclone não instalado")
class TestRcloneLocal(StorageContract, unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.tmp)
        self.storage = cloud.RcloneStorage(self.tmp)


class TestParentFolderCreatedOnce(unittest.TestCase):
    def test_parallel_puts_into_a_new_folder_create_it_a_single_time(self):
        from concurrent.futures import ThreadPoolExecutor
        import subprocess
        mkdirs = []

        def run(cmd, **kwargs):
            if cmd[1] == 'mkdir':
                mkdirs.append(cmd[2])
            return subprocess.CompletedProcess(cmd, 0, b'null', b'')
        storage = cloud.RcloneStorage('drive:x', run=run)
        with ThreadPoolExecutor(8) as pool:
            list(pool.map(lambda n: storage._ensure_dir(f'states/pc/blobs/{n}'), range(16)))
        self.assertEqual(mkdirs, ['drive:x/states/pc/blobs'])


class TestDecide(unittest.TestCase):
    def test_table(self):
        cases = [
            (None, None, [], "none"), ("a", None, [], "push"), ("a", "a", ["a"], "same"),
            (None, "a", ["a"], "pull"), (None, None, ["a", "b"], "conflict"),
            ("a", "a", ["b"], "pull"), ("a", "a", ["b", "c"], "conflict"),
            ("b", "a", ["a"], "push"), ("b", "a", ["c"], "conflict"), ("b", None, ["c"], "conflict"),
            ("b", "a", ["b"], "same"), ("b", "a", ["b", "c"], "conflict"),
        ]
        for local, baseline, heads, expected in cases:
            with self.subTest(local=local, baseline=baseline, heads=heads):
                self.assertEqual(decide(local, baseline, set(heads)), expected)


class Devices(unittest.TestCase):
    storage_factory = staticmethod(cloud.MemoryStorage)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp)
        self.storage = self.storage_factory()
        self.clock = iter(range(1000, 100000))
        self.a_root, self.b_root = self.tmp / "a", self.tmp / "b"
        self.a_root.mkdir(); self.b_root.mkdir()
        self.a = CloudSaves(self.storage, "pc", self.a_root, now=lambda: next(self.clock))
        self.b = CloudSaves(self.storage, "celular", self.b_root, now=lambda: next(self.clock))

    def write(self, root, rel, data):
        path = root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)

    def actions(self, device):
        return {i["path"]: i["action"] for i in device.plan()}

    def test_first_push_then_other_device_pulls_and_both_are_in_sync(self):
        self.write(self.a_root, "SFC/Jogo.srm", b"v1")
        self.assertEqual(self.actions(self.a), {"SFC/Jogo.srm": "push"})
        self.assertTrue(all(r["ok"] for r in self.a.apply()))
        self.assertEqual(self.actions(self.b), {"SFC/Jogo.srm": "pull"})
        self.b.apply()
        self.assertEqual((self.b_root / "SFC/Jogo.srm").read_bytes(), b"v1")
        self.assertEqual(self.actions(self.a), {}); self.assertEqual(self.actions(self.b), {})

    def test_fast_forward_both_ways_and_history_keeps_the_replaced_file(self):
        self.write(self.a_root, "Jogo.srm", b"v1"); self.a.apply(); self.b.apply()
        self.write(self.b_root, "Jogo.srm", b"v2"); self.assertEqual(self.actions(self.b), {"Jogo.srm": "push"}); self.b.apply()
        self.assertEqual(self.actions(self.a), {"Jogo.srm": "pull"}); self.a.apply()
        self.assertEqual((self.a_root / "Jogo.srm").read_bytes(), b"v2")
        history = list((self.a_root / ".pyretro-history/Jogo.srm").iterdir())
        self.assertEqual([p.read_bytes() for p in history], [b"v1"])

    def test_divergence_is_a_conflict_and_nothing_is_overwritten(self):
        self.write(self.a_root, "Jogo.srm", b"v1"); self.a.apply(); self.b.apply()
        self.write(self.a_root, "Jogo.srm", b"do-pc"); self.write(self.b_root, "Jogo.srm", b"do-celular")
        self.b.apply()  # o celular chega primeiro
        self.assertEqual(self.actions(self.a), {"Jogo.srm": "conflict"})
        result = self.a.apply()
        self.assertFalse(result[0]["ok"] and result[0]["action"] != "conflict")
        self.assertEqual((self.a_root / "Jogo.srm").read_bytes(), b"do-pc")
        self.assertEqual(self.actions(self.b), {})

    def test_resolve_local_replaces_all_heads_and_resolve_remote_keeps_local_in_history(self):
        self.write(self.a_root, "Jogo.srm", b"v1"); self.a.apply(); self.b.apply()
        self.write(self.a_root, "Jogo.srm", b"do-pc"); self.write(self.b_root, "Jogo.srm", b"do-celular"); self.b.apply()
        self.assertTrue(self.a.resolve("Jogo.srm", "local")["ok"])
        self.assertEqual(self.actions(self.b), {"Jogo.srm": "pull"})
        self.b.apply()
        self.assertEqual((self.b_root / "Jogo.srm").read_bytes(), b"do-pc")
        self.assertIn(b"do-celular", [p.read_bytes() for p in (self.b_root / ".pyretro-history/Jogo.srm").iterdir()])
        # outro conflito, agora resolvido a favor da nuvem
        self.write(self.a_root, "Jogo.srm", b"a2"); self.write(self.b_root, "Jogo.srm", b"b2"); self.b.apply()
        self.assertEqual(self.actions(self.a), {"Jogo.srm": "conflict"})
        self.assertTrue(self.a.resolve("Jogo.srm", "remote")["ok"])
        self.assertEqual((self.a_root / "Jogo.srm").read_bytes(), b"b2")
        self.assertIn(b"a2", [p.read_bytes() for p in (self.a_root / ".pyretro-history/Jogo.srm").iterdir()])

    def test_rerun_is_idempotent_and_deleted_local_file_is_restored_not_propagated(self):
        self.write(self.a_root, "Jogo.srm", b"v1"); self.a.apply()
        before = dict(self.storage.files)
        self.a.apply(); self.assertEqual(self.storage.files, before)
        (self.a_root / "Jogo.srm").unlink()
        self.assertEqual(self.actions(self.a), {"Jogo.srm": "pull"}); self.a.apply()
        self.assertEqual((self.a_root / "Jogo.srm").read_bytes(), b"v1")

    def test_remote_manifest_with_hostile_paths_or_tampered_blob_is_not_trusted(self):
        self.write(self.a_root, "Jogo.srm", b"v1"); self.a.apply()
        manifest = json.loads(self.storage.files["saves/devices/pc.json"])
        entry = manifest["files"]["Jogo.srm"]
        manifest["files"]["../../fora"] = entry
        manifest["files"][".pyretro-history/x"] = entry
        self.storage.files["saves/devices/pc.json"] = json.dumps(manifest).encode()
        self.assertEqual(self.actions(self.b), {"Jogo.srm": "pull"})  # os caminhos hostis foram ignorados
        self.storage.files[f"saves/blobs/{entry['sha256']}"] = b"adulterado"
        result = self.b.apply()
        self.assertFalse(result[0]["ok"]); self.assertIn("não confere", result[0]["error"])
        self.assertFalse((self.b_root / "Jogo.srm").exists())

    def test_two_entries_that_cite_each_other_keep_the_newer_one_as_the_only_head(self):
        a, b = "a" * 64, "b" * 64
        manifests = {"pc": {"files": {"Jogo.srm": {"sha256": b, "base": [a], "at": 100}}},
                     "celular": {"files": {"Jogo.srm": {"sha256": a, "base": [b], "at": 200}}}}
        self.assertEqual(CloudSaves.heads(manifests), {"Jogo.srm": {a: ["celular"]}})

    def test_hidden_state_folders_are_never_uploaded(self):
        self.write(self.a_root, ".pyretro-history/Jogo.srm/1.previous", b"x")
        self.write(self.a_root, ".pyretro-pending/Jogo.srm/1.pending", b"y")
        self.assertEqual(self.a.plan(), [])


@unittest.skipUnless(shutil.which("rclone"), "rclone não instalado")
class DevicesOnRcloneLocal(Devices):
    def setUp(self):
        self.remote = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.remote)
        super().setUp()
        self.storage = cloud.RcloneStorage(self.remote)
        self.a.storage = self.b.storage = self.storage

    def test_rerun_is_idempotent_and_deleted_local_file_is_restored_not_propagated(self):
        self.write(self.a_root, "Jogo.srm", b"v1"); self.a.apply()
        before = sorted(i["path"] for i in self.storage.list(""))
        self.a.apply(); self.assertEqual(sorted(i["path"] for i in self.storage.list("")), before)
        (self.a_root / "Jogo.srm").unlink()
        self.a.apply()
        self.assertEqual((self.a_root / "Jogo.srm").read_bytes(), b"v1")

    def test_remote_manifest_with_hostile_paths_or_tampered_blob_is_not_trusted(self):
        self.write(self.a_root, "Jogo.srm", b"v1"); self.a.apply()
        manifest = json.loads(self.storage.get("saves/devices/pc.json"))
        entry = manifest["files"]["Jogo.srm"]
        manifest["files"]["../../fora"] = entry
        self.storage.put("saves/devices/pc.json", json.dumps(manifest).encode(), overwrite=True)
        self.assertEqual(self.actions(self.b), {"Jogo.srm": "pull"})
        self.storage.put(f"saves/blobs/{entry['sha256']}", b"adulterado", overwrite=True)
        self.assertFalse(self.b.apply()[0]["ok"])
        self.assertFalse((self.b_root / "Jogo.srm").exists())


if __name__ == "__main__":
    unittest.main()


class TestCloudSync(unittest.TestCase):
    """cloud_sync a partir da configuração, com armazenamento em memória."""

    def setUp(self):
        from core import cloud_sync
        self.cs = cloud_sync
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / "saves/SFC").mkdir(parents=True); (self.tmp / "runtime-logs").mkdir()
        (self.tmp / "saves/SFC/Jogo.srm").write_bytes(b"v1"); (self.tmp / "runtime-logs/x.lrtl").write_bytes(b"log")
        self.cfg = {"pc": {"saves_root": str(self.tmp / "saves")}, "cloud": {"remote": "x", "device": "pc"}}
        self.store = cloud.MemoryStorage()

    def test_disabled_without_cloud_section_and_logs_are_never_uploaded(self):
        self.assertFalse(self.cs.enabled({"pc": {}}))
        with self.assertRaises(ValueError):
            self.cs.storage({"pc": {}})
        status = self.cs.status(self.cfg, self.store)
        self.assertEqual(status["counts"], {"push": 1})
        out = self.cs.sync(self.cfg, self.store)
        self.assertEqual((out["errors"], out["conflicts"]), ([], []))
        self.assertFalse(any("runtime-logs" in p for p in self.store.files))
        self.assertEqual(self.cs.status(self.cfg, self.store)["counts"], {})

    def test_hash_cache_skips_rehashing_unchanged_files(self):
        self.cs.sync(self.cfg, self.store)
        from unittest import mock
        with mock.patch.object(cloud_saves, "sha256_file", side_effect=AssertionError("não devia reler")):
            self.assertEqual(self.cs.status(self.cfg, self.store)["counts"], {})
