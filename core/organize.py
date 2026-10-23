"""
Pasta de organização automática ("0-Organizar" dentro de roms_root,
nome configurável em config.toml [pc] organizar_dir). O "upload" de ROM
nova vira literalmente o Google Drive: o usuário larga o arquivo ali
(do PC ou do celular, sincroniza sozinho) e o PyRetro identifica o
sistema pela extensão e move pra roms_root/<CODIGO>/ - sem precisar de
upload HTTP, o que seria arriscado pra ROM de vários GB.

Muitas extensões são ambíguas entre sistemas (.iso: PS2/GameCube/Wii/
PSP; .cue/.chd/.cdi/.gdi: PS/PCECD/PS2...) - quando
isso acontece, não decide sozinho, lista os candidatos pro usuário
escolher (GUI: dropdown por item; CLI: só lista, não move)."""
from pathlib import Path

from core import sanitize as sanitize_mod


def build_ext_index(systems_cfg: dict, heavy_systems_cfg: dict) -> dict:
    """{ext_sem_ponto_minusculo: [{"code", "nome", "kind": "leve"|"pesado"}, ...]}
    Alguns códigos (PS) existem tanto em [systems] quanto em
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


# --- Organizar também a pasta de downloads (23/10, pedido do Victor) -------------------------
# Itens vêm de mais de uma origem (pasta de organizar e Downloads), arquivos compactados são
# abertos sem extrair para listar as ROMs de dentro (cada ROM vira uma linha), downloads ainda em
# andamento aparecem mas não podem ser mexidos, e uma imagem com o mesmo nome ao lado vira a capa.
import json as _json
import re as _re
import shutil as _shutil
import subprocess as _subprocess
import tempfile as _tempfile
import unicodedata as _unicodedata

from core import rom_bundles as _bundles

ARCHIVES = {".zip", ".7z", ".rar"}
PARTIAL = {".crdownload", ".part", ".tmp", ".download", ".!qb"}
IMAGES = {".jpg", ".jpeg", ".png", ".webp"}


def _norm(text: str) -> str:
    text = _unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return _re.sub(r"[^a-z0-9]", "", text.lower())


def archive_members(path: Path, run=_subprocess.run) -> list:
    """[(nome dentro do arquivo, tamanho)] pelo 7z, sem extrair."""
    out = run(["7z", "l", "-ba", "-slt", str(path)], capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise ValueError("não foi possível ler o arquivo compactado")
    members, current = [], {}
    for line in out.stdout.splitlines() + [""]:
        if not line.strip():
            if current.get("Path") and current.get("Folder") != "+":
                members.append((current["Path"], int(current.get("Size") or 0)))
            current = {}
        elif " = " in line:
            key, value = line.split(" = ", 1)
            current[key] = value
    return members


def match_image(stems: list, images: list) -> str | None:
    """Imagem cujo nome normalizado é o começo de um dos nomes (ou o contrário): a capa que o
    usuário deixou ao lado da ROM ("Pokemon-Ghost-Grey-Version.jpg" ↔ "...Version v103")."""
    keys = [k for k in (_norm(s) for s in stems) if len(k) >= 4]
    for image in images:
        key = _norm(Path(image).stem)
        if len(key) >= 4 and any(k.startswith(key) or key.startswith(k) for k in keys):
            return image
    return None


def _item(source, name, member, size, candidates, status, roms_root, images, stems):
    final = clean_name(Path(member).name if member else name)
    exists = [c["code"] for c in candidates if (roms_root / c["code"] / final).exists()]
    return {"id": f"{source}/{name}" + (f"::{member}" if member else ""), "source": source, "name": name,
            "member": member, "size": size, "candidates": candidates, "status": status, "final": final,
            "exists_in": exists, "cover_image": match_image(stems, images) if status == "pronto" else None}


def scan(roms_root: Path, sources: list, ext_index: dict, run=_subprocess.run) -> list:
    """Itens de todas as origens [(id da origem, pasta)]. Arquivos soltos de ROM, ROMs dentro de
    .zip/.7z/.rar e downloads em andamento; imagens soltas só servem de capa."""
    items = []
    for source, folder in sources:
        if not folder.is_dir():
            continue
        entries = sorted(e for e in folder.iterdir() if not e.name.startswith("."))
        images = [e.name for e in entries if e.is_file() and e.suffix.lower() in IMAGES]
        for entry in entries:
            suffix = entry.suffix.lower()
            if entry.is_dir() or suffix in IMAGES:
                continue
            if suffix in PARTIAL:
                items.append(_item(source, entry.name, None, entry.stat().st_size, [], "baixando", roms_root, images, []))
                continue
            if suffix in ARCHIVES:
                try:
                    members = archive_members(entry, run)
                except (ValueError, OSError, _subprocess.SubprocessError):
                    items.append(_item(source, entry.name, None, entry.stat().st_size, [], "ilegível", roms_root, images, []))
                    continue
                # Faixas de um .cue entram com ele (lê só o .cue, pequeno); patches e textos ficam de fora.
                tracks = set()
                for cue, size in members:
                    if cue.lower().endswith(".cue") and size <= _bundles.MAX_TEXT:
                        text = run(["7z", "x", "-so", "-spd", str(entry), cue], capture_output=True, timeout=120).stdout
                        try:
                            tracks |= {Path(r).name.lower() for r in _bundles.references(text.decode("utf-8", "replace"), ".cue")}
                        except ValueError:
                            pass
                found = False
                for member, size in members:
                    ext = Path(member).suffix.lower().lstrip(".")
                    if Path(member).name.lower() in tracks:
                        continue
                    candidates = ext_index.get(ext, [])
                    if candidates:
                        found = True
                        items.append(_item(source, entry.name, member, size, candidates, "pronto", roms_root, images,
                                           [Path(member).stem, entry.stem]))
                if not found:
                    items.append(_item(source, entry.name, None, entry.stat().st_size, [], "sem ROM reconhecida", roms_root, images, []))
                continue
            candidates = ext_index.get(suffix.lstrip("."), [])
            if candidates or source == "organizar":
                items.append(_item(source, entry.name, None, entry.stat().st_size, candidates,
                                   "pronto" if candidates else "extensão não reconhecida", roms_root, images, [entry.stem]))
    return items


def _trash(path: Path, run=_subprocess.run, fallback: Path | None = None):
    """Lixeira do sistema (recuperável); sem `gio`, move para `fallback`."""
    if run(["gio", "trash", str(path)], capture_output=True).returncode == 0:
        return
    if fallback is None:
        raise OSError(f"não foi possível mandar {path.name} para a lixeira")
    fallback.mkdir(parents=True, exist_ok=True)
    _shutil.move(str(path), str(fallback / path.name))


def place(files: list, dest_dir: Path, trash) -> list:
    """Coloca os arquivos com nome limpo em dest_dir, sobrescrevendo o que tiver o mesmo nome
    (o antigo vai para a lixeira). Um .cue é reescrito para os nomes novos das faixas."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    renamed = {f.name: clean_name(f.name) for f in files}
    placed = []
    for f in files:
        target = dest_dir / renamed[f.name]
        if f.suffix.lower() == ".cue":
            text = f.read_text(encoding="utf-8", errors="replace")
            for old, new in renamed.items():
                text = text.replace(f'"{old}"', f'"{new}"')
            f.write_text(text, encoding="utf-8")
        if target.exists():
            trash(target)
        _shutil.move(str(f), str(target))
        placed.append(target)
    return placed


