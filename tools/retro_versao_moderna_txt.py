#!/usr/bin/env python3
"""Monta o TXT de proposta a partir de `cache/retro_moderna.json` (ver retro_versao_moderna.py). Não apaga nada."""
from __future__ import annotations
import json, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import retrosync
from core import library as lib_mod, cloud_sync, onde_roda as orr

CATS = {1: "REMAKE OU REMASTER", 2: "PORT OU RELANÇAMENTO", 3: "COLEÇÃO"}
ROT = {"remake": "remake", "remaster": "remaster", "port": "port", "versao": "relançamento", "mesmonome": "mesmo nome",
       "colecao": "coleção"}
SIST = {"FC": "NES", "SFC": "SNES", "MD": "Mega Drive", "SMS": "Master System", "GG": "Game Gear", "GB": "Game Boy",
        "GBC": "GBC", "GBA": "GBA", "N64": "N64", "PCE": "PC Engine", "PCECD": "PC Engine CD", "ARCADE": "Arcade"}


def saves_pc(cfg, library):
    raiz = Path(cfg["pc"]["saves_root"]).expanduser()
    idx = lib_mod.index_by_rom_name(library)
    achados = {}
    for sub, rot in (("saves", "save"), ("states", "estado")):
        base = raiz.parent / sub if (raiz.parent / sub).exists() and raiz.name == "saves" else raiz
        base = Path(cfg["pc"][f"{sub}_root"]).expanduser()
        for pasta in base.glob("*"):
            if not pasta.is_dir() or pasta.name == "Backup":
                continue
            for arq in pasta.iterdir():
                nome = arq.name.split(".")[0] if not arq.name.endswith((".state.auto",)) else arq.name[:-len(".state.auto")]
                g = lib_mod.find_for_rom(idx, nome, pasta.name)
                if g:
                    auto = arq.name.endswith(".auto")
                    achados.setdefault(g["id"], set()).add(rot + (" automático" if auto else ""))
    return achados


def progresso(g):
    p = []
    if g.get("nota") is not None: p.append(f"nota {g['nota']}")
    if g.get("finalizado"): p.append("finalizado")
    if g.get("platinado"): p.append("platinado")
    if g.get("tempo"): p.append(f"tempo {g['tempo']}")
    if g.get("iniciado") and not g.get("finalizado"): p.append("iniciado")
    return ", ".join(p) or "não"


def main():
    cfg = retrosync.load_config()
    library = lib_mod.load_library(cloud_sync.library_file(cfg))
    por_id = {g["id"]: g for g in library["games"]}
    res = json.loads((RAIZ / "cache" / "retro_moderna.json").read_text())["resultados"]
    sv = saves_pc(cfg, library)
    grupos = {1: [], 2: [], 3: []}
    info, sem = [], 0
    for gid, r in res.items():
        g = por_id.get(gid)
        if not g:
            continue
        if r["estado"] != "igdb":
            sem += 1; continue
        cod = next((f[4:] for f in g["fontes"] if f.startswith("rom:")), "")
        base_cols = (g["nome"], SIST.get(cod, cod))
        em_andamento = "sim" if g.get("iniciado") and not g.get("finalizado") else "não"
        tem_save = ", ".join(sorted(sv.get(gid, []))) or "não"
        if not r["itens"]:
            if r["info"] or r["ficha_propria"]:
                nomes = [x["nome"] for x in r["info"]][:2]
                info.append(f"{g['nome']} | {base_cols[1]} | {'; '.join(nomes) or 'ficha do IGDB lista ' + '/'.join(r['ficha_propria'])}"
                            f" | {'/'.join(r['ficha_propria']) or '/'.join(sorted({p for x in r['info'] for p in x['plats']}))}")
            continue
        melhor = r["itens"][0]
        cat = {"remake": 1, "remaster": 1, "port": 2, "versao": 2, "mesmonome": 2, "colecao": 3}[melhor["tipo"]]
        outros = [x for x in r["itens"][1:] if x["nome"] != melhor["nome"]][:2]
        duvida = r["sim"] < 0.95 or melhor["tipo"] == "mesmonome" or not r.get("origem_ok", True)
        mod = f"{melhor['nome']} ({ROT[melhor['tipo']]})"
        if outros:
            mod += " — também: " + "; ".join(f"{x['nome']} ({ROT[x['tipo']]})" for x in outros)
        linha = " | ".join([g["nome"], base_cols[1], mod, "/".join(melhor["plats"]), progresso(g), tem_save, em_andamento])
        if duvida:
            linha += " [?]" + (f" casamento {r['igdb_nome']!r} ({r['sim']})" if r["sim"] < 0.95 else (" sem relação no IGDB" if melhor["tipo"] == "mesmonome" else " o IGDB não lista este console no jogo casado"))
        grupos[cat].append((g["nome"].lower(), linha))
    saida = ["PyRetro - retrô com versão moderna (proposta, nada foi apagado)", "",
             "Fonte: IGDB (remakes, remasters, ports, bundles). Não conta: Nintendo Switch Online, Arcade Archives e emulação (listados à parte).",
             "Colunas: nome no banco | sistema | versão moderna | Switch/PS4 | progresso | save/estado no PC | em andamento",
             "[?] = dúvida (casamento fraco ou só pelo nome igual).", ""]
    for c in (1, 2, 3):
        itens = sorted(grupos[c])
        saida += [f"=== {CATS[c]} ({len(itens)}) ===", *[l for _, l in itens], ""]
    saida += [f"=== SÓ ASSINATURA/EMULAÇÃO, PARA INFORMAÇÃO ({len(info)}) ===", *sorted(info), "",
              f"Sem casamento no IGDB: {sem} cards (não listados)."]
    alvo = Path("~/Downloads/PyRetro - retrô com versão moderna.txt").expanduser()
    alvo.write_text("\n".join(saida) + "\n", encoding="utf-8")
    print({c: len(v) for c, v in grupos.items()}, "info", len(info), "sem", sem)


if __name__ == "__main__":
    main()
