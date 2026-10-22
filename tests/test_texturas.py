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


class TexturasFontesTest(unittest.TestCase):
    """Índice de fontes externas (planilha): só casa com jogos da Biblioteca."""
    fontes = [
        {"sistema": "PS1", "nome": "Castlevania: Symphony of the Night", "url": "https://gbatemp.net/a", "serial": "SLUS-00067"},
        {"sistema": "PS2", "nome": "Need for Speed: Underground 2", "url": "https://gbatemp.net/b", "serial": ""},
        {"sistema": "PS2", "nome": "Need for Speed: Underground", "url": "https://gbatemp.net/c", "serial": ""},
        {"sistema": "GC", "nome": "Harry Potter & the Chamber of Secrets", "url": "https://gbatemp.net/d", "serial": ""},
        {"sistema": "PSP", "nome": "Tetris", "url": "https://gbatemp.net/e", "serial": "lixo"},
    ]
    catalogo = [{"sistema": "PS2", "nome": "Need for Speed - Underground 2 (USA)", "id_jogo": "SLUS-21065"}]
    jogos = [
        {"nome": "Castlevania - Symphony of the Night", "plataforma": "Sony - PlayStation"},
        {"nome": "NFSU2", "nomes_alt": ["Need for Speed Underground 2"], "plataforma": "Sony - PlayStation 2"},
        {"nome": "Harry Potter and the Chamber of Secrets", "plataforma": "Nintendo - GameCube"},
        {"nome": "Tetris", "plataforma": "Sony - PSP"},
        {"nome": "Castlevania - Symphony of the Night", "plataforma": "Xbox"},
    ]

    def test_casa_por_nome_e_nome_alternativo_no_mesmo_sistema(self):
        r = tx.fontes_da_biblioteca(self.jogos, list(tx.PLATAFORMAS), self.fontes, self.catalogo)
        por = {f["url"]: f for f in r}
        self.assertEqual(set(por), {"https://gbatemp.net/a", "https://gbatemp.net/b", "https://gbatemp.net/d", "https://gbatemp.net/e"})
        self.assertEqual(por["https://gbatemp.net/a"]["id_jogo"], "SLUS-00067")
        self.assertEqual(por["https://gbatemp.net/b"]["id_jogo"], "SLUS-21065")  # veio do catálogo
        self.assertTrue(por["https://gbatemp.net/b"]["no_catalogo"])
        self.assertEqual(por["https://gbatemp.net/b"]["jogo"], "NFSU2")
        self.assertEqual(por["https://gbatemp.net/e"]["id_jogo"], "")  # serial inválido não vira pasta

    def test_filtra_pelos_sistemas_do_alvo(self):
        r = tx.fontes_da_biblioteca(self.jogos, tx.sistemas_celular(), self.fontes, self.catalogo)
        self.assertEqual({f["sistema"] for f in r}, {"PS1", "PSP"})

    def test_indice_real_sem_pagos_e_so_https(self):
        fontes = tx.carregar_fontes()
        self.assertGreater(len(fontes), 0)
        for f in fontes:
            self.assertTrue(f["url"].startswith("https://"), f)
            self.assertNotIn("patreon.com", f["site"])
            self.assertNotEqual(f["restricao"].lower(), "paywall")
            self.assertIn(f["sistema"], tx.PLATAFORMAS)


