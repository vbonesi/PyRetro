"""Testes de core/library.py - as regras de identidade de jogo.

Este módulo é o que decide "esses dois registros são o mesmo jogo?", e
cada regra aqui existe por causa de um problema real que apareceu em
produção (estão citados nos testes). São justamente as regras que
quebram em silêncio: um merge errado não dá erro, só junta ou duplica
jogo, e a pessoa só descobre olhando a tela dias depois.

Sem dependência externa (unittest da stdlib), igual ao resto do projeto:
    python3 -m unittest discover -s tests -v
"""
import json
import io
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import library as lm


class TestSteamWishlistCompleta(unittest.TestCase):
    def test_falha_em_um_detalhe_cancela_lista_inteira(self):
        respostas = [
            io.BytesIO(json.dumps({"response": {"items": [{"appid": 1}, {"appid": 2}]}}).encode()),
            io.BytesIO(json.dumps({"1": {"success": True, "data": {"name": "Jogo 1"}}}).encode()),
            OSError("falha temporária"),
        ]
        with patch.object(lm.urllib.request, "urlopen", side_effect=respostas):
            with patch.object(lm, "find_cover_steam_cdn", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "appid 2.*sincronização cancelada"):
                    lm.read_steam_wishlist({"steamid64": "123"})

    def test_resposta_incompleta_nao_vira_lista_vazia(self):
        with patch.object(lm.urllib.request, "urlopen", return_value=io.BytesIO(b'{"response": {}}')):
            with self.assertRaisesRegex(RuntimeError, "sem lista de itens válida"):
                lm.read_steam_wishlist({"steamid64": "123"})


def jogo(nome, plataforma, **campos):
    g = lm._blank_game(nome, plataforma)
    g.update(campos)
    return g


class TestPlataformaParaROM(unittest.TestCase):
    """rom_code_for_plataforma decide se uma plataforma da Biblioteca
    corresponde a um sistema de ROM. Errar pra MENOS só deixa de cruzar;
    errar pra MAIS mistura jogos diferentes (ver TestNaoMisturaPlataforma)."""

    def test_reconhece_rotulos_da_planilha_e_do_config(self):
        # Os dois vocabulários que aparecem de verdade: o que o usuário
        # escreveu na planilha e o que o config.toml usa como nome.
        casos = {
            "SNES": "SFC", "Nintendo - Super Nintendo Entertainment System": "SFC",
            "PlayStation 2": "PS2", "Sony - PlayStation 2": "PS2",
            "Game Boy Advanced": "GBA",   # com "d" a mais, como estava na planilha
            "Arcade": "ARCADE", "Mega Drive": "MD", "PlayStation": "PS",
        }
        for texto, esperado in casos.items():
            self.assertEqual(lm.rom_code_for_plataforma(texto), esperado, texto)

    def test_loja_nunca_vira_sistema_de_rom(self):
        for texto in ("Steam", "Xbox One", "GOG", "Epic Games Store", "iOS", ""):
            self.assertIsNone(lm.rom_code_for_plataforma(texto), texto)


class TestNaoMisturaPlataforma(unittest.TestCase):
    """Achado real (27/08): cruzar ROM<->Biblioteca só por NOME juntou
    "Celeste" do Xbox com um "Celeste.gba" (romhack, jogo diferente), e
    fez o Chrono Trigger da Steam "roubar" o card da ROM de SNES."""

    def setUp(self):
        self.lib = {"games": [
            jogo("Celeste", "Xbox One", nota=11.0, finalizado=True),
            jogo("Celeste", "Nintendo - Game Boy Advance"),
        ]}

    def test_acha_o_da_plataforma_pedida(self):
        achado = lm.find_for_rom(lm.index_by_rom_name(self.lib), "Celeste", "GBA")
        self.assertEqual(achado["plataforma"], "Nintendo - Game Boy Advance")
        self.assertIsNone(achado["nota"], "pegou o registro do Xbox por engano")

    def test_nao_acha_em_plataforma_sem_correspondencia(self):
        self.assertIsNone(lm.find_for_rom(lm.index_by_rom_name(self.lib), "Celeste", "SFC"))

    def test_criar_para_rom_nao_encosta_no_registro_de_loja(self):
        novo = lm.get_or_create_for_rom(
            self.lib, "Celeste", "SFC", "Nintendo - Super Nintendo Entertainment System", "rom:SFC")
        self.assertEqual(len(self.lib["games"]), 3, "devia ter criado um registro à parte")
        self.assertIsNone(novo["nota"])
        xbox = next(g for g in self.lib["games"] if g["plataforma"] == "Xbox One")
        self.assertEqual(xbox["nota"], 11.0, "o registro do Xbox foi alterado")

    def test_criar_duas_vezes_nao_duplica(self):
        for _ in range(2):
            lm.get_or_create_for_rom(self.lib, "Celeste", "GBA",
                                     "Nintendo - Game Boy Advance", "rom:GBA")
        self.assertEqual(len(self.lib["games"]), 2)


