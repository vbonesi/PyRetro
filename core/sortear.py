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


def build_pool(cfg: dict, roms_root: Path, catalog: dict, system: str | None) -> list:
    """[(codigo, nome, "leve"|"pesado")]. Sem `system`, junta leve
    (local, ao vivo) + pesado (catálogo cacheado) - cada JOGO com peso
    igual, não cada sistema, então um sistema com mais jogos tem mais
    chance de propósito (reflete o tamanho real da coleção em vez de
    dar o mesmo peso pra FC com 200 jogos e N64 com 20). Levanta
    ValueError(codigo) se `system` não bater com nenhum sistema
    conhecido (leve ou pesado)."""
    light = cfg["systems"]
    heavy = heavy_mod.load_heavy_systems(cfg)

    if system:
        code = system.upper()
        if code in light:
            names = playlist_mod.list_local_names(code, roms_root, light[code]["exts"])
            return [(code, n, "leve") for n in names]
        if code in heavy:
            return [(code, item["name"], "pesado") for item in catalog.get(code, [])]
        raise ValueError(code)

    pool = []
    for code, info in light.items():
        pool += [(code, n, "leve") for n in playlist_mod.list_local_names(code, roms_root, info["exts"])]
    for code, items in catalog.items():
        pool += [(code, item["name"], "pesado") for item in items]
    return pool


def draw(pool: list) -> tuple:
    return random.choice(pool)
