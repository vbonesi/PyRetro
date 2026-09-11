"""
Sorteio aleatório de jogos da coleção - junta sistemas leves (sempre
locais, roms_root/<CODE>/ já sincronizado via Google Drive) e pesados
(PS/PS2/GameCube/Wii/PSP/3DS, ver core/heavy_roms.py) num pool só.

Sistema pesado é o complicado: boa parte só existe no Google Drive,
nunca foi baixada pro PC, então sortear "de verdade" entre eles pede o
catálogo completo da nuvem, não só roms_root local. Mas listar isso ao
vivo via rclone (heavy_roms.list_drive_items) pode levar até ~90s POR
SISTEMA (ver docstring de lá) - inviável rodar em toda chamada de
sortear, ainda mais pra "sortear de tudo" (6 sistemas pesados = minutos
de espera). Por isso o catálogo fica cacheado em
cache/heavy_catalog.json, atualizado sob demanda por
`retrosync heavy-catalog --apply`, e o sortear só lê esse arquivo -
funciona offline, só fica desatualizado se algo mudar no Drive depois
do último refresh (aceitável pra esse caso de uso).
"""
import json
import random
from pathlib import Path

from core import heavy_roms as heavy_mod
from core import playlist as playlist_mod


def refresh_heavy_catalog(cfg: dict) -> dict:
    """{codigo: [{"name","size","is_dir"}]} de tudo que existe no Drive
    pra cada sistema pesado, filtrado pelas extensões configuradas -
    mesmo critério de heavy_roms.list_local (pasta inteira sempre conta
    como um item, arquivo solto só se a extensão bater). Guarda o item
    inteiro (não só o nome) pra GUI poder mostrar tamanho sem precisar
    de outra chamada ao Drive - achado 27/08: só nome perdia o tamanho
    de tudo que ainda não foi baixado pro PC."""
    heavy = heavy_mod.load_heavy_systems(cfg)
    catalog = {}
    for code, sysinfo in heavy.items():
        exts_lower = {e.lower().lstrip(".") for e in sysinfo.get("exts", [])}
        items = heavy_mod.list_drive_items(code, cfg)
        catalog[code] = sorted(
            (i for i in items if i["is_dir"] or Path(i["name"]).suffix.lower().lstrip(".") in exts_lower),
            key=lambda i: i["name"],
        )
    return catalog


def load_heavy_catalog(cache_path: Path) -> dict:
    if not cache_path.exists():
        return {}
    return json.loads(cache_path.read_text()).get("systems", {})


def save_heavy_catalog(cache_path: Path, catalog: dict) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps({"systems": catalog}, indent=1, ensure_ascii=False))


GRUPOS = {"leve", "pesado", "biblioteca"}


def _pool_biblioteca(library: dict, rom_names_by_code: dict) -> list:
    """[(None, nome, "biblioteca")] - só jogo que não "mora" numa ROM
    (mesma exclusão de is_rom_backed do gui/server.py, reimplementada
    aqui pra não criar dependência circular com o servidor) e não
    oculto, senão sortear traria de volta um jogo que o usuário
    escondeu de propósito."""
    from core import library as library_mod

    pool = []
    for g in library["games"]:
        if g.get("oculto"):
            continue
        code = library_mod.rom_code_for_plataforma(g["plataforma"])
        if code and library_mod.covers_mod.normalize(g["nome"]) in rom_names_by_code.get(code, set()):
            continue
        pool.append((None, g["nome"], "biblioteca"))
    return pool