class TestRomTrackingInfo(unittest.TestCase):
    """gui/server.py tinha essa MESMA lógica copiada em dois lugares
    (ROM leve e pesada) e uma cópia nunca ganhou tempo/observacoes
    quando os outros campos de tracking foram adicionados - o popup de
    comentário e o "✎ Editar dados do jogo" de ROM sempre apareciam
    vazios mesmo com tempo/comentário já salvo (achado do usuário
    11/09: "os jogos de roms leves estão sem tempo e comentario, pelo
    menos no lapiszinho"). Extraído pra um lugar só (rom_tracking_info)
    exatamente pra essa dessincronia não voltar a acontecer."""

    def test_traz_todos_os_campos_de_tracking(self):
        lib = {"games": [jogo("Celeste", "Nintendo - Game Boy Advance",
                              iniciado=True, finalizado=True, platinado=False, nota=9.5,
                              genero="Plataforma", tempo="12:30:00", observacoes="Ótimo jogo")]}
        info = lm.rom_tracking_info(lm.index_by_rom_name(lib), "Celeste", "GBA")
        self.assertEqual(info, {
            "iniciado": True, "finalizado": True, "platinado": False, "nota": 9.5,
            "genero": "Plataforma", "tempo": "12:30:00", "observacoes": "Ótimo jogo",
        })

    def test_sem_registro_devolve_none(self):
        lib = {"games": []}
        self.assertIsNone(lm.rom_tracking_info(lm.index_by_rom_name(lib), "Celeste", "GBA"))


class TestMergeDeFontes(unittest.TestCase):
    """merge_owned: nome exato anota a fonte; parecido só reporta."""

    def test_nome_igual_anota_fonte_sem_tocar_no_progresso(self):
        lib = {"games": [jogo("Hollow Knight", "Steam", nota=9.5, finalizado=True)]}
        r = lm.merge_owned(lib, [{"nome": "Hollow Knight", "plataforma": "Steam", "fonte": "steam"}])
        self.assertEqual((r["added"], r["merged"]), (0, 1))
        self.assertEqual(lib["games"][0]["fontes"], ["steam"])
        self.assertEqual(lib["games"][0]["nota"], 9.5)

    def test_nome_parecido_nao_mescla_sozinho(self):
        # "Pikmin 2" vs "Pikmin" são jogos diferentes - o relatório
        # existe pra revisão humana, nunca pra aplicar automático.
        lib = {"games": [jogo("Pikmin", "Nintendo Switch")]}
        r = lm.merge_owned(lib, [{"nome": "Pikmin 2", "plataforma": "Nintendo Switch", "fonte": "switch"}])
        self.assertEqual(r["added"], 1, "mesclou por aproximação")
        self.assertEqual(len(lib["games"]), 2)
        self.assertTrue(r["possible_dupes"], "devia ter reportado a semelhança")


class TestRenomearSobrevive(unittest.TestCase):
    """Achado real (28/08): renomear pela tela quebrava o casamento por
    nome, e a próxima sincronização recriava o jogo do zero - duplicado
    e sem o progresso."""

    def test_fonte_continua_reconhecendo_pelo_nome_antigo(self):
        lib = {"games": [jogo("Hollow Knight", "Steam", nota=9.5, fontes=["steam"])]}
        lm.update_game(lib, lib["games"][0]["id"], "nome", "Hollow Knight (2017)")
        self.assertEqual(lib["games"][0]["nomes_alt"], ["Hollow Knight"])

        r = lm.merge_owned(lib, [{"nome": "Hollow Knight", "plataforma": "Steam", "fonte": "steam"}])
        self.assertEqual(r["added"], 0, "recriou o jogo depois do rename")
        self.assertEqual(len(lib["games"]), 1)
        self.assertEqual(lib["games"][0]["nota"], 9.5)

    def test_rom_tambem_casa_pelo_nome_antigo(self):
        lib = {"games": [jogo("Final Fantasy VI", "Nintendo - Super Nintendo Entertainment System")]}
        lm.update_game(lib, lib["games"][0]["id"], "nome", "Final Fantasy VI - Traduzido")
        achado = lm.find_for_rom(lm.index_by_rom_name(lib), "Final Fantasy VI", "SFC")
        self.assertIsNotNone(achado, "perdeu o vínculo com a ROM depois do rename")

    def test_nome_atual_nunca_fica_como_apelido(self):
        # Renomear e voltar atrás: "A" volta a ser o nome vigente, então
        # não pode continuar na lista de apelidos. Sobra só "B", que o
        # registro de fato já teve.
        lib = {"games": [jogo("A", "Steam")]}
        gid = lib["games"][0]["id"]
        lm.update_game(lib, gid, "nome", "B")
        lm.update_game(lib, gid, "nome", "A")
        self.assertEqual(lib["games"][0]["nomes_alt"], ["B"])

    def test_apelido_nao_sequestra_jogo_homonimo_de_verdade(self):
        # Cenário que o teste anterior expôs: alguém renomeia "Portal"
        # pra "Portal 2" por engano e volta atrás, deixando "Portal 2"
        # como apelido. Quando o "Portal 2" DE VERDADE chega da loja,
        # ele tem que casar com o próprio registro, não com o apelido.
        lib = {"games": [jogo("Portal", "Steam", nota=9.4), jogo("Portal 2", "Steam")]}
        lm.update_game(lib, lib["games"][0]["id"], "nome", "Portal 2")
        lm.update_game(lib, lib["games"][0]["id"], "nome", "Portal")
        self.assertIn("Portal 2", lib["games"][0]["nomes_alt"])

        r = lm.merge_owned(lib, [{"nome": "Portal 2", "plataforma": "Steam", "fonte": "steam"}])
        self.assertEqual(r["added"], 0)
        self.assertEqual(lib["games"][1]["fontes"], ["steam"], "a fonte foi parar no jogo errado")
        self.assertEqual(lib["games"][0]["fontes"], [], "o Portal recebeu a fonte do Portal 2")


