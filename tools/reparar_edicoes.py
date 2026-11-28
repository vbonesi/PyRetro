#!/usr/bin/env python3
"""Corrige as `edicoes` já gravadas (plataforma original e sem repetidos), pela API. Pesquisa no IGDB os jogos de dentro de
cada coleção (com release_dates) e manda para `/api/onde-roda/reparar-edicoes`. `--aplicar` grava; sem ele só simula."""
from __future__ import annotations
import json, sys, urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import retrosync
from core import cloud_sync, library as lib_mod
import tools.onde_roda_igdb as f2

BASE = "http://127.0.0.1:8000"


def post(corpo):
    tok = list(json.load(urllib.request.urlopen(BASE + "/api/csrf")).values())[0]
    req = urllib.request.Request(BASE + "/api/onde-roda/reparar-edicoes", json.dumps(corpo).encode(),
                                 {"Content-Type": "application/json", "X-PyRetro-CSRF": tok})
    return json.load(urllib.request.urlopen(req))


def main():
    cfg = retrosync.load_config()
    lib = lib_mod.load_library(cloud_sync.library_file(cfg))
    filhos = {}
    for g in lib["games"]:
        iid = (g.get("pesquisa") or {}).get("igdb_id")
        if g.get("tipo_card") == "colecao" and iid:
            filhos[g["id"]] = f2.q("games", f'fields {f2.CAMPOS_FILHOS}; where bundles = ({iid}); limit 100;')
    r = post({"filhos": filhos, "apply": "--aplicar" in sys.argv})
    print(r["aplicado"], len(r["mudados"]), "cards", r["mudados"][:10])


if __name__ == "__main__":
    main()
