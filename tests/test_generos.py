"""Testes de gênero (31/08) - core/screenscraper._genero_pt e
core/launchbox.traduzir_genero/find_genero. Só as funções PURAS (sem
rede) - buscar_genero/find_cover_screenscraper de verdade continuam sem
teste automatizado, mesmo padrão do resto do projeto pra chamada de API.

    python3 -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import launchbox as lb
from core import screenscraper as ss


class TestGeneroScreenScraper(unittest.TestCase):
    """_genero_pt lê o campo "genres" (achado 31/08: a API já devolve
    tradução pt nativa, sem precisar de mapeamento manual)."""

    def _jeu(self, generos):
        return {"genres": generos}

    def _genero(self, id_, principale, pt, en="X"):
        noms = [{"langue": "en", "text": en}]
        if pt:
            noms.append({"langue": "pt", "text": pt})
        return {"id": id_, "principale": principale, "noms": noms}

    def test_prefere_o_principal(self):
        jeu = self._jeu([
            self._genero("2915", "0", "Plataforma / Corre e Pula"),
            self._genero("7", "1", "Plataforma"),
        ])
        self.assertEqual(ss._genero_pt(jeu), "Plataforma")

    def test_sem_principal_cai_pro_primeiro_com_pt(self):
        jeu = self._jeu([
            self._genero("1", "0", None),
            self._genero("2", "0", "Aventura"),
        ])
        self.assertEqual(ss._genero_pt(jeu), "Aventura")

    def test_tira_prefixo_jogos_de(self):
        jeu = self._jeu([self._genero("8", "1", "Jogos de RPG")])
        self.assertEqual(ss._genero_pt(jeu), "RPG")

    def test_sem_genero_nenhum_devolve_none(self):
        self.assertIsNone(ss._genero_pt(self._jeu([])))
        self.assertIsNone(ss._genero_pt(self._jeu([self._genero("1", "1", None)])))


class TestGeneroLaunchBox(unittest.TestCase):
    """traduzir_genero (mapa manual EN->PT, LaunchBox só tem inglês) e
    find_genero (match exato, mesma regra de find_cover)."""

    def test_traduz_generos_conhecidos(self):
        self.assertEqual(lb.traduzir_genero("Platform"), "Plataforma")
        self.assertEqual(lb.traduzir_genero("Role-Playing"), "RPG")
        self.assertEqual(lb.traduzir_genero("Shooter"), "Tiro")

    def test_usa_so_o_primeiro_quando_tem_varios(self):
        self.assertEqual(lb.traduzir_genero("Role-Playing; Shooter"), "RPG")

    def test_sem_mapa_mantem_o_original(self):
        self.assertEqual(lb.traduzir_genero("Some Weird Genre"), "Some Weird Genre")

    def test_vazio_ou_none_vira_none(self):
        self.assertIsNone(lb.traduzir_genero(None))
        self.assertIsNone(lb.traduzir_genero(""))

    def test_find_genero_match_exato(self):
        index = {"SFC": {"chronotrigger": [None, "Chrono Trigger", "Role-Playing"]}}
        self.assertEqual(lb.find_genero("SFC", "Chrono Trigger", index), "RPG")

    def test_find_genero_sem_match_devolve_none(self):
        index = {"SFC": {"chronotrigger": [None, "Chrono Trigger", "Role-Playing"]}}
        self.assertIsNone(lb.find_genero("SFC", "Outro Jogo", index))
        self.assertIsNone(lb.find_genero("PS2", "Chrono Trigger", index))

    def test_find_genero_nao_faz_match_por_prefixo(self):
        # Ao contrário de find_cover, gênero errado por semelhança de
        # nome é pior que não preencher - sem fallback de prefixo aqui.
        index = {"SFC": {"chronotriggerdeluxe": [None, "Chrono Trigger Deluxe", "RPG"]}}
        self.assertIsNone(lb.find_genero("SFC", "Chrono Trigger", index))


if __name__ == "__main__":
    unittest.main()
