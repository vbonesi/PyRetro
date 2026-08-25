"""
Pasta de organização automática ("0-Organizar" dentro de roms_root,
nome configurável em config.toml [pc] organizar_dir). O "upload" de ROM
nova vira literalmente o Google Drive: o usuário larga o arquivo ali
(do PC ou do celular, sincroniza sozinho) e o PyRetro identifica o
sistema pela extensão e move pra roms_root/<CODIGO>/ - sem precisar de
upload HTTP, o que seria arriscado pra ROM de vários GB.

Muitas extensões são ambíguas entre sistemas (.iso: PS2/GameCube/Wii/
PSP; .cue/.chd/.cdi/.gdi: PS/SDC/SS/PCECD/PS2...) - quando
isso acontece, não decide sozinho, lista os candidatos pro usuário
escolher (GUI: dropdown por item; CLI: só lista, não move)."""
from pathlib import Path

from core import sanitize as sanitize_mod


def build_ext_index(systems_cfg: dict, heavy_systems_cfg: dict) -> dict:
    """{ext_sem_ponto_minusculo: [{"code", "nome", "kind": "leve"|"pesado"}, ...]}
    Alguns códigos (PS, SDC) existem tanto em [systems] quanto em
    [heavy_systems] - o destino do organize é o mesmo (roms_root/<code>),
    então deduplica por code em vez de listar duas vezes com o mesmo
    nome (confuso no dropdown da GUI). [heavy_systems] tem prioridade
    de exibição (kind="pesado") por ser o caso mais comum pra essas
    extensões pesadas."""
    by_code: dict = {}
    for code, info in systems_cfg.items():
        for ext in info.get("exts", []):
            by_code.setdefault(ext.lower().lstrip("."), {})[code] = {
                "code": code, "nome": info.get("capas", code), "kind": "leve",
            }
    for code, info in heavy_systems_cfg.items():
        for ext in info.get("exts", []):
            by_code.setdefault(ext.lower().lstrip("."), {})[code] = {
                "code": code, "nome": info.get("nome", code), "kind": "pesado",
            }
    return {ext: list(codes.values()) for ext, codes in by_code.items()}


def list_pending(roms_root: Path, staging_dir_name: str, ext_index: dict) -> list:
    """[{"name", "is_dir", "size", "candidates": [...]}], ordenado por
    nome. Ignora arquivos ocultos (ex: .DS_Store, artefatos de sync)."""
    staging = roms_root / staging_dir_name
    if not staging.is_dir():
        return []
    items = []
    for entry in sorted(staging.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
            candidates: list = []  # pasta por jogo (Switch-style) - fora do escopo hoje
        else:
            size = entry.stat().st_size
            candidates = ext_index.get(entry.suffix.lower().lstrip("."), [])
        items.append({"name": entry.name, "is_dir": entry.is_dir(), "size": size, "candidates": candidates})
    return items


def clean_name(name: str) -> str:
    """Nome final que um item leva pra roms_root/<code> - troca
    & : * (sanitize_name) e remove tag de crédito de tradução/hack
    (strip_translation_tags), ver core/sanitize.py pros dois."""
    return sanitize_mod.strip_translation_tags(sanitize_mod.sanitize_name(name))


def move_to_system(roms_root: Path, staging_dir_name: str, name: str, code: str) -> tuple[bool, str]:
    """Move um item da pasta de organização pra roms_root/<code>/, já
    com o nome limpo (clean_name) - senão o item cai lá com & : * ou
    tag de tradução intactos até alguém lembrar de corrigir à parte.
    Nunca sobrescreve um item que já existe lá."""
    src = roms_root / staging_dir_name / name
    if not src.exists():
        return False, "não encontrado na pasta de organização"
    dest_dir = roms_root / code
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_name = clean_name(name)
    dest = dest_dir / dest_name
    if dest.exists():
        return False, f"já existe um item com esse nome em {code}/"
    src.rename(dest)
    return True, f"movido pra {code}/{dest_name}"
