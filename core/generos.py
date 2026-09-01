"""Preenchimento de gênero pro acervo INTEIRO - Biblioteca, ROM leve e
ROM pesada (pedido do usuário 31/08: "gênero para tudo, inclusive as
ROMs leves e pesadas"). Cascata em fontes automáticas, cada uma só
tentando o que a anterior não achou - todas já devolvem português
direto, sem mapa manual meu exceto o do LaunchBox (que só tem inglês):
  - ROM: ScreenScraper (pt nativo) -> LaunchBox (traduzido)
  - Biblioteca: Steam (pt nativo, appdetails) -> LaunchBox plataforma
    "PC" (traduzido)
Match sempre EXATO (nome normalizado) - gênero errado por semelhança de
nome é pior que deixar em branco.

Diferente de fetch_covers (só mexe em jogo que JÁ tem registro), o
preenchimento de ROM CRIA um registro pra cada uma que ainda não tem
(decisão explícita do usuário, "todo o acervo, ROM por ROM") - usa
get_or_create_for_rom, a mesma função que o tracking universal da GUI já
usa pra isso, então um registro criado aqui é indistinguível de um
criado marcando "iniciado" na tela. O de Biblioteca nunca cria - só
completa o que já existe (criar registro de loja é decisão de
library-refresh/library-add, não deste preenchimento).

Isso pode rodar por HORAS com a GUI aberta ao mesmo tempo (milhares de
chamada de rede) - salvar direto do snapshot carregado no início
sobrescreveria qualquer edição feita pela tela nesse meio tempo. Por
isso `_persistir` RECARREGA o arquivo do disco a cada checkpoint e só
aplica as mudanças ACUMULADAS (gênero por id, registro novo por
nome+plataforma) em cima do que está lá agora, em vez de salvar o
dict inteiro que foi carregado há uma hora."""
from pathlib import Path

from core import covers as covers_mod
from core import heavy_roms as heavy_mod
from core import launchbox as launchbox_mod
from core import library as library_mod
from core import screenscraper as screenscraper_mod
from core import sortear as sortear_mod

HEAVY_CATALOG_PATH = Path(__file__).parent.parent / "cache" / "heavy_catalog.json"

# Achado 31/08 testando PCECD real: nem todo gênero do ScreenScraper
# tem tradução pt de verdade - "Shoot'em Up" vem idêntico em TODOS os
# idiomas (inclusive pt) no banco deles, não é bug meu, é dado deles.
# Normalização final aplicada em CIMA do que qualquer fonte devolver
# (ScreenScraper, LaunchBox ou Steam), pra bater com o vocabulário mais
# enxuto que a Biblioteca já usa (ex: "Navinha" pra shmup).
NORMALIZACAO_FINAL = {
    "shoot'em up": "Navinha", "shoot em up": "Navinha", "shmup": "Navinha",
    "beat'em up": "Luta", "beat em up": "Luta", "beat'em all": "Luta",
}


def _normalizar(genero: str | None) -> str | None:
    if not genero:
        return None
    return NORMALIZACAO_FINAL.get(genero.strip().lower(), genero)


class _Persistidor:
    """Acumula mudanças em memória e só toca o disco em `checkpoint()`
    - sempre recarregando fresco primeiro, pra não perder edição feita
    pela GUI enquanto esse preenchimento (potencialmente de horas)
    está rodando. `genero_por_id` nunca sobrescreve um gênero que já
    exista no disco na hora do checkpoint (pode ter sido preenchido na
    tela nesse meio tempo) - só o registro em memória usado pra decidir
    "já tem, pula" é que fica um passo desatualizado entre checkpoints,
    aceitável (pior caso: uma chamada de API a mais, nunca perda de
    dado)."""

    def __init__(self, library_path: Path, criar_rom=False):
        self.path = library_path
        self.criar_rom = criar_rom
        self.genero_por_id: dict[str, str] = {}
        self.novos_rom: list[tuple[str, str, str, str]] = []  # (nome, code, plataforma, fonte)

    def marcar_genero(self, game_id: str, genero: str) -> None:
        self.genero_por_id[game_id] = genero

    def marcar_novo_rom(self, nome: str, code: str, plataforma: str, fonte: str) -> None:
        self.novos_rom.append((nome, code, plataforma, fonte))

    def checkpoint(self) -> None:
        if not self.genero_por_id and not self.novos_rom:
            return
        library = library_mod.load_library(self.path)
        por_id = {g["id"]: g for g in library["games"]}

        for nome, code, plataforma, fonte in self.novos_rom:
            library_mod.get_or_create_for_rom(library, nome, code, plataforma, fonte)
        self.novos_rom.clear()
        por_id = {g["id"]: g for g in library["games"]}  # recalcula, pode ter crescido

        for game_id, genero in self.genero_por_id.items():
            game = por_id.get(game_id)
            if game and not game.get("genero"):
                game["genero"] = genero
        self.genero_por_id.clear()

        library_mod.save_library(self.path, library)


def _roms_leves(cfg: dict, roms_root: Path) -> list:
    """[(nome, code, plataforma_lib, fonte)] de toda ROM leve local.
    Sistema leve guarda o nome de exibição em "capas" (achado 31/08 -
    diferente do pesado, que usa "nome" - usar a chave errada criaria
    registro com `plataforma="SFC"` em vez do texto que
    PLATAFORMA_ROM_CODES realmente reconhece)."""
    itens = []
    for code, info in cfg["systems"].items():
        for nome in covers_mod.light_rom_display_names(code, info, roms_root):
            itens.append((nome, code, info.get("capas", code), f"rom:{code}"))
    return itens


