"""Modelo de armazenamento: resolvedor de destinos e prévia de migração (somente leitura)."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import storage


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.jogos = self.tmp / "Drive" / "Jogos"
        for sub in ("ROMs/SFC", "ROMs/PS", "ROMs/NSW/Titulo A", "ROMs/0-Organizar", "Saves/saves/SFC", "Capas", "Biblioteca", "Backups", "BIOS"):
            (self.jogos / sub).mkdir(parents=True)
        (self.jogos / "ROMs/SFC/Jogo.sfc").write_bytes(b"x" * 100)
        (self.jogos / "Saves/saves/SFC/Jogo.srm").write_bytes(b"s" * 10)
        (self.jogos / "ROMs/NSW/Titulo A/base.nsp").write_bytes(b"n" * 50)
        (self.jogos / "ROMs/NSW/Outro Jogo [0100ABC][v65536].nsp").write_bytes(b"u" * 20)
        (self.jogos / "ROMs/NSW/Outro Jogo [0100ABD][UPD].nsp").write_bytes(b"d" * 20)
        (self.jogos / "ROMs/PS/Disco.cue").write_text('FILE "Disco.bin" BINARY\n  TRACK 01 MODE2/2352\n')
        (self.jogos / "ROMs/PS/Disco.bin").write_bytes(b"b" * 30)
        (self.jogos / "ROMs/PS/Quebrado.cue").write_text('FILE "sumiu.bin" BINARY\n  TRACK 01 MODE2/2352\n')
        self.cfg = {"pc": {"roms_root": str(self.jogos / "ROMs"), "saves_root": str(self.jogos / "Saves/saves"),
                           "capas_root": str(self.jogos / "Capas"), "library_root": str(self.jogos / "Biblioteca"),
                           "backups_root": str(self.jogos / "Backups")}}
        self.games = self.tmp / "Games" / "PyRetro"; self.nsw = self.tmp / "Downloads" / "NSW"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def plan(self, **kw):
        return storage.plan(self.cfg, self.games, self.nsw, consumers=[], **kw)

    def test_resolver_current_target_and_configured(self):
        cur, new = storage.Layout.current(self.cfg), storage.Layout.target(self.games, self.nsw)
        self.assertEqual(cur.rom_dir("SFC"), self.jogos / "ROMs/SFC"); self.assertEqual(cur.rom_dir("NSW"), self.jogos / "ROMs/NSW")
        self.assertEqual(new.rom_dir("SFC"), self.games / "ROMs/SFC"); self.assertEqual(new.rom_dir("NSW"), self.nsw)
        self.assertEqual(new.saves_dir("states"), self.games / "Saves/states")
        self.assertFalse(storage.Layout.configured(self.cfg).migrated)
        self.assertTrue(storage.Layout.configured({**self.cfg, "storage": {"games_root": str(self.games)}}).migrated)

    def test_nsw_title_folders_group_base_update_and_dlc(self):
        self.assertEqual(storage.nsw_title("Outro Jogo [0100ABC][v65536].nsp"), "Outro Jogo")
        self.assertEqual(storage.nsw_title("Zelda (USA) [0100].xci"), "Zelda")
        self.assertEqual(storage.nsw_title("[0100].nsp"), "")
        self.assertEqual(storage.Layout.target(self.games, self.nsw).nsw_title_dir("Mario [UPD].nsp"), self.nsw / "Mario")
        with self.assertRaises(ValueError):
            storage.Layout.target(self.games, self.nsw).nsw_title_dir("[0100].nsp")

    def test_plan_is_read_only_and_maps_every_category(self):
        before = sorted(p.relative_to(self.tmp) for p in self.tmp.rglob("*"))
        result = self.plan()
        self.assertEqual(sorted(p.relative_to(self.tmp) for p in self.tmp.rglob("*")), before)
        self.assertFalse(self.games.exists() or self.nsw.exists())
        targets = {i["target"] for i in result["items"]}
        self.assertIn(str(self.games / "ROMs/SFC"), targets); self.assertIn(str(self.games / "Saves"), targets)
        self.assertIn(str(self.nsw / "Titulo A"), targets); self.assertIn(str(self.nsw / "Outro Jogo"), targets)
        grouped = [i for i in result["items"] if i["target"] == str(self.nsw / "Outro Jogo")][0]
        self.assertEqual((grouped["files"], grouped["bytes"]), (2, 40))
        self.assertEqual(result["issues"]["blocking"], [])
        self.assertIn("copiar e verificar", result["method"])

    def test_incomplete_disc_descriptor_is_a_warning_with_the_missing_track(self):
        warnings = self.plan()["issues"]["warnings"]
        self.assertTrue(any("Quebrado.cue" in w and "faixas ausentes" in w for w in warnings))
        self.assertFalse(any("Disco.cue" in w for w in warnings))

    def test_roots_inside_drive_or_overlapping_are_blocking(self):
        self.games = self.jogos / "Games"
        self.assertTrue(any("dentro do Drive" in m for m in self.plan()["issues"]["blocking"]))
        self.games = self.tmp / "G"; self.nsw = self.games / "NSW"
        self.assertTrue(any("se conter" in m for m in self.plan()["issues"]["blocking"]))

    def test_existing_target_is_checked_not_overwritten_and_symlinks_are_reported(self):
        (self.games / "ROMs/SFC").mkdir(parents=True)
        (self.jogos / "ROMs/SFC/atalho").symlink_to(self.jogos / "ROMs/PS")
        result = self.plan()
        self.assertTrue(any("já existe" in w for w in result["issues"]["warnings"]))
        self.assertTrue(any("link(s) simbólico(s)" in w for w in result["issues"]["warnings"]))
        self.assertEqual([i for i in result["items"] if i["target"] == str(self.games / "ROMs/SFC")][0]["symlink_count"], 1)

    def test_not_enough_space_blocks(self):
        usage = shutil.disk_usage(self.tmp)
        with mock.patch.object(storage.shutil, "disk_usage", return_value=usage._replace(free=10)):
            self.assertTrue(any("espaço insuficiente" in m for m in self.plan()["issues"]["blocking"]))

    def test_consumers_find_old_root_in_launcher_and_retroarch(self):
        home = self.tmp / "home"; (home / ".local/bin").mkdir(parents=True)
        (home / ".local/bin/bonisarch-emulator").write_text("root = Path.home() / 'Drive/Jogos/ROMs'\n")
        cfg = home / ".var/app/org.libretro.RetroArch/config/retroarch"; cfg.mkdir(parents=True)
        (cfg / "retroarch.cfg").write_text(f'savefile_directory = "{self.jogos}/Saves/saves"\nvideo_driver = "vulkan"\n')
        with mock.patch.object(storage.subprocess, "run", side_effect=OSError):
            found = storage.find_consumers(self.jogos, home)
        self.assertEqual({(c["kind"]) for c in found}, {"lançador", "retroarch"})
        self.assertEqual([c["detail"] for c in found if c["kind"] == "retroarch"], ["savefile_directory"])


if __name__ == "__main__":
    unittest.main()