class TestValidacaoDeCampos(unittest.TestCase):
    """update_game é a única porta de escrita da tela - valor inválido
    tem que ser recusado aqui, não gravado e descoberto depois."""

    def setUp(self):
        self.lib = {"games": [jogo("Jogo", "Steam")]}
        self.gid = self.lib["games"][0]["id"]

    def test_campo_desconhecido_e_recusado(self):
        self.assertFalse(lm.update_game(self.lib, self.gid, "id", "outro"))
        self.assertFalse(lm.update_game(self.lib, self.gid, "fontes", ["x"]))

    def test_jogo_inexistente_devolve_falso(self):
        self.assertFalse(lm.update_game(self.lib, "nao-existe", "nota", 5))

    def test_nome_e_plataforma_nao_podem_ficar_vazios(self):
        for campo in ("nome", "plataforma"):
            with self.assertRaises(ValueError, msg=campo):
                lm.update_game(self.lib, self.gid, campo, "   ")

    def test_nota_fora_da_faixa(self):
        with self.assertRaises(ValueError):
            lm.update_game(self.lib, self.gid, "nota", 12)
        self.assertTrue(lm.update_game(self.lib, self.gid, "nota", 11))   # 11 é válido (nota "fora da escala")

    def test_data_aceita_os_dois_formatos_e_recusa_lixo(self):
        lm.update_game(self.lib, self.gid, "lancamento", "25/10/2025")
        self.assertEqual(self.lib["games"][0]["lancamento"], "2025-10-25")
        lm.update_game(self.lib, self.gid, "data_final", "2024-01-02")
        self.assertEqual(self.lib["games"][0]["data_final"], "2024-01-02")
        with self.assertRaises(ValueError):
            lm.update_game(self.lib, self.gid, "lancamento", "banana")

    def test_texto_vazio_vira_none(self):
        lm.update_game(self.lib, self.gid, "observacoes", "   ")
        self.assertIsNone(self.lib["games"][0]["observacoes"])


class TestGravacaoAtomica(unittest.TestCase):
    """Achado real (28/08): write_text direto deixava o arquivo pela
    metade se alguém lesse no meio - a GUI é multi-thread e ainda tem
    job de fundo escrevendo."""

    def test_nunca_deixa_arquivo_parcial(self):
        with tempfile.TemporaryDirectory() as d:
            alvo = Path(d) / "library.json"
            lm.save_library(alvo, {"games": [jogo("A", "Steam")]})
            lm.save_library(alvo, {"games": [jogo(f"Jogo {i}", "Steam") for i in range(500)]})
            # Se a gravação não fosse atômica, um leitor poderia pegar
            # JSON truncado; aqui garantimos ao menos que o resultado
            # final é sempre parseável e completo.
            self.assertEqual(len(json.loads(alvo.read_text())["games"]), 500)
            self.assertFalse(list(Path(d).glob("*.tmp")), "deixou temporário pra trás")

    def test_cria_a_pasta_se_nao_existir(self):
        with tempfile.TemporaryDirectory() as d:
            alvo = Path(d) / "nova" / "library.json"
            lm.save_library(alvo, {"games": []})
            self.assertTrue(alvo.exists())

    def test_recusa_id_duplicado_sem_tocar_no_arquivo_anterior(self):
        with tempfile.TemporaryDirectory() as d:
            alvo = Path(d) / "library.json"
            antes = {"games": [jogo("Íntegro", "Steam")]}
            lm.save_library(alvo, antes)
            duplicado = {"games": [jogo("A", "Steam", id="mesmo"),
                                    jogo("B", "Xbox", id="mesmo")]}
            with self.assertRaisesRegex(ValueError, "id\\(s\\) duplicado"):
                lm.save_library(alvo, duplicado)
            self.assertEqual(json.loads(alvo.read_text()), antes)


