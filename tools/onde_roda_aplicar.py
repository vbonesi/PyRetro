#!/usr/bin/env python3
"""F2: grava no banco (pela API do pyretro-gui) o resultado de `tools/onde_roda_igdb.py` e escreve o
relatório de dúvidas. A correção manual do Victor nunca é sobrescrita (regra em core/onde_roda.py)."""
import json, sys, urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8000"


def api(caminho, corpo=None, token=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["X-PyRetro-CSRF"] = token
    req = urllib.request.Request(BASE + caminho, data=json.dumps(corpo).encode() if corpo is not None else None, headers=h)
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def relatorio(dados, destino):
    nomes, res = dados["nomes"], dados["resultados"]
    nv = [(nomes[i], r) for i, r in res.items() if r["estado"] != "igdb"]
    inc = [(nomes[i], r) for i, r in res.items() if r["estado"] == "igdb" and any("casamento incerto" in d for d in r["duvidas"])]
    ed = [(nomes[i], r) for i, r in res.items() if r["estado"] == "igdb" and any(not d.startswith("casamento") for d in r["duvidas"])]
    L = [f"PyRetro - dúvidas do F2 (onde roda) - gerado em {dados['gerado']}", "",
         f"Cards pesquisados: {len(res)}. Não verificados (sem casamento no IGDB): {len(nv)}. Casamento incerto: {len(inc)}. "
         f"Edição/relação duvidosa: {len(ed)}.", "",
         "Como corrigir: no card, ✎ onde roda (ou POST /api/onde-roda/set); a correção manual vence qualquer pesquisa.", "",
         "== NÃO VERIFICADOS (marcados sem resposta, nada chutado) =="]
    L += [f"- {n}" + (f"  [{r['duvidas'][0]}]" if r["duvidas"] else "") for n, r in sorted(nv, key=lambda x: x[0].lower())]
    L += ["", "== CASAMENTO DE NOME INCERTO =="]
    L += [f"- {n}: {d}" for n, r in sorted(inc, key=lambda x: x[0].lower()) for d in r["duvidas"] if d.startswith("casamento")]
    L += ["", "== EDIÇÃO OU RELAÇÃO DUVIDOSA (existe em PS4/Switch por remaster, port, coleção ou só pelo nome) =="]
    L += [f"- {n}: {d}" for n, r in sorted(ed, key=lambda x: x[0].lower()) for d in r["duvidas"] if not d.startswith("casamento")]
    Path(destino).write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    dados = json.loads((RAIZ / "cache" / "onde_roda_f2.json").read_text())
    token = api("/api/csrf")["token"]
    itens = [{"id": i, **r} for i, r in dados["resultados"].items()]
    tot = 0
    for k in range(0, len(itens), 100):
        d = api("/api/onde-roda/pesquisa", {"resultados": itens[k:k + 100]}, token)
        tot += d["atualizados"]
        print(k, d["atualizados"], d["ausentes"])
    print("atualizados", tot)
    relatorio(dados, Path.home() / "Downloads" / "PyRetro - dúvidas onde roda.txt")


if __name__ == "__main__":
    main()
