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
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import library as lm


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


if __name__ == "__main__":
    unittest.main()