class TestIdsUnicos(unittest.TestCase):
    def test_sufixo_evitar_colisao_do_slug(self):
        lib = {"games": [jogo("A B", "Steam")]}
        self.assertEqual(lm._unique_game_id(lib, "A:B", "Steam"), "a-b-steam-2")

    def test_criadores_usam_id_unico(self):
        # Mesmo uma biblioteca antiga com id incoerente não pode fazer uma
        # entrada nova sequestrar a mesma chave.
        antigo = jogo("Outro", "Xbox", id="a-b-steam")
        lib = {"games": [antigo]}
        lm.merge_owned(lib, [{"nome": "A B", "plataforma": "Steam", "fonte": "steam"}])
        self.assertEqual(lib["games"][1]["id"], "a-b-steam-2")


class TestNomeDeJogoSwitch(unittest.TestCase):
    """A pasta do Switch usa tag de formato no nome ("[NSZ]"), que não
    faz parte do nome do jogo."""

    def test_remove_tag_de_formato(self):
        self.assertEqual(lm._limpa_nome_switch("Nine Sols [NSZ]"), "Nine Sols")
        self.assertEqual(lm._limpa_nome_switch("Pikmin 4 [NSP]"), "Pikmin 4")
        self.assertEqual(lm._limpa_nome_switch("Cat Rescue Story [XCI]"), "Cat Rescue Story")

    def test_nome_sem_tag_fica_igual(self):
        self.assertEqual(lm._limpa_nome_switch("Crash Bandicoot N. Sane Trilogy"),
                         "Crash Bandicoot N. Sane Trilogy")


class TestSugestaoDeColecao(unittest.TestCase):
    """nomes_dentro_da_colecao pré-preenche a tela de decompor a partir
    do que existe DENTRO da pasta. É chute assumido - o usuário corrige
    na mão - mas os três formatos reais têm que sair limpos."""

    def test_subpasta_por_jogo(self):
        self.assertEqual(
            lm.nomes_dentro_da_colecao([{"name": "Portal"}, {"name": "Portal 2"}]),
            ["Portal", "Portal 2"])

    def test_arquivo_com_title_id_e_versao(self):
        # Base + update do mesmo jogo viram uma entrada só.
        self.assertEqual(lm.nomes_dentro_da_colecao([
            {"name": "Pikmin 1 [0100AA80194B0000][v0].nsp"},
            {"name": "Pikmin 1 [0100AA80194B0800][v65536].nsp"},
            {"name": "Pikmin 2 [0100D680194B2000][v0].nsp"},
        ]), ["Pikmin 1", "Pikmin 2"])

    def test_anotacao_de_tamanho_e_removida(self):
        self.assertEqual(lm.nomes_dentro_da_colecao([
            {"name": "Demonschool (0.89 GB)"}, {"name": "Demonschool (1.23 GB)"},
        ]), ["Demonschool"])

    def test_colecao_que_nao_revela_o_conteudo(self):
        # Castlevania Dominus: os arquivos têm só o nome da própria
        # coletânea. Devolver ela mesma é honesto - não dá pra adivinhar.
        self.assertEqual(lm.nomes_dentro_da_colecao([
            {"name": "Castlevania Dominus Collection [0100FA][v0].nsp"},
            {"name": "Castlevania Dominus Collection [0100FA][v196608].nsp"},
        ]), ["Castlevania Dominus Collection"])

    def test_numeracao_de_ordem_da_subpasta_sai(self):
        # Pasta real do acervo (29/08): o usuário numera a subpasta pra
        # manter a ordem da série. O número é da pasta, não do jogo.
        self.assertEqual(lm.nomes_dentro_da_colecao([
            {"name": "1. Demons of Asteborg"}, {"name": "2. Astebros"},
        ]), ["Demons of Asteborg", "Astebros"])

    def test_numero_que_faz_parte_do_nome_fica(self):
        # A trava do "ponto + espaço": jogo que COMEÇA com número não
        # pode ser mutilado.
        self.assertEqual(lm.nomes_dentro_da_colecao([
            {"name": "1979 Revolution Black Friday"}, {"name": "13 Sentinels"},
            {"name": "2020 Super Baseball"},
        ]), ["1979 Revolution Black Friday", "13 Sentinels", "2020 Super Baseball"])


