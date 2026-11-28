"""Onde cada jogo existe entre as plataformas do Victor (plano de 27/11/2026).

Fora do retrô o card não carrega mais ROM: ele diz em que plataforma o jogo
roda (Switch, PS4, Xbox Series S, PC, Switch 2 emulado) e, quando o Victor
baixa ou compra, em qual ele tem. Guardado no próprio registro:

    onde_roda = {"ps4": {"existe": True, "gb": 40, "manual": False}, ...}
    jogar     = {"estado": "quero"|"tenho", "plataforma": "ps4", "loja": None}

`manual=True` é correção do Victor e **vence qualquer pesquisa ou inferência**.
Tamanho em GB é ordem de grandeza, sem fonte.
"""
from __future__ import annotations

# Ordem de prioridade do card: Switch e PS4 primeiro.
PLATAFORMAS = ("switch", "ps4", "xbox", "pc", "switch2")
ROTULOS = {"switch": "Switch", "ps4": "PS4", "xbox": "Xbox Series S", "pc": "PC", "switch2": "Switch 2"}
ESTADOS = ("quero", "tenho")

# Fonte do registro -> plataforma em que ela prova que o jogo existe.
_FONTE_PLATAFORMA = {
    "wishlist:switch": "switch", "switch": "switch",
    "wishlist:psn": "ps4", "psn": "ps4",
    "wishlist:xbox": "xbox", "xbox": "xbox",
    "wishlist:steam": "pc", "steam": "pc",
    "wishlist:switch2": "switch2", "switch2": "switch2",
}
_LOJAS_PC = {"steam": "Steam", "heroic:epic": "Epic", "heroic:gog": "GOG", "heroic:amazon": "Amazon"}


def plataforma_da_fonte(fonte: str) -> str | None:
    if fonte in _FONTE_PLATAFORMA:
        return _FONTE_PLATAFORMA[fonte]
    return "pc" if fonte in _LOJAS_PC or fonte.startswith("heroic:") else None


def _checa_plataforma(plat: str) -> str:
    if plat not in PLATAFORMAS:
        raise ValueError(f"plataforma desconhecida: {plat}")
    return plat


def _entrada(game: dict, plat: str) -> dict:
    mapa = game.setdefault("onde_roda", {})
    return mapa.setdefault(plat, {"existe": None, "gb": None, "manual": False})


def _gb(valor):
    if valor is None or valor == "":
        return None
    gb = float(valor)
    if gb < 0:
        raise ValueError("tamanho negativo")
    return round(gb, 1)


def definir(game: dict, plat: str, existe=None, gb=None) -> dict:
    """Correção manual do Victor: grava e trava (`manual`)."""
    e = _entrada(game, _checa_plataforma(plat))
    if existe is not None:
        e["existe"] = bool(existe)
    if gb is not None:
        e["gb"] = _gb(gb)
    e["manual"] = True
    return e


def desmarcar_manual(game: dict, plat: str) -> None:
    """Devolve a plataforma à pesquisa/inferência (apaga a correção)."""
    game.get("onde_roda", {}).pop(_checa_plataforma(plat), None)


def pesquisa(game: dict, plat: str, existe=None, gb=None) -> bool:
    """Resultado de pesquisa (IGDB, lojas): grava só se o Victor não corrigiu à mão."""
    e = _entrada(game, _checa_plataforma(plat))
    if e["manual"]:
        return False
    if existe is not None:
        e["existe"] = bool(existe)
    if gb is not None:
        e["gb"] = _gb(gb)
    return True


def inferir(game: dict) -> int:
    """Marca como existente as plataformas provadas pelas fontes do card (sem tocar no manual)."""
    n = 0
    for f in game.get("fontes", []):
        plat = plataforma_da_fonte(f)
        if not plat:
            continue
        e = _entrada(game, plat)
        if not e["manual"] and e["existe"] is not True:
            e["existe"] = True
            n += 1
    return n


def quero_jogar(game: dict) -> dict:
    game["jogar"] = {"estado": "quero", "plataforma": None, "loja": None}
    return game["jogar"]


def tenho_em(game: dict, plat: str, loja: str | None = None) -> dict:
    """"Baixei/comprei em…": no PC a loja é obrigatória."""
    _checa_plataforma(plat)
    loja = (loja or "").strip() or None
    if plat == "pc" and not loja:
        raise ValueError("no PC informe a loja (Steam, Epic, GOG...)")
    if plat != "pc":
        loja = None
    e = _entrada(game, plat)
    if not e["manual"]:
        e["existe"] = True
    game["jogar"] = {"estado": "tenho", "plataforma": plat, "loja": loja}
    return game["jogar"]


def estado(game: dict) -> dict:
    return game.get("jogar") or {"estado": None, "plataforma": None, "loja": None}


def existentes(game: dict) -> list[str]:
    """Plataformas em que o jogo existe, na ordem de prioridade."""
    mapa = game.get("onde_roda") or {}
    return [p for p in PLATAFORMAS if (mapa.get(p) or {}).get("existe") is True]


def _fonte_de_posse(game: dict):
    """(plataforma, loja) da primeira fonte de posse não retrô, ou None."""
    for f in game.get("fontes", []):
        if f.startswith("wishlist:") or f.startswith("rom:"):
            continue
        plat = plataforma_da_fonte(f)
        if plat:
            return plat, (_LOJAS_PC.get(f) or f.split(":", 1)[-1].title()) if plat == "pc" else None
    return None


def eh_retro(game: dict) -> bool:
    return any(f.startswith("rom:") for f in game.get("fontes", []))


