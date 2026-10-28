"""Modelo de armazenamento: resolvedor de destinos e prévia de migração (somente leitura)."""
import os
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


class TestCopyVerified(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "src"; self.dst = self.tmp / "dst"
        (self.src / "SFC").mkdir(parents=True)
        (self.src / "SFC/Jogo.sfc").write_bytes(b"jogo" * 1000)
        (self.src / "SFC/leia.txt").write_text("oi")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def items(self):
        return [{"category": "roms", "source": str(self.src / "SFC"), "target": str(self.dst / "SFC")},
                {"category": "capas", "source": str(self.src), "target": str(self.dst / "outra")}]

    def test_copies_verifies_keeps_source_and_writes_receipt(self):
        result = storage.copy_items(self.items(), {"roms"}, self.dst, log=lambda m: None)
        self.assertEqual((result["copied"], result["identical"], result["errors"]), (2, 0, []))
        self.assertEqual((self.dst / "SFC/Jogo.sfc").read_bytes(), b"jogo" * 1000)
        self.assertTrue((self.src / "SFC/Jogo.sfc").exists())
        self.assertFalse((self.dst / "outra").exists())
        self.assertFalse(list(self.dst.rglob("*.pyretro-part")))
        self.assertTrue(Path(result["receipt"]).is_file())
        self.assertEqual(len(result["files"][0]["sha256"]), 64)

    def test_rerun_is_idempotent_and_never_overwrites_a_different_file(self):
        storage.copy_items(self.items(), {"roms"}, self.dst, log=lambda m: None)
        again = storage.copy_items(self.items(), {"roms"}, self.dst, log=lambda m: None)
        self.assertEqual((again["copied"], again["identical"]), (0, 2))
        (self.dst / "SFC/leia.txt").write_text("alterado")
        third = storage.copy_items(self.items(), {"roms"}, self.dst, log=lambda m: None)
        self.assertEqual(len(third["errors"]), 1)
        self.assertEqual((self.dst / "SFC/leia.txt").read_text(), "alterado")

    def test_corrupt_copy_is_removed_and_reported(self):
        real = storage._sha256
        calls = []
        def broken(path):
            calls.append(path); return "0" * 64
        with mock.patch.object(storage, "_sha256", broken):
            result = storage.copy_items(self.items(), {"roms"}, self.dst, log=lambda m: None)
        self.assertEqual(len(result["errors"]), 2)
        self.assertFalse((self.dst / "SFC/Jogo.sfc").exists())
        self.assertFalse(list(self.dst.rglob("*.pyretro-part")))
        self.assertTrue((self.src / "SFC/Jogo.sfc").exists())

    def test_source_changed_during_copy_is_refused(self):
        source = self.src / "SFC/Jogo.sfc"
        original = Path.stat
        calls = []

        def stat(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if path == source:
                calls.append(1)
                if len(calls) >= 2:  # a leitura depois da cópia vê outro mtime
                    return mock.Mock(st_size=result.st_size, st_mtime_ns=result.st_mtime_ns + 1)
            return result
        with mock.patch.object(Path, "stat", stat):
            with self.assertRaisesRegex(OSError, "origem mudou"):
                storage.copy_verified(source, self.dst / "x.sfc")
        self.assertFalse((self.dst / "x.sfc").exists())
        self.assertFalse(list(self.dst.rglob("*.pyretro-part")))


if __name__ == "__main__":
    unittest.main()
