"""
Sanitização de nomes de arquivo - RetroArch não aceita `&`, `:`, `*`
em nome de arquivo (e `/` nem poderia aparecer literalmente, mas fica
o tratamento defensivo por segurança). Troca:
    & -> and
    / -> _   (defensivo)
    : -> -
    * -> (removido)

Roda em capas E ROMs - as duas pastas usam o mesmo "label" como base
do nome (`<label>.png` / `<label>.ext`), então sanitizar só um lado
quebraria o casamento entre capa e ROM. Nunca sobrescreve um arquivo
que já existe com o nome novo (marca como "conflito" e não mexe, pra
não perder nada por engano).
"""
from pathlib import Path

_REPLACEMENTS = [
    ("&", "and"),
    ("/", "_"),
    (":", "-"),
    ("*", ""),
]


def sanitize_name(name: str) -> str:
    for old, new in _REPLACEMENTS:
        name = name.replace(old, new)
    return name


def needs_sanitizing(name: str) -> bool:
    return any(ch in name for ch in "&/:*")


def scan_and_rename(root: Path, apply: bool = False) -> list:
    """Varre root recursivamente. Retorna lista de dicts
    {old, new, status}, status em: renomeado | seria_renomeado | conflito."""
    results = []
    if not root.is_dir():
        return results
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if not needs_sanitizing(path.name):
            continue
        new_name = sanitize_name(path.name)
        if new_name == path.name:
            continue
        new_path = path.parent / new_name
        if new_path.exists():
            results.append({"old": str(path), "new": str(new_path), "status": "conflito"})
            continue
        if apply:
            path.rename(new_path)
            results.append({"old": str(path), "new": str(new_path), "status": "renomeado"})
        else:
            results.append({"old": str(path), "new": str(new_path), "status": "seria_renomeado"})
    return results
