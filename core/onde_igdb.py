"""Lógica pura do F2 (plano de 27/11/2026): casar um card com o IGDB e decidir onde o jogo existe.

Sem rede aqui: `tools/onde_roda_igdb.py` faz as consultas e chama estas funções.
Tamanhos em GB são ordem de grandeza (sem fonte), por plataforma."""
from __future__ import annotations
import difflib
import math
import re
import unicodedata

# IDs de plataforma do IGDB
ID = {"switch": (130,), "ps4": (48,), "xbox": (169, 49, 12), "pc": (6,), "switch2": (508,)}
ID_ROTULO = {130: "Switch", 48: "PS4", 169: "Xbox Series X|S", 49: "Xbox One", 12: "Xbox 360", 6: "PC", 508: "Switch 2"}
TODOS_ALVO = tuple(i for v in ID.values() for i in v)
NATIVA = {  # plataforma do card -> ids IGDB onde ele nasceu
    "Sony - PlayStation": (7,), "Sony - PlayStation 2": (8,), "Sony - PSP": (38,), "Nintendo - Nintendo DS": (20,),
    "Nintendo - 3DS": (37,), "Nintendo - GameCube": (21,), "Nintendo - Wii": (5,), "Nintendo Switch": (130,),
    "Nintendo Switch 2": (508,), "PlayStation 4": (48,), "Xbox": (169, 49, 12, 11), "Xbox One": (49,),
    "Xbox Series S": (169,), "Xbox 360": (12,), "Steam": (6,), "Epic Games Store": (6,), "GOG": (6,),
}
VELHAS = {7, 8, 38, 20, 37, 21, 5, 9, 12, 11}
TIPOS_BASE_RUINS = {1, 2, 5, 6, 7, 14}  # dlc, expansão, mod, episódio, temporada, update (bundle e pack contam: o card pode ser a coletânea)
_PALAVRAS_EDICAO = ("remastered", "remaster", "hd", "definitive", "edition", "deluxe", "complete", "goty", "game of the year",
                    "directors cut", "director s cut", "enhanced", "anniversary", "ultimate", "legendary", "standard",
                    "special", "collection", "trilogy", "the", "a", "and", "of")

FONTE_PRIORIDADE = {"mesma": 0, "versao": 1, "port": 2, "remaster": 3, "remake": 4, "colecao": 5, "mesmonome": 6}


def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def limpar_nome(nome: str) -> str:
    """Tira etiquetas de ROM/loja: (USA), [PT-BR], ™, ®."""
    n = re.sub(r"[\(\[][^\)\]]*[\)\]]", " ", nome)
    n = n.replace("™", "").replace("®", "").replace("©", "")
    return re.sub(r"\s+", " ", n).strip()