class TestNomeAlternativoDeCapa(unittest.TestCase):
    """O selo da linha de relançamento vem grudado no título oficial e
    quebra a busca de capa. Achado 29/08: depois de decompor os bundles,
    99 dos 108 "ACA NEOGEO ..." ficaram sem capa - o SteamGridDB não tem
    "ACA NEOGEO METAL SLUG", tem "Metal Slug"."""

    def test_tira_o_selo(self):
        self.assertEqual(lm.nomes_alternativos_de_capa("ACA NEOGEO METAL SLUG"),
                         ["METAL SLUG"])
        self.assertEqual(lm.nomes_alternativos_de_capa("SEGA AGES Out Run"), ["Out Run"])

    def test_nome_normal_nao_ganha_alternativa(self):
        for n in ("Metal Slug", "Hades II", "Turrican Anthology Vol. 1"):
            self.assertEqual(lm.nomes_alternativos_de_capa(n), [], n)

    def test_selo_sozinho_nao_vira_nome_vazio(self):
        self.assertEqual(lm.nomes_alternativos_de_capa("ACA NEOGEO "), [])


class TestFetchCoversFallback(unittest.TestCase):
    """A ordem importa nos dois sentidos, e é por isso que o alternativo
    é FALLBACK e não substituição: "SEGA AGES Out Run" tem capa própria
    (arte do relançamento) e "Out Run" sozinho não; "ACA NEOGEO METAL
    SLUG" é o contrário. Trocar a busca em vez de acrescentar perderia
    metade dos casos."""

    def setUp(self):
        self._original = lm.find_cover_steamgriddb
        self.consultas = []

    def tearDown(self):
        lm.find_cover_steamgriddb = self._original

    def _rodar(self, nome_do_jogo, catalogo):
        """catalogo = nomes que a fonte "tem". Devolve (capa?, consultas)."""
        def falso(nome, api_key):
            self.consultas.append(nome)
            return "http://exemplo/capa.png" if nome in catalogo else None
        lm.find_cover_steamgriddb = falso

        biblioteca = {"games": [jogo(nome_do_jogo, "Nintendo Switch")]}
        with tempfile.TemporaryDirectory() as d:
            capas = Path(d) / "capas"
            # Sem rede de verdade: o download é o único passo que sobra,
            # então é ele que precisa ser neutralizado.
            original_urlopen = lm.urllib.request.urlopen
            lm.urllib.request.urlopen = lambda *a, **k: _RespostaFalsa()
            try:
                r = lm.fetch_covers(biblioteca, capas, "chave-falsa")
            finally:
                lm.urllib.request.urlopen = original_urlopen
        return r, self.consultas

    def test_nome_de_verdade_vem_primeiro(self):
        # Se o nome completo resolve, o alternativo nem é consultado.
        r, consultas = self._rodar("SEGA AGES Out Run", {"SEGA AGES Out Run"})
        self.assertEqual(r["baixado"], 1)
        self.assertEqual(consultas, ["SEGA AGES Out Run"], "consultou o alternativo à toa")
        self.assertEqual(r["via_alias"], 0)

    def test_alternativo_salva_quando_o_completo_falha(self):
        r, consultas = self._rodar("ACA NEOGEO METAL SLUG", {"METAL SLUG"})
        self.assertEqual(r["baixado"], 1)
        self.assertEqual(consultas, ["ACA NEOGEO METAL SLUG", "METAL SLUG"])
        self.assertEqual(r["via_alias"], 1)
        self.assertEqual(r["aliases"], [("ACA NEOGEO METAL SLUG", "METAL SLUG")])

    def test_nenhum_dos_dois_continua_sem_capa(self):
        r, _ = self._rodar("ACA NEOGEO ZUPAPA!", set())
        self.assertEqual((r["baixado"], r["sem_match"]), (0, 1))


class TestTempoParaHoras(unittest.TestCase):
    """tempo_para_horas soma o campo livre "tempo" (HH:MM:SS) pra
    estatística de tempo total. Achado 31/08 ao somar a biblioteca real:
    93 dos 94 preenchidos eram HH:MM:SS exato, 1 só tinha HH:MM."""

    def test_hhmmss(self):
        self.assertAlmostEqual(lm.tempo_para_horas("31:40:00"), 31 + 40 / 60)
        self.assertAlmostEqual(lm.tempo_para_horas("120:38:00"), 120 + 38 / 60)

    def test_hhmm_sem_segundos(self):
        self.assertAlmostEqual(lm.tempo_para_horas("01:26"), 1 + 26 / 60)

    def test_vazio_ou_invalido_vira_zero(self):
        for v in (None, "", "várias horas", "abc"):
            self.assertEqual(lm.tempo_para_horas(v), 0.0, v)


