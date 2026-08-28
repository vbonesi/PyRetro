"""Testes de gui/server.py - as partes que não dependem de rede/config.

Foco em segurança de caminho e no cruzamento ROM<->Biblioteca, que são
as duas coisas do servidor que erram em silêncio: travessia de caminho
grava fora da pasta sem avisar, e um cruzamento errado some com o jogo
de uma aba (ou o duplica) sem nenhum erro na tela.

    python3 -m unittest discover -s tests -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "gui"))
import server as srv
from core import library as lm


class TestNomeDeArquivoSeguro(unittest.TestCase):
    """Achado numa auditoria (28/08): os endpoints de capa montavam
    `capas_dir / f"{label}.png"` com o label vindo da requisição, sem
    checar nada - e o servidor escuta em 0.0.0.0 (rede local inteira).
    Um label com "../" gravava FORA da pasta de capas."""

    def test_recusa_travessia_e_caminho_absoluto(self):
        perigosos = [
            "../PWNED", "../../../../etc/passwd", "/etc/passwd",
            "pasta/arquivo", "..\\\\windows", "", ".", "..", "nulo\x00byte",
        ]
        for nome in perigosos:
            self.assertFalse(srv.nome_de_arquivo_seguro(nome), f"aceitou {nome!r}")

    def test_aceita_nome_de_jogo_de_verdade(self):
        # Nome de jogo tem apóstrofo, dois pontos, parênteses, acento e
        # ponto - a validação não pode ser tão rígida a ponto de barrar
        # o uso normal.
        validos = [
            "Zool", "Tony Hawk's Pro Skater", "Final Fantasy VI (USA)",
            "Sonic 3 & Knuckles", "Pokémon Shield", "Mr. Do!",
            "Castlevania: Symphony of the Night", "19XX - The War Against Destiny",
        ]
        for nome in validos:
            self.assertTrue(srv.nome_de_arquivo_seguro(nome), f"barrou {nome!r}")


class TestDentroDe(unittest.TestCase):
    """Segunda linha de defesa: mesmo com nome validado, o caminho final
    tem que cair dentro da pasta esperada."""

    def test_detecta_dentro_e_fora(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "capas"
            base.mkdir()
            self.assertTrue(srv.dentro_de(base, base / "jogo.png"))
            self.assertTrue(srv.dentro_de(base, base / "sub" / "jogo.png"))
            self.assertFalse(srv.dentro_de(base, Path(d) / "fora.png"))
            self.assertFalse(srv.dentro_de(base, base / ".." / "fora.png"))

    def test_symlink_pra_fora_nao_engana(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "capas"
            base.mkdir()
            fora = Path(d) / "segredo"
            fora.mkdir()
            atalho = base / "atalho"
            atalho.symlink_to(fora)
            self.assertFalse(srv.dentro_de(base, atalho / "x.png"),
                             "symlink permitiu escapar da pasta")


class TestJogoEhROM(unittest.TestCase):
    """is_rom_backed decide se um jogo da Biblioteca some da listagem
    porque já "mora" numa aba de ROM. Exige nome E plataforma - só nome
    misturava Celeste do Xbox com Celeste.gba (achado 27/08)."""

    def setUp(self):
        self.roms = {"GBA": {lm.covers_mod.normalize("Celeste")},
                     "SFC": {lm.covers_mod.normalize("Chrono Trigger")}}

    def _jogo(self, nome, plataforma):
        return lm._blank_game(nome, plataforma)

    def test_rom_de_verdade_e_reconhecida(self):
        g = self._jogo("Celeste", "Nintendo - Game Boy Advance")
        self.assertTrue(srv.is_rom_backed(g, self.roms))

    def test_jogo_de_loja_com_nome_igual_nao_e_confundido(self):
        for plataforma in ("Xbox One", "Steam", "Epic Games Store"):
            g = self._jogo("Celeste", plataforma)
            self.assertFalse(srv.is_rom_backed(g, self.roms), plataforma)

    def test_plataforma_certa_mas_nome_que_nao_existe(self):
        g = self._jogo("Jogo Que Nao Tenho", "Nintendo - Game Boy Advance")
        self.assertFalse(srv.is_rom_backed(g, self.roms))


class TestVersaoDaCapa(unittest.TestCase):
    """Achado 28/08: trocar a capa não aparecia na tela - o arquivo
    mudava mas a URL era a mesma, e o navegador servia a antiga do
    cache."""

    def test_url_ganha_versao_e_muda_quando_o_arquivo_muda(self):
        import os
        import time
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "capa.png"
            f.write_bytes(b"a")
            u1 = srv.com_versao("/images/SFC/capa.png", f)
            self.assertIn("?v=", u1)

            os.utime(f, (time.time() + 10, time.time() + 10))  # simula reescrita
            self.assertNotEqual(u1, srv.com_versao("/images/SFC/capa.png", f))

    def test_arquivo_inexistente_devolve_url_crua(self):
        url = "/images/SFC/nao-existe.png"
        self.assertEqual(srv.com_versao(url, Path("/nao/existe.png")), url)


if __name__ == "__main__":
    unittest.main()
