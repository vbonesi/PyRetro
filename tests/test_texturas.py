"""Testes de core/texturas.py: instalação, manifesto, remoção e validações.
Sem rede: o pacote é um .zip criado na hora e o download é pulado passando
`arquivo=`."""
import hashlib
import json
import sys
import tempfile
import unittest
import urllib.request
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import texturas as tx


def _zip(path: Path, arquivos: dict) -> Path:
    with zipfile.ZipFile(path, "w") as z:
        for nome, dados in arquivos.items():
            z.writestr(nome, dados)
    return path


class TexturasTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.cfg = {"texturas": {"ps2": str(self.dir / "ps2"), "psp": str(self.dir / "psp")}}
        self.pacote = {"id": "ps2-slus-21065", "sistema": "PS2", "id_jogo": "SLUS-21065",
                       "nome": "Need for Speed Underground 2 (USA)", "arquivo": "x.zip"}
        self.addCleanup(self._tmp.cleanup)

    def test_instala_pasta_do_serial_com_replacements(self):
        z = _zip(self.dir / "p.zip", {"SLUS-21065/replacements/a.png": "1",
                                      "SLUS-21065/replacements/sub/b.png": "2"})
        with mock.patch.object(tx, "CACHE_DIR", self.dir / "cache"):
            n = tx.instalar(self.pacote, self.cfg, arquivo=z)
        self.assertEqual(n, 2)
        base = self.dir / "ps2/SLUS-21065/replacements"
        self.assertEqual((base / "a.png").read_text(), "1")
        self.assertEqual((base / "sub/b.png").read_text(), "2")
        self.assertEqual(tx.estado(self.pacote, self.cfg), {"instalado": True, "arquivos": 2})

    def test_instala_zip_so_com_png_soltos_no_ps2(self):
        z = _zip(self.dir / "p.zip", {"a.png": "1"})
        with mock.patch.object(tx, "CACHE_DIR", self.dir / "cache"):
            tx.instalar(self.pacote, self.cfg, arquivo=z)
        self.assertTrue((self.dir / "ps2/SLUS-21065/replacements/a.png").is_file())

    def test_remover_apaga_so_o_que_o_pacote_instalou(self):
        dest = self.dir / "ps2/SLUS-21065/replacements"
        dest.mkdir(parents=True)
        (dest / "meu_dump.png").write_text("meu")
        z = _zip(self.dir / "p.zip", {"a.png": "1", "s/b.png": "2"})
        with mock.patch.object(tx, "CACHE_DIR", self.dir / "cache"):
            tx.instalar(self.pacote, self.cfg, arquivo=z)
        self.assertEqual(tx.remover(self.pacote, self.cfg), 2)
        self.assertTrue((dest / "meu_dump.png").is_file())
        self.assertFalse((dest / "a.png").exists())
        self.assertFalse((dest / "s").exists())
        self.assertFalse(tx.estado(self.pacote, self.cfg)["instalado"])

    def test_remover_sem_instalar_falha(self):
        with self.assertRaises(tx.TexturaErro):
            tx.remover(self.pacote, self.cfg)

    def test_id_de_jogo_invalido_nao_vira_pasta(self):
        for ruim in ("../x", "SLUS-2106", "", "SLUS-21065/../../x"):
            with self.assertRaises(tx.TexturaErro):
                tx.pasta_jogo("PS2", ruim, self.cfg)

    def test_zip_com_caminho_fugindo_e_recusado(self):
        z = _zip(self.dir / "p.zip", {"../fora.png": "x"})
        with self.assertRaises(tx.TexturaErro):
            tx.extrair(z, self.dir / "out")

    def test_ps1_usa_replacements_e_serial(self):
        cfg = {"texturas": {"ps1": str(self.dir / "ps1")}}
        p = {"id": "ps1-sles-00049", "sistema": "PS1", "id_jogo": "SLES-00049", "nome": "Rayman", "arquivo": "x.zip"}
        z = _zip(self.dir / "p.zip", {"SLES-00049/vram-write-AB.png": "1"})
        with mock.patch.object(tx, "CACHE_DIR", self.dir / "cache"):
            tx.instalar(p, cfg, arquivo=z)
        self.assertTrue((self.dir / "ps1/SLES-00049/replacements/vram-write-AB.png").is_file())

    def test_psp_usa_pasta_do_id_sem_replacements(self):
        p = {"id": "psp-ulus10000", "sistema": "PSP", "id_jogo": "ULUS10000", "nome": "Jogo", "arquivo": "x.zip"}
        z = _zip(self.dir / "p.zip", {"ULUS10000/a.png": "1"})
        with mock.patch.object(tx, "CACHE_DIR", self.dir / "cache"):
            tx.instalar(p, self.cfg, arquivo=z)
        self.assertTrue((self.dir / "psp/ULUS10000/a.png").is_file())

    def test_download_confere_sha1_e_descarta_arquivo_errado(self):
        dados = b"conteudo"
        pacote = {**self.pacote, "url": "https://archive.org/download/x/x.zip",
                  "arquivo": "x.zip", "sha1": "0" * 40, "tamanho": len(dados)}

        class Resp:
            def __init__(self): self.b = dados
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def geturl(self): return "https://dn.ca.archive.org/x.zip"
            def read(self, n):
                b, self.b = self.b, b""
                return b
        with mock.patch.object(urllib.request, "urlopen", return_value=Resp()):
            with self.assertRaises(tx.TexturaErro):
                tx.baixar(pacote, cache_dir=self.dir / "c")
        self.assertEqual(list((self.dir / "c").iterdir()), [])
        pacote["sha1"] = hashlib.sha1(dados).hexdigest()
        with mock.patch.object(urllib.request, "urlopen", return_value=Resp()):
            arq = tx.baixar(pacote, cache_dir=self.dir / "c")
        self.assertEqual(arq.read_bytes(), dados)

    def test_url_fora_da_lista_e_recusada(self):
        with self.assertRaises(tx.TexturaErro):
            tx.baixar({**self.pacote, "url": "http://evil.example/x.zip", "sha1": "0"}, cache_dir=self.dir)

    def test_set_loading_liga_e_nao_duplica(self):
        ini = self.dir / "PCSX2.ini"
        ini.write_text("[EmuCore/GS]\nLoadTextureReplacements = false\nOutra = 1\n")
        chaves = dict(tx._CHAVES, PS2=(str(ini), "EmuCore/GS", "LoadTextureReplacements", "true"))
        with mock.patch.object(tx, "_CHAVES", chaves), mock.patch.object(tx, "emulador_aberto", return_value=False):
            self.assertEqual(tx.set_loading("PS2"), "ligado")
            self.assertEqual(tx.set_loading("PS2"), "ja_ligado")
        self.assertEqual(ini.read_text(), "[EmuCore/GS]\nLoadTextureReplacements = true\nOutra = 1\n")

    def test_set_loading_recusa_com_emulador_aberto(self):
        with mock.patch.object(tx, "emulador_aberto", return_value=True):
            with self.assertRaises(tx.TexturaErro):
                tx.set_loading("PS2")

    def test_tem_rom_ignora_regiao_e_versao(self):
        self.assertTrue(tx.tem_rom(self.pacote, ["Need for Speed - Underground 2 (USA).iso"]))
        self.assertFalse(tx.tem_rom(self.pacote, ["Need for Speed - Underground (USA).iso"]))
        u1 = {**self.pacote, "nome": "Need for Speed Underground (USA)"}
        self.assertFalse(tx.tem_rom(u1, ["Need for Speed - Underground 2.iso"]))

    def test_catalogo_real_tem_ids_unicos_e_campos(self):
        cat = tx.carregar_catalogo()
        self.assertEqual(len({p["id"] for p in cat}), len(cat))
        u2 = tx.achar_pacote("ps2-slus-21065", cat)
        self.assertEqual(u2["sha1"], "c592ef292590f146b7e30f804d4958d38fdaed2c")
        for p in cat:
            self.assertTrue(tx._ID_JOGO[p["sistema"]].match(p["id_jogo"]), p["id"])
            self.assertTrue(p["url"].startswith(tx.URL_PERMITIDAS))
            self.assertEqual(len(p["sha1"]), 40)


if __name__ == "__main__":
    unittest.main()