class TestMinutosParaTempo(unittest.TestCase):
    """Inversa de tempo_para_horas - playtime_forever da Steam (minutos)
    pro mesmo formato HH:MM:SS que o campo `tempo` já usa (pedido do
    usuário 11/09: "tempo total de jogos contabilizado de todas as
    fontes")."""

    def test_converte_minutos(self):
        self.assertEqual(lm.minutos_para_tempo(90), "01:30:00")
        self.assertEqual(lm.minutos_para_tempo(1523), "25:23:00")

    def test_zero_ou_none_vira_none(self):
        for v in (0, None, -5):
            self.assertIsNone(lm.minutos_para_tempo(v))

    def test_ida_e_volta_bate_com_tempo_para_horas(self):
        tempo = lm.minutos_para_tempo(150)  # 2h30
        self.assertAlmostEqual(lm.tempo_para_horas(tempo), 2.5)


class TestMergeOwnedPreenceTempo(unittest.TestCase):
    """merge_owned só ganhou o preenchimento de tempo em 11/09 - a
    Steam é a única fonte que manda playtime de verdade (via
    read_steam_library); o resto do merge (fontes, possible_dupes)
    continua igual, só não pode NUNCA sobrescrever tempo já digitado
    pelo usuário."""

    def test_registro_novo_ganha_o_tempo_da_fonte(self):
        lib = {"games": []}
        r = lm.merge_owned(lib, [{"nome": "Hades", "plataforma": "Steam", "fonte": "steam", "tempo": "10:00:00"}])
        self.assertEqual(r["added"], 1)
        self.assertEqual(lib["games"][0]["tempo"], "10:00:00")

    def test_registro_existente_sem_tempo_e_preenchido(self):
        g = jogo("Hades", "Steam")
        lib = {"games": [g]}
        lm.merge_owned(lib, [{"nome": "Hades", "plataforma": "Steam", "fonte": "steam", "tempo": "10:00:00"}])
        self.assertEqual(g["tempo"], "10:00:00")

    def test_registro_com_tempo_manual_nao_e_sobrescrito(self):
        g = jogo("Hades", "Steam", tempo="99:00:00")
        lib = {"games": [g]}
        lm.merge_owned(lib, [{"nome": "Hades", "plataforma": "Steam", "fonte": "steam", "tempo": "10:00:00"}])
        self.assertEqual(g["tempo"], "99:00:00")

    def test_fonte_sem_tempo_nao_mexe_em_nada(self):
        g = jogo("Some Game", "Xbox")
        lib = {"games": [g]}
        lm.merge_owned(lib, [{"nome": "Some Game", "plataforma": "Xbox", "fonte": "xbox:jogado"}])
        self.assertIsNone(g["tempo"])


class TestGravarPNG(unittest.TestCase):
    """Achado 29/08: 20 das 116 capas baixadas eram JPEG dentro de um
    arquivo .png. O projeto já sabia disso desde 02/08 (launchbox
    converte, validate-covers caça o estrago), mas o caminho da
    Biblioteca gravava direto o que a URL devolvia."""

    def test_png_de_verdade_passa_intacto(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "capa.png"
            data = b"\x89PNG\r\n\x1a\n" + b"conteudo" * 200
            self.assertTrue(lm.gravar_png(data, dest))
            self.assertEqual(dest.read_bytes(), data, "reescreveu um PNG que já estava certo")

    def test_jpeg_vira_png_de_verdade(self):
        import shutil
        if not shutil.which("convert"):
            self.skipTest("ImageMagick não instalado")
        with tempfile.TemporaryDirectory() as d:
            origem = Path(d) / "origem.jpg"
            subprocess.run(["convert", "-size", "600x900", "xc:red", str(origem)], check=True)
            dest = Path(d) / "capa.png"
            self.assertTrue(lm.gravar_png(origem.read_bytes(), dest))
            self.assertTrue(dest.read_bytes().startswith(b"\x89PNG"),
                            "gravou JPEG com nome .png de novo")

    def test_temporario_nao_fica_pra_tras(self):
        import shutil
        if not shutil.which("convert"):
            self.skipTest("ImageMagick não instalado")
        with tempfile.TemporaryDirectory() as d:
            origem = Path(d) / "o.jpg"
            subprocess.run(["convert", "-size", "60x90", "xc:blue", str(origem)], check=True)
            dest = Path(d) / "capa.png"
            lm.gravar_png(origem.read_bytes(), dest)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ["capa.png", "o.jpg"])


class _RespostaFalsa:
    """Context manager mínimo no formato que urlopen devolve."""
    def read(self):
        return b"\x89PNG\r\n\x1a\n" + b"0" * 100

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestImportacaoDaPlanilha(unittest.TestCase):
    def test_reimportar_atualiza_em_vez_de_duplicar(self):
        with tempfile.TemporaryDirectory() as d:
            csv_path = Path(d) / "planilha.csv"
            csv_path.write_text(
                "Nome do Jogo,Plataforma,Nota,Finalizado\nCeleste,Xbox One,10,SIM\n", encoding="utf-8")
            lib = {"games": []}
            lm.import_sheet_csv(lib, csv_path)
            csv_path.write_text(
                "Nome do Jogo,Plataforma,Nota,Finalizado\nCeleste,Xbox One,11,SIM\n", encoding="utf-8")
            r = lm.import_sheet_csv(lib, csv_path)
            self.assertEqual((len(lib["games"]), r["updated"]), (1, 1))
            self.assertEqual(lib["games"][0]["nota"], 11.0)


