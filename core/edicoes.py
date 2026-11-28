"""F2b (plano de 27/11/2026): várias edições do mesmo jogo viram um card só.

Duas formas, decididas pelo Victor:
- **Versão** (remaster, remake, port de um jogo só): fica o card da edição mais moderna, que mostra as antigas
  em `edicoes`; o progresso (nota, finalizado, tempo, observações) migra para ele.
- **Coleção** (Castlevania Requiem, Mega Man X Legacy Collection 2): fica o card da coleção, com `edicoes` listando
  cada jogo de dentro (nome e plataforma originais). Entrada que é ROM retrô guarda a fonte `rom:` e segue jogável.

Nada se perde: o registro completo de cada card absorvido fica em `edicoes[i]["registro"]` e os IDs antigos em
`ids_antigos` (alias). Este módulo só calcula e aplica em memória; gravar no banco é decisão posterior (V1)."""
from __future__ import annotations
import copy
from core import onde_igdb as ig

CAMPOS_PROGRESSO = ("nota", "finalizado", "platinado", "iniciado", "tempo", "observacoes", "data_final", "savestate")
_MODERNIDADE = {"Xbox Series S": 5, "PlayStation 4": 5, "Nintendo Switch 2": 5, "Nintendo Switch": 4, "Xbox One": 4,
                "Xbox": 3, "Steam": 3, "Epic Games Store": 3, "GOG": 3}


# Rótulos de plataforma do IGDB para mostrar a plataforma original de um jogo dentro de uma coleção.
_ROT = {7: "PS1", 8: "PS2", 9: "PS3", 38: "PSP", 46: "PS Vita", 48: "PS4", 167: "PS5", 20: "DS", 37: "3DS", 21: "GameCube",
        5: "Wii", 41: "Wii U", 130: "Switch", 508: "Switch 2", 4: "N64", 19: "SNES", 18: "NES", 24: "GBA", 33: "Game Boy",
        22: "Game Boy Color", 29: "Mega Drive", 32: "Saturn", 23: "Dreamcast", 86: "PC Engine", 150: "PC Engine CD",
        6: "PC", 12: "Xbox 360", 11: "Xbox", 49: "Xbox One", 169: "Xbox Series X|S", 34: "Android", 3: "Linux", 14: "Mac",
        52: "Arcade", 64: "Master System", 35: "Game Gear", 27: "Mega CD"}
_ROM_ROTULO = {"PS": "PS1", "PS2": "PS2", "PSP": "PSP", "NDS": "DS", "3DS": "3DS", "NGC": "GameCube", "WII": "Wii",
               "FC": "NES", "SFC": "SNES", "MD": "Mega Drive", "SMS": "Master System", "GG": "Game Gear", "GB": "Game Boy",
               "GBC": "Game Boy Color", "GBA": "GBA", "N64": "N64", "PCE": "PC Engine", "PCECD": "PC Engine CD", "ARCADE": "Arcade"}
_MODERNAS = {48, 167, 130, 508, 169, 49, 6, 3, 14, 34, 41}


def rotulo_plataformas(ids) -> str | None:
    """Plataformas antigas primeiro (a original); se só houver modernas, mostra as modernas."""
    ids = list(ids or [])
    antigas = [i for i in ids if i not in _MODERNAS]
    escolha = antigas or ids
    return ", ".join(_ROT.get(i, f"#{i}") for i in escolha[:3]) or None


def progresso(g: dict) -> dict:
    """Só o que tem valor: é o que migra e o que a proposta mostra."""
    return {c: g[c] for c in CAMPOS_PROGRESSO if g.get(c) not in (None, "", False, 0)}


def _modernidade(g: dict, igdb_det: dict | None) -> tuple:
    data = (igdb_det or {}).get("first_release_date") or 0
    return (data, _MODERNIDADE.get(g.get("plataforma"), 1), len(progresso(g)))


def _componentes(arestas: list[tuple[str, str]]) -> list[set[str]]:
    pai: dict[str, str] = {}

    def achar(x):
        pai.setdefault(x, x)
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    for a, b in arestas:
        pai[achar(a)] = achar(b)
    out: dict[str, set[str]] = {}
    for x in list(pai):
        out.setdefault(achar(x), set()).add(x)
    return list(out.values())


