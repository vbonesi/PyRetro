"""Testes de integração da GUI: sobe o servidor de verdade contra um
acervo de mentira e conversa com ele por HTTP.

Diferente de tests/test_server.py (que chama função solta), aqui o
caminho é o mesmo do uso real - roteamento, leitura do config, JSON de
ida e volta, gravação em disco. É o que pega regressão de endpoint:
rota que sumiu, contrato de resposta que mudou, escrita que não
persiste, validação que deixou passar.

Nada de rede externa: nenhum teste aqui fala com Steam/SteamGridDB/
ScreenScraper/rclone/adb - só com o acervo temporário criado no setUp.

    python3 -m unittest discover -s tests -v
"""
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "gui"))
import server as srv
from core import library as lm

CONFIG_MODELO = """
[pc]
roms_root       = "{raiz}/ROMs"
capas_root      = "{raiz}/Capas"
saves_root      = "{raiz}/Saves/saves"
states_root     = "{raiz}/Saves/states"
backups_root    = "{raiz}/Backups"
retroarch_root  = "{raiz}/RetroArch"
library_root    = "{raiz}/Biblioteca"
organizar_dir   = "0-Organizar"

[android]
device_serial     = ""
jogos_root        = "/storage/emulated/0/Jogos"
thumbnails_root   = "/storage/emulated/0/RetroArch/thumbnails"
saves_root        = "/storage/emulated/0/RetroArch/saves"
states_root       = "/storage/emulated/0/RetroArch/states"
runtime_logs_root = "/storage/emulated/0/RetroArch/logs"
retroarch_root    = "/storage/emulated/0/RetroArch"
retroarch_cfg_path = "/data/data/com.retroarch/retroarch.cfg"
library_root      = "/storage/emulated/0/Jogos/Biblioteca"

[systems.SFC]
capas = "Nintendo - Super Nintendo Entertainment System"
repo  = "Nintendo_-_Super_Nintendo_Entertainment_System"
exts  = ["sfc", "smc"]

[heavy_systems.PS2]
nome  = "Sony - PlayStation 2"
capas = "Sony - PlayStation 2"
repo  = "Sony_-_PlayStation_2"
exts  = ["iso", "chd"]
"""