def organize(roms_root: Path, sources: dict, item_id: str, code: str, trash, run=_subprocess.run) -> dict:
    """Move um item (arquivo solto ou ROM de dentro de um compactado) para roms_root/<code>.
    Devolve {"files": [destinos], "rom": arquivo principal, "label": nome sem extensão}."""
    source, _, rest = item_id.partition("/")
    name, _, member = rest.partition("::")
    folder = sources.get(source)
    if folder is None or "/" in name or name.startswith("."):
        raise ValueError("item desconhecido")
    src = folder / name
    if not src.is_file():
        raise LookupError("o item não está mais na pasta; atualize a lista")
    if src.suffix.lower() in PARTIAL:
        raise ValueError("download ainda em andamento")
    with _tempfile.TemporaryDirectory(prefix="pyretro-organizar-", dir=str(Path.home() / ".cache")) as tmp:
        tmpdir = Path(tmp)
        if member:
            wanted = [member]
            if member.lower().endswith(".cue"):
                listed = {Path(m).name: m for m, _ in archive_members(src, run)}
                run(["7z", "e", "-y", f"-o{tmpdir}", "-spd", str(src), member], capture_output=True, timeout=600)
                refs = _bundles.references((tmpdir / Path(member).name).read_text(encoding="utf-8", errors="replace"), ".cue")
                wanted += [listed[r] for r in refs if r in listed]
            result = run(["7z", "e", "-y", f"-o{tmpdir}", "-spd", str(src), *wanted], capture_output=True, timeout=1800)
            if result.returncode != 0:
                raise ValueError("falha ao extrair do arquivo compactado")
            files = [tmpdir / Path(m).name for m in dict.fromkeys(wanted)]
        else:
            files = [src]
            if src.suffix.lower() == ".cue":
                files += [folder / r for r in _bundles.references(src.read_text(encoding="utf-8", errors="replace"), ".cue") if (folder / r).is_file()]
        placed = place(files, roms_root / code, trash)
    return {"files": [str(p) for p in placed], "rom": str(placed[0]), "label": placed[0].stem}