def propor(jogos: dict, igdb_de: dict, det: dict, filhos: dict, res: dict) -> list[dict]:
    """Lista de grupos {tipo, fica, entram:[{id, nome, plataforma, motivo, incerto, progresso}], ...}.

    `jogos` id->card; `igdb_de` id->igdb_id; `det` igdb_id->jogo IGDB (com remakes/remasters/ports/bundles);
    `filhos` igdb_id da coleção -> jogos de dentro; `res` resultados do F2 (confiança do casamento)."""
    por_igdb: dict[int, list[str]] = {}
    for gid, iid in igdb_de.items():
        por_igdb.setdefault(iid, []).append(gid)
    grupos, usados = [], set()

    def incerto(gid):
        r = res.get(gid) or {}
        return bool(r) and (r.get("confianca", 1) < 0.95)

    # 1) coleções: card cuja base é um bundle, mais os cards que casam com os jogos de dentro
    for iid, itens_igdb in filhos.items():
        for fica in por_igdb.get(iid, []):
            entram = []
            for f in itens_igdb:
                if f.get("game_type") in ig.TIPOS_BASE_RUINS:
                    continue  # DLC, expansão, kit: não é jogo da coleção
                alvo, via = None, None
                for gid, g in jogos.items():
                    if gid == fica or gid in usados:
                        continue
                    base = det.get(igdb_de.get(gid)) or {}
                    parentes = {x for c in ("remakes", "remasters", "ports") for x in base.get(c) or []}
                    if igdb_de.get(gid) == f["id"]:
                        alvo, via = gid, "igdb"
                    elif f["id"] in parentes:
                        alvo, via = gid, "igdb"          # o card é o original e o IGDB liga ao jogo da coleção
                    elif ig.similaridade(g["nome"], f["name"]) >= 0.97 and g.get("plataforma") != "Steam":
                        alvo, via = gid, "nome"
                    if alvo:
                        break
                plat = rotulo_plataformas(f.get("platforms"))
                if alvo and via == "nome":
                    rom = next((x[4:] for x in jogos[alvo].get("fontes", []) if x.startswith("rom:")), None)
                    plat = _ROM_ROTULO.get(rom) or jogos[alvo].get("plataforma") or plat
                if alvo and via == "igdb" and igdb_de.get(alvo) != f["id"]:
                    plat = ", ".join(x for x in (_ROT.get(i) for i in det[igdb_de[alvo]].get("platforms") or []) if x)[:60] or plat
                entram.append({"id": alvo, "nome": f["name"], "plataforma": plat or None,
                               "motivo": "jogo de dentro da coleção (IGDB)" if via != "nome" else "casado só pelo nome",
                               "incerto": bool(alvo and (via == "nome" or incerto(alvo))),
                               "progresso": progresso(jogos[alvo]) if alvo else {}})
                if alvo:
                    usados.add(alvo)
            if entram:
                usados.add(fica)
                grupos.append({"tipo": "colecao", "fica": _resumo(jogos[fica]), "entram": entram,
                               "incerto": incerto(fica)})
    # 2) versões: A.remakes/remasters/ports contém B -> B é a moderna, A entra
    arestas, motivo = [], {}
    for gid, iid in igdb_de.items():
        if gid in usados:
            continue
        for campo in ("remakes", "remasters", "ports"):
            for alvo_igdb in (det.get(iid) or {}).get(campo) or []:
                for outro in por_igdb.get(alvo_igdb, []):
                    if outro not in usados and outro != gid:
                        arestas.append((gid, outro))
                        motivo[(gid, outro)] = campo[:-1] if campo != "ports" else "port"
    for comp in _componentes(arestas):
        cards = sorted(comp, key=lambda i: _modernidade(jogos[i], det.get(igdb_de[i])), reverse=True)
        fica, resto = cards[0], cards[1:]
        entram = []
        for gid in resto:
            m = motivo.get((gid, fica)) or motivo.get((fica, gid)) or "relação indireta"
            entram.append({"id": gid, "nome": jogos[gid]["nome"], "plataforma": jogos[gid].get("plataforma"),
                           "motivo": f"edição antiga ({m} no IGDB)", "incerto": incerto(gid) or incerto(fica),
                           "progresso": progresso(jogos[gid])})
        grupos.append({"tipo": "versao", "fica": _resumo(jogos[fica]), "entram": entram, "incerto": incerto(fica)})
    return grupos


def _resumo(g: dict) -> dict:
    return {"id": g["id"], "nome": g["nome"], "plataforma": g.get("plataforma"), "progresso": progresso(g)}


def texto_proposta(grupos: list[dict]) -> str:
    L = ["PyRetro - proposta de unificação de edições (F2b) - SÓ PROPOSTA, nada foi aplicado.", "",
         "Regras do Victor: versão (remaster/remake/port) = card único com a cara da moderna, edições antigas dentro; "
         "coleção = card da coleção listando cada jogo de dentro com nome e plataforma originais. Progresso migra, IDs antigos viram alias.",
         "[?] = casamento incerto, conferir. Para recusar um grupo, diga o nome do card que fica.", ""]
    for tipo, titulo in (("colecao", "COLEÇÕES"), ("versao", "VERSÕES (mesmo jogo)")):
        gs = [g for g in grupos if g["tipo"] == tipo]
        L += [f"== {titulo} ({len(gs)}) =="]
        for g in sorted(gs, key=lambda x: x["fica"]["nome"].lower()):
            f = g["fica"]
            L.append(f"* FICA: {f['nome']} [{f['plataforma']}]" + (" [?]" if g["incerto"] else "") + _prog(f["progresso"]))
            for e in g["entram"]:
                if e["id"] is None:
                    L.append(f"    - lista (sem card próprio): {e['nome']} [{e['plataforma']}]")
                else:
                    L.append(f"    - entra: {e['nome']} [{e['plataforma']}]" + (" [?]" if e["incerto"] else "") +
                             f" - {e['motivo']}" + _prog(e["progresso"]))
        L.append("")
    return "\n".join(L) + "\n"