class BaseAPI(unittest.TestCase):
    """Sobe um servidor por classe de teste, apontando pra um acervo
    temporário - config, ROMs, capas e biblioteca são todos de mentira,
    então nada aqui toca no acervo real do usuário."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.raiz = Path(cls._tmp.name)

        (cls.raiz / "ROMs" / "SFC").mkdir(parents=True)
        (cls.raiz / "ROMs" / "SFC" / "Chrono Trigger.sfc").write_bytes(b"rom")
        (cls.raiz / "ROMs" / "SFC" / "Final Fantasy VI.sfc").write_bytes(b"rom")
        capas = cls.raiz / "Capas" / "Nintendo - Super Nintendo Entertainment System" / "Named_Boxarts"
        capas.mkdir(parents=True)
        (capas / "Chrono Trigger.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 2000)
        cls.capas_dir = capas
        for sub in ("Saves/saves", "Saves/states", "Biblioteca", "cache"):
            (cls.raiz / sub).mkdir(parents=True, exist_ok=True)

        cfg_path = cls.raiz / "config.toml"
        cfg_path.write_text(CONFIG_MODELO.format(raiz=cls.raiz))

        # Aponta o módulo pro acervo falso (são constantes de módulo).
        cls._orig = (srv.CONFIG_PATH, srv.REGISTRY_PATH, srv.HEAVY_CATALOG_PATH)
        srv.CONFIG_PATH = cfg_path
        srv.REGISTRY_PATH = cls.raiz / "cache" / "covers_registry.json"
        srv.HEAVY_CATALOG_PATH = cls.raiz / "cache" / "heavy_catalog.json"
        srv.HEAVY_CATALOG_PATH.write_text(json.dumps({"systems": {"PS2": [
            {"name": "Bomba Patch.iso", "size": 123, "is_dir": False}]}}))

        cls.lib_path = cls.raiz / "Biblioteca" / "library.json"
        cls.servidor = ThreadingHTTPServer(("127.0.0.1", 0), srv.Handler)
        cls.url = f"http://127.0.0.1:{cls.servidor.server_address[1]}"
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        srv.CONFIG_PATH, srv.REGISTRY_PATH, srv.HEAVY_CATALOG_PATH = cls._orig
        cls._tmp.cleanup()

    def gravar_biblioteca(self, jogos):
        lm.save_library(self.lib_path, {"games": jogos})

    def pedir(self, rota, corpo=None):
        """(status, json) - não levanta em erro HTTP, pra poder testar
        os caminhos de recusa."""
        dados = json.dumps(corpo).encode() if corpo is not None else None
        req = urllib.request.Request(
            self.url + rota, data=dados,
            headers={"Content-Type": "application/json"} if dados else {})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            with e:                      # fecha o socket (senão vaza ResourceWarning)
                corpo_erro = e.read()
            try:
                return e.code, json.loads(corpo_erro or b"null")
            except json.JSONDecodeError:
                return e.code, corpo_erro


class TestLeitura(BaseAPI):
    def test_systems_lista_o_sistema_configurado(self):
        status, dados = self.pedir("/api/systems")
        self.assertEqual(status, 200)
        self.assertEqual([s["code"] for s in dados], ["SFC"])
        self.assertEqual(dados[0]["count"], 1, "contou capas errado")
        self.assertEqual(dados[0]["missing"], 1, "Final Fantasy VI não tem capa e devia contar")

    def test_covers_traz_rom_com_e_sem_capa(self):
        status, dados = self.pedir("/api/covers/SFC")
        self.assertEqual(status, 200)
        por_label = {i["label"]: i for i in dados}
        self.assertIn("Chrono Trigger", por_label)
        self.assertEqual(por_label["Final Fantasy VI"]["status"], "no_cover")

    def test_sistema_desconhecido_devolve_404(self):
        status, _ = self.pedir("/api/covers/NAOEXISTE")
        self.assertEqual(status, 404)

    def test_rota_inexistente_devolve_404(self):
        status, _ = self.pedir("/api/nao/existe")
        self.assertEqual(status, 404)


class TestBibliotecaHTTP(BaseAPI):
    def setUp(self):
        self.gravar_biblioteca([
            lm._blank_game("Hollow Knight", "Steam"),
            lm._blank_game("Black Desert", "Steam"),
            lm._blank_game("Chrono Trigger", "Nintendo - Super Nintendo Entertainment System"),
        ])

    def test_jogo_que_e_rom_nao_aparece_na_biblioteca(self):
        # "Chrono Trigger" existe como ROM de SFC: o dado dele mora na
        # aba do sistema, não na Biblioteca.
        _, dados = self.pedir("/api/library")
        nomes = [g["nome"] for g in dados]
        self.assertIn("Hollow Knight", nomes)
        self.assertNotIn("Chrono Trigger", nomes)

    def test_update_persiste_em_disco(self):
        _, dados = self.pedir("/api/library")
        gid = next(g["id"] for g in dados if g["nome"] == "Hollow Knight")
        status, _ = self.pedir("/api/library/update", {"id": gid, "field": "nota", "value": 9.5})
        self.assertEqual(status, 200)
        salvo = json.loads(self.lib_path.read_text())
        self.assertEqual(next(g["nota"] for g in salvo["games"] if g["id"] == gid), 9.5)

    def test_update_recusa_campo_protegido(self):
        _, dados = self.pedir("/api/library")
        gid = dados[0]["id"]
        status, _ = self.pedir("/api/library/update", {"id": gid, "field": "fontes", "value": ["x"]})
        self.assertEqual(status, 400)

    def test_edit_e_tudo_ou_nada(self):
        _, dados = self.pedir("/api/library")
        gid = next(g["id"] for g in dados if g["nome"] == "Hollow Knight")
        # nome válido + data inválida: NADA pode ser gravado
        status, _ = self.pedir("/api/library/edit",
                               {"id": gid, "campos": {"nome": "Novo Nome", "lancamento": "banana"}})
        self.assertEqual(status, 400)
        salvo = json.loads(self.lib_path.read_text())
        self.assertEqual(next(g["nome"] for g in salvo["games"] if g["id"] == gid), "Hollow Knight",
                         "gravou parte da edição mesmo com um campo inválido")

    def test_ocultar_some_do_ranking_e_iniciados(self):
        _, dados = self.pedir("/api/library")
        gid = next(g["id"] for g in dados if g["nome"] == "Black Desert")
        self.pedir("/api/library/update", {"id": gid, "field": "nota", "value": 8})
        self.pedir("/api/library/update", {"id": gid, "field": "iniciado", "value": True})
        _, ranking = self.pedir("/api/ranking")
        self.assertIn("Black Desert", [g["nome"] for g in ranking])

        self.pedir("/api/library/update", {"id": gid, "field": "oculto", "value": True})
        _, ranking = self.pedir("/api/ranking")
        _, iniciados = self.pedir("/api/iniciados")
        self.assertNotIn("Black Desert", [g["nome"] for g in ranking])
        self.assertNotIn("Black Desert", [g["nome"] for g in iniciados])


class TestTrackingDeROM(BaseAPI):
    """A primeira edição numa ROM cria o registro sozinha."""

    def setUp(self):
        self.gravar_biblioteca([])

    def _track(self, nome, code, plataforma, campo, valor):
        return self.pedir("/api/library/track", {
            "nome": nome, "code": code, "plataforma": plataforma,
            "fonte": f"rom:{code}", "field": campo, "value": valor})

    def test_cria_registro_na_primeira_edicao(self):
        status, r = self._track("Final Fantasy VI", "SFC",
                                "Nintendo - Super Nintendo Entertainment System", "iniciado", True)
        self.assertEqual(status, 200)
        salvo = json.loads(self.lib_path.read_text())
        self.assertEqual(len(salvo["games"]), 1)
        self.assertEqual(salvo["games"][0]["fontes"], ["rom:SFC"])

    def test_segunda_edicao_nao_duplica(self):
        self._track("Final Fantasy VI", "SFC", "Nintendo - Super Nintendo Entertainment System",
                    "iniciado", True)
        self._track("Final Fantasy VI", "SFC", "Nintendo - Super Nintendo Entertainment System",
                    "nota", 9)
        salvo = json.loads(self.lib_path.read_text())
        self.assertEqual(len(salvo["games"]), 1)
        self.assertEqual(salvo["games"][0]["nota"], 9)

    def test_rom_marcada_aparece_em_iniciados_com_capa(self):
        self._track("Chrono Trigger", "SFC", "Nintendo - Super Nintendo Entertainment System",
                    "iniciado", True)
        _, iniciados = self.pedir("/api/iniciados")
        self.assertEqual([g["nome"] for g in iniciados], ["Chrono Trigger"])
        self.assertIsNotNone(iniciados[0]["capa_url"], "não resolveu a capa da pasta do sistema")

    def test_exige_code(self):
        status, _ = self.pedir("/api/library/track", {
            "nome": "X", "plataforma": "Y", "fonte": "rom:SFC", "field": "iniciado", "value": True})
        self.assertEqual(status, 400)


class TestDecomporColecao(BaseAPI):
    """Coletânea decomposta não pode voltar na próxima varredura - o
    nome da PASTA continua existindo pra sempre, e a varredura casa por
    nome. Foi exatamente o que aconteceu com "Portal Companion
    Collection" (29/08): o usuário separou em Portal e Portal 2, e a
    varredura seguinte recriou a coletânea."""

    def setUp(self):
        self.gravar_biblioteca([
            # "Portal" já vinha da planilha, COM progresso - decompor
            # não pode duplicar nem zerar isso.
            dict(lm._blank_game("Portal", "Nintendo Switch"), nota=9.4,
                 iniciado=True, finalizado=True),
            dict(lm._blank_game("Portal Companion Collection", "Nintendo Switch"),
                 fontes=["switch"]),
        ])

    def _colecao_id(self):
        _, dados = self.pedir("/api/library")
        return next(g["id"] for g in dados if g["nome"] == "Portal Companion Collection")

    def test_decompoe_reaproveitando_o_que_ja_existe(self):
        status, r = self.pedir("/api/library/decompor",
                               {"id": self._colecao_id(), "nomes": ["Portal", "Portal 2"]})
        self.assertEqual(status, 200)
        self.assertEqual((r["criados"], r["reaproveitados"]), (1, 1))

        salvo = json.loads(self.lib_path.read_text())["games"]
        nomes = sorted(g["nome"] for g in salvo)
        self.assertEqual(nomes, ["Portal", "Portal 2"], "a coletânea devia ter sumido")
        portal = next(g for g in salvo if g["nome"] == "Portal")
        self.assertEqual(portal["nota"], 9.4, "zerou o progresso que veio da planilha")

    def test_pasta_original_nao_recria_a_colecao(self):
        self.pedir("/api/library/decompor",
                   {"id": self._colecao_id(), "nomes": ["Portal", "Portal 2"]})
        biblioteca = lm.load_library(self.lib_path)
        # A varredura do Switch continua devolvendo o nome da PASTA:
        r = lm.merge_owned(biblioteca, [{"nome": "Portal Companion Collection",
                                         "plataforma": "Nintendo Switch", "fonte": "switch"}])
        self.assertEqual(r["added"], 0, "a coletânea voltou como registro novo")
        self.assertEqual(len(biblioteca["games"]), 2)

    def test_apelidos_antigos_da_colecao_sao_preservados(self):
        # Se a coletânea já respondia por outro nome, esse vínculo não
        # pode se perder na decomposição.
        biblioteca = lm.load_library(self.lib_path)
        col = next(g for g in biblioteca["games"] if g["nome"] == "Portal Companion Collection")
        col["nomes_alt"] = ["Portal Collection"]
        lm.save_library(self.lib_path, biblioteca)

        self.pedir("/api/library/decompor",
                   {"id": self._colecao_id(), "nomes": ["Portal", "Portal 2"]})
        biblioteca = lm.load_library(self.lib_path)
        r = lm.merge_owned(biblioteca, [{"nome": "Portal Collection",
                                         "plataforma": "Nintendo Switch", "fonte": "switch"}])
        self.assertEqual(r["added"], 0, "perdeu um apelido que a coletânea já tinha")

    def test_lista_vazia_e_recusada(self):
        status, _ = self.pedir("/api/library/decompor", {"id": self._colecao_id(), "nomes": []})
        self.assertEqual(status, 400)

    def test_nao_reaproveita_jogo_de_OUTRA_plataforma(self):
        # Achado 29/08 ao decompor "Final Fantasy 1-6 Bundle" do Switch:
        # o "Final Fantasy VI" que já existe é ROM de SNES. Casar por
        # nome sem olhar plataforma juntaria os dois num registro só -
        # o mesmo erro do Celeste (GBA x Xbox).
        self.gravar_biblioteca([
            dict(lm._blank_game("Final Fantasy VI",
                                "Nintendo - Super Nintendo Entertainment System"),
                 nota=10.0, finalizado=True),
            dict(lm._blank_game("Final Fantasy 1-6 Bundle Remastered", "Nintendo Switch"),
                 fontes=["switch"]),
        ])
        _, dados = self.pedir("/api/library")
        bundle = next(g["id"] for g in dados if g["nome"].startswith("Final Fantasy 1-6"))
        _, r = self.pedir("/api/library/decompor",
                          {"id": bundle, "nomes": ["Final Fantasy V", "Final Fantasy VI"]})
        self.assertEqual((r["criados"], r["reaproveitados"]), (2, 0))

        salvo = json.loads(self.lib_path.read_text())["games"]
        ff6 = [g for g in salvo if g["nome"] == "Final Fantasy VI"]
        self.assertEqual(len(ff6), 2, "o do Switch e o do SNES viraram um só")
        snes = next(g for g in ff6 if g["plataforma"].startswith("Nintendo - Super"))
        self.assertEqual(snes["fontes"], [], "contaminou a ROM de SNES com a fonte do Switch")
        self.assertEqual(snes["nota"], 10.0)

    def test_reaproveita_por_apelido_na_mesma_plataforma(self):
        # Jogo renomeado antes continua sendo o mesmo jogo.
        biblioteca = lm.load_library(self.lib_path)
        portal = next(g for g in biblioteca["games"] if g["nome"] == "Portal")
        portal["nome"], portal["nomes_alt"] = "Portal (Switch)", ["Portal"]
        lm.save_library(self.lib_path, biblioteca)

        _, r = self.pedir("/api/library/decompor",
                          {"id": self._colecao_id(), "nomes": ["Portal", "Portal 2"]})
        self.assertEqual(r["reaproveitados"], 1, "não achou o jogo pelo apelido")


class TestSegurancaHTTP(BaseAPI):
    """Travessia de caminho pelos endpoints de verdade - o servidor
    escuta na rede, então isso não é hipotético."""

    def test_upload_de_capa_com_travessia_e_bloqueado(self):
        import base64
        payload = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"x" * 2000).decode()
        for label in ("../../../../PWNED", "/tmp/PWNED", "..", "", "sub/dir"):
            status, _ = self.pedir("/api/cover/upload", {
                "code": "SFC", "label": label, "filename": "x.png", "data": payload})
            self.assertEqual(status, 404, f"aceitou label perigoso {label!r}")
        self.assertFalse(list(self.raiz.glob("PWNED*")), "gravou fora da pasta de capas")

    def test_imagem_com_travessia_nao_vaza_arquivo(self):
        status, _ = self.pedir("/images/SFC/../../../../etc/passwd")
        self.assertEqual(status, 404)

    def test_library_images_com_travessia_nao_vaza_arquivo(self):
        status, _ = self.pedir("/library-images/../../../../etc/passwd")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
