"""Testes de core/sortear.py - filtro de gênero do sorteio (11/09).

Cobre só as funções puras (sem tocar filesystem/Drive): `_filtrar_por_genero`
e `generos_disponiveis`. `build_pool` em si depende de roms_root/catalog
reais, fora do escopo de um teste unitário rápido.

Sem dependência externa (unittest da stdlib), igual ao resto do projeto:
    python3 -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import library as lm
from core import sortear as sortear_mod


def jogo(nome, plataforma, **campos):
    g = lm._blank_game(nome, plataforma)
    g.update(campos)
    return g


class TestGenerosDisponiveis(unittest.TestCase):
    def test_lista_ordenada_sem_duplicata_e_sem_vazio(self):
        library = {"games": [
            jogo("A", "Steam", genero="RPG"),
            jogo("B", "Steam", genero="Ação"),
            jogo("C", "Steam", genero="RPG"),
            jogo("D", "Steam", genero=None),
        ]}
        self.assertEqual(sortear_mod.generos_disponiveis(library), ["Ação", "RPG"])


class TestFiltrarPorGenero(unittest.TestCase):
    """Achado 11/09 testando a combinação grupo+gênero na tela: ROM leve/
    pesada no pool vem com o nome de ARQUIVO (com extensão, ver
    list_local_names/catalog), mas find_for_rom casa pelo nome gravado no
    registro (sem extensão) - sem tirar o stem antes, o filtro nunca achava
    nada pra ROM (sempre pool vazio), só funcionava por acidente pra
    Biblioteca (que já guarda o nome puro no próprio pool)."""

    def test_biblioteca_casa_por_nome_direto(self):
        library = {"games": [jogo("Hades", "Steam", genero="Ação")]}
        pool = [(None, "Hades", "biblioteca"), (None, "Outro", "biblioteca")]
        resultado = sortear_mod._filtrar_por_genero(pool, "Ação", library, rom_index=None)
        self.assertEqual(resultado, [(None, "Hades", "biblioteca")])

    def test_rom_leve_precisa_tirar_extensao_do_nome_de_arquivo(self):
        library = {"games": [jogo("Chrono Trigger", "Nintendo - Super Nintendo Entertainment System",
                                   genero="RPG")]}
        rom_index = lm.index_by_rom_name(library)
        pool = [("SFC", "Chrono Trigger.smc", "leve"), ("SFC", "Outro Jogo.smc", "leve")]
        resultado = sortear_mod._filtrar_por_genero(pool, "RPG", library, rom_index)
        self.assertEqual(resultado, [("SFC", "Chrono Trigger.smc", "leve")])

    def test_rom_sem_registro_na_biblioteca_fica_de_fora(self):
        library = {"games": []}
        rom_index = lm.index_by_rom_name(library)
        pool = [("SFC", "ROM Qualquer.smc", "leve")]
        resultado = sortear_mod._filtrar_por_genero(pool, "RPG", library, rom_index)
        self.assertEqual(resultado, [])

    def test_genero_diferente_nao_casa(self):
        library = {"games": [jogo("Hades", "Steam", genero="Ação")]}
        pool = [(None, "Hades", "biblioteca")]
        resultado = sortear_mod._filtrar_por_genero(pool, "RPG", library, rom_index=None)
        self.assertEqual(resultado, [])


if __name__ == "__main__":
    unittest.main()
