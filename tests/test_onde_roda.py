"""Modelo `onde_roda` (plano de 27/11/2026): plataformas, quero/tenho, junção e migração."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import library as lm
from core import onde_roda as orr
from tests.test_api import BaseAPI


def jogo(nome, plataforma="Steam", **campos):
    g = lm._blank_game(nome, plataforma)
    g.update(campos)
    return g


class TestModelo(unittest.TestCase):
    def test_ordem_de_prioridade(self):
        self.assertEqual(orr.PLATAFORMAS, ("switch", "ps4", "xbox", "pc", "switch2"))

    def test_manual_vence_a_pesquisa(self):
        g = jogo("A")
        orr.definir(g, "ps4", existe=False, gb=12)
        self.assertFalse(orr.pesquisa(g, "ps4", existe=True, gb=99))
        self.assertEqual(g["onde_roda"]["ps4"], {"existe": False, "gb": 12.0, "manual": True})

    def test_pesquisa_grava_quando_nao_ha_manual(self):
        g = jogo("A")
        self.assertTrue(orr.pesquisa(g, "switch", existe=True, gb=3))
        self.assertEqual(orr.existentes(g), ["switch"])

    def test_inferencia_nao_toca_no_manual(self):
        g = jogo("A", fontes=["wishlist:psn", "wishlist:xbox"])
        orr.definir(g, "ps4", existe=False)
        orr.inferir(g)
        self.assertEqual(orr.existentes(g), ["xbox"])

    def test_plataforma_invalida(self):
        with self.assertRaises(ValueError):
            orr.definir(jogo("A"), "dreamcast", existe=True)

    def test_tenho_no_pc_exige_loja(self):
        g = jogo("A")
        with self.assertRaises(ValueError):
            orr.tenho_em(g, "pc")
        self.assertEqual(orr.tenho_em(g, "pc", "GOG"), {"estado": "tenho", "plataforma": "pc", "loja": "GOG"})
        self.assertTrue(g["onde_roda"]["pc"]["existe"])

    def test_tenho_fora_do_pc_ignora_loja(self):
        g = jogo("A")
        self.assertIsNone(orr.tenho_em(g, "ps4", "Steam")["loja"])

    def test_tenho_nao_desfaz_correcao_manual(self):
        g = jogo("A")
        orr.definir(g, "xbox", existe=False)
        orr.tenho_em(g, "xbox")
        self.assertFalse(g["onde_roda"]["xbox"]["existe"])


class TestJuncao(unittest.TestCase):
    def test_junta_card_repetido_entre_listas(self):
        a = jogo("Hades", "PlayStation 4", fontes=["wishlist:psn"], nota=9)
        b = jogo("Hades™", "Xbox", fontes=["wishlist:xbox"], genero="Ação")
        lib = {"games": [a, b]}
        feitos = orr.juntar_repetidos(lib)
        self.assertEqual(len(feitos), 1)
        self.assertEqual(len(lib["games"]), 1)
        g = lib["games"][0]
        self.assertEqual(g["fontes"], ["wishlist:psn", "wishlist:xbox"])
        self.assertEqual((g["nota"], g["genero"]), (9, "Ação"))
        self.assertIn("Hades™", g["nomes_alt"])

    def test_simulacao_nao_altera(self):
        lib = {"games": [jogo("X", fontes=["wishlist:psn"]), jogo("X", "Xbox", fontes=["wishlist:xbox"])]}
        self.assertEqual(len(orr.juntar_repetidos(lib, aplicar=False)), 1)
        self.assertEqual(len(lib["games"]), 2)

    def test_nao_junta_posse_nem_rom(self):
        lib = {"games": [jogo("Celeste", fontes=["steam"]), jogo("Celeste", "Xbox", fontes=["wishlist:xbox"]),
                         jogo("Celeste", "Game Boy Advance", fontes=["rom:GBA"])]}
        self.assertEqual(orr.juntar_repetidos(lib), [])
        self.assertEqual(len(lib["games"]), 3)

    def test_switch_e_switch2_nao_juntam(self):
        lib = {"games": [jogo("Star Fox", fontes=["wishlist:switch"]), jogo("Star Fox", fontes=["wishlist:switch2"])]}
        self.assertEqual(orr.juntar_repetidos(lib), [])

    def test_manual_sobrevive_a_juncao(self):
        a, b = jogo("Y", "PlayStation 4", fontes=["wishlist:psn"]), jogo("Y", "Xbox", fontes=["wishlist:xbox"])
        orr.definir(b, "ps4", existe=False, gb=5)
        lib = {"games": [a, b]}
        orr.juntar_repetidos(lib)
        self.assertEqual(lib["games"][0]["onde_roda"]["ps4"]["manual"], True)
        self.assertFalse(lib["games"][0]["onde_roda"]["ps4"]["existe"])


class TestMigracao(unittest.TestCase):
    def test_desejo_vira_quero_e_posse_vira_tenho(self):
        d = jogo("D", fontes=["wishlist:switch"])
        p = jogo("P", fontes=["heroic:epic"])
        r = jogo("R", "Super Nintendo", fontes=["rom:SFC"])
        lib = {"games": [d, p, r]}
        orr.migrar(lib)
        self.assertEqual(d["jogar"]["estado"], "quero")
        self.assertEqual(orr.existentes(d), ["switch"])
        self.assertEqual(p["jogar"], {"estado": "tenho", "plataforma": "pc", "loja": "Epic"})
        self.assertFalse(r["onde_roda"])
        self.assertIsNone(r["jogar"])

    def test_idempotente(self):
        lib = {"games": [jogo("D", fontes=["wishlist:psn"])]}
        orr.migrar(lib)
        snap = json.dumps(lib, sort_keys=True)
        self.assertEqual(orr.migrar(lib)["atualizados"], 0)
        self.assertEqual(json.dumps(lib, sort_keys=True), snap)


class TestAPI(BaseAPI):
    def setUp(self):
        self.a = jogo("Hades", "PlayStation 4", fontes=["wishlist:psn"])
        self.b = jogo("Hades", "Xbox", fontes=["wishlist:xbox"])
        self.gravar_biblioteca([self.a, self.b])

    def salvo(self):
        return json.loads(self.lib_path.read_text())["games"]

    def test_migrar_simula_e_aplica(self):
        status, d = self.pedir("/api/onde-roda/migrar", {"apply": False})
        self.assertEqual((status, d["aplicado"], len(d["juntados"])), (200, False, 1))
        self.assertEqual(len(self.salvo()), 2)
        status, d = self.pedir("/api/onde-roda/migrar", {"apply": True})
        jogos = self.salvo()
        self.assertEqual(len(jogos), 1)
        self.assertEqual(jogos[0]["jogar"]["estado"], "quero")
        self.assertEqual(sorted(k for k, v in jogos[0]["onde_roda"].items() if v["existe"]), ["ps4", "xbox"])

    def test_set_e_jogar(self):
        status, _ = self.pedir("/api/onde-roda/set", {"id": self.a["id"], "plataforma": "switch", "existe": True, "gb": 8})
        self.assertEqual(status, 200)
        self.assertTrue(next(g for g in self.salvo() if g["id"] == self.a["id"])["onde_roda"]["switch"]["manual"])
        status, _ = self.pedir("/api/onde-roda/jogar", {"id": self.a["id"], "estado": "tenho", "plataforma": "pc"})
        self.assertEqual(status, 400)
        status, d = self.pedir("/api/onde-roda/jogar", {"id": self.a["id"], "estado": "tenho", "plataforma": "pc", "loja": "Steam"})
        self.assertEqual(d["resultado"]["loja"], "Steam")

    def test_pesquisa_em_lote_respeita_manual_e_fonte(self):
        self.pedir("/api/onde-roda/set", {"id": self.a["id"], "plataforma": "switch", "existe": False})
        res = {"id": self.a["id"], "estado": "igdb", "igdb_id": 1, "plataformas": {
            "switch": {"existe": True, "gb": 5, "edicao": "X (original, Switch)"},
            "ps4": {"existe": False, "gb": None}, "pc": {"existe": True, "gb": 20, "lojas": ["Steam"]}}}
        status, d = self.pedir("/api/onde-roda/pesquisa", {"resultados": [res, {"id": "nao", "estado": "igdb"}]})
        self.assertEqual((status, d["ausentes"]), (200, ["nao"]))
        g = next(g for g in self.salvo() if g["id"] == self.a["id"])
        self.assertEqual(g["onde_roda"]["switch"]["existe"], False)   # manual vence
        self.assertEqual(g["onde_roda"]["ps4"]["existe"], True)       # fonte wishlist:psn prova
        self.assertEqual(g["onde_roda"]["pc"]["lojas"], ["Steam"])
        self.assertEqual(g["pesquisa"]["igdb_id"], 1)

    def test_id_desconhecido_404(self):
        status, _ = self.pedir("/api/onde-roda/set", {"id": "nao", "plataforma": "ps4", "existe": True})
        self.assertEqual(status, 404)

    def test_reset_apaga_correcao(self):
        self.pedir("/api/onde-roda/set", {"id": self.a["id"], "plataforma": "ps4", "existe": False})
        self.pedir("/api/onde-roda/reset", {"id": self.a["id"], "plataforma": "ps4"})
        self.assertNotIn("ps4", next(g for g in self.salvo() if g["id"] == self.a["id"])["onde_roda"])


if __name__ == "__main__":
    unittest.main()


class TestFaltamNaWishlist(unittest.TestCase):
    def test_steam_lista_o_que_roda_no_pc_e_nao_esta_nem_e_dele(self):
        a = jogo("Falta", "PlayStation 4", fontes=["wishlist:psn"]); orr.pesquisa(a, "pc", existe=True)
        b = jogo("Ja na lista", fontes=["wishlist:steam"]); orr.inferir(b)
        c = jogo("Ja comprei", fontes=["wishlist:psn"]); orr.pesquisa(c, "pc", existe=True); orr.tenho_em(c, "ps4")
        d = jogo("Retro", "Super Nintendo", fontes=["rom:SFC"]); orr.pesquisa(d, "pc", existe=True)
        e = jogo("Oculto", "PlayStation 4", fontes=["wishlist:psn"], oculto=True); orr.pesquisa(e, "pc", existe=True)
        f = jogo("So no PS4", "PlayStation 4", fontes=["wishlist:psn"]); orr.pesquisa(f, "pc", existe=False)
        lib = {"games": [a, b, c, d, e, f]}
        self.assertEqual(orr.faltam_na_wishlist(lib, "steam"), ["Falta"])

    def test_xbox_e_o_texto(self):
        a = jogo("Zeta", "PlayStation 4", fontes=["wishlist:psn"]); orr.pesquisa(a, "xbox", existe=True)
        b = jogo("alfa", "PlayStation 4", fontes=["wishlist:psn"]); orr.pesquisa(b, "xbox", existe=True)
        nomes = orr.faltam_na_wishlist({"games": [a, b]}, "xbox")
        self.assertEqual(nomes, ["alfa", "Zeta"])
        self.assertEqual(orr.texto_faltam("xbox", nomes).splitlines(), ["# Falta na wishlist da Xbox (2 jogos): adicione à mão", "alfa", "Zeta"])

    def test_loja_desconhecida(self):
        with self.assertRaises(ValueError):
            orr.faltam_na_wishlist({"games": []}, "gog")


class TestFaltamAPI(BaseAPI):
    def test_rota_e_txt_em_downloads(self):
        a = jogo("Falta no PC", "PlayStation 4", fontes=["wishlist:psn"]); orr.pesquisa(a, "pc", existe=True)
        self.gravar_biblioteca([a])
        status, d = self.pedir("/api/onde-roda/faltam")
        self.assertEqual((status, d), (200, {"steam": ["Falta no PC"], "xbox": []}))
        status, d = self.pedir("/api/onde-roda/faltam-txt", {})
        self.assertEqual(status, 200)
        txt = Path(d["pasta"]) / "falta-na-wishlist-steam.txt"
        self.assertIn("Falta no PC", txt.read_text(encoding="utf-8"))
        self.assertEqual(d["arquivos"]["xbox"]["total"], 0)


class TestSortearQuatroGruposAPI(BaseAPI):
    def test_grupos_e_sorteio_de_quero_jogar(self):
        a = jogo("Quero no PS4", "PlayStation 4", fontes=["wishlist:psn"]); orr.migrar_game(a)
        b = jogo("Quero so no Xbox", "Xbox", fontes=["wishlist:xbox"]); orr.migrar_game(b)
        self.gravar_biblioteca([a, b])
        status, d = self.pedir("/api/sortear/systems")
        self.assertEqual([g["code"] for g in d["grupos"]], ["retro", "geracoes", "quero", "tenho", "todos"])
        for _ in range(5):
            status, r = self.pedir("/api/sortear?system=quero")
            self.assertEqual((status, r["nome"]), (200, "Quero no PS4"))
        self.assertEqual(self.pedir("/api/sortear?system=tenho")[0], 404)

    def test_entre_geracoes(self):
        ps2 = jogo("Jogo de PS2", "Sony - PlayStation 2", fontes=["rom:PS2"])
        snes = jogo("Jogo de SNES", "Nintendo - Super Nintendo Entertainment System", fontes=["rom:SFC"])
        oculto = jogo("Escondido", "Sony - PSP", fontes=["rom:PSP"], oculto=True)
        self.gravar_biblioteca([ps2, snes, oculto])
        for _ in range(5):
            status, r = self.pedir("/api/sortear?system=geracoes")
            self.assertEqual((status, r["nome"]), (200, "Jogo de PS2"))


class TestShopAposentado(unittest.TestCase):
    def test_comando_e_modulos_sairam(self):
        import importlib.util
        self.assertIsNone(importlib.util.find_spec("core.switch_shop"))
        self.assertIsNone(importlib.util.find_spec("core.tinfoil_auth"))
        txt = (Path(__file__).parent.parent / "retrosync.py").read_text()
        self.assertNotIn("switch-shop", txt)
        self.assertNotIn("tinfoil-auth", txt)


class TestIgdbPuro(unittest.TestCase):
    def test_nome_limpo_e_nucleo(self):
        from core import onde_igdb as ig
        self.assertEqual(ig.norm("Resident Evil 4 (USA) [PT-BR]™"), "resident evil 4")
        self.assertGreaterEqual(ig.similaridade("Dino Crisis 2", "Dino Crisis 2"), 1.0)
        self.assertGreaterEqual(ig.similaridade("Tomb Raider", "Tomb Raider Remastered"), 0.9)

    def test_base_prefere_plataforma_nativa_e_port_conta(self):
        from core import onde_igdb as ig
        pool = [{"id": 416083, "name": "Dino Crisis 2", "platforms": [48, 167], "game_type": 11},
                {"id": 4132, "name": "Dino Crisis 2", "platforms": [9, 6, 7], "game_type": 0, "ports": [416083]}]
        base, sim, _ = ig.escolher_base(["Dino Crisis 2"], "Sony - PlayStation", pool)
        self.assertEqual(base["id"], 4132)
        tipos = ig.ids_relacionados(base)
        evs = ig.evidencias(base, {416083: pool[0]}, tipos, [])
        self.assertEqual(evs["ps4"][0]["tipo"], "port")
        r = ig.montar("Dino Crisis 2", "Sony - PlayStation", base, sim, evs)
        self.assertTrue(r["plataformas"]["ps4"]["existe"])
        self.assertFalse(r["plataformas"]["switch"]["existe"])
        self.assertTrue(r["plataformas"]["ps4"]["gb"] > 0)

    def test_sem_casamento_fica_nao_verificado(self):
        from core import onde_igdb as ig
        r = ig.montar("Zzz", "Steam", None, 0.3, None)
        self.assertEqual(r["estado"], "nao_verificado")
