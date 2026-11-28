#!/usr/bin/env python3
"""F2 (plano de 27/11/2026): pesquisa no IGDB onde cada card fora do retrô existe.

Só lê a biblioteca (pelo código do projeto) e grava `cache/onde_roda_f2.json`; quem grava no banco é
`tools/onde_roda_aplicar.py`, pela API. Cache de cada consulta em `cache/igdb/` (pode repetir à vontade)."""
from __future__ import annotations
import json
import os, re, sys, time, urllib.request
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import retrosync
from core import igdb, onde_igdb as ig, onde_roda as orr
from core import library as lib_mod

CACHE = RAIZ / "cache" / "igdb"
SAIDA = RAIZ / "cache" / "onde_roda_f2.json"
CAMPOS = ("name,alternative_names.name,platforms,game_type,first_release_date,remakes,remasters,ports,bundles,"
          "version_parent,total_rating_count,genres")
CAMPOS_FILHOS = CAMPOS + ",release_dates.platform,release_dates.date"   # jogos de dentro de uma coleção: precisa da data por plataforma
PLAT_ESCOPO = {"Sony - PlayStation", "Sony - PlayStation 2", "Sony - PSP", "Nintendo - Nintendo DS", "Nintendo - 3DS",
               "Nintendo - GameCube", "Nintendo - Wii", "Nintendo Switch", "Nintendo Switch 2"}


def q(endpoint, corpo):
    return igdb.com_cache(CACHE, "", endpoint, corpo)


def esc(s):
    return s.replace("\\", " ").replace('"', " ")


def escopo(library):
    out = []
    for g in library["games"]:
        if g.get("oculto") or orr.eh_retro(g):
            continue
        fontes = g.get("fontes") or []
        if any(f.startswith("wishlist:") for f in fontes) or g.get("plataforma") in PLAT_ESCOPO:
            out.append(g)
    return out


def variantes(nome):
    limpo = ig.limpar_nome(nome)
    v = [limpo]
    for sep in (":", " - ", " – "):
        if sep in limpo:
            v.append(limpo.split(sep)[0].strip())
    sem_ed = re.sub(r"\b(remastered|definitive edition|deluxe edition|complete edition|goty|game of the year edition|"
                    r"ultimate edition|enhanced edition|hd)\b", "", limpo, flags=re.I).strip(" -:")
    if sem_ed and sem_ed != limpo:
        v.append(sem_ed)
    return list(dict.fromkeys(x for x in v if len(x) > 1))


def pool_do_card(g):
    pool = {}
    plats = "(" + ",".join(map(str, ig.TODOS_ALVO)) + ")"
    for nome in variantes(g["nome"])[:3]:
        for filtro in ("", f"where platforms = {plats}; "):
            for c in q("games", f'search "{esc(nome)}"; fields {CAMPOS}; {filtro}limit 15;'):
                pool[c["id"]] = c
        nomes = [g["nome"], *g.get("nomes_alt", [])[:2]]
        base, sim, _ = ig.escolher_base(nomes, g.get("plataforma"), list(pool.values()))
        if base and sim >= 0.95:
            break
    return list(pool.values())


def buscar_ids(ids):
    out = {}
    ids = list(ids)
    for i in range(0, len(ids), 100):
        lote = ids[i:i + 100]
        for c in q("games", f'fields {CAMPOS}; where id = ({",".join(map(str, lote))}); limit 500;'):
            out[c["id"]] = c
    return out


def externos(ids):
    out = defaultdict(dict)
    ids = list(ids)
    for i in range(0, len(ids), 100):
        lote = ids[i:i + 100]
        for e in q("external_games", f'fields game,uid,url,external_game_source; where game = ({",".join(map(str, lote))}) '
                   f'& external_game_source = (1,5,26); limit 500;'):
            out[e["game"]].setdefault(e["external_game_source"], e)
    return out


