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
        6: "PC", 12: "Xbox 360", 11: "Xbox", 49: "Xbox One", 169: "Xbox Series X|S", 34: "Android", 39: "iOS", 55: "Windows Phone", 3: "Linux", 14: "Mac",
        52: "Arcade", 64: "Master System", 35: "Game Gear", 27: "Mega CD", 13: "DOS", 15: "C64", 16: "Amiga", 25: "Amstrad CPC",
        26: "ZX Spectrum", 63: "Atari ST", 51: "Famicom Disk System", 58: "Super Famicom", 99: "Famicom", 78: "Sega CD", 30: "32X",
        50: "3DO", 59: "Atari 2600", 53: "MSX2", 73: "BlackBerry", 132: "Fire TV"}
# Ano de lançamento do aparelho: só desempata quando o IGDB não dá a data por plataforma.
_ERA = {13: 1981, 15: 1982, 26: 1982, 25: 1984, 16: 1985, 63: 1985, 18: 1983, 99: 1983, 51: 1986, 64: 1985, 29: 1988, 33: 1989,
        86: 1987, 150: 1988, 19: 1990, 58: 1990, 35: 1990, 78: 1991, 30: 1994, 7: 1994, 32: 1994, 50: 1993, 4: 1996, 6: 1996,
        14: 1998, 22: 1998, 23: 1998, 8: 2000, 3: 2000, 24: 2001, 21: 2001, 11: 2001, 20: 2004, 38: 2004, 12: 2005, 9: 2006,
        5: 2006, 34: 2008, 39: 2008, 73: 2008, 37: 2011, 46: 2011, 41: 2012, 48: 2013, 49: 2013, 132: 2014, 130: 2017,
        169: 2020, 167: 2020, 508: 2025, 52: 1975}
# Plataforma de card (nome do PyRetro) -> rótulo curto.
_CARD_ROT = {"Sony - PlayStation": "PS1", "Sony - PlayStation 2": "PS2", "Sony - PSP": "PSP", "Nintendo - Nintendo DS": "DS",
             "Nintendo - 3DS": "3DS", "Nintendo - GameCube": "GameCube", "Nintendo - Wii": "Wii", "Nintendo Switch": "Switch",
             "Nintendo Switch 2": "Switch 2", "Nintendo - Nintendo 64": "N64", "Nintendo - Super Nintendo Entertainment System": "SNES",
             "Nintendo - Nintendo Entertainment System": "NES", "Nintendo - Game Boy": "Game Boy",
             "Nintendo - Game Boy Color": "Game Boy Color", "Nintendo - Game Boy Advance": "GBA", "Sega - Mega Drive - Genesis": "Mega Drive",
             "Sega - Master System - Mark III": "Master System", "Sega - Game Gear": "Game Gear", "PlayStation 4": "PS4",
             "Xbox One": "Xbox One", "Xbox Series S": "Xbox Series", "Xbox 360": "Xbox 360", "Xbox": "Xbox", "Steam": "PC", "GOG": "PC",
             "Epic Games Store": "PC", "FBNeo - Arcade Games": "Arcade", "Android": "Android", "iOS": "iOS"}
_MODERNOS_CARD = {"Nintendo Switch", "Nintendo Switch 2", "PlayStation 4", "Xbox One", "Xbox Series S", "Steam", "GOG", "Epic Games Store",
                  "Switch", "Switch 2", "PS4", "Xbox Series", "PC"}
_ROM_ROTULO = {"PS": "PS1", "PS2": "PS2", "PSP": "PSP", "NDS": "DS", "3DS": "3DS", "NGC": "GameCube", "WII": "Wii",
               "FC": "NES", "SFC": "SNES", "MD": "Mega Drive", "SMS": "Master System", "GG": "Game Gear", "GB": "Game Boy",
               "GBC": "Game Boy Color", "GBA": "GBA", "N64": "N64", "PCE": "PC Engine", "PCECD": "PC Engine CD", "ARCADE": "Arcade"}
_MODERNAS = {48, 167, 130, 508, 169, 49, 6, 3, 14, 34, 41}


def rotulo_plataformas(ids) -> str | None:
    """Plataformas antigas primeiro (a original); se só houver modernas, mostra as modernas. IDs sem rótulo são ignorados."""
    ids = [i for i in ids or [] if i in _ROT]
    antigas = [i for i in ids if i not in _MODERNAS]
    escolha = antigas or ids
    return ", ".join(_ROT[i] for i in escolha[:3]) or None


def plataforma_original(jogo_igdb: dict | None) -> str | None:
    """Rótulo da plataforma de LANÇAMENTO de um jogo do IGDB: a de `release_dates` mais antiga; sem isso, a mais antiga
    pela era do aparelho. Se o jogo traz `origens` (os jogos dos quais ele é remake/remaster/port), valem as deles também.
    Plataformas sem rótulo conhecido são ignoradas (nunca devolve '#123' se houver outra)."""
    jogo_igdb = jogo_igdb or {}
    todos = [jogo_igdb, *(jogo_igdb.get("origens") or [])]
    datas = [(rd["date"], _ERA.get(rd["platform"], 9999), rd["platform"]) for j in todos for rd in j.get("release_dates") or []
             if isinstance(rd, dict) and rd.get("date") and rd.get("platform") in _ROT]
    if datas:
        return _ROT[min(datas)[2]]
    conhecidas = [i for j in todos for i in j.get("platforms") or [] if i in _ROT]
    if conhecidas:
        return _ROT[min(conhecidas, key=lambda i: _ERA.get(i, 9999))]
    return None