def norm(nome: str) -> str:
    n = sem_acento(limpar_nome(nome)).lower().replace("&", " and ")
    n = re.sub(r"[^a-z0-9]+", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def nucleo(nome: str) -> str:
    """Nome sem palavras de edição, para comparar 'X' com 'X Remastered'."""
    toks = [t for t in norm(nome).split() if t not in _PALAVRAS_EDICAO]
    return " ".join(toks)


def similaridade(a: str, b: str) -> float:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if nucleo(a) and nucleo(a) == nucleo(b):
        return 0.97
    return difflib.SequenceMatcher(None, na, nb).ratio()


def nomes_do_candidato(c: dict) -> list[str]:
    alts = [a.get("name") for a in (c.get("alternative_names") or []) if isinstance(a, dict) and a.get("name")]
    return [c.get("name", ""), *alts]


def sim_candidato(card_nomes: list[str], c: dict) -> float:
    return max((similaridade(a, b) for a in card_nomes for b in nomes_do_candidato(c)), default=0.0)


def escolher_base(card_nomes: list[str], plataforma_card: str, pool: list[dict], minimo: float = 0.86):
    """(candidato, similaridade, pontos) ou (None, melhor_sim, 0). Prefere o jogo nascido na plataforma do card."""
    nat = set(NATIVA.get(plataforma_card, ()))
    melhor, melhor_pts, melhor_sim = None, -1.0, 0.0
    for c in pool:
        if c.get("game_type") in TIPOS_BASE_RUINS:
            continue
        s = sim_candidato(card_nomes, c)
        melhor_sim = max(melhor_sim, s)
        if s < minimo:
            continue
        pts = s * 100
        if nat and nat & set(c.get("platforms") or []):
            pts += 30
        if c.get("game_type") == 0:
            pts += 5
        pts += min(math.log10(1 + (c.get("total_rating_count") or 0)), 4)
        if pts > melhor_pts:
            melhor, melhor_pts = c, pts
    if melhor is None:
        return None, melhor_sim, 0.0
    return melhor, sim_candidato(card_nomes, melhor), melhor_pts


def ids_relacionados(base: dict) -> dict[int, str]:
    """id -> tipo de relação (versao/port/remaster/remake/colecao) a partir dos campos do IGDB."""
    rel: dict[int, str] = {}
    for campo, tipo in (("ports", "port"), ("remasters", "remaster"), ("remakes", "remake"), ("bundles", "colecao")):
        for i in base.get(campo) or []:
            rel.setdefault(i, tipo)
    return rel


def evidencias(base: dict, relacionados: dict[int, dict], tipos: dict[int, str], extras: list[dict]) -> dict[str, list[dict]]:
    """Por plataforma do PyRetro: lista de {tipo, nome, plat_id, igdb_id} ordenada por prioridade."""
    out: dict[str, list[dict]] = {p: [] for p in ID}
    fontes: list[tuple[dict, str]] = [(base, "mesma")]
    for i, g in relacionados.items():
        fontes.append((g, tipos.get(i, "versao")))
    for g in extras:
        fontes.append((g, "mesmonome"))
    for g, tipo in fontes:
        for plat, ids in ID.items():
            for pid in g.get("platforms") or []:
                if pid in ids:
                    out[plat].append({"tipo": tipo, "nome": g.get("name"), "plat_id": pid, "igdb_id": g.get("id"),
                                      "tipo_igdb": g.get("game_type")})
    for plat in out:
        out[plat].sort(key=lambda e: (FONTE_PRIORIDADE[e["tipo"]], 0 if e["plat_id"] != 12 else 1))
    return out


_TIPO_ROTULO = {"mesma": "original", "versao": "edição", "port": "port", "remaster": "remaster", "remake": "remake",
                "colecao": "coleção", "mesmonome": "mesmo nome, sem relação no IGDB"}


def rotulo_edicao(plat: str, ev: list[dict]) -> str | None:
    if not ev:
        return None
    e = ev[0]
    txt = f"{e['nome']} ({_TIPO_ROTULO[e['tipo']]}, {ID_ROTULO.get(e['plat_id'], '?')})"
    if plat == "xbox" and e["plat_id"] == 12:
        txt += " — retrocompatível, conferir"
    return txt


# --- tamanhos (ordem de grandeza) -------------------------------------------------------------------
_CLASSICO = {7: 2.0, 8: 4.5, 38: 2.0, 20: 1.0, 37: 1.5, 21: 5.0, 5: 5.0}


def _arred(gb: float) -> float:
    return round(gb) if gb >= 10 else round(gb, 1)


def tamanho_base(rating_count: int, indie: bool) -> float:
    rc = rating_count or 0
    if indie:
        return 2.0 if rc < 30 else 4.0 if rc < 150 else 8.0
    return 6.0 if rc < 30 else 15.0 if rc < 100 else 30.0 if rc < 300 else 50.0


def estimar_gb(plat: str, ev: list[dict], base: dict, steam_gb: float | None = None, local_switch_gb: float | None = None) -> float | None:
    """Tamanho aproximado do jogo na plataforma `plat`, dado a evidência escolhida."""
    if not ev:
        return None
    if plat == "switch" and local_switch_gb:
        return _arred(local_switch_gb)
    e = ev[0]
    nativas = set(base.get("platforms") or [])
    antigo = bool(nativas) and nativas <= VELHAS | {6} and bool(nativas & VELHAS) and not (nativas & {48, 130, 169, 49, 508})
    if e["tipo"] in ("port", "mesmonome", "colecao") and antigo and e.get("tipo_igdb") in (11, None) and steam_gb is None:
        orig = max((_CLASSICO.get(p, 3.0) for p in nativas if p in VELHAS), default=3.0)
        return _arred(min(orig, 8.0) * (0.5 if plat == "switch" else 1.0))
    ano = 2015
    if base.get("first_release_date"):
        ano = 1970 + base["first_release_date"] / 31556952
    indie = 32 in (base.get("genres") or [])
    if steam_gb:
        gb = steam_gb
    else:
        gb = tamanho_base(base.get("total_rating_count") or 0, indie)
        if ano < 2008:
            gb = min(gb, 6.0)
        elif ano < 2013:
            gb = min(gb, 15.0)
        if e["tipo"] == "colecao":
            gb = max(gb, 8.0)
    mult = {"pc": 1.0, "ps4": 1.0, "xbox": 1.0, "switch": 0.5, "switch2": 0.8}[plat]
    gb *= mult
    if plat == "switch":
        gb = min(gb, 32.0)
    return _arred(max(gb, 0.3))


def montar(card_nome: str, plataforma_card: str, base: dict | None, sim: float, evs: dict[str, list[dict]] | None,
           steam_gb=None, lojas_pc: list[str] | None = None, local_switch_gb=None) -> dict:
    """Resultado por card: {estado, igdb_id, confianca, plataformas:{plat:{existe,gb,edicao,lojas}}, duvidas:[...]}."""
    r: dict = {"estado": "nao_verificado", "igdb_id": None, "igdb_nome": None, "confianca": round(sim, 2),
               "plataformas": {}, "duvidas": []}
    if base is None or evs is None:
        r["duvidas"].append("sem casamento no IGDB" + (f" (melhor similaridade {sim:.2f})" if sim else ""))
        return r
    r.update(estado="igdb", igdb_id=base["id"], igdb_nome=base.get("name"))
    if sim < 0.95:
        r["duvidas"].append(f"casamento incerto: card '{card_nome}' ~ IGDB '{base.get('name')}' ({sim:.2f})")
    for plat in ID:
        ev = evs[plat]
        e = {"existe": bool(ev), "gb": None, "edicao": rotulo_edicao(plat, ev)}
        if ev:
            e["gb"] = estimar_gb(plat, ev, base, steam_gb=steam_gb if plat != "switch" or True else None,
                                 local_switch_gb=local_switch_gb)
            if ev[0]["tipo"] == "mesmonome":
                r["duvidas"].append(f"{plat}: '{ev[0]['nome']}' só pelo nome igual (sem relação no IGDB)")
            if plat == "xbox" and ev[0]["plat_id"] == 12:
                r["duvidas"].append("xbox: só existe no 360; confirmar retrocompatibilidade no Series S")
            if ev[0]["tipo"] in ("port", "remaster", "remake", "colecao") and plat in ("ps4", "switch"):
                r["duvidas"].append(f"{plat}: edição diferente do original → {e['edicao']}")
        if plat == "pc" and lojas_pc:
            e["lojas"] = lojas_pc
        r["plataformas"][plat] = e
    return r
