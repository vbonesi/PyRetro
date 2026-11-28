#!/usr/bin/env python3
"""Levanta, pelo IGDB, cada ROM retrô do banco que tem versão nativa à venda no Switch ou no PS4 (28/11/2026).

Só lê a biblioteca (pelo código do projeto); grava `cache/retro_moderna.json` e o TXT de proposta em ~/Downloads.
Nada é apagado aqui: o Victor revisa a lista antes. Cache das consultas em `cache/igdb/`."""
from __future__ import annotations
import json, re, sys, time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))
import retrosync
from core import onde_igdb as ig, onde_roda as orr, library as lib_mod, cloud_sync
import onde_roda_igdb as oi

SAIDA = RAIZ / "cache" / "retro_moderna.json"
ORIGEM = {"FC": (18, 99, 51), "SFC": (19, 58), "MD": (29, 78), "SMS": (64,), "GG": (35,), "GB": (33,), "GBC": (22, 33), "GBA": (24,),
          "N64": (4,), "PCE": (86, 128, 150), "PCECD": (150, 86), "ARCADE": (52, 79, 80)}
ALVO = {130: "Switch", 48: "PS4"}
# Assinaturas e emulação à parte (não contam como versão à venda): NSO, Arcade Archives (Hamster), clássicos do PS4.
NSO = re.compile(r"arcade archives|switch online|nintendo classics|game ?boy.*nintendo|virtual console|"
                 r"\baca\b|neogeo selection|eggconsole|\bnes\b.*nintendo|ps4 classics|playstation classics|plus classics|hamster", re.I)
TIPO_IGDB = {8: "remake", 9: "remaster", 11: "port", 3: "colecao", 13: "colecao", 4: "versao", 10: "versao"}
CAT = {"remake": 1, "remaster": 1, "port": 2, "versao": 2, "mesmonome": 2, "colecao": 3}


def codigo_rom(g):
    for f in g.get("fontes") or []:
        if f.startswith("rom:") and f[4:] in ORIGEM:
            return f[4:]
    return None


def main():
    cfg = retrosync.load_config()
    library = lib_mod.load_library(cloud_sync.library_file(cfg))
    cards = [g for g in library["games"] if not g.get("oculto") and orr.eh_retro(g) and codigo_rom(g)]
    print(len(cards), "cards retrô", flush=True)
    bases, pools = {}, {}
    for n, g in enumerate(cards, 1):
        pool = oi.pool_do_card(g)
        nomes = [g["nome"], *g.get("nomes_alt", [])[:2]]
        # prefere o jogo nascido no console de origem do card
        ig.NATIVA["__retro__"] = ORIGEM[codigo_rom(g)]
        base, sim, _ = ig.escolher_base(nomes, "__retro__", pool)
        bases[g["id"]] = (base, sim); pools[g["id"]] = pool
        if n % 50 == 0:
            print(f"busca {n}/{len(cards)}", flush=True)
    rel = {g["id"]: ig.ids_relacionados(b) for g in cards if (b := bases[g["id"]][0])}
    detalhes = oi.buscar_ids({i for r in rel.values() for i in r})
    print(len(detalhes), "relacionados", flush=True)
    out = {}
    for g in cards:
        base, sim = bases[g["id"]]
        if not base:
            out[g["id"]] = {"estado": "sem_casamento", "sim": round(sim, 2)}
            continue
        tipos = dict(rel[g["id"]])
        achados = {i: detalhes[i] for i in tipos if i in detalhes}
        for c in pools[g["id"]]:
            if c["id"] == base["id"]:
                continue
            if c.get("version_parent") == base["id"]:
                achados[c["id"]] = c; tipos[c["id"]] = "versao"
            elif c["id"] not in achados and c.get("game_type") not in ig.TIPOS_BASE_RUINS \
                    and set(c.get("platforms") or []) & set(ALVO) and ig.nucleo(c["name"]) == ig.nucleo(base["name"]) \
                    and (c.get("first_release_date") or 0) > (base.get("first_release_date") or 0) + 86400 * 365:
                achados[c["id"]] = c; tipos[c["id"]] = "mesmonome"
        itens, info = [], []
        for i, c in achados.items():
            plats = [ALVO[p] for p in c.get("platforms") or [] if p in ALVO]
            if not plats or c.get("game_type") in (1, 2, 5, 6, 7, 14):
                continue
            tipo = TIPO_IGDB.get(c.get("game_type")) or tipos[i]
            item = {"nome": c["name"], "tipo": tipo, "plats": plats, "igdb_id": i}
            (info if NSO.search(c["name"]) else itens).append(item)
        proprios = [ALVO[p] for p in base.get("platforms") or [] if p in ALVO]
        itens.sort(key=lambda x: (CAT[x["tipo"]], 0 if ig.nucleo(x["nome"]) == ig.nucleo(base["name"]) else 1, -len(x["plats"])))
        out[g["id"]] = {"estado": "igdb", "sim": round(sim, 2), "igdb_nome": base["name"], "itens": itens,
                        "info": info, "ficha_propria": proprios,
                        "origem_ok": bool(set(ORIGEM[codigo_rom(g)]) & set(base.get("platforms") or []))}
    SAIDA.write_text(json.dumps({"gerado": time.strftime("%Y-%m-%d %H:%M"), "resultados": out}, ensure_ascii=False))
    print("pronto", len(out), flush=True)


if __name__ == "__main__":
    main()