def steam_gb(appid):
    arq = CACHE / f"steam_{appid}.json"
    if arq.exists():
        return json.loads(arq.read_text()).get("gb")
    gb = None
    for t in range(4):
        try:
            with urllib.request.urlopen(f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english", timeout=30) as r:
                d = json.load(r)
            req = ((d.get(str(appid)) or {}).get("data") or {}).get("pc_requirements") or {}
            texto = req.get("minimum", "") if isinstance(req, dict) else ""
            texto = re.sub(r"<[^>]+>", " ", texto)
            m = re.search(r"(?:storage|hard drive|disk|space)[^0-9]{0,40}(\d+(?:[.,]\d+)?)\s*(TB|GB|MB)", texto, re.I) \
                or re.search(r"(\d+(?:[.,]\d+)?)\s*(TB|GB|MB)\s*(?:of\s*)?(?:available|free)?\s*(?:hard|space|storage)", texto, re.I)
            if m:
                v = float(m.group(1).replace(",", "."))
                gb = v * {"TB": 1024, "GB": 1, "MB": 1 / 1024}[m.group(2).upper()]
            break
        except Exception:
            time.sleep(8 * (t + 1))
    else:
        return None
    arq.write_text(json.dumps({"gb": gb}))
    time.sleep(1.7)
    return gb


def tamanhos_switch_locais():
    """Tamanho (GB) de cada pasta NSW do manifesto do F0 → para os cards 'switch' que já são dump.
    O manifesto é privado (fora do repositório): caminho em PYRETRO_MANIFESTO_NSW."""
    caminho = os.environ.get("PYRETRO_MANIFESTO_NSW")
    arq = Path(caminho).expanduser() if caminho else None
    if not arq or not arq.exists():
        return {}
    soma = defaultdict(int)
    for it in json.loads(arq.read_text()):
        if it.get("IsDir"):
            continue
        soma[it["Path"].split("/")[0]] += it.get("Size", 0)
    return {ig.norm(k): v / 2**30 for k, v in soma.items()}


def main():
    cfg = retrosync.load_config()
    library = lib_mod.load_library(Path(cfg["pc"]["library_root"]).expanduser() / "library.json")
    cards = escopo(library)
    print(f"{len(cards)} cards no escopo", flush=True)
    locais = tamanhos_switch_locais()
    bases, pools = {}, {}
    for n, g in enumerate(cards, 1):
        pool = pool_do_card(g)
        nomes = [g["nome"], *g.get("nomes_alt", [])[:2]]
        base, sim, _ = ig.escolher_base(nomes, g.get("plataforma"), pool)
        bases[g["id"]] = (base, sim)
        pools[g["id"]] = pool
        if n % 50 == 0:
            print(f"busca {n}/{len(cards)}", flush=True)
    rel_ids = {}
    for gid, (base, _) in bases.items():
        if base:
            rel_ids[gid] = ig.ids_relacionados(base)
    todos = {i for r in rel_ids.values() for i in r}
    detalhes = buscar_ids(todos)
    print(f"{len(todos)} jogos relacionados", flush=True)
    # evidências por card
    evs, extras_de = {}, {}
    for g in cards:
        base, sim = bases[g["id"]]
        if not base:
            continue
        tipos = dict(rel_ids[g["id"]])
        rel = {i: detalhes[i] for i in tipos if i in detalhes}
        for c in pools[g["id"]]:
            if c["id"] != base["id"] and c.get("version_parent") == base["id"]:
                rel[c["id"]] = c; tipos[c["id"]] = "versao"
        extras = []
        for c in pools[g["id"]]:
            if c["id"] == base["id"] or c["id"] in rel or c.get("game_type") in ig.TIPOS_BASE_RUINS:
                continue
            if set(c.get("platforms") or []) & set(ig.TODOS_ALVO) and ig.nucleo(c["name"]) == ig.nucleo(base["name"]) \
                    and (c.get("first_release_date") or 0) >= (base.get("first_release_date") or 0) - 86400 * 30:
                extras.append(c)
        evs[g["id"]] = ig.evidencias(base, rel, tipos, extras)
    # lojas de PC e Steam
    pc_ids = {e["igdb_id"] for ev in evs.values() for e in ev["pc"][:1]}
    ext = externos(pc_ids)
    lojas_nome = {1: "Steam", 5: "GOG", 26: "Epic"}
    resultados = {}
    contador = 0
    for g in cards:
        base, sim = bases[g["id"]]
        if not base:
            resultados[g["id"]] = ig.montar(g["nome"], g.get("plataforma"), None, sim, None)
            continue
        ev = evs[g["id"]]
        lojas, sgb = None, None
        if ev["pc"]:
            e = ext.get(ev["pc"][0]["igdb_id"], {})
            lojas = [lojas_nome[k] for k in sorted(e)]
            if 1 in e and not str(g.get("fontes")).count("wishlist:xbox"):
                contador += 1
                if contador % 40 == 0:
                    print(f"steam {contador}", flush=True)
                sgb = steam_gb(e[1]["uid"])
        local = None
        for n in [g["nome"], *g.get("nomes_alt", [])]:
            if ig.norm(n) in locais:
                local = locais[ig.norm(n)]; break
        r = ig.montar(g["nome"], g.get("plataforma"), base, sim, ev, steam_gb=sgb, lojas_pc=lojas, local_switch_gb=local)
        resultados[g["id"]] = r
    SAIDA.write_text(json.dumps({"gerado": time.strftime("%Y-%m-%d %H:%M"), "resultados": resultados,
                                 "nomes": {g["id"]: g["nome"] for g in cards}}, ensure_ascii=False))
    print("pronto", len(resultados), flush=True)


if __name__ == "__main__":
    main()
