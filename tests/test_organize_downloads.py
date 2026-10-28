"""Organizar a partir de Downloads: compactados, cue/bin, imagem como capa, sobrescrita."""
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from core import organize as om
from test_api import BaseAPI

INDEX = {"gba": [{"code": "GBA", "nome": "GBA", "kind": "leve"}], "bin": [{"code": "MD", "nome": "MD", "kind": "leve"}],
         "sfc": [{"code": "SFC", "nome": "SNES", "kind": "leve"}],
         "cue": [{"code": "PS", "nome": "PlayStation", "kind": "pesado"}]}


class TestScanAndOrganize(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.roms = self.tmp / "ROMs"; self.down = self.tmp / "Downloads"
        self.roms.mkdir(); self.down.mkdir()
        with zipfile.ZipFile(self.down / "Hack v1.zip", "w") as z:
            z.writestr("Meu Hack v1 (BR) (T1.0) (www.romsportugues.com).gba", b"A" * 2048)
            z.writestr("patch.bps", b"x")
        with zipfile.ZipFile(self.down / "Disco (BR).zip", "w") as z:
            z.writestr("Disco (BR) (T1.0) (www.romsportugues.com).cue",
                       'FILE "Disco (BR) (T1.0) (www.romsportugues.com).bin" BINARY\n  TRACK 01 MODE2/2352\n')
            z.writestr("Disco (BR) (T1.0) (www.romsportugues.com).bin", b"B" * 4096)
        with zipfile.ZipFile(self.down / "Multi (BR-J).zip", "w") as z:
            z.writestr("Multi (BR-J) (T1.0).cue", 'FILE "Multi (BR-J) (Track1) (T1.0).bin" BINARY\n  TRACK 01 MODE2/2352\nFILE "Multi (BR-J) (Track2) (T1.0).bin" BINARY\n  TRACK 02 AUDIO\n')
            z.writestr("Multi (BR-J) (Track1) (T1.0).bin", b"1" * 2048)
            z.writestr("Multi (BR-J) (Track2) (T1.0).bin", b"2" * 2048)
        (self.down / "Meu-Hack.jpg").write_bytes(b"img")
        (self.down / "Jogo (BR) (T2.0) (www.romsportugues.com).sfc").write_bytes(b"S" * 1024)
        (self.down / "Não confirmado 1.crdownload").write_bytes(b"...")
        self.sources = {"downloads": self.down}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def items(self):
        return {i["id"]: i for i in om.scan(self.roms, list(self.sources.items()), INDEX)}

    def test_scan_lists_members_partials_and_side_image(self):
        items = self.items()
        hack = items["downloads/Hack v1.zip::Meu Hack v1 (BR) (T1.0) (www.romsportugues.com).gba"]
        self.assertEqual((hack["final"], hack["cover_image"]), ("Meu Hack v1.gba", "Meu-Hack.jpg"))
        self.assertNotIn("downloads/Hack v1.zip::patch.bps", items)
        self.assertEqual(items["downloads/Não confirmado 1.crdownload"]["status"], "baixando")
        self.assertEqual([c["code"] for c in items["downloads/Disco (BR).zip::Disco (BR) (T1.0) (www.romsportugues.com).cue"]["candidates"]], ["PS"])

    def test_multitrack_bins_are_tracks_not_roms(self):
        items = self.items()
        multi = [i for i in items.values() if i["name"] == "Multi (BR-J).zip"]
        self.assertEqual([i["final"] for i in multi], ["Multi.cue"])
        om.organize(self.roms, self.sources, multi[0]["id"], "PS", trash=mock.Mock())
        cue = (self.roms / "PS" / "Multi.cue").read_text()
        self.assertIn('FILE "Multi (Track1).bin"', cue); self.assertIn('FILE "Multi (Track2).bin"', cue)
        self.assertEqual(sorted(p.name for p in (self.roms / "PS").iterdir()), ["Multi (Track1).bin", "Multi (Track2).bin", "Multi.cue"])

    def test_cue_from_archive_keeps_tracks_and_rewrites_names(self):
        result = om.organize(self.roms, self.sources, "downloads/Disco (BR).zip::Disco (BR) (T1.0) (www.romsportugues.com).cue", "PS", trash=mock.Mock())
        cue = self.roms / "PS" / "Disco.cue"
        self.assertEqual(result["label"], "Disco")
        self.assertIn('FILE "Disco.bin" BINARY', cue.read_text())
        self.assertEqual((self.roms / "PS" / "Disco.bin").stat().st_size, 4096)

    def test_incomplete_cue_is_refused_and_left_in_place(self):
        (self.down / "Solto.cue").write_text('FILE "faltando.bin" BINARY\n  TRACK 01 MODE2/2352\n')
        with self.assertRaisesRegex(ValueError, "faltando.bin"):
            om.organize(self.roms, self.sources, "downloads/Solto.cue", "PS", trash=mock.Mock())
        self.assertTrue((self.down / "Solto.cue").exists())
        self.assertFalse((self.roms / "PS").exists())

    def test_incomplete_cue_inside_archive_is_refused(self):
        with zipfile.ZipFile(self.down / "Quebrado.zip", "w") as z:
            z.writestr("Quebrado.cue", 'FILE "sumiu.bin" BINARY\n  TRACK 01 MODE2/2352\n')
        with self.assertRaisesRegex(ValueError, "sumiu.bin"):
            om.organize(self.roms, self.sources, "downloads/Quebrado.zip::Quebrado.cue", "PS", trash=mock.Mock())
        self.assertFalse((self.roms / "PS").exists())

    def test_tracks_that_collide_after_cleaning_are_refused_before_moving(self):
        (self.down / "Colide.cue").write_text('FILE "A*B.bin" BINARY\n  TRACK 01 MODE2/2352\nFILE "AB.bin" BINARY\n  TRACK 02 AUDIO\n')
        (self.down / "A*B.bin").write_bytes(b"1"); (self.down / "AB.bin").write_bytes(b"2")
        trash = mock.Mock()
        with self.assertRaisesRegex(ValueError, "mesmo nome"):
            om.organize(self.roms, self.sources, "downloads/Colide.cue", "PS", trash)
        trash.assert_not_called()
        self.assertTrue((self.down / "A*B.bin").exists() and (self.down / "AB.bin").exists())
        self.assertFalse((self.roms / "PS").exists())

    def test_cue_is_published_last(self):
        order = []
        real = om._shutil.move
        with mock.patch.object(om._shutil, "move", side_effect=lambda a, b: (order.append(Path(b).suffix), real(a, b))):
            om.organize(self.roms, self.sources, "downloads/Multi (BR-J).zip::Multi (BR-J) (T1.0).cue", "PS", trash=mock.Mock())
        self.assertEqual(order[-1], ".cue")

    def test_loose_file_overwrites_existing_and_trashes_old(self):
        (self.roms / "SFC").mkdir()
        old = self.roms / "SFC" / "Jogo.sfc"; old.write_bytes(b"velho")
        trash = mock.Mock(side_effect=lambda p: p.unlink())
        om.organize(self.roms, self.sources, "downloads/Jogo (BR) (T2.0) (www.romsportugues.com).sfc", "SFC", trash)
        trash.assert_called_once_with(old)
        self.assertEqual((self.roms / "SFC" / "Jogo.sfc").read_bytes(), b"S" * 1024)
        self.assertFalse((self.down / "Jogo (BR) (T2.0) (www.romsportugues.com).sfc").exists())

    def test_refuses_partial_and_unknown(self):
        with self.assertRaises(ValueError):
            om.organize(self.roms, self.sources, "downloads/Não confirmado 1.crdownload", "SFC", mock.Mock())
        with self.assertRaises(ValueError):
            om.organize(self.roms, self.sources, "downloads/../fora.sfc", "SFC", mock.Mock())
        with self.assertRaises(LookupError):
            om.organize(self.roms, self.sources, "downloads/Sumiu.sfc", "SFC", mock.Mock())


class TestOrganizeRoutes(BaseAPI):
    def setUp(self):
        self.down = self.raiz / "Downloads"
        shutil.rmtree(self.down, ignore_errors=True); self.down.mkdir()
        shutil.rmtree(self.raiz / "ROMs/SFC", ignore_errors=True)
        (self.down / "Jogo (BR) (www.romsportugues.com).sfc").write_bytes(b"S" * 1024)
        (self.down / "Outro.sfc").write_bytes(b"O" * 1024)

    def test_pending_move_with_cover_and_genre_then_discard(self):
        import server
        status, data = self.pedir("/api/organize/pending")
        self.assertEqual(status, 200)
        ids = {i["id"] for i in data["items"]}
        self.assertIn("downloads/Jogo (BR) (www.romsportugues.com).sfc", ids)
        with mock.patch.object(server, "_organize_cover", return_value="libretro") as cover, \
                mock.patch.object(server, "_organize_genre", return_value="RPG") as genre:
            status, data = self.pedir("/api/organize/move", {"id": "downloads/Jogo (BR) (www.romsportugues.com).sfc", "code": "SFC"})
        self.assertEqual(status, 200, data)
        self.assertEqual((data["cover"], data["genero"]), ("libretro", "RPG"))
        self.assertTrue((self.raiz / "ROMs/SFC/Jogo.sfc").exists())
        cover.assert_called_once(); genre.assert_called_once_with(mock.ANY, "SFC", "Jogo")
        self.assertEqual(self.pedir("/api/organize/move", {"id": "downloads/Outro.sfc", "code": "PS2"})[0], 400)
        with mock.patch.object(server.organize_mod, "_trash", side_effect=lambda p, **k: p.unlink()):
            self.assertEqual(self.pedir("/api/organize/discard", {"id": "downloads/Outro.sfc"})[0], 200)
        self.assertFalse((self.down / "Outro.sfc").exists())
        self.assertEqual(self.pedir("/api/organize/discard", {"id": "downloads/../x"})[0], 404)


class TestCleanNames(unittest.TestCase):
    def test_translation_credits_go_standard_tags_stay(self):
        casos = {
            "Flicky (BR-U-E) (T1.0) (www.romsportugues.com).md": "Flicky.md",
            "Terranigma (BR) (DindoeCia) (T2.0) (www.romsportugues.com).sfc": "Terranigma.sfc",
            "Popeye - Ijiwaru Majo Sea Hag no Maki (BR) (T1.0) (Starman) (www.romsportugues.com).sfc": "Popeye - Ijiwaru Majo Sea Hag no Maki.sfc",
            "Vandal Hearts II (BR-EUR) (T107-Beta) (www.romsportugues.com).cue": "Vandal Hearts II.cue",
            "Jogo (Europe) (T1.0).sfc": "Jogo (Europe).sfc",
            "Jogo (USA) (Rev 1).sfc": "Jogo (USA) (Rev 1).sfc",
            "Final Fantasy (Disc 1) (T2.0) (Grupo).bin": "Final Fantasy (Disc 1).bin",
            "Castlevania - Lament of Innocence (BR) (DUB) (Matth) (T1.0) (www.romsportugues).iso": "Castlevania - Lament of Innocence.iso",
            "PoPoLoCrois (BR-EUR) (T201_RC5) (www.romsportugues.com).iso": "PoPoLoCrois.iso",
        }
        for original, esperado in casos.items():
            self.assertEqual(om.clean_name(original), esperado, original)
