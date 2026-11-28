#!/usr/bin/env python3
"""Unificação dos jogos removidos (F5, 28/11/2026): como o F2b, mas vale qualquer versão moderna (Switch, PS4, Xbox, PC).

Pesquisa o IGDB dos cards fora do escopo do F2 (Steam, Epic, GOG, Xbox...), junta com `cache/onde_roda_f2.json` e gera a
proposta em `cache/proposta_removidos.json`. Só propõe: aplicar é `tools/proposta_unificacao_removidos.py --aplicar`
(pela API, só os grupos sem [?]) e o TXT final vai para ~/Downloads."""
from __future__ import annotations
import json, re, sys, urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import retrosync
from core import onde_igdb as ig, onde_roda as orr, edicoes, cloud_sync
from core import library as lib_mod
import tools.onde_roda_igdb as f2

REMOVIDAS = {"Sony - PlayStation", "Sony - PlayStation 2", "Sony - PSP", "Nintendo - Nintendo DS", "Nintendo - 3DS",
             "Nintendo - GameCube", "Nintendo - Wii", "Nintendo Switch"}
# Ficam no Drive (lista de remoção V1: "- manter" e os 9 de Jogando): não entram em unificação como edição antiga.
MANTER = {"cat rescue story", "final fantasy vi", "pokemon legends z a", "super mario 3d all stars", "blood will tell",
          "dororo", "patapon 2", "life is strange true colors", "portal 2", "squad 51 vs the flying saucers",
          "streets of rage 4", "super mario bros wonder", "the legend of zelda breath of the wild", "touhou luna nights",
          "guitar hero iii", "need for speed underground 2"}


def eh_manter(nome):
    n = ig.norm(nome)
    return any(n == m or n.startswith(m) for m in MANTER)


def main(aplicar=False):
    cfg = retrosync.load_config()
    lib = lib_mod.load_library(cloud_sync.library_file(cfg))
    jogos = {g["id"]: g for g in lib["games"] if not g.get("oculto") and not orr.eh_retro(g)}
    res = json.loads((RAIZ / "cache" / "onde_roda_f2.json").read_text())["resultados"]
    igdb_de = {i: r["igdb_id"] for i, r in res.items() if r["estado"] == "igdb" and i in jogos}
    extras = [g for i, g in jogos.items() if i not in res]
    print(len(extras), "cards fora do F2 para pesquisar", flush=True)
    res = dict(res)
    for n, g in enumerate(extras, 1):
        pool = f2.pool_do_card(g)
        base, sim, _ = ig.escolher_base([g["nome"], *g.get("nomes_alt", [])[:2]], g.get("plataforma"), pool)
        if base:
            igdb_de[g["id"]] = base["id"]
            res[g["id"]] = {"estado": "igdb", "igdb_id": base["id"], "confianca": round(sim, 2)}
        if n % 50 == 0:
            print(f"busca {n}/{len(extras)}", flush=True)
    det = f2.buscar_ids(set(igdb_de.values()))
    filhos = {}
    for gid, iid in igdb_de.items():
        if (det.get(iid) or {}).get("game_type") in (3, 13):
            filhos[iid] = f2.q("games", f'fields {f2.CAMPOS}; where bundles = ({iid}); limit 100;')
    grupos = edicoes.propor(jogos, igdb_de, det, filhos, res)
    bons = []
    for g in grupos:
        membros = [g["fica"], *[e for e in g["entram"] if e["id"]]]
        if not any(m.get("plataforma") in REMOVIDAS for m in membros):
            continue            # nenhum jogo removido no grupo: fora do pedido
        g["entram"] = [e for e in g["entram"] if not (e["id"] and eh_manter(e["nome"]))]
        if not [e for e in g["entram"] if e["id"]]:
            continue
        bons.append(g)
    (RAIZ / "cache" / "proposta_removidos.json").write_text(json.dumps(bons, ensure_ascii=False, indent=1))
    claros = [g for g in bons if not g["incerto"] and not any(e["incerto"] for e in g["entram"])]
    print(len(bons), "grupos;", len(claros), "claros;", len(bons) - len(claros), "com [?]")


if __name__ == "__main__":
    main()
