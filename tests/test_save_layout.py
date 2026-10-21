"""Migração de saves achatados para pasta por sistema (core/save_layout.py)."""
import tempfile
import unittest
from pathlib import Path

from core import rom_rename, save_layout


class TestSaveLayout(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(); self.raiz = Path(self._tmp.name)
        for code, names in {"N64": ["Super Mario 64.z64"], "FC": ["Aladdin.nes", "Super Mario Bros.nes", "Super Mario Bros. 3.nes"], "MD": ["Aladdin.md"], "ARCADE": ["kof97.zip"]}.items():
            (self.raiz / "ROMs" / code).mkdir(parents=True)
            for n in names: (self.raiz / "ROMs" / code / n).write_bytes(b"rom")
        self.codes = ["N64", "FC", "MD", "ARCADE", "SFC"]
        self.saves = self.raiz / "saves"; self.saves.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def labels(self):
        return save_layout.rom_labels(self.raiz / "ROMs", self.codes)

    def test_plan_moves_unique_owners_and_reports_the_rest(self):
        for n in ("Super Mario 64.srm", "Aladdin.srm", "Super Mario Bros. 3.srm", "Orfao.srm"):
            (self.saves / n).write_bytes(b"s")
        (self.saves / "Backup").mkdir(); (self.saves / "Backup" / "x.srm").write_bytes(b"s")
        (self.saves / "fbneo").mkdir(); (self.saves / "fbneo" / "kof97.fs").write_bytes(b"s")
        result = save_layout.plan(save_layout.local_entries(self.saves), self.labels(), self.codes)
        self.assertEqual(sorted(result["moves"]), [("Super Mario 64.srm", "N64/Super Mario 64.srm"),
            ("Super Mario Bros. 3.srm", "FC/Super Mario Bros. 3.srm"), ("fbneo/kof97.fs", "ARCADE/fbneo/kof97.fs")])
        reasons = dict(result["skipped"])
        self.assertIn("FC, MD", reasons["Aladdin.srm"]); self.assertIn("nenhuma ROM", reasons["Orfao.srm"])
        self.assertNotIn("Backup/", reasons)

    def test_apply_checks_everything_before_moving_and_never_overwrites(self):
        (self.saves / "Super Mario 64.srm").write_bytes(b"velho")
        (self.saves / "N64").mkdir(); (self.saves / "N64" / "Super Mario 64.srm").write_bytes(b"novo")
        (self.saves / "fbneo").mkdir(); (self.saves / "fbneo" / "kof97.fs").write_bytes(b"s")
        moves = [("fbneo/kof97.fs", "ARCADE/fbneo/kof97.fs"), ("Super Mario 64.srm", "N64/Super Mario 64.srm")]
        with self.assertRaises(FileExistsError):
            save_layout.apply_local(self.saves, moves)
        self.assertTrue((self.saves / "fbneo" / "kof97.fs").exists())  # nada foi movido
        self.assertEqual((self.saves / "N64" / "Super Mario 64.srm").read_bytes(), b"novo")

    def test_apply_moves_and_removes_empty_core_folder(self):
        (self.saves / "fbneo").mkdir(); (self.saves / "fbneo" / "kof97.fs").write_bytes(b"s")
        save_layout.apply_local(self.saves, [("fbneo/kof97.fs", "ARCADE/fbneo/kof97.fs")])
        self.assertTrue((self.saves / "ARCADE" / "fbneo" / "kof97.fs").exists())
        self.assertFalse((self.saves / "fbneo").exists())

    def test_cascade_uses_system_folder_even_for_shared_label(self):
        (self.saves / "FC").mkdir(); (self.saves / "FC" / "Aladdin.srm").write_bytes(b"nes")
        (self.saves / "MD").mkdir(); (self.saves / "MD" / "Aladdin.srm").write_bytes(b"md")
        states = self.raiz / "states"; states.mkdir()
        result = rom_rename.delete_with_cascade(self.raiz / "ROMs" / "FC", None, self.saves, states, "Aladdin", ["nes"], skip_flat=True)
        self.assertEqual(result["saves"], [str(self.saves / "FC" / "Aladdin.srm")])
        self.assertTrue((self.saves / "MD" / "Aladdin.srm").exists())
