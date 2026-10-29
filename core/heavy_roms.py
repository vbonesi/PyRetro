"""
Gestão de ROMs dos consoles "pesados" (PS, PS2, GameCube, Wii, PSP,
3DS) - configurados em config.toml [heavy_systems]. Diferente de
[systems] (sempre sincronizado com o celular via Google Drive), esses
ficam só no PC até serem enviados sob demanda. Nintendo Switch fica de
fora de propósito - a gestão de ROM dele é feita por fora do PyRetro.
Saturn (SS) e Dreamcast (SDC) passaram por aqui até 24/08 - voltaram a
ser sistema leve normal (só [systems], sync automático) a pedido do
usuário, ver docs/changelog.md.

Um "item" aqui é qualquer entrada de primeiro nível dentro de
roms_root/<CODE>/ - normalmente um arquivo (.iso, .3ds, etc), mas o
suporte a pasta inteira como um item só fica pra formatos que usam
pasta por jogo (base + updates/DLC separados).

PS usa .cue + .bin separado (achado em 02/08: .cue não está sozinho na
pasta - "Front Mission 3.cue" tem "Front Mission 3.bin" do lado; o
caso multi-track com vários ".bin" tipo "Sonic Adventure (Track 1).bin"
era do Dreamcast, que não passa mais por este módulo - ver acima).
Mandar só o .cue sem os .bin quebra o jogo no celular - list_local
soma o tamanho dos sidecars no item, e send_to_phone manda todos
juntos.

Visão do Google Drive (via `rclone`, achado em 04/08 - sugestão do
usuário): o Drive tem MUITO mais jogos do que o que já foi baixado pro
PC (ex: dezenas de PS2 na nuvem contra só 3 localmente) - list_drive_
names mostra o catálogo completo sem precisar do celular conectado via
adb, e download_from_drive baixa sob demanda. No PC, o download NUNCA
vai direto pra roms_root/<CODE>/ (que é a própria pasta sincronizada
pelo Google Drive Desktop - escrever ali enquanto o rclone baixa
arriscaria os dois mexerem no mesmo arquivo ao mesmo tempo) - baixa
primeiro em staging_dir (config [rclone], padrão ~/Downloads) e só
depois move pro lugar certo, um rename local instantâneo."""
import json
import re
import os
import ctypes
import errno
import tempfile
import subprocess
from pathlib import Path

from core import adb as adb_mod
from core import file_lock as file_lock_mod
from core import play as play_mod

_TRACK_RE = re.compile(r"^(.+) \(Track \d+\)$")


def load_heavy_systems(cfg: dict) -> dict:
    return cfg.get("heavy_systems", {})


def _dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _stem_matches(candidate_stem: str, primary_stem: str) -> bool:
    if candidate_stem == primary_stem:
        return True
    m = _TRACK_RE.match(candidate_stem)
    return bool(m and m.group(1) == primary_stem)


def _sidecars(primary: Path, exts_lower: set) -> list:
    """Arquivos vizinhos que pertencem ao mesmo item (mesmo nome base,
    ou "<nome> (Track N)") mas cuja extensão NÃO é uma das "primárias"
    do sistema - isso evita confundir um formato alternativo do mesmo
    jogo (ex: .cue E .chd juntos) com um sidecar de verdade."""
    sidecars = []
    for sib in primary.parent.iterdir():
        if sib == primary or not sib.is_file():
            continue
        if sib.suffix.lower().lstrip(".") in exts_lower:
            continue
        if _stem_matches(sib.stem, primary.stem):
            sidecars.append(sib)
    return sidecars


