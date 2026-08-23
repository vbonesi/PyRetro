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
import re
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


# Tags de crédito de ROM hack/tradução de fã (região da tradução tipo
# "(BR)"/"(BR-USA)"/"(BR-U)", versão do patch "(T1.02)", site de origem
# "(www.site.com)") - achado real em 22/08 com o lote de ROMs traduzidas
# do romsportugues.com organizado pro GBA. Deliberadamente NÃO mexe em
# tag padrão de região/revisão (USA)/(Europe)/(Rev 1)/(Beta)/(Disc 1) -
# só esses três padrões específicos de site de tradução.
_TRANSLATION_TAG_RE = re.compile(
    r"\s*\("
    r"(?:BR(?:-[A-Z]+)?"                        # (BR), (BR-USA), (BR-U)
    r"|T\d+(?:\.\d+)*[a-z]?"                     # (T1.0), (T1.1), (T1.02), (T2)
    r"|[^()]*\.(?:com|net|org|com\.br)[^()]*"    # (www.romsportugues.com) etc.
    r")\)",
    re.IGNORECASE,
)


def strip_translation_tags(name: str) -> str:
    """Remove as tags de crédito de tradução do nome (mantém a
    extensão intacta) - ver _TRANSLATION_TAG_RE pros três padrões
    reconhecidos."""
    stem, _, ext = name.rpartition(".")
    if not stem:
        stem, ext = name, ""
    cleaned = _TRANSLATION_TAG_RE.sub("", stem)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return f"{cleaned}.{ext}" if ext else cleaned


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
