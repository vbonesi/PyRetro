"""Cascata ROM → save/state: saves_root/states_root são achatados, então o
vínculo jogo ↔ save é só o nome. Nunca pode pegar save de outro jogo."""
import tempfile
import unittest
from pathlib import Path

from core import rom_rename
from test_api import BaseAPI


class TestFlatMatches(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmp.name)
        self.roms = self.raiz / "ROMs" / "FC"; self.roms.mkdir(parents=True)
        self.saves = self.raiz / "saves"; self.saves.mkdir()
        self.states = self.raiz / "states"; self.states.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def test_title_continuing_after_dot_is_another_game(self):
        for name in ("Super Mario Bros.srm", "Super Mario Bros. 3.srm", "Super Mario Bros.state.auto", "Super Mario Bros.state1.png"):
            (self.saves / name).write_bytes(b"s")
        found = [p.name for p in rom_rename.find_flat_matches(self.saves, "Super Mario Bros")]
        self.assertEqual(found, ["Super Mario Bros.srm", "Super Mario Bros.state.auto", "Super Mario Bros.state1.png"])
        self.assertEqual([p.name for p in rom_rename.find_flat_matches(self.saves, "Super Mario Bros. 3")], ["Super Mario Bros. 3.srm"])

    def test_delete_cascade_keeps_other_game_save(self):
        (self.roms / "Super Mario Bros.nes").write_bytes(b"rom")
        (self.saves / "Super Mario Bros.srm").write_bytes(b"s")
        (self.saves / "Super Mario Bros. 3.srm").write_bytes(b"s3")
        result = rom_rename.delete_with_cascade(self.roms, None, self.saves, self.states, "Super Mario Bros", ["nes"])
        self.assertEqual(result["rom"]["status"], "apagado")
        self.assertTrue((self.saves / "Super Mario Bros. 3.srm").exists())
        self.assertFalse((self.saves / "Super Mario Bros.srm").exists())

    def test_skip_flat_leaves_shared_saves_untouched(self):
        (self.roms / "Aladdin.nes").write_bytes(b"rom")
        (self.saves / "Aladdin.srm").write_bytes(b"s")
        renamed = rom_rename.rename_with_cascade(self.roms, self.saves, self.states, "Aladdin", "Aladdin (USA)", ["nes"], skip_flat=True)
        self.assertEqual(renamed["rom"]["status"], "renomeado")
        self.assertTrue(renamed["flat_skipped"])
        self.assertTrue((self.saves / "Aladdin.srm").exists())
        self.assertEqual(renamed["flat_kept"], ["Aladdin.srm"], "a tela precisa dizer quais arquivos ficaram")

    def test_systems_with_label(self):
        md = self.raiz / "ROMs" / "MD"; md.mkdir()
        (self.roms / "Aladdin.nes").write_bytes(b"rom"); (md / "Aladdin.md").write_bytes(b"rom")
        self.assertEqual(rom_rename.systems_with_label(self.raiz / "ROMs", ["FC", "MD", "SFC"], "Aladdin"), ["FC", "MD"])
        self.assertEqual(rom_rename.systems_with_label(self.raiz / "ROMs", ["FC", "MD"], "Alad"), [])


class TestSharedSaveAPI(BaseAPI):
    def test_delete_save_refuses_label_shared_between_systems(self):
        ps2 = self.raiz / "ROMs" / "PS2"; ps2.mkdir(exist_ok=True)
        (ps2 / "Final Fantasy VI.iso").write_bytes(b"rom")
        save = self.raiz / "Saves" / "saves" / "Final Fantasy VI.srm"; save.write_bytes(b"save")
        try:
            status, body = self.pedir("/api/cover/delete_save", {"label": "Final Fantasy VI", "kind": "save"})
            self.assertEqual(status, 409, body)
            self.assertTrue(save.exists())
        finally:
            (ps2 / "Final Fantasy VI.iso").unlink(); save.unlink(missing_ok=True)

    def test_delete_save_rejects_invalid_label(self):
        self.assertEqual(self.pedir("/api/cover/delete_save", {"label": "../x", "kind": "save"})[0], 400)
        self.assertEqual(self.pedir("/api/cover/delete_save", {"kind": "save"})[0], 400)