def list_local(code: str, roms_root: Path, exts: list) -> list:
    """[{name, size, is_dir, sidecar_count}], ordenado por nome. `name`
    é o que send_to_phone espera receber pra identificar o item. `size`
    já inclui os sidecars (.bin etc) quando existirem."""
    sysdir = roms_root / code
    if not sysdir.is_dir():
        return []
    exts_lower = {e.lower().lstrip(".") for e in exts}
    items = []
    try:
        entries = sorted(sysdir.iterdir())
    except OSError:
        # pasta existe mas não é legível - achado real no Termux (modo
        # Android): algumas subpastas do armazenamento compartilhado
        # voltam PermissionError mesmo com a permissão de arquivos
        # concedida ao app. Sem isso derrubava a aba inteira de ROMs
        # Pesadas por causa de UM sistema sem acesso.
        return []
    for entry in entries:
        if entry.is_dir():
            items.append({"name": entry.name, "size": _dir_size(entry), "is_dir": True, "sidecar_count": 0})
        elif entry.is_file() and entry.suffix.lower().lstrip(".") in exts_lower:
            sidecars = _sidecars(entry, exts_lower)
            total = entry.stat().st_size + sum(s.stat().st_size for s in sidecars)
            items.append({"name": entry.name, "size": total, "is_dir": False, "sidecar_count": len(sidecars)})
    return items


def list_remote_names(code: str, jogos_root: str, serial: str | None) -> set:
    """Nomes (arquivo ou pasta) já presentes no celular pra esse
    sistema - uma chamada só via find, não uma por item. Retorna
    conjunto vazio (não levanta erro) se a pasta remota ainda não
    existir - é o caso normal na primeira vez."""
    remote_dir = f"{jogos_root.rstrip('/')}/{code}"
    try:
        out = adb_mod.shell(
            f"find {adb_mod.shquote(remote_dir)} -mindepth 1 -maxdepth 1 2>/dev/null",
            serial=serial,
        )
    except adb_mod.AdbError:
        return set()
    prefix = remote_dir + "/"
    names = set()
    for line in out.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            names.add(line[len(prefix):])
    return names


def send_to_phone(code: str, name: str, roms_root: Path, jogos_root: str, serial: str | None,
                   exts: list, overwrite: bool = False) -> tuple[bool, str]:
    """Manda UM item (arquivo ou pasta) pro celular via adb push, junto
    com os sidecars (.bin de .cue/.gdi) se houver. Nunca sobrescreve por
    padrão - confere se o item principal já existe lá antes. Retorna
    (ok, mensagem)."""
    local_path = roms_root / code / name
    if not local_path.exists():
        return False, "não encontrado no PC"

    remote_dir = f"{jogos_root.rstrip('/')}/{code}"
    remote_path = f"{remote_dir}/{name}"

    if not overwrite:
        try:
            out = adb_mod.shell(f"[ -e {adb_mod.shquote(remote_path)} ] && echo EXISTS", serial=serial)
        except adb_mod.AdbError:
            out = ""
        if "EXISTS" in out:
            return False, "já existe no celular (use overwrite pra sobrescrever)"

    adb_mod.run(["shell", "mkdir", "-p", remote_dir], serial=serial, timeout=15)

    to_send = [local_path]
    if local_path.is_file():
        exts_lower = {e.lower().lstrip(".") for e in exts}
        to_send += _sidecars(local_path, exts_lower)

    for src in to_send:
        ok = adb_mod.push(src, f"{remote_dir}/{src.name}", serial=serial, timeout=1800)
        if not ok:
            return False, f"falha ao enviar '{src.name}'" + (f" ({len(to_send)} arquivos no total)" if len(to_send) > 1 else "")

    plural = "s" if len(to_send) != 1 else ""
    return True, f"enviado ({len(to_send)} arquivo{plural})"


def _rclone_cfg(cfg: dict) -> dict:
    rc = cfg.get("rclone", {})
    return {
        "remote": rc.get("remote", "drive"),
        "drive_roms_root": rc.get("drive_roms_root", "Jogos/ROMs"),
        "staging_dir": rc.get("staging_dir", "~/Downloads"),
    }


