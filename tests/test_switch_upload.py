import tempfile
import unittest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace

from core import switch_upload as su

CFG = {"rclone": {"remote": "drive", "drive_roms_root": "Jogos/ROMs"},
       "pc": {"library_root": "/nonexistent"}}


class FakeRun:
    def __init__(self, fail_check=False):
        self.calls, self.fail_check = [], fail_check

    def __call__(self, args, **kw):
        self.calls.append(args)
        bad = self.fail_check and args[1] == "check"
        return SimpleNamespace(returncode=1 if bad else 0, stdout="", stderr="x")


class SwitchUploadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dl = Path(self.tmp.name)
        pasta = self.dl / "Outbound [NSZ]"
        pasta.mkdir()
        (pasta / "Outbound [0100ED9024EB8000][v0] (1.62 GB).nsz").write_bytes(b"a")
        (pasta / "leiame.txt").write_text("x")
        (self.dl / "Outro Jogo (0.5 GB).nsp").write_bytes(b"b")
        (self.dl / "foto.png").write_bytes(b"c")

    def tearDown(self):
        self.tmp.cleanup()

    def test_nome_limpo(self):
        self.assertEqual(su.nome_do_jogo("Outbound [NSZ]"), "Outbound")
        self.assertEqual(su.nome_do_jogo("Outro Jogo (0.5 GB).nsp"), "Outro Jogo")

    def test_scan_ignora_nao_switch(self):
        itens = {i["entry"]: i for i in su.scan(self.dl)}
        self.assertEqual(set(itens), {"Outbound [NSZ]", "Outro Jogo (0.5 GB).nsp"})
        self.assertEqual(len(itens["Outbound [NSZ]"]["files"]), 1)

    def test_upload_confere_e_manda_para_lixeira(self):
        run, lixo = FakeRun(), []
        with mock.patch.object(su, "registrar", lambda lib, nome, cfg, genero=None: {"id": "x", "capa": None, "genero": genero}):
            r = su.upload(self.dl, "Outbound [NSZ]", "Outbound", CFG, lixo.append,
                          lambda fn: fn({"games": []}), genero="Simulação", run=run)
        self.assertEqual(r["genero"], "Simulação")
        self.assertEqual(lixo, [self.dl / "Outbound [NSZ]"])
        self.assertTrue(run.calls[0][3].endswith("drive:Jogos/ROMs/NSW/Outbound/Outbound [0100ED9024EB8000][v0] (1.62 GB).nsz"))

    def test_divergencia_mantem_origem(self):
        lixo = []
        with self.assertRaises(OSError):
            su.upload(self.dl, "Outro Jogo (0.5 GB).nsp", "Outro Jogo", CFG, lixo.append, lambda fn: None,
                      run=FakeRun(fail_check=True))
        self.assertEqual(lixo, [])

    def test_recusa_caminho(self):
        with self.assertRaises(ValueError):
            su.upload(self.dl, "../x", "x", CFG, lambda p: None, lambda fn: None, run=FakeRun())


if __name__ == "__main__":
    unittest.main()
