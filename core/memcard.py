"""
Editor de memory card PS1/PS2 - ver docs/memory_card_editor.md pra
pesquisa/decisão. Envelopa os binários `ps1vmc-tool`/`ps2vmc-tool`
(bucanero/ps2vmc-tool, GPLv3) via subprocess, mesma filosofia de
`curl`/`convert`/`adb`/`rclone` já usada no projeto - espera os dois
binários no PATH (baixar o release "ubuntu" em
https://github.com/bucanero/ps2vmc-tool/releases e colocar em
~/.local/bin, por exemplo).

Um memory card real (PS1 .mcd/.gme/PS2 .ps2/.bin) guarda os saves só
com o SERIAL do jogo (o slot/pasta se chama algo como
"BASCUS-9424400000000" no PS1 ou "BASLUS-21672" no PS2), nunca o nome
- por isso toda função aqui devolve o nome junto quando dá pra
resolver via core/serials.py (senão a tela ficaria uma lista de
códigos ilegíveis, que era exatamente o problema que motivou pedir
essa integração).

Testado em 05/08/2026 direto contra os cartões reais do usuário
(~/Drive/Jogos/Saves/PS1-DuckStation/memcards/ e
~/Drive/Jogos/Saves/PS2/memcards/): listagem batendo com os saves
reais (Crash Bandicoot - Warped, Gran Turismo 2, Driver, Jeremy
McGrath Supercross 2000, Yu-Gi-Oh! Forbidden Memories no PS1; Guitar
Hero III, Need for Speed Underground 2 no PS2) e exportação real
(-mcs/-x no PS1, -px no PS2) confirmada produzindo arquivo não-vazio.
"""
import re
import shutil
import subprocess
from pathlib import Path

from core import serials as serials_mod

TOOL_BIN = {"PS1": "ps1vmc-tool", "PS2": "ps2vmc-tool"}

_PS1_ROW_RE = re.compile(
    r"^\s*(?P<slot>\d+)\s*\|\s*(?P<name>.*?)\s*\|\s*<(?P<type>\w+)>\s*\|\s*(?P<size>\d+)\s*\|\s*(?P<prod>[A-Z0-9-]*)\s*\|\s*(?P<region>\S*)"
)


class MemcardError(Exception):
    pass


def tool_available(console: str) -> bool:
    return shutil.which(TOOL_BIN[console]) is not None


def _run(console: str, card_path: Path, args: list, timeout: int = 30) -> str:
    binname = TOOL_BIN.get(console)
    if not binname:
        raise MemcardError(f"console desconhecido: {console}")
    if not shutil.which(binname):
        raise MemcardError(
            f"'{binname}' não encontrado no PATH - baixe em "
            f"https://github.com/bucanero/ps2vmc-tool/releases e coloque em ~/.local/bin"
        )
    r = subprocess.run(
        [binname, str(card_path), *args], capture_output=True, text=True, timeout=timeout
    )
    if r.returncode != 0:
        raise MemcardError(r.stderr.strip() or r.stdout.strip() or "falha desconhecida")
    return r.stdout


def mc_info(console: str, card_path: Path) -> str:
    return _run(console, card_path, ["-i"])


def list_card(console: str, card_path: Path, serials_index: dict) -> list:
    """Lista o conteúdo do card, cruzando cada slot/pasta com o nome do
    jogo via core/serials.py. Formato de saída igual pros dois
    consoles: [{"slot", "raw_name", "serial", "name", "type", "size"}].
    "name" vem None quando o serial não bate com nenhum jogo conhecido
    (save homebrew, região não coberta pelo DAT de redump, etc)."""
    out = _run(console, card_path, ["-ls", "/"])
    items = []
    if console == "PS1":
        for line in out.splitlines():
            m = _PS1_ROW_RE.match(line)
            if not m or m.group("type") == "link" and not m.group("name").strip():
                continue
            raw_name = m.group("name").strip()
            if not raw_name:
                continue
            prod = m.group("prod").strip()
            serial = prod or serials_mod.normalize_slot_serial(raw_name)
            items.append({
                "slot": m.group("slot"), "raw_name": raw_name, "serial": serial,
                "name": serials_index.get("PS1", {}).get(serial) if serial else None,
                "type": m.group("type"), "size": int(m.group("size")),
            })
    else:
        for line in out.splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3 or parts[0] in (".", "..") or parts[0].startswith("--"):
                continue
            name = parts[0]
            type_ = parts[1].strip("<>")
            try:
                size = int(parts[2])
            except ValueError:
                continue
            serial = serials_mod.normalize_slot_serial(name)
            items.append({
                "slot": None, "raw_name": name, "serial": serial,
                "name": serials_index.get("PS2", {}).get(serial) if serial else None,
                "type": type_, "size": size,
            })
    return items


def export_save(console: str, card_path: Path, item: dict, dest_dir: Path) -> Path:
    """Exporta um save pro formato mais portável de cada console (PSU
    no PS2, MCS no PS1) dentro de dest_dir. Retorna o caminho final."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = (item.get("name") or item["raw_name"]).replace("/", "-")
    if console == "PS1":
        dest = dest_dir / f"{safe_name}.mcs"
        _run(console, card_path, ["-mcs", item["slot"], str(dest)])
    else:
        dest = dest_dir / f"{safe_name}.psu"
        _run(console, card_path, ["-px", item["raw_name"], str(dest)])
    return dest