def list_drive_items(code: str, cfg: dict) -> list:
    """[{name, size, is_dir}] presentes no Google Drive pra esse sistema
    via `rclone lsjson` - não depende de adb nem do celular conectado,
    só do rclone configurado (`rclone config`, remote definido em
    config.toml [rclone]). Retorna lista vazia (não levanta erro) se o
    rclone não estiver instalado/configurado, ou a pasta não existir no
    Drive ainda.

    Achado em 04/08: pastas com muitos itens (PS2 com 97) podem levar
    até ~1min pra listar via API do Drive - um timeout de 30s cortava
    isso no meio e devolvia lista vazia silenciosamente (parecia "nada
    no Drive" quando na verdade só estava demorando). Timeout mais
    generoso (90s)."""
    rc = _rclone_cfg(cfg)
    remote_path = f"{rc['remote']}:{rc['drive_roms_root']}/{code}"
    try:
        r = subprocess.run(
            ["rclone", "lsjson", remote_path],
            capture_output=True, text=True, timeout=90,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if r.returncode != 0:
        return []
    try:
        entries = json.loads(r.stdout)
    except ValueError:
        return []
    return [
        {"name": e["Name"], "size": max(e.get("Size", 0), 0), "is_dir": bool(e.get("IsDir"))}
        for e in entries
    ]


def downloadable_systems(cfg: dict) -> dict:
    """Sistemas que o PyRetro baixa do Drive sob demanda: pesados e leves (todos têm a mesma
    pasta `<drive_roms_root>/<código>/` e as extensões em `exts`)."""
    return {**cfg.get("systems", {}), **load_heavy_systems(cfg)}


def download_staging(cfg: dict) -> Path:
    """Pasta temporária dos downloads. Com `[storage] games_root` fica dentro dele (mesmo disco do
    destino, fora do Drive); senão usa `[rclone] staging_dir`, como antes."""
    games_root = (cfg.get("storage") or {}).get("games_root")
    if games_root:
        return Path(games_root).expanduser() / ".pyretro" / "staging"
    return Path(_rclone_cfg(cfg)["staging_dir"]).expanduser()


def download_from_drive(code: str, name: str, roms_root: Path, cfg: dict) -> tuple[bool, str]:
    """Baixa para staging exclusivo e publica somente arquivos completos.

    CUE/GDI/M3U incluem suas referências explícitas, inclusive quando o descritor
    já existe localmente mas faltam as faixas. Não substitui arquivos existentes.
    """
    try:
        if not isinstance(code, str) or code not in downloadable_systems(cfg):
            raise ValueError("sistema desconhecido")
        rel = play_mod.safe_relative(name)
        if len(rel.parts) != 1:
            raise ValueError("selecione um item do catálogo, sem subpastas")
        root = roms_root.expanduser() / code
        if not root.resolve().is_relative_to(roms_root.expanduser().resolve()):
            raise ValueError("pasta do sistema fora do acervo")
        with file_lock_mod.exclusive(root / ".download"):
            result = _download_item(code, name, root, cfg)
            if code == "ARCADE" and (result[0] or "já existe" in result[1]):
                _download_arcade_parents(code, name, root, cfg)
            return result
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def _download_arcade_parents(code, name, root, cfg):
    """Clones de fliperama não rodam sem o zip do pai: baixa os que faltam e existem no Drive. BIOS
    (neogeo, pgm…) fica em BIOS/RetroArch e não é tocada aqui."""
    from core import arcade
    needed = arcade.required_zips(name, arcade.load_dat(arcade.dat_dir(cfg)))
    have = {p.name for p in root.glob("*.zip")}
    for parent in needed:
        if parent in have:
            continue
        try:
            _download_item(code, parent, root, cfg)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass  # o pai pode ser uma BIOS que não está no Drive de ROMs


def _download_item(code, name, root, cfg):
    rc = _rclone_cfg(cfg)
    remote = f"{rc['remote']}:{rc['drive_roms_root']}/{code}"
    staging = download_staging(cfg)
    # Downloads não podem ser escritos dentro da árvore sincronizada.
    if staging.resolve().is_relative_to(root.parent.resolve()):
        raise ValueError("staging precisa ficar fora da pasta de ROMs")
    staging.mkdir(parents=True, exist_ok=True)
    dest = root / name
    if not dest.resolve().is_relative_to(root.resolve()):
        raise ValueError("destino fora da pasta do sistema")

    def run(args):
        result = subprocess.run(["rclone", *args], capture_output=True, text=True, timeout=3600)
        if result.returncode:
            raise ValueError("rclone falhou: " + result.stderr.strip()[:200])
        return result.stdout

    # --stat distingue arquivo de pasta; copy de uma pasta copia seu conteúdo.
    metadata = json.loads(run(["lsjson", remote + '/' + name, "--stat"]))
    is_dir = metadata.get("IsDir")
    if not isinstance(is_dir, bool):
        raise ValueError("tipo de item inválido no Drive")
    if dest.exists() and (is_dir or dest.suffix.lower() not in ('.cue', '.gdi', '.m3u')):
        return False, "já existe no PC"
    with tempfile.TemporaryDirectory(prefix="pyretro-rom-", dir=staging) as work:
        stage = Path(work)
        primary = stage / name
        if is_dir:
            run(["copy", remote + '/' + name, str(primary)])
            if not primary.is_dir() or not any(primary.rglob('*')):
                raise ValueError("download da pasta vazio ou incompleto")
            for path in primary.rglob('*'):
                if path.is_symlink():
                    raise ValueError("symlink inesperado no download")
                if path.suffix.lower() in ('.cue', '.gdi', '.m3u') and path.is_file():
                    play_mod.validate_bundle(primary, str(path.relative_to(primary)))
            root.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                return False, "destino surgiu durante o download; não foi substituído"
            # renameat2(RENAME_NOREPLACE), no Linux: até uma pasta vazia
            # que o Insync tenha criado no intervalo deve ser preservada.
            libc = ctypes.CDLL(None, use_errno=True)
            rename = getattr(libc, "renameat2", None)
            if rename is None:
                raise OSError(errno.ENOTSUP, "publicação segura de pastas indisponível")
            rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
            rename.restype = ctypes.c_int
            if rename(-100, os.fsencode(primary), -100, os.fsencode(dest), 1):
                error = ctypes.get_errno()
                raise OSError(error, os.strerror(error))
            return True, "baixado"

        pending = {}
        visited = set()
        def collect(relative, branch):
            relative = str(play_mod.safe_relative(relative))
            if relative in branch:
                raise ValueError("referência circular no conjunto de discos")
            if relative in visited:
                return
            if len(visited) >= 1000 or len(branch) >= 100:
                raise ValueError("conjunto de discos excessivamente grande")
            visited.add(relative)
            local = root / relative
            if not local.resolve().is_relative_to(root.resolve()):
                raise ValueError("arquivo associado fora da pasta do sistema")
            if local.exists():
                source = play_mod.checked_file(root, relative)
            else:
                source = stage / relative
                source.parent.mkdir(parents=True, exist_ok=True)
                run(["copyto", remote + '/' + relative, str(source)])
                play_mod.checked_file(stage, relative)
                pending[relative] = source
            for ref in play_mod.references(source):
                collect(str(Path(relative).parent / ref), branch | {relative})
        collect(name, set())
        if not pending:
            return False, "já existe no PC e os arquivos associados estão completos"
        # Faixas primeiro, descritores por último. link é atômico e recusa um
        # destino que tenha surgido após a validação, sem sobrescrevê-lo.
        for relative, source in sorted(pending.items(), key=lambda pair: pair[1].suffix.lower() in ('.cue', '.gdi', '.m3u')):
            final = root / relative
            final.parent.mkdir(parents=True, exist_ok=True)
            if not final.parent.resolve().is_relative_to(root.resolve()):
                raise ValueError("destino alterado durante o download")
            os.link(source, final)
        play_mod.validate_bundle(root, name)
        return True, "baixado (arquivos associados conferidos)"