class TestRemoveGame(unittest.TestCase):
    def test_remove_tira_do_arquivo(self):
        lib = {"games": [jogo("A", "PC"), jogo("B", "PC")]}
        alvo = lib["games"][0]["id"]
        self.assertTrue(lm.remove_game(lib, alvo))
        self.assertEqual([g["nome"] for g in lib["games"]], ["B"])

    def test_remove_id_inexistente_nao_quebra(self):
        lib = {"games": [jogo("A", "PC")]}
        self.assertFalse(lm.remove_game(lib, "nao-existe"))
        self.assertEqual(len(lib["games"]), 1)


class TestAddToWishlist(unittest.TestCase):
    """add_to_wishlist é o caminho de PSN/Xbox: só acrescenta, NUNCA
    tira. O teste que importa aqui é justamente o que não pode
    acontecer - a lista incompleta digitada pelo usuário não pode
    encostar em quem já está na lista (incidente de 21/09: 3 nomes na
    PSN e 1 no Xbox apagaram 154 registros)."""

    def test_nome_novo_cria_registro_com_a_fonte(self):
        lib = {"games": []}
        r = lm.add_to_wishlist(lib, "wishlist:psn", "PSN", ["God of War"])
        self.assertEqual(r["adicionados"], 1)
        self.assertEqual(lib["games"][0]["fontes"], ["wishlist:psn"])

    def test_nome_que_ja_existe_so_ganha_a_fonte_sem_duplicar(self):
        existente = jogo("God of War", "PSN")
        lib = {"games": [existente]}
        r = lm.add_to_wishlist(lib, "wishlist:psn", "PSN", ["God of War"])
        self.assertEqual(len(lib["games"]), 1)
        self.assertEqual(r["adicionados"], 1)
        self.assertIn("wishlist:psn", existente["fontes"])

    def test_quem_nao_esta_na_lista_nao_e_tocado(self):
        # O incidente de 21/09 em uma linha: o usuário digita só os
        # jogos novos, e o resto da lista tem que continuar lá.
        antigo = jogo("Erica", "PSN", fontes=["wishlist:psn"])
        lib = {"games": [antigo]}
        r = lm.add_to_wishlist(lib, "wishlist:psn", "PSN", ["Dreams"])
        self.assertEqual((r["removidos"], r["apagados"]), (0, 0))
        self.assertEqual(len(lib["games"]), 2)
        self.assertIn(antigo, lib["games"])
        self.assertEqual(antigo["fontes"], ["wishlist:psn"])

    def test_ja_marcado_nao_conta_como_novo(self):
        g = jogo("God of War", "PSN", fontes=["wishlist:psn"])
        lib = {"games": [g]}
        r = lm.add_to_wishlist(lib, "wishlist:psn", "PSN", ["God of War"])
        self.assertEqual((r["adicionados"], r["ja_tinha"]), (0, 1))


class TestRemoveFromWishlist(unittest.TestCase):
    """Saída item a item, pelo ✎ (21/09). Mesma regra de sempre: só
    apaga o registro se não sobrar nenhuma outra fonte."""

    def test_sem_outra_fonte_o_registro_e_apagado(self):
        g = jogo("Erica", "PSN", fontes=["wishlist:psn"])
        lib = {"games": [g]}
        r = lm.remove_from_wishlist(lib, "wishlist:psn", g["id"])
        self.assertEqual(r, {"removido": True, "apagado": True})
        self.assertEqual(lib["games"], [])

    def test_com_outra_fonte_so_perde_a_marca(self):
        g = jogo("Diablo", "PSN", fontes=["wishlist:psn", "heroic:gog"])
        lib = {"games": [g]}
        r = lm.remove_from_wishlist(lib, "wishlist:psn", g["id"])
        self.assertEqual(r, {"removido": True, "apagado": False})
        self.assertEqual(g["fontes"], ["heroic:gog"])

    def test_so_mexe_na_lista_pedida(self):
        g = jogo("EDENS ZERO", "Xbox", fontes=["wishlist:steam", "wishlist:xbox"])
        lib = {"games": [g]}
        lm.remove_from_wishlist(lib, "wishlist:xbox", g["id"])
        self.assertEqual(g["fontes"], ["wishlist:steam"])

    def test_id_desconhecido_devolve_none(self):
        self.assertIsNone(lm.remove_from_wishlist({"games": []}, "wishlist:psn", "nada"))


