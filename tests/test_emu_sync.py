"""Testes da janela plan→apply da sincronização de saves."""
import os
import tempfile
import unittest
from pathlib import Path

from core import emu_sync


class TestRevalidacaoAntesDeCopiar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.drive = root / "drive"
        self.android = root / "android"
        self.drive.mkdir()
        self.android.mkdir()
        self.original = dict(emu_sync.SOURCES)
        emu_sync.SOURCES["teste"] = {
            "nome": "Teste",
            "get_pc_root": None,
            "get_drive_root": lambda _cfg: self.drive,
            "android_root": str(self.android),
        }

    def tearDown(self):
        emu_sync.SOURCES.clear()
        emu_sync.SOURCES.update(self.original)
        self.tmp.cleanup()

    def _preparar(self):
        drive_file = self.drive / "save.bin"
        android_file = self.android / "save.bin"
        drive_file.write_bytes(b"antigo")
        android_file.write_bytes(b"novo")
        os.utime(drive_file, (1000, 1000))
        os.utime(android_file, (2000, 2000))
        plano = emu_sync.plan("teste", {}, local_mode=True)
        self.assertEqual(plano["actions"][0]["direction"], "android->drive")
        return drive_file, android_file, plano["actions"]

    def test_cancela_se_origem_mudou_depois_do_plano(self):
        drive_file, android_file, actions = self._preparar()
        android_file.write_bytes(b"mudou outra vez")
        os.utime(android_file, (3000, 3000))

        result = emu_sync.apply(actions, {}, local_mode=True)
        self.assertFalse(result[0]["ok"])
        self.assertIn("origem mudou", result[0]["erro"])
        self.assertEqual(drive_file.read_bytes(), b"antigo")

    def test_copia_quando_origem_continua_igual(self):
        drive_file, _android_file, actions = self._preparar()
        result = emu_sync.apply(actions, {}, local_mode=True)
        self.assertTrue(result[0]["ok"])
        self.assertEqual(drive_file.read_bytes(), b"novo")


if __name__ == "__main__":
    unittest.main()
