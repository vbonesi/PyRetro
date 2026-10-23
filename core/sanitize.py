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
    r"(?:BR(?:-[A-Z]+)*"                        # (BR), (BR-USA), (BR-U), (BR-U-E)
    r"|T\d+(?:[._]\w+)*[a-z]?(?:-[A-Za-z]+)?"     # (T1.0), (T1.02), (T2), (T107-Beta), (T201_RC5)
    r"|DUB"                                      # (DUB): versão dublada do mesmo lote
    r"|[^()]*\.(?:com|net|org|com\.br)[^()]*"    # (www.romsportugues.com) etc.
    r"|www\.[^()]*"                              # (www.romsportugues), site sem domínio
    r")\)",
    re.IGNORECASE,
)
# Grupo tradutor: o parêntese colado antes ou depois da versão do patch, como
# "(DindoeCia) (T2.0)" e "(T1.0) (Starman)" (achado em 23/10 no lote do romsportugues.com).
# Tag padrão de região/idioma/revisão/disco nunca conta como grupo.
_PATCH_VERSION = r"\(T\d+(?:[._]\w+)*[a-z]?(?:-[A-Za-z]+)?\)"
_STANDARD_TAG = re.compile(
    r"\((?:USA|Europe|Japan|World|Brazil|Korea|China|Asia|Australia|France|Germany|Spain|Italy|"
    r"[A-Z][a-z](?:,[A-Z][a-z])+|Rev \w+|v\d[\w.]*|Beta\s*\d*|Proto\w*|Disc \d+|Track\s*\d+|Unl|Demo|Sample)\)", re.IGNORECASE)
_CREDIT_BEFORE = re.compile(r"\s*(\([^()]*\))(?=\s*" + _PATCH_VERSION + ")", re.IGNORECASE)



def strip_translation_tags(name: str) -> str:
    """Remove as tags de crédito de tradução do nome (mantém a
    extensão intacta) - ver _TRANSLATION_TAG_RE pros três padrões
    reconhecidos."""
    stem, _, ext = name.rpartition(".")
    if not stem:
        stem, ext = name, ""
    # Créditos colados na versão do patch saem antes das tags de tradução.
    stem = _CREDIT_BEFORE.sub(lambda m: m.group(0) if _STANDARD_TAG.fullmatch(m.group(1)) else "", stem)
    stem = re.sub(r"(" + _PATCH_VERSION + r")(\s*\([^()]*\))",
                  lambda m: m.group(1) if not _STANDARD_TAG.fullmatch(m.group(2).strip()) else m.group(0), stem, flags=re.IGNORECASE)
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
