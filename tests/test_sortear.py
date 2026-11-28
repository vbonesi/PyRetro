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


class TestPoolBibliotecaPorSubgrupo(unittest.TestCase):
    """Sub-grupos de plataforma da Biblioteca no sorteio (11/09, pedido
    do usuário: "colocar em sistemas específicos o biblioteca também,
    com o nintendo switch, PS4 e Xbox's ... e o resto como PC")."""

    def test_agrupa_geracoes_de_xbox_juntas(self):
        library = {"games": [
            jogo("A", "Xbox"), jogo("B", "Xbox One"),
            jogo("C", "Xbox Series S"), jogo("D", "Xbox 360"),
        ]}
        pool = sortear_mod._pool_biblioteca(library, {}, subgrupo="xbox")
        self.assertEqual({p[1] for p in pool}, {"A", "B", "C", "D"})

    def test_agrupa_psn_e_playstation_juntas(self):
        library = {"games": [
            jogo("A", "PSN"), jogo("B", "PlayStation 4"), jogo("C", "PlayStation 3"),
        ]}
        pool = sortear_mod._pool_biblioteca(library, {}, subgrupo="playstation")
        self.assertEqual({p[1] for p in pool}, {"A", "B", "C"})

    def test_pc_e_o_que_sobra(self):
        library = {"games": [
            jogo("Steam game", "Steam"), jogo("GOG game", "GOG"),
            jogo("Switch game", "Nintendo Switch"),
        ]}
        pool = sortear_mod._pool_biblioteca(library, {}, subgrupo="pc")
        self.assertEqual({p[1] for p in pool}, {"Steam game", "GOG game"})

    def test_sem_subgrupo_pega_tudo_igual_antes(self):
        library = {"games": [jogo("A", "Xbox"), jogo("B", "Nintendo Switch")]}
        pool = sortear_mod._pool_biblioteca(library, {})
        self.assertEqual({p[1] for p in pool}, {"A", "B"})


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


class TestPoolLeveComDrive(unittest.TestCase):
    """Sorteio de ROM leve vê o que está no Drive, não só o que está no PC."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); (self.root / "SFC").mkdir()
        (self.root / "SFC" / "Local.sfc").write_bytes(b"x")
        self.cfg = {"systems": {"SFC": {"exts": ["sfc"]}}, "heavy_systems": {"PS": {"exts": ["cue"]}}}
        self.catalog = {"SFC": [{"name": "Local.sfc", "size": 1, "is_dir": False}, {"name": "Só no Drive.sfc", "size": 2, "is_dir": False}],
                        "PS": [{"name": "Disco.cue", "size": 3, "is_dir": False}]}

    def test_light_pool_is_local_plus_drive_without_duplicates_and_heavy_stays_heavy(self):
        pool = sortear_mod.build_pool(self.cfg, self.root, self.catalog, None)
        self.assertEqual(sorted(p for p in pool if p[2] == "leve"), [("SFC", "Local.sfc", "leve"), ("SFC", "Só no Drive.sfc", "leve")])
        self.assertEqual([p for p in pool if p[2] == "pesado"], [("PS", "Disco.cue", "pesado")])
        self.assertEqual(len(sortear_mod.build_pool(self.cfg, self.root, self.catalog, "SFC")), 2)
        self.assertEqual(len(sortear_mod.build_pool(self.cfg, self.root, self.catalog, "leve")), 2)


class TestQuatroGrupos(unittest.TestCase):
    """Plano de 27/11: Sortear em retrô, quero jogar (Switch/PS4), já tenho (PS4/Xbox/PC) e todos."""

    def setUp(self):
        import tempfile
        from core import library as lm, onde_roda as orr
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for code, nome in (("SFC", "Chrono.sfc"), ("NDS", "Pokemon.nds")):
            (self.root / code).mkdir(); (self.root / code / nome).write_bytes(b"x")
        self.cfg = {"systems": {"SFC": {"exts": ["sfc"]}, "NDS": {"exts": ["nds"]}}, "heavy_systems": {"PS": {"exts": ["cue"]}}}
        self.catalog = {"PS": [{"name": "Disco.cue", "size": 3, "is_dir": False}]}

        def g(nome, fontes, **k):
            x = lm._blank_game(nome, "Steam"); x["fontes"] = fontes; x.update(k); return x
        quero_ps4 = g("Quero PS4", ["wishlist:psn"]); orr.migrar_game(quero_ps4)
        quero_xbox = g("Quero so Xbox", ["wishlist:xbox"]); orr.migrar_game(quero_xbox)
        tenho_pc = g("Tenho PC", ["heroic:gog"]); orr.migrar_game(tenho_pc)
        tenho_switch = g("Tenho Switch", ["switch"]); orr.migrar_game(tenho_switch)
        retro = g("Retro", ["rom:SFC"])
        self.lib = {"games": [quero_ps4, quero_xbox, tenho_pc, tenho_switch, retro]}

    def nomes(self, grupo):
        return sorted(n for _, n, _ in sortear_mod.build_pool(self.cfg, self.root, self.catalog, grupo, library=self.lib))

    def test_retro_so_tem_sistemas_retro_do_drive(self):
        self.assertEqual(self.nomes("retro"), ["Chrono.sfc"])

    def test_quero_exige_switch_ou_ps4(self):
        self.assertEqual(self.nomes("quero"), ["Quero PS4"])

    def test_tenho_aceita_ps4_xbox_pc_mas_nao_switch(self):
        self.assertEqual(self.nomes("tenho"), ["Tenho PC"])

    def test_todos_junta_os_tres(self):
        self.assertEqual(self.nomes("todos"), ["Chrono.sfc", "Quero PS4", "Tenho PC"])