class TestRenameFollowsLinks(BaseAPI):
    def test_cover_rename_keeps_library_tv_time_and_android_alias(self):
        from core import playtime, library as lm, rename_links
        rom = self.raiz / "ROMs" / "SFC" / "Zelda Link.sfc"; rom.write_bytes(b"rom")
        capa = self.capas_dir / "Zelda Link.png"; capa.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 2000)
        jogo = lm._blank_game("Zelda Link", "Super Nintendo"); jogo["finalizado"] = True
        self.gravar_biblioteca([jogo])
        old_key = rename_links.rom_key("SFC", "Zelda Link")
        playtime.record(self.raiz / "cache/playtime.json", old_key, 600, event="e1")
        try:
            status, body = self.pedir("/api/cover/rename", {"code": "SFC", "label": "Zelda Link", "new_label": "A Link to the Past"})
            self.assertEqual(status, 200, body)
            self.assertEqual(body["cascade"]["rom"]["status"], "renomeado")
            self.assertTrue(body["links"]["biblioteca"])
            self.assertTrue(body["links"]["tempo"])
            lib = lm.load_library(self.lib_path)
            index = lm.index_by_rom_name(lib)
            self.assertTrue(lm.find_for_rom(index, "A Link to the Past", "SFC")["finalizado"])
            new_key = rename_links.rom_key("SFC", "A Link to the Past")
            times = playtime.load(self.raiz / "cache/playtime.json")
            self.assertNotIn(old_key, times); self.assertEqual(times[new_key]["seconds"], 600)
            self.assertEqual(self.pedir("/api/tv/key_aliases")[1], {old_key: new_key})
        finally:
            for p in (self.raiz / "ROMs/SFC/A Link to the Past.sfc", self.capas_dir / "A Link to the Past.png", rom, capa):
                p.unlink(missing_ok=True)
            for p in ("cache/playtime.json", "cache/key_aliases.json"):
                (self.raiz / p).unlink(missing_ok=True)

    def test_region_only_rename_needs_no_alias(self):
        from core import rename_links
        self.assertEqual(rename_links.rom_key("SFC", "Aladdin"), rename_links.rom_key("SFC", "Aladdin (USA)"))


class TestDeleteSaveSystemFolder(BaseAPI):
    def test_delete_save_with_code_uses_system_folder_even_if_shared(self):
        ps2 = self.raiz / "ROMs" / "PS2"; ps2.mkdir(exist_ok=True)
        (ps2 / "Final Fantasy VI.iso").write_bytes(b"rom")
        pasta = self.raiz / "Saves" / "saves" / "SFC"; pasta.mkdir(exist_ok=True)
        save = pasta / "Final Fantasy VI.srm"; save.write_bytes(b"save")
        try:
            status, body = self.pedir("/api/cover/delete_save", {"code": "SFC", "label": "Final Fantasy VI", "kind": "save"})
            self.assertEqual(status, 200, body)
            self.assertFalse(save.exists())
        finally:
            (ps2 / "Final Fantasy VI.iso").unlink(); save.unlink(missing_ok=True)


class TestGameSaves(unittest.TestCase):
    def test_lists_system_folder_and_marks_legacy_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            saves, states = Path(tmp, "saves"), Path(tmp, "states")
            (saves / "SFC").mkdir(parents=True); (states / "SFC").mkdir(parents=True)
            Path(saves, "SFC", "Final Fantasy VI.srm").write_bytes(b"x" * 8192)
            Path(states, "SFC", "Final Fantasy VI.state.auto").write_bytes(b"y")
            Path(saves, "Final Fantasy VI.srm").write_bytes(b"old")
            Path(saves, "SFC", "Final Fantasy VI - Bonus.srm").write_bytes(b"z")  # outro jogo
            items = rom_rename.game_saves(saves, states, "SFC", "Final Fantasy VI")
            self.assertEqual(sorted((i["kind"], i["name"], i["legado"]) for i in items),
                             [("save", "Final Fantasy VI.srm", False), ("save", "Final Fantasy VI.srm", True),
                              ("state", "Final Fantasy VI.state.auto", False)])

    def test_heavy_label_with_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            saves = Path(tmp, "saves"); (saves / "PS").mkdir(parents=True)
            Path(saves, "PS", "Crash.srm").write_bytes(b"x")
            self.assertEqual([i["name"] for i in rom_rename.game_saves(saves, Path(tmp, "states"), "PS", "Crash.chd")], ["Crash.srm"])