def migrar_game(game: dict) -> bool:
    """Preenche `onde_roda`/`jogar` de um card antigo. Idempotente; nunca sobrescreve o manual."""
    antes = (repr(game.get("onde_roda")), repr(game.get("jogar")))
    if eh_retro(game):
        return False
    inferir(game)
    if not game.get("jogar"):
        posse = _fonte_de_posse(game)
        if posse:
            game["jogar"] = {"estado": "tenho", "plataforma": posse[0], "loja": posse[1]}
        elif game.get("fontes") and all(f.startswith("wishlist:") for f in game["fontes"]):
            quero_jogar(game)
    return antes != (repr(game.get("onde_roda")), repr(game.get("jogar")))


def _norm(nome: str) -> str:
    from core.library import _wishlist_key
    return _wishlist_key(nome)


def _so_desejo(g: dict) -> bool:
    f = g.get("fontes") or []
    return bool(f) and all(x.startswith("wishlist:") for x in f)


def grupos_repetidos(library: dict) -> list[list[dict]]:
    """Cards só de desejo com o mesmo nome em listas diferentes.

    Switch × Switch 2 nunca juntam (pode ser remake/edição à parte)."""
    por_nome: dict[str, list[dict]] = {}
    for g in library.get("games", []):
        if _so_desejo(g):
            por_nome.setdefault(_norm(g["nome"]), []).append(g)
    out = []
    for lista in por_nome.values():
        if len(lista) < 2:
            continue
        fontes = [set(g["fontes"]) for g in lista]
        if any("wishlist:switch" in a and "wishlist:switch2" in b for a in fontes for b in fontes):
            continue
        out.append(lista)
    return out


_CAMPOS_VAZIOS = ("genero", "subgenero", "sinopse", "lancamento", "desenvolvedora", "capa", "observacoes",
                  "tempo", "nota", "data_final", "meta")


def juntar(library: dict, manter_id: str, descartar_id: str) -> dict:
    """Funde `descartar` em `manter`: une fontes/apelidos/onde_roda e completa campos vazios."""
    jogos = library["games"]
    a = next((g for g in jogos if g["id"] == manter_id), None)
    b = next((g for g in jogos if g["id"] == descartar_id), None)
    if a is None or b is None or a is b:
        raise ValueError("ids inválidos para juntar")
    for f in b.get("fontes", []):
        if f not in a["fontes"]:
            a["fontes"].append(f)
    alt = a.setdefault("nomes_alt", [])
    for n in [b["nome"], *b.get("nomes_alt", [])]:
        if n != a["nome"] and n not in alt:
            alt.append(n)
    for c in _CAMPOS_VAZIOS:
        if a.get(c) in (None, "", False) and b.get(c) not in (None, "", False):
            a[c] = b[c]
    for k in ("iniciado", "finalizado", "platinado", "savestate"):
        a[k] = bool(a.get(k) or b.get(k))
    for plat, eb in (b.get("onde_roda") or {}).items():
        ea = _entrada(a, plat)
        if eb.get("manual") and not ea["manual"]:
            ea.update(eb)
        elif not ea["manual"]:
            if ea["existe"] is None:
                ea["existe"] = eb.get("existe")
            if ea["gb"] is None:
                ea["gb"] = eb.get("gb")
    if not a.get("jogar") and b.get("jogar"):
        a["jogar"] = b["jogar"]
    jogos.remove(b)
    return a


def juntar_repetidos(library: dict, aplicar: bool = True) -> list[dict]:
    """Junta os grupos de `grupos_repetidos`; devolve o que foi (ou seria) fundido."""
    feitos = []
    for lista in grupos_repetidos(library):
        # Mantém o card que tem mais campos preenchidos (nota/capa/sinopse), depois o primeiro.
        lista = sorted(lista, key=lambda g: -sum(1 for c in _CAMPOS_VAZIOS if g.get(c) not in (None, "", False)))
        base = lista[0]
        for outro in lista[1:]:
            feitos.append({"manteve": base["id"], "juntou": outro["id"], "nome": base["nome"]})
            if aplicar:
                juntar(library, base["id"], outro["id"])
    return feitos


def migrar(library: dict, aplicar: bool = True) -> dict:
    """Migração única (e repetível): junta repetidos, infere plataformas, define quero/tenho."""
    juntados = juntar_repetidos(library, aplicar)
    tocados = 0
    if aplicar:
        for g in library["games"]:
            if migrar_game(g):
                tocados += 1
    return {"juntados": juntados, "atualizados": tocados}


# --- F4: o que falta nas wishlists de preço (Steam e Xbox) -----------------------------------------
# Não há API para escrever wishlist: o PyRetro só lista, o Victor adiciona à mão.
LISTAS_PRECO = {"steam": ("pc", "wishlist:steam", ("steam",), "Steam"), "xbox": ("xbox", "wishlist:xbox", ("xbox",), "Xbox")}


def faltam_na_wishlist(library: dict, loja: str) -> list[str]:
    """Nomes dos cards que existem na plataforma da loja, ainda não são dele e não estão na wishlist dela."""
    if loja not in LISTAS_PRECO:
        raise ValueError(f"loja desconhecida: {loja}")
    plat, marca, posse, _ = LISTAS_PRECO[loja]
    nomes = []
    for g in library.get("games", []):
        if g.get("oculto") or eh_retro(g):
            continue
        fontes = g.get("fontes") or []
        if marca in fontes or any(f in fontes for f in posse):
            continue
        if estado(g)["estado"] == "tenho":
            continue
        if (g.get("onde_roda") or {}).get(plat, {}).get("existe") is True:
            nomes.append(g["nome"])
    return sorted(set(nomes), key=str.lower)


def texto_faltam(loja: str, nomes: list[str]) -> str:
    return f"# Falta na wishlist da {LISTAS_PRECO[loja][3]} ({len(nomes)} jogos): adicione à mão\n" + "".join(n + "\n" for n in nomes)
