"""Caminho inverso do download de ROM pesada: dumps de Switch (NSP/NSZ/XCI/XCZ) que estão em
Downloads viram `<drive_roms_root>/NSW/<Jogo>/` no Google Drive, com nome limpo, cadastro na
Biblioteca (capa e gênero). Só PC: depende de rclone e da pasta de downloads local.

O nome dos arquivos dentro da pasta é mantido (carregam title-id e versão, que é o que separa
base, update e DLC); só a pasta do jogo recebe o nome limpo. A origem só vai para a lixeira
depois de conferida no Drive (`rclone check`)."""
import re
import subprocess
import tempfile
from pathlib import Path

from core import covers as covers_mod
from core import heavy_roms as heavy_mod
from core import library as library_mod
from core import sanitize as sanitize_mod
from core import screenscraper as screenscraper_mod

EXTS = (".nsp", ".nsz", ".xci", ".xcz")
PARCIAIS = (".part", ".crdownload", ".aria2", ".!qb", ".tmp")
PLATAFORMA = "Nintendo Switch"
CODIGO = "NSW"


def nome_do_jogo(nome_bruto: str) -> str:
    """Nome limpo para a pasta do jogo: sem extensão de dump, tags entre colchetes, anotação de
    tamanho e caracteres que o Drive/SO não aceitam."""
    base = library_mod.nomes_dentro_da_colecao([nome_bruto])
    nome = sanitize_mod.sanitize_name(base[0] if base else nome_bruto)
    return re.sub(r"\s+", " ", nome).strip(" .")


def _dumps(entry: Path) -> list:
    if entry.is_file():
        return [entry] if entry.suffix.lower() in EXTS else []
    return sorted(f for f in entry.rglob("*") if f.is_file() and f.suffix.lower() in EXTS)


def _baixando(entry: Path) -> bool:
    if entry.is_file():
        return entry.suffix.lower() in PARCIAIS
    return any(f.suffix.lower() in PARCIAIS for f in entry.rglob("*") if f.is_file())


def scan(downloads: Path) -> list:
    """Itens de `downloads` (arquivo solto ou pasta) com algum dump de Switch."""
    itens = []
    if not downloads.is_dir():
        return itens
    for entry in sorted(downloads.iterdir()):
        if entry.name.startswith("."):
            continue
        files = _dumps(entry)
        if not files:
            continue
        itens.append({
            "entry": entry.name,
            "nome": nome_do_jogo(entry.name),
            "files": [{"name": f.name, "size": f.stat().st_size} for f in files],
            "size": sum(f.stat().st_size for f in files),
            "baixando": _baixando(entry),
        })
    return itens


def _run(args, run, timeout):
    return run(args, capture_output=True, text=True, timeout=timeout)


def _enviar(files: list, destino: str, run, emit) -> None:
    """Copia cada arquivo e confere no Drive pelo hash; qualquer divergência interrompe."""
    for i, f in enumerate(files, 1):
        emit({"type": "progress", "status": f"enviando {i}/{len(files)}: {f.name}"})
        r = _run(["rclone", "copyto", str(f), f"{destino}/{f.name}"], run, 7200)
        if r.returncode != 0:
            raise OSError(f"falha ao enviar '{f.name}': {r.stderr.strip()[-200:]}")
        with tempfile.TemporaryDirectory(prefix="pyretro-nsw-") as tmp:
            lista = Path(tmp) / "files.txt"
            lista.write_text(f.name + "\n", encoding="utf-8")  # --files-from é literal ([ ] não viram glob)
            c = _run(["rclone", "check", str(f.parent), destino, "--one-way", "--files-from", str(lista)], run, 7200)
        if c.returncode != 0:
            raise OSError(f"'{f.name}' não bateu com a cópia no Drive; a origem foi mantida")


def registrar(library: dict, nome: str, cfg: dict, genero: str | None = None) -> dict:
    """Cadastra o jogo (ou anota a fonte `switch` no que já existe), tenta capa e define o gênero:
    o informado, senão ScreenScraper. Devolve {"id", "capa", "genero"}; opera em `library`
    em memória (quem chama carrega e salva dentro da transação)."""
    library_mod.merge_owned(library, [{"nome": nome, "plataforma": PLATAFORMA, "fonte": "switch"}])
    chave = covers_mod.normalize(nome)
    game = next((g for g in library["games"]
                 if g["plataforma"] == PLATAFORMA and chave in {covers_mod.normalize(n) for n in [g["nome"], *g.get("nomes_alt", [])]}),
                None)
    if game is None:
        raise LookupError("jogo não encontrado na Biblioteca depois do cadastro")
    library_root = Path(cfg["pc"]["library_root"]).expanduser()
    api_key = cfg.get("steamgriddb", {}).get("api_key")
    if not game.get("capa"):
        try:  # só este jogo: a lista passada tem só ele, o registro é o mesmo objeto
            library_mod.fetch_covers({"games": [game]}, library_root / "capas", api_key, cfg=cfg)
        except Exception:
            pass
    if genero:
        game["genero"] = genero
    elif not game.get("genero"):
        try:
            achado = screenscraper_mod.buscar_genero(CODIGO, nome, cfg)
        except Exception:
            achado = None
        if achado:
            from core import generos as generos_mod
            game["genero"] = generos_mod._normalizar(achado)
    return {"id": game["id"], "capa": game.get("capa"), "genero": game.get("genero")}


def upload(downloads: Path, entry_name: str, nome: str, cfg: dict, trash, library_update,
           genero: str | None = None, run=subprocess.run, emit=lambda e: None) -> dict:
    """Sobe `downloads/entry_name` para `<drive>/NSW/<nome>/`, cadastra e manda a origem para a
    lixeira. `library_update(fn)` roda `fn(library)` com a biblioteca carregada, dentro da
    transação de quem chama, e a salva. Falha antes da conferência não apaga nada."""
    if "/" in entry_name or entry_name.startswith(".") or entry_name in ("", ".."):
        raise ValueError("item inválido")
    entry = downloads / entry_name
    if not entry.exists():
        raise LookupError("o item não está mais em Downloads; atualize a lista")
    if _baixando(entry):
        raise ValueError("download ainda em andamento")
    nome = nome_do_jogo(nome)
    if not nome:
        raise ValueError("nome vazio")
    files = _dumps(entry)
    if not files:
        raise ValueError("nenhum dump de Switch (NSP/NSZ/XCI/XCZ) neste item")
    if len({f.name.casefold() for f in files}) != len(files):
        raise ValueError("dois arquivos com o mesmo nome; nada foi enviado")
    rc = heavy_mod._rclone_cfg(cfg)
    destino = f"{rc['remote']}:{rc['drive_roms_root']}/{CODIGO}/{nome}"
    _enviar(files, destino, run, emit)
    emit({"type": "progress", "status": "cadastrando na Biblioteca"})
    resultado = {}

    def aplicar(library):
        resultado.update(registrar(library, nome, cfg, genero=genero))

    library_update(aplicar)
    trash(entry)
    return {"pasta": nome, "arquivos": len(files), **resultado}