def rotulo_card(card: dict, jogo_igdb: dict | None = None) -> str | None:
    """Plataforma curta de um card antigo; se for versão moderna de jogo antigo (sem ROM), vale a original do IGDB."""
    rom = next((f[4:] for f in card.get("fontes", []) if f.startswith("rom:")), None)
    proprio = _ROM_ROTULO.get(rom) or _CARD_ROT.get(card.get("plataforma")) or card.get("plataforma")
    orig = plataforma_original(jogo_igdb)
    if orig and not rom and card.get("plataforma") in _MODERNOS_CARD:
        return orig
    return proprio


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
                if alvo:
                    plat = rotulo_card(jogos[alvo], f)
                else:
                    plat = plataforma_original(f) or rotulo_plataformas(f.get("platforms"))
                entram.append({"id": alvo, "nome": f["name"], "plataforma": plat or None,
                               "motivo": "jogo de dentro da coleção (IGDB)" if via != "nome" else "casado só pelo nome",
                               "incerto": bool(alvo and (via == "nome" or incerto(alvo))),
                               "progresso": progresso(jogos[alvo]) if alvo else {}})
                if alvo:
                    usados.add(alvo)
            entram = sem_repetidos(entram, marcar=False)
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


def _chave_jogo(nome: str) -> str:
    """Nome sem 'Super'/'The' na frente: 'Mario Sunshine' = 'Super Mario Sunshine'."""
    n = ig.norm(nome)
    for pre in ("super ", "the "):
        if n.startswith(pre):
            n = n[len(pre):]
    return n


def _idade(rotulo: str | None) -> int:
    for i, r in _ROT.items():
        if r == rotulo:
            return _ERA.get(i, 9999)
    return 9999


def sem_repetidos(entradas: list[dict], marcar: bool = True) -> list[dict]:
    """O mesmo jogo de dentro de uma coleção pode vir de um card antigo e do IGDB (ou de dois cards). Fica uma linha:
    a de card (se houver) e, entre elas, a de plataforma mais antiga. Linha sem card repetida some; linha de card repetida
    segue guardada (tem o registro do card) mas com `repetido: true`, para a tela escondê-la."""
    grupos: dict[str, list[dict]] = {}
    for e in entradas:
        grupos.setdefault(_chave_jogo(e.get("nome") or ""), []).append(e)
    sair = set()
    for chave, itens in grupos.items():
        if not chave or len(itens) < 2:
            continue
        itens = sorted(itens, key=lambda e: (e.get("id") is None, 0 if e.get("rom") else 1, _idade(e.get("plataforma"))))
        for e in itens[1:]:
            if e.get("id") is None:
                sair.add(id(e))
            elif marcar:
                e["repetido"] = True
    return [e for e in entradas if id(e) not in sair]


def reparar_edicoes(card: dict, filhos: list[dict] | None = None) -> bool:
    """Conserta `edicoes` já gravadas: plataforma curta e original, sem '#id' cru e sem repetidos. `filhos` = jogos do IGDB
    (com `release_dates`) da coleção. Idempotente. Devolve se algo mudou."""
    ed = card.get("edicoes")
    if not ed:
        return False
    antes = copy.deepcopy([{k: v for k, v in e.items() if k != "registro"} for e in ed])
    for e in ed:
        if e.get("tipo") == "atual":
            continue
        filho = None
        if filhos:
            chave = _chave_jogo(e.get("nome") or "")
            filho = next((f for f in filhos if _chave_jogo(f.get("name", "")) == chave), None)
        reg = e.get("registro")
        if e.get("id") is not None:
            base = reg or {"fontes": e.get("fontes", []), "plataforma": e.get("plataforma")}
            e["plataforma"] = rotulo_card(base, filho) or e.get("plataforma")
        elif filho is not None:
            e["plataforma"] = plataforma_original(filho) or e.get("plataforma")
        else:
            limpo = ", ".join(t for t in (e.get("plataforma") or "").split(", ") if t and not t.startswith("#"))
            e["plataforma"] = limpo or None
    if card.get("tipo_card") == "colecao":
        itens = [e for e in ed if e.get("tipo") == "item"]
        mantidos = sem_repetidos(itens)
        ids_m = {id(e) for e in mantidos}
        card["edicoes"] = [e for e in ed if e.get("tipo") != "item" or id(e) in ids_m]
    return antes != [{k: v for k, v in e.items() if k != "registro"} for e in card["edicoes"]]


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
    return {"id": g["id"], "nome": g["nome"], "plataforma": rotulo_card(g) if tipo == "item" else g.get("plataforma"), "tipo": tipo,
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
    if tipo == "colecao":
        itens = [e for e in ed if e.get("tipo") == "item"]
        mantidos = sem_repetidos(itens)
        ids_m = {id(e) for e in mantidos}
        fica["edicoes"] = [e for e in ed if e.get("tipo") != "item" or id(e) in ids_m]
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