def _roms_pesadas(cfg: dict) -> list:
    """[(nome, code, plataforma_lib, fonte)] do catálogo pesado
    cacheado (mesma fonte que sortear/heavy-catalog já usam - listar ao
    vivo via rclone levaria minutos)."""
    heavy = heavy_mod.load_heavy_systems(cfg)
    catalog = sortear_mod.load_heavy_catalog(HEAVY_CATALOG_PATH)
    itens = []
    for code, info in heavy.items():
        for item in catalog.get(code, []):
            nome = item["name"] if item["is_dir"] else Path(item["name"]).stem
            itens.append((nome, code, info.get("nome", code), f"rom:{code}"))
    return itens


def preencher_generos_roms(cfg: dict, apply: bool, on_progress=None) -> dict:
    """Preenche `genero` de toda ROM (leve + pesada) que ainda não tem
    - cria o registro na Biblioteca quando não existe (ver docstring do
    módulo). `on_progress(nome, status)`, se passado, mesmo padrão de
    fetch_covers. Checkpoint a cada 40 (mesmo período de fetch_covers) -
    RECARREGA o arquivo antes de salvar, ver `_Persistidor`."""
    roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
    library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
    library_atual = library_mod.load_library(library_path)  # só pra decidir o que já existe/tem gênero
    lb_index = launchbox_mod.build_index()
    persist = _Persistidor(library_path)

    itens = _roms_leves(cfg, roms_root) + _roms_pesadas(cfg)
    result = {"criados": 0, "via_screenscraper": 0, "via_launchbox": 0, "sem_match": 0, "ja_tinha": 0}
    rom_index = library_mod.index_by_rom_name(library_atual)

    counter = 0
    for nome, code, plataforma_lib, fonte in itens:
        game = library_mod.find_for_rom(rom_index, nome, code)
        if game is None:
            result["criados"] += 1
            if apply:
                persist.marcar_novo_rom(nome, code, plataforma_lib, fonte)
        elif game.get("genero"):
            result["ja_tinha"] += 1
            continue

        if not apply:
            result["sem_match"] += 1
            continue

        genero, via = None, None
        try:
            genero = screenscraper_mod.buscar_genero(code, nome, cfg)
        except Exception:
            genero = None
        via = "screenscraper" if genero else None
        if not genero:
            genero = launchbox_mod.find_genero(code, nome, lb_index)
            via = "launchbox" if genero else None

        if genero:
            genero = _normalizar(genero)
            if game is not None:
                persist.marcar_genero(game["id"], genero)
            else:
                # registro ainda nem existe no disco - marca_novo_rom já
                # garante a criação no próximo checkpoint; o gênero some
                # se não guardarmos, então cria AGORA na cópia em
                # memória local só pra saber o id determinístico.
                fantasma = library_mod._blank_game(nome, plataforma_lib)
                persist.marcar_genero(fantasma["id"], genero)
            result[f"via_{via}"] += 1
            if on_progress:
                on_progress(nome, f"achado ({via}): {genero}")
        else:
            result["sem_match"] += 1
            if on_progress:
                on_progress(nome, "sem_match")

        counter += 1
        if apply and counter % 40 == 0:
            persist.checkpoint()

    if apply:
        persist.checkpoint()
    return result


def preencher_generos_biblioteca(cfg: dict, apply: bool, on_progress=None) -> dict:
    """Preenche `genero` de jogo de Biblioteca (Steam/Epic/GOG/Switch/
    etc) que ainda não tem - NUNCA cria registro (diferente de
    preencher_generos_roms). Steam primeiro (API oficial, mais
    confiável que adivinhar pelo LaunchBox) pra quem tem
    `steam_appid_index`; LaunchBox (plataforma "PC") pro resto."""
    library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
    library_atual = library_mod.load_library(library_path)
    lb_index = launchbox_mod.build_index()
    steam_appids = library_mod.steam_appid_index(cfg.get("steam", {}))
    persist = _Persistidor(library_path)

    pendentes = [g for g in library_atual["games"] if not g.get("genero") and not g.get("oculto")]
    result = {"via_steam": 0, "via_launchbox": 0, "sem_match": 0}

    counter = 0
    for game in pendentes:
        if not apply:
            result["sem_match"] += 1
            continue

        genero, via = None, None
        appid = steam_appids.get(covers_mod.normalize(game["nome"]))
        if appid:
            try:
                genero = library_mod.steam_genero(appid)
            except Exception:
                genero = None
            via = "steam" if genero else None
        if not genero:
            genero = launchbox_mod.find_genero("PC", game["nome"], lb_index)
            via = "launchbox" if genero else None

        if genero:
            genero = _normalizar(genero)
            persist.marcar_genero(game["id"], genero)
            result[f"via_{via}"] += 1
            if on_progress:
                on_progress(game["nome"], f"achado ({via}): {genero}")
        else:
            result["sem_match"] += 1
            if on_progress:
                on_progress(game["nome"], "sem_match")

        counter += 1
        if apply and counter % 40 == 0:
            persist.checkpoint()

    if apply:
        persist.checkpoint()
    return result
