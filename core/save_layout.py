"""Migração de saves/states do RetroArch da pasta achatada para uma por sistema.

Com `sort_savefiles_by_content_enable`/`sort_savestates_by_content_enable`, o
RetroArch grava em `<raiz>/<pasta da ROM>/`. As ROMs ficam em `ROMs/<código>/`
(PC) e `Jogos/<código>/` (celular), então a pasta nova é o código do sistema e é
a mesma nos dois lados.

O sistema de cada arquivo vem da ROM com o mesmo nome (`rom_rename.is_save_of`).
Fica onde está, e aparece no relatório: nome sem ROM, nome em 2+ sistemas
(precisa decisão manual) e destino já existente (nunca sobrescreve). Pastas
"Backup" ficam intactas. Pastas que o próprio core cria (FBNeo: `fbneo/`) vão
para dentro da pasta do sistema.

Uso (simula por padrão; `--aplicar` move de verdade, só no PC):
    python3 -m core.save_layout [--aplicar]
    python3 -m core.save_layout --celular   # imprime o plano do celular via adb
"""
import argparse
import subprocess
import tomllib
from pathlib import Path, PurePosixPath

from core import rom_rename

KEEP_DIRS = {"Backup"}
CORE_DIRS = {"fbneo": "ARCADE"}


def rom_labels(roms_root: Path, codes) -> dict:
    labels = {}
    for code in codes:
        folder = Path(roms_root) / code
        if folder.is_dir():
            labels[code] = {p.stem if p.is_file() else p.name for p in folder.iterdir()}
    return labels


def plan(entries, labels: dict, codes) -> dict:
    """`entries`: [(nome, é_pasta, [arquivos internos relativos])] da raiz.
    Devolve {"moves": [(origem, destino)], "skipped": [(nome, motivo)]}, caminhos
    relativos à raiz."""
    moves, skipped = [], []
    taken = set()
    codes = set(codes)
    for name, is_dir, inner in entries:
        if is_dir:
            if name in KEEP_DIRS or name in codes:
                continue
            code = CORE_DIRS.get(name)
            if not code:
                skipped.append((name + "/", "pasta desconhecida"))
                continue
            for rel in inner:
                moves.append((f"{name}/{rel}", f"{code}/{name}/{rel}"))
            continue
        owners = sorted({code for code, names in labels.items() for label in names if rom_rename.is_save_of(name, label)})
        if not owners:
            skipped.append((name, "nenhuma ROM com esse nome"))
        elif len(owners) > 1:
            skipped.append((name, "nome existe em " + ", ".join(owners) + "; escolher à mão"))
        else:
            moves.append((name, f"{owners[0]}/{name}"))
    for src, dst in moves:
        if dst in taken:
            raise ValueError(f"dois arquivos iriam para {dst}")
        taken.add(dst)
    return {"moves": moves, "skipped": skipped}


def local_entries(root: Path):
    out = []
    for p in sorted(Path(root).iterdir()):
        inner = [str(f.relative_to(p)) for f in sorted(p.rglob("*")) if f.is_file()] if p.is_dir() else []
        out.append((p.name, p.is_dir(), inner))
    return out


def apply_local(root: Path, moves) -> list:
    root = Path(root)
    for src, dst in moves:  # confere tudo antes de mexer em qualquer arquivo
        if not (root / src).is_file():
            raise FileNotFoundError(root / src)
        if (root / dst).exists():
            raise FileExistsError(root / dst)
    done = []
    for src, dst in moves:
        (root / dst).parent.mkdir(parents=True, exist_ok=True)
        (root / src).rename(root / dst)
        done.append(dst)
    for src, _ in moves:  # pastas de core que ficaram vazias (fbneo/)
        parent = (root / src).parent
        if parent != root and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
    return done


def adb_entries(remote_root: str):
    listing = subprocess.run(["adb", "shell", f"cd '{remote_root}' && find . -type f"], capture_output=True, text=True, check=True).stdout
    tops = {}
    for line in listing.splitlines():
        parts = PurePosixPath(line.strip()).parts[1:]
        if not parts:
            continue
        if len(parts) == 1:
            tops.setdefault(parts[0], (False, []))
        else:
            tops.setdefault(parts[0], (True, []))[1].append("/".join(parts[1:]))
    return [(name, is_dir, inner) for name, (is_dir, inner) in sorted(tops.items())]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    parser.add_argument("--celular", action="store_true")
    args = parser.parse_args()
    cfg = tomllib.load(open(Path(__file__).resolve().parents[1] / "config.toml", "rb"))
    codes = list(cfg["systems"])
    labels = rom_labels(Path(cfg["pc"]["roms_root"]).expanduser(), codes)
    roots = ([(cfg["android"]["saves_root"], "saves"), (cfg["android"]["states_root"], "states")] if args.celular else
             [(Path(cfg["pc"]["saves_root"]).expanduser(), "saves"), (Path(cfg["pc"]["states_root"]).expanduser(), "states")])
    for root, kind in roots:
        result = plan(adb_entries(root) if args.celular else local_entries(root), labels, codes)
        print(f"== {kind}: {root}")
        for src, dst in result["moves"]:
            print(f"   mover   {src}  ->  {dst}")
        for name, why in result["skipped"]:
            print(f"   manter  {name}  ({why})")
        if args.aplicar and not args.celular and result["moves"]:
            print("   movidos:", len(apply_local(root, result["moves"])))


if __name__ == "__main__":
    main()
