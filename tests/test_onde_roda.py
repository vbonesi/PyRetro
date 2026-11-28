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

    def test_id_desconhecido_404(self):
        status, _ = self.pedir("/api/onde-roda/set", {"id": "nao", "plataforma": "ps4", "existe": True})
        self.assertEqual(status, 404)

    def test_reset_apaga_correcao(self):
        self.pedir("/api/onde-roda/set", {"id": self.a["id"], "plataforma": "ps4", "existe": False})
        self.pedir("/api/onde-roda/reset", {"id": self.a["id"], "plataforma": "ps4"})
        self.assertNotIn("ps4", next(g for g in self.salvo() if g["id"] == self.a["id"])["onde_roda"])


if __name__ == "__main__":
    unittest.main()
