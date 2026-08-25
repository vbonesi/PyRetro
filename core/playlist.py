"""
Monta playlist (.lpl) do RetroArch a partir do que existe DE VERDADE em
roms_root/<CODE>/ (PC) ou jogos_root/<CODE>/ (Android, via adb find) -
usa [systems.<CODE>] do config.toml (capas/exts) pra saber o db_name
("<capas>.lpl", mesmo nome que o RetroArch usa de verdade) e quais
extensões contam como ROM principal (mesma lista que fetch-covers/
sanitize-names já usam - ignora sidecar tipo .bin de .cue/.gdi, BIOS
solto etc., porque a extensão deles não bate).

Sistemas "pesados" (heavy_systems) não sincronizam PC<->Android
sozinhos - achado em 24/08 ao configurar a primeira playlist de
sistema pesado (Saturn, na época - depois voltou a ser sistema leve
normal, ver docs/changelog.md): o mesmo código pode ter jogos
DIFERENTES em cada lado (ex: Saturn no PC tinha Daytona USA + Rabbit,
no celular tinha NiGHTS + Virtua Fighter 2 + Virtua Racing). A
playlist de cada plataforma reflete só o que aquela plataforma tem
local - por isso list_local_names/list_remote_names são funções
separadas em vez de uma lista única compartilhada. Isso vale pra
QUALQUER sistema, pesado ou não - só é mais visível em sistema pesado
porque o conteúdo dos dois lados diverge por design.

Cada item usa core_path/core_name "DETECT" e crc32 "00000000|crc" -
mesmo padrão que toda playlist de sistema em disco gerada pelo próprio
RetroArch já usa (conferido em "NEC - PC Engine CD - TurboGrafx-CD.lpl"
real). default_core_path/default_core_name ficam em branco de
propósito: não dá pra confirmar núcleo instalado no Android via adb
(RetroArch guarda os .so em storage privado do app, sem acesso sem
root - só config/playlists/thumbnails ficam em
/storage/emulated/0/RetroArch/, fora da sandbox) e no PC o núcleo pode
nem estar instalado ainda. DETECT por item já resolve sozinho assim que
o núcleo certo existir, sem precisar reescrever a playlist depois.
"""
import json
from pathlib import Path

from core import adb as adb_mod

PLAYLIST_VERSION = "1.5"


def _exts_lower(exts: list) -> set:
    return {e.lower().lstrip(".") for e in exts}


def list_local_names(code: str, roms_root: Path, exts: list) -> list:
    """Nomes de arquivo (só top-level, sem recursão) em roms_root/<CODE>/
    cuja extensão bate com [systems.<CODE>].exts. Ignora pasta (ex: BIOS
    solto tipo ROMs/SS/Saturn/) e qualquer sidecar (.bin de .cue/.gdi
    tem extensão diferente, não entra)."""
    sysdir = roms_root / code
    if not sysdir.is_dir():
        return []
    exts_lower = _exts_lower(exts)
    return sorted(
        e.name for e in sysdir.iterdir()
        if e.is_file() and e.suffix.lower().lstrip(".") in exts_lower
    )


def list_remote_names(code: str, jogos_root: str, exts: list, serial: str | None) -> list:
    """Mesma coisa que list_local_names, só que no celular via adb find
    (uma chamada só, mesmo padrão de heavy_roms.list_remote_names).
    Retorna lista vazia (não levanta erro) se a pasta remota ainda não
    existir."""
    remote_dir = f"{jogos_root.rstrip('/')}/{code}"
    exts_lower = _exts_lower(exts)
    try:
        out = adb_mod.shell(
            f"find {adb_mod.shquote(remote_dir)} -mindepth 1 -maxdepth 1 -type f 2>/dev/null",
            serial=serial,
        )
    except adb_mod.AdbError:
        return []
    prefix = remote_dir + "/"
    names = []
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith(prefix):
            continue
        name = line[len(prefix):]
        if name.rsplit(".", 1)[-1].lower() in exts_lower:
            names.append(name)
    return sorted(names)


def make_playlist(items_with_paths: list, scan_content_dir: str, exts: list, db_name: str) -> dict:
    """items_with_paths = [(caminho_completo, label), ...] - PC e
    Android montam o caminho completo do jeito certo pra cada lado
    (raiz local vs. remota) antes de chamar isso."""
    return {
        "version": PLAYLIST_VERSION,
        "default_core_path": "",
        "default_core_name": "",
        "label_display_mode": 0,
        "right_thumbnail_mode": 0,
        "left_thumbnail_mode": 0,
        "thumbnail_match_mode": 0,
        "sort_mode": 0,
        "scan_content_dir": scan_content_dir,
        "scan_file_exts": "|".join(_exts_lower(exts)),
        "scan_dat_file_path": "",
        "scan_search_recursively": True,
        "scan_search_archives": False,
        "scan_filter_dat_content": False,
        "scan_overwrite_playlist": False,
        "items": [
            {
                "path": path,
                "label": label,
                "core_path": "DETECT",
                "core_name": "DETECT",
                "crc32": "00000000|crc",
                "db_name": db_name,
            }
            for path, label in items_with_paths
        ],
    }


def push_playlist(playlist: dict, remote_path: str, serial: str | None, tmp_dir: Path) -> bool:
    """Escreve num arquivo temporário local e manda pro celular via adb
    push (RetroArch não expõe jeito de escrever playlist remota direto -
    o app precisa só encontrar o arquivo no lugar certo na próxima vez
    que abrir)."""
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_file = tmp_dir / Path(remote_path).name
    tmp_file.write_text(json.dumps(playlist, indent=1, ensure_ascii=False))
    remote_dir = remote_path.rsplit("/", 1)[0]
    adb_mod.run(["shell", "mkdir", "-p", remote_dir], serial=serial, timeout=15)
    return adb_mod.push(tmp_file, remote_path, serial=serial, timeout=60)