def build_pool(cfg: dict, roms_root: Path, catalog: dict, system: str | None,
               library: dict | None = None, rom_names_by_code: dict | None = None,
               rom_index: dict | None = None, genero: str | None = None) -> list:
    """[(codigo, nome, "leve"|"pesado"|"biblioteca")]. Sem `system`,
    junta leve (local, ao vivo) + pesado (catálogo cacheado) + Biblioteca
    (se `library` foi passada) - cada JOGO com peso igual, não cada
    sistema, então um sistema com mais jogos tem mais chance de
    propósito (reflete o tamanho real da coleção em vez de dar o mesmo
    peso pra FC com 200 jogos e N64 com 20).

    `system` também aceita os 3 GRUPOS ("leve"/"pesado"/"biblioteca",
    28/08→31/08: pedido do usuário depois de notar que só dava pra
    sortear sistema por sistema, "permitir sorteio por grupos") - sorteia
    só dentro daquele grupo, mesmo peso por jogo de sempre.

    `genero` (11/09, pedido do usuário: "no sorteio de jogo, permitir
    combo de grupo/plataforma e gênero") filtra o pool no final, depois
    de montado - precisa de `rom_index` (core.library.index_by_rom_name)
    pra achar o gênero de ROM leve/pesada (só tem se a ROM já tiver
    registro na Biblioteca; sem registro, fica de fora do sorteio com
    filtro de gênero ativo, mesmo critério de "sem dado = fica de fora"
    usado no preenchimento de gênero).

    Levanta ValueError(codigo) se `system` não bater com nenhum sistema
    OU grupo conhecido."""
    light = cfg["systems"]
    heavy = heavy_mod.load_heavy_systems(cfg)

    if system:
        code = system.upper()
        chave = system.lower()
        if chave in GRUPOS:
            if chave == "biblioteca":
                pool = _pool_biblioteca(library, rom_names_by_code or {}) if library is not None else []
            else:
                pool = []
                fontes = light if chave == "leve" else heavy
                for c, info in fontes.items():
                    if chave == "leve":
                        pool += [(c, n, "leve") for n in playlist_mod.list_local_names(c, roms_root, info["exts"])]
                    else:
                        pool += [(c, item["name"], "pesado") for item in catalog.get(c, [])]
        elif code in light:
            names = playlist_mod.list_local_names(code, roms_root, light[code]["exts"])
            pool = [(code, n, "leve") for n in names]
        elif code in heavy:
            pool = [(code, item["name"], "pesado") for item in catalog.get(code, [])]
        else:
            raise ValueError(code)
    else:
        pool = []
        for code, info in light.items():
            pool += [(code, n, "leve") for n in playlist_mod.list_local_names(code, roms_root, info["exts"])]
        for code, items in catalog.items():
            pool += [(code, item["name"], "pesado") for item in items]
        if library is not None:
            pool += _pool_biblioteca(library, rom_names_by_code or {})

    if genero:
        pool = _filtrar_por_genero(pool, genero, library, rom_index)
    return pool


def _filtrar_por_genero(pool: list, genero: str, library: dict | None, rom_index: dict | None) -> list:
    from core import library as library_mod

    biblioteca_por_nome = {g["nome"]: g for g in library["games"]} if library else {}
    out = []
    for code, nome, kind in pool:
        if kind == "biblioteca":
            g = biblioteca_por_nome.get(nome)
        else:
            # nome aqui é o de ARQUIVO (com extensão, ver
            # list_local_names/catalog) - find_for_rom casa pelo nome
            # gravado no registro (sem extensão), então precisa do
            # stem primeiro, mesmo critério já usado pra exibir
            # iniciado/finalizado/gênero na galeria de ROM (ver
            # `label = Path(f).stem` em gui/server.py).
            g = library_mod.find_for_rom(rom_index, Path(nome).stem, code) if rom_index else None
        if g and g.get("genero") == genero:
            out.append((code, nome, kind))
    return out


def generos_disponiveis(library: dict) -> list[str]:
    """Lista ordenada de gêneros distintos já usados na Biblioteca -
    popula o <select> de gênero do sorteio."""
    return sorted({g["genero"] for g in library["games"] if g.get("genero")})


def draw(pool: list) -> tuple:
    return random.choice(pool)