class TexturasGeradorFontesTest(unittest.TestCase):
    def test_gerador_tira_pagos_e_normaliza_serial(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        import gerar_fontes_texturas as g
        cab = {c: (t, None) for c, t in zip("BCEFH", ["Game Title", "Download", "Region", "Serial Number", "Restriction"])}
        abas = {"PSOne": [cab,
                          {"B": ("Livre", None), "C": ("Link", "https://gbatemp.net/x"), "F": ("SLUS00067", None), "H": ("N/A", None)},
                          {"B": ("Pago", None), "C": ("Link", "https://www.patreon.com/y"), "H": ("Paywall", None)},
                          {"B": ("Pago 2", None), "C": ("Link", "https://www.mediafire.com/z"), "H": ("Paywall", None)},
                          {"B": ("Sem link", None), "C": ("Link", None)}],
                "N64": [cab, {"B": ("Mario", None), "C": ("Link", "https://emulationking.com/m")}]}
        r = g.fontes(abas)
        self.assertEqual([(f["nome"], f["serial"], f["restricao"]) for f in r], [("Livre", "SLUS-00067", "")])


class TexturasCelularTest(unittest.TestCase):
    """O celular é simulado: shell/push de core.adb viram operações num dict."""
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.remoto = {}
        self.cmds = []
        from core import adb as adb_mod
        self.adb = adb_mod

        def shell(cmd, serial=None, timeout=30):
            self.cmds.append(cmd)
            if cmd.startswith("cat "):
                caminho = cmd[4:].split(" 2>")[0].strip("'")
                if caminho not in self.remoto and "; true" not in cmd:
                    raise self.adb.AdbError("adb shell falhou: cat inexistente")  # como o adb real (exit 1)
                return self.remoto.get(caminho, "")
            return ""

        def push(local, remote, serial=None, timeout=1800, archive=False):
            if str(local).endswith("/."):
                raiz = Path(str(local)[:-2])
                for f in raiz.rglob("*"):
                    if f.is_file():
                        self.remoto[remote + "/" + f.relative_to(raiz).as_posix()] = f.read_text()
            else:
                self.remoto[remote] = Path(local).read_text()
            return True
        for nome, fn in (("shell", shell), ("push", push)):
            p = mock.patch.object(adb_mod, nome, fn)
            p.start()
            self.addCleanup(p.stop)
        c = mock.patch.object(tx, "CACHE_DIR", self.dir / "cache")
        c.start()
        self.addCleanup(c.stop)

    def test_destinos_do_celular(self):
        self.assertTrue(tx._cel_destino("PS1", "SLES-00049").endswith("/textures/SLES-00049/replacements"))
        self.assertEqual(tx._cel_destino("PSP", "ULUS10307"), "/sdcard/Jogos/PSP/PSP/TEXTURES/ULUS10307")
        self.assertEqual(tx._cel_destino("3DS", "000400000008F800"), "/sdcard/Jogos/3DS/load/textures/000400000008F800")
        for sis, ruim in (("3DS", "../x"), ("3DS", "123"), ("PSP", "ULUS-10307"), ("GC", "G2MP01")):
            with self.assertRaises(tx.TexturaErro):
                tx._cel_destino(sis, ruim)

    def test_instala_e_remove_no_celular(self):
        p = {"id": "psp-x", "sistema": "PSP", "id_jogo": "ULUS10307", "nome": "J", "arquivo": "x.zip"}
        z = _zip(self.dir / "p.zip", {"ULUS10307/a.png": "1", "ULUS10307/textures.ini": "[options]"})
        self.assertEqual(tx.instalar_celular(p, arquivo=z), 2)
        base = "/sdcard/Jogos/PSP/PSP/TEXTURES/ULUS10307"
        self.assertEqual(self.remoto[base + "/a.png"], "1")
        self.assertIn(base + "/" + tx.MANIFESTO, self.remoto)
        self.assertEqual(tx.estado_celular(p), {"instalado": True, "arquivos": 2})
        self.assertEqual(tx.remover_celular(p), 2)
        self.assertTrue(any(c.startswith("rm -f") and "a.png" in c for c in self.cmds))

    def test_remover_celular_sem_instalar_falha(self):
        p = {"id": "psp-x", "sistema": "PSP", "id_jogo": "ULUS10307", "nome": "J", "arquivo": "x.zip"}
        with self.assertRaises(tx.TexturaErro):
            tx.remover_celular(p)

    def test_ini_valor(self):
        t, mudou = tx._ini_valor("[Graphics]\nReplaceTextures = False\nX = 1\n", "Graphics", "ReplaceTextures", "True")
        self.assertTrue(mudou)
        self.assertEqual(t, "[Graphics]\nReplaceTextures = True\nX = 1\n")
        self.assertFalse(tx._ini_valor(t, "Graphics", "ReplaceTextures", "True")[1])
        t2, _ = tx._ini_valor("[A]\nb = 1\n", "Utility", "custom_textures", "true")
        self.assertIn("[Utility]\ncustom_textures = true", t2)
        t3, _ = tx._ini_valor("", "TextureReplacements", "EnableVRAMWriteReplacements", "true")
        self.assertIn("EnableVRAMWriteReplacements = true", t3)

    def test_set_loading_celular_cria_arquivo_que_nao_existe(self):
        self.assertEqual(tx.set_loading_celular("PS1", "SLUS-00619"), "ligado")
        self.assertIn("EnableVRAMWriteReplacements = true",
                      self.remoto[tx._CEL_DUCK + "/gamesettings/SLUS-00619.ini"])
        self.assertEqual(tx.set_loading_celular("3DS", "0004000000055D00"), "ligado")
        self.assertIn("custom_textures = 1", self.remoto[tx._CEL_INI_3DS])

    def test_set_loading_celular_so_envia_quando_muda(self):
        self.remoto["/sdcard/Jogos/PSP/PSP/SYSTEM/ppsspp.ini"] = "[Graphics]\nReplaceTextures = False\n"
        self.assertEqual(tx.set_loading_celular("PSP", "ULUS10307"), "ligado")
        self.assertIn("ReplaceTextures = True", self.remoto["/sdcard/Jogos/PSP/PSP/SYSTEM/ppsspp.ini"])
        self.assertEqual(tx.set_loading_celular("PSP", "ULUS10307"), "ja_ligado")


class TexturasLinkTest(unittest.TestCase):
    """Download por link avulso: validação de URL e limites, sem rede (DNS e opener simulados)."""
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        import socket
        self.dns = {"exemplo.org": "93.184.216.34", "interno.lan": "192.168.1.9"}
        p = mock.patch.object(socket, "getaddrinfo", side_effect=lambda h, *a, **k: [(2, 1, 6, "", (self.dns.get(h, h), 443))])
        p.start()
        self.addCleanup(p.stop)

    def test_validar_url(self):
        self.assertEqual(tx.validar_url("https://exemplo.org/a.zip"), "exemplo.org")
        for ruim in ("http://exemplo.org/a.zip", "ftp://exemplo.org/a.zip", "https://u:p@exemplo.org/a.zip",
                     "https://exemplo.org:8443/a.zip", "https://interno.lan/a.zip", "https://127.0.0.1/a.zip",
                     "https://10.0.0.1/a.zip", "https://100.64.0.5/a.zip", "https:///a.zip", "nao e url"):
            with self.assertRaises(tx.TexturaErro, msg=ruim):
                tx.validar_url(ruim)

    def _opener(self, dados=b"conteudo", tipo="application/zip", cd=None, url="https://exemplo.org/p.zip", tamanho=None):
        class Resp:
            headers = {"Content-Type": tipo, "Content-Length": str(len(dados) if tamanho is None else tamanho)}
            def __init__(self):
                self.b = dados
                if cd:
                    self.headers["Content-Disposition"] = cd
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def geturl(self): return url
            def read(self, n):
                b, self.b = self.b, b""
                return b
        class Opener:
            def open(self, req, timeout=0): return Resp()
        return mock.patch.object(urllib.request, "build_opener", return_value=Opener())

    def test_baixa_e_devolve_sha1(self):
        with self._opener():
            arq, sha = tx.baixar_url("https://exemplo.org/p.zip", cache_dir=self.dir)
        self.assertEqual(arq.read_bytes(), b"conteudo")
        self.assertEqual(sha, hashlib.sha1(b"conteudo").hexdigest())
        self.assertEqual(arq.suffix, ".zip")

    def test_nome_vem_do_content_disposition(self):
        with self._opener(cd='attachment; filename="pack.7z"', url="https://exemplo.org/download?id=3"):
            arq, _ = tx.baixar_url("https://exemplo.org/download?id=3", cache_dir=self.dir)
        self.assertEqual(arq.suffix, ".7z")

    def test_recusas_sem_deixar_arquivo(self):
        casos = {
            "pagina html": self._opener(tipo="text/html; charset=utf-8"),
            "extensao": self._opener(url="https://exemplo.org/p.exe"),
            "tamanho declarado": self._opener(tamanho=10 * 1024 ** 4),
        }
        for nome, op in casos.items():
            with op, self.assertRaises(tx.TexturaErro, msg=nome):
                tx.baixar_url("https://exemplo.org/p.zip", cache_dir=self.dir)
        with self._opener(dados=b"x" * 100, tamanho=0), self.assertRaises(tx.TexturaErro):
            tx.baixar_url("https://exemplo.org/p.zip", cache_dir=self.dir, limite=10)
        self.assertEqual(list(self.dir.iterdir()), [])

    def test_redirecionamento_para_endereco_interno_e_recusado(self):
        h = tx._RedirectSeguro()
        with self.assertRaises(tx.TexturaErro):
            h.redirect_request(mock.Mock(), None, 302, "Found", {}, "https://interno.lan/a.zip")


if __name__ == "__main__":
    unittest.main()