class TestMarkWishlistOwned(unittest.TestCase):
    """"✅ Comprado": sai dos Desejados e entra na Biblioteca, sem
    perder nada do que o registro já tinha."""

    def test_troca_a_marca_de_desejo_pela_fonte_de_posse(self):
        g = jogo("Dreams", "PSN", fontes=["wishlist:psn"])
        g["genero"], g["capa"] = "Sandbox", "capas/dreams.png"
        lib = {"games": [g]}
        r = lm.mark_wishlist_owned(lib, "wishlist:psn", g["id"])
        self.assertEqual(r, {"fonte_posse": "psn", "ja_tinha_posse": False})
        self.assertEqual(g["fontes"], ["psn"])
        self.assertEqual((g["genero"], g["capa"]), ("Sandbox", "capas/dreams.png"))
        self.assertEqual(len(lib["games"]), 1)

    def test_quem_ja_era_posse_so_perde_a_marca_sem_duplicar_fonte(self):
        g = jogo("Horizon Zero Dawn", "PSN", fontes=["psn:fisico", "wishlist:psn", "psn"])
        lib = {"games": [g]}
        r = lm.mark_wishlist_owned(lib, "wishlist:psn", g["id"])
        self.assertTrue(r["ja_tinha_posse"])
        self.assertEqual(g["fontes"], ["psn:fisico", "psn"])

    def test_id_desconhecido_devolve_none(self):
        self.assertIsNone(lm.mark_wishlist_owned({"games": []}, "wishlist:psn", "nada"))

    def test_id_de_jogo_fora_da_lista_nao_vira_posse(self):
        g = jogo("Jogo de outra lista", "Xbox", fontes=["wishlist:xbox"])
        lib = {"games": [g]}
        self.assertIsNone(lm.mark_wishlist_owned(lib, "wishlist:psn", g["id"]))
        self.assertEqual(g["fontes"], ["wishlist:xbox"])


class TestSyncWishlist(unittest.TestCase):
    """sync_wishlist (só a Steam usa, onde a lista vem da API ao vivo)
    é a única rotina do projeto que apaga registro sozinha (pedido
    explícito do usuário 11/09: lista de desejos não tem progresso pra
    perder) - por isso o cuidado extra de testar o caso que NÃO pode
    apagar: jogo que saiu da lista mas já é posse de verdade por outra
    fonte."""

    def test_nome_novo_cria_registro_com_a_fonte(self):
        lib = {"games": []}
        r = lm.sync_wishlist(lib, "wishlist:steam", "Steam", ["God of War"])
        self.assertEqual(r["adicionados"], 1)
        self.assertEqual(lib["games"][0]["fontes"], ["wishlist:steam"])

    def test_nome_que_ja_existe_so_ganha_a_fonte_sem_duplicar(self):
        existente = jogo("God of War", "Steam")
        lib = {"games": [existente]}
        r = lm.sync_wishlist(lib, "wishlist:steam", "Steam", ["God of War"])
        self.assertEqual(len(lib["games"]), 1)
        self.assertEqual(r["adicionados"], 1)
        self.assertIn("wishlist:steam", existente["fontes"])

    def test_nome_que_sai_da_lista_sem_outra_fonte_e_apagado(self):
        g = jogo("Erica", "Steam", fontes=["wishlist:steam"])
        lib = {"games": [g]}
        r = lm.sync_wishlist(lib, "wishlist:steam", "Steam", [])
        self.assertEqual((r["removidos"], r["apagados"]), (1, 1))
        self.assertEqual(lib["games"], [])

    def test_nome_que_sai_da_lista_mas_e_posse_de_verdade_so_perde_a_marca(self):
        # achado real (pedido do usuário): jogo saiu da wishlist ao vivo
        # porque o usuário já conseguiu em outra fonte (ex: Heroic) -
        # o registro tem que sobreviver, só sem a marca de desejo.
        g = jogo("Diablo", "Steam", fontes=["wishlist:steam", "heroic:gog"])
        lib = {"games": [g]}
        r = lm.sync_wishlist(lib, "wishlist:steam", "Steam", [])
        self.assertEqual((r["removidos"], r["apagados"]), (1, 0))
        self.assertEqual(lib["games"], [g])
        self.assertEqual(g["fontes"], ["heroic:gog"])

    def test_ja_marcado_nao_conta_como_novo(self):
        g = jogo("God of War", "Steam", fontes=["wishlist:steam"])
        lib = {"games": [g]}
        r = lm.sync_wishlist(lib, "wishlist:steam", "Steam", ["God of War"])
        self.assertEqual((r["adicionados"], r["ja_tinha"]), (0, 1))

    def test_nao_encosta_em_lista_de_outra_loja(self):
        # Sincronizar a Steam não pode mexer no que é da PSN/Xbox.
        g = jogo("Erica", "PSN", fontes=["wishlist:psn"])
        lib = {"games": [g]}
        lm.sync_wishlist(lib, "wishlist:steam", "Steam", [])
        self.assertEqual(lib["games"], [g])


if __name__ == "__main__":
    unittest.main()
