#!/usr/bin/env python3
"""F2b (proposta, sem aplicar): agrupa cards que são edições do mesmo jogo ou coleções, pelas relações do IGDB.

Lê a biblioteca só pelo código do projeto e o `cache/onde_roda_f2.json` do F2; grava
`cache/proposta_unificacao.json` e o TXT em ~/Downloads. Nada vai para o banco."""
from __future__ import annotations
import json, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import retrosync
from core import onde_igdb as ig, onde_roda as orr, igdb, edicoes
from core import library as lib_mod
import tools.onde_roda_igdb as f2

CACHE = f2.CACHE


def main():
    cfg = retrosync.load_config()
    lib = lib_mod.load_library(Path(cfg["pc"]["library_root"]).expanduser() / "library.json")
    jogos = {g["id"]: g for g in lib["games"] if not g.get("oculto")}
    res = json.loads((RAIZ / "cache" / "onde_roda_f2.json").read_text())["resultados"]
    igdb_de = {i: r["igdb_id"] for i, r in res.items() if r["estado"] == "igdb" and i in jogos}
    det = f2.buscar_ids(set(igdb_de.values()))
    # filhos de cada coleção (bundle) que é card
    filhos = {}
    for gid, iid in igdb_de.items():
        b = det.get(iid) or {}
        if b.get("game_type") in (3, 13):
            filhos[iid] = f2.filhos_da_colecao(iid)
    grupos = edicoes.propor(jogos, igdb_de, det, filhos, res)
    (RAIZ / "cache" / "proposta_unificacao.json").write_text(json.dumps(grupos, ensure_ascii=False, indent=1))
    Path.home().joinpath("Downloads", "PyRetro - proposta de unificação.txt").write_text(edicoes.texto_proposta(grupos), encoding="utf-8")
    print(len(grupos), "grupos")


if __name__ == "__main__":
    main()
