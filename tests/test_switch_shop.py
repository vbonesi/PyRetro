import json
import unittest
from datetime import datetime
from types import SimpleNamespace

from core import switch_shop as shop

CFG = {"rclone": {"remote": "drive", "drive_roms_root": "Jogos/ROMs"}, "cloud": {"remote": "drive:Nuvem"}}
AGORA = datetime(2026, 1, 2, 3, 4)


def item(nome, id_, size=10, pasta="Jogo A", is_dir=False):
    return {"Name": nome, "Path": f"{pasta}/{nome}", "Size": size, "ID": id_, "IsDir": is_dir}


class FakeRun:
    def __init__(self, entradas=None, lsjson_rc=0, stdout=None, rcat_rc=0):
        self.calls, self.inputs = [], []
        self.entradas, self.lsjson_rc, self.stdout, self.rcat_rc = entradas or [], lsjson_rc, stdout, rcat_rc

    def __call__(self, args, **kw):
        self.calls.append(args)
        if args[1] == "lsjson":
            out = json.dumps(self.entradas) if self.stdout is None else self.stdout
            return SimpleNamespace(returncode=self.lsjson_rc, stdout=out, stderr="falhou")
        self.inputs.append(kw.get("input"))
        return SimpleNamespace(returncode=self.rcat_rc, stdout="", stderr="sem escrita")


class SwitchShopTest(unittest.TestCase):
    def test_monta_formato_tinfoil(self):
        idx = shop.montar([
            item("X [0100AAAA00000000][v0].nsp", "ID1", 5),
            item("X [0100AAAA00000800][v65536].NSZ", "ID2", 7),
            item("Y.xci", "ID3"), item("Z.xcz", "ID4"),
        ], AGORA)
        self.assertEqual(idx["files"][0], {"url": "gdrive:/ID1#X [0100AAAA00000000][v0].nsp", "size": 5})
        self.assertEqual(len(idx["files"]), 4)
        self.assertIn("4 arquivo(s)", idx["success"])
        self.assertIn("02/01/2026 03:04", idx["success"])

    def test_ignora_parciais_pastas_e_extensoes(self):
        idx = shop.montar([
            item("a.nsp.part", "1"), item("b.nsz.crdownload", "2"), item("c.txt", "3"),
            item("d.nsp", "4", is_dir=True), item("e.nsp", ""), item("ok.nsp", "5"),
        ], AGORA)
        self.assertEqual([f["url"] for f in idx["files"]], ["gdrive:/5#ok.nsp"])

    def test_pasta_vazia(self):
        r = FakeRun([])
        out = shop.gerar(CFG, run=r)
        self.assertEqual(out["arquivos"], 0)
        self.assertEqual(json.loads(r.inputs[0])["files"], [])

    def test_gera_e_sobe_com_uma_listagem(self):
        r = FakeRun([item("A.nsp", "ID1", 3)])
        out = shop.gerar(CFG, run=r)
        self.assertEqual(out, {"arquivos": 1, "destino": "drive:Nuvem/switch"})
        listagens = [c for c in r.calls if c[1] == "lsjson"]
        self.assertEqual(len(listagens), 1)
        self.assertIn("-R", listagens[0])
        self.assertEqual(listagens[0][-1], "drive:Jogos/ROMs/NSW")
        self.assertEqual(r.calls[-1], ["rclone", "rcat", "drive:Nuvem/switch/shop.json"])
        self.assertEqual(json.loads(r.inputs[0])["files"][0]["url"], "gdrive:/ID1#A.nsp")

    def test_destino_padrao_sem_cloud(self):
        cfg = {"rclone": {"remote": "meu", "drive_roms_root": "R"}}
        r = FakeRun([])
        self.assertEqual(shop.gerar(cfg, run=r)["destino"], "meu:Jogos/PyRetro-Nuvem/switch")

    def test_falha_do_rclone_nao_grava(self):
        r = FakeRun([item("A.nsp", "1")], lsjson_rc=3)
        with self.assertRaises(OSError):
            shop.gerar(CFG, run=r)
        self.assertFalse(any(c[1] == "rcat" for c in r.calls))

    def test_resposta_ilegivel_nao_grava(self):
        r = FakeRun(stdout="não é json")
        with self.assertRaises(OSError):
            shop.gerar(CFG, run=r)
        self.assertFalse(any(c[1] == "rcat" for c in r.calls))

    def test_falha_ao_gravar(self):
        with self.assertRaises(OSError):
            shop.gerar(CFG, run=FakeRun([], rcat_rc=1))

    def test_rclone_ausente(self):
        def run(*a, **k):
            raise FileNotFoundError("rclone")
        with self.assertRaises(OSError):
            shop.gerar(CFG, run=run)


if __name__ == "__main__":
    unittest.main()