def _prog(p: dict) -> str:
    return "  | progresso: " + ", ".join(f"{k}={v}" for k, v in p.items() if k != "observacoes") + (" +obs" if "observacoes" in p else "") if p else ""


# --- aplicação em memória (testada; o banco só é gravado depois da revisão do Victor) -------------------
def resolver_id(library: dict, gid: str) -> str:
    """Segue o alias de um ID antigo até o card que o absorveu."""
    for g in library["games"]:
        if gid == g["id"] or gid in g.get("ids_antigos", []):
            return g["id"]
    return gid


def _fundir_progresso(a: dict, b: dict) -> None:
    for k in ("iniciado", "finalizado", "platinado", "savestate"):
        a[k] = bool(a.get(k) or b.get(k))
    if a.get("nota") in (None, "", 0) and b.get("nota") not in (None, "", 0):
        a["nota"] = b["nota"]
    try:
        a["tempo"] = (a.get("tempo") or 0) + (b.get("tempo") or 0)
    except TypeError:
        a["tempo"] = a.get("tempo") or b.get("tempo")
    if b.get("data_final") and (not a.get("data_final") or b["data_final"] > a["data_final"]):
        a["data_final"] = b["data_final"]
    if b.get("observacoes"):
        a["observacoes"] = (a.get("observacoes") + "\n" if a.get("observacoes") else "") + f"[{b.get('plataforma')}] {b['observacoes']}"


def _entrada(g: dict, tipo: str) -> dict:
    return {"id": g["id"], "nome": g["nome"], "plataforma": g.get("plataforma"), "tipo": tipo,
            "fontes": list(g.get("fontes", [])), "rom": next((f for f in g.get("fontes", []) if f.startswith("rom:")), None),
            "progresso": progresso(g), "registro": copy.deepcopy(g)}


def unificar(library: dict, fica_id: str, entram_ids: list[str], tipo: str = "versao", extras: list[dict] | None = None) -> dict:
    """Absorve os cards `entram_ids` em `fica_id`. `extras` = entradas de coleção sem card próprio
    ({"nome","plataforma"}). Em memória; quem chama decide gravar."""
    if tipo not in ("versao", "colecao"):
        raise ValueError("tipo deve ser versao ou colecao")
    jogos = library["games"]
    fica = next((g for g in jogos if g["id"] == fica_id), None)
    if fica is None or fica_id in entram_ids:
        raise ValueError("card que fica inválido")
    absorvidos = []
    for i in entram_ids:
        g = next((x for x in jogos if x["id"] == i), None)
        if g is None:
            raise ValueError(f"card desconhecido: {i}")
        absorvidos.append(g)
    ed = fica.setdefault("edicoes", [])
    if not ed and tipo == "versao":
        ed.append({**_entrada(fica, "atual"), "registro": None})
    for g in absorvidos:
        ed.append(_entrada(g, "item" if tipo == "colecao" else "edicao"))
        _fundir_progresso(fica, g)
        alt = fica.setdefault("nomes_alt", [])
        for n in [g["nome"], *g.get("nomes_alt", [])]:
            if n != fica["nome"] and n not in alt:
                alt.append(n)
        fica.setdefault("ids_antigos", [])
        for i in [g["id"], *g.get("ids_antigos", [])]:
            if i not in fica["ids_antigos"]:
                fica["ids_antigos"].append(i)
        jogos.remove(g)
    for x in extras or []:
        ed.append({"id": None, "nome": x["nome"], "plataforma": x.get("plataforma"), "tipo": "item", "fontes": [],
                   "rom": None, "progresso": {}, "registro": None})
    fica["tipo_card"] = tipo
    return fica


def aplicar_proposta(library: dict, grupos: list[dict], aplicar: bool = False) -> list[dict]:
    """Aplica (ou só simula) os grupos da proposta. Sem `aplicar`, trabalha numa cópia e devolve o que mudaria."""
    alvo = library if aplicar else copy.deepcopy(library)
    feitos = []
    for g in grupos:
        ids = [e["id"] for e in g["entram"] if e["id"]]
        extras = [e for e in g["entram"] if not e["id"]]
        unificar(alvo, g["fica"]["id"], ids, g["tipo"], extras)
        feitos.append({"fica": g["fica"].get("nome"), "entraram": len(ids), "so_lista": len(extras)})
    return feitos
