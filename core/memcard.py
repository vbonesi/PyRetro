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
    # Achado real em 05/08: os dois binários às vezes devolvem returncode
    # 0 MESMO quando imprimem uma linha "Error: ..." (ex: -in rejeitando
    # save duplicado, -pu com diretório já existente) - por isso não dá
    # pra confiar só no returncode, tem que checar a saída também.
    err_line = next((ln for ln in r.stdout.splitlines() if ln.strip().startswith("Error:")), None)
    if r.returncode != 0 or err_line:
        raise MemcardError(err_line or r.stderr.strip() or r.stdout.strip() or "falha desconhecida")
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


def delete_save(console: str, card_path: Path, item: dict) -> None:
    """Apaga um save do card. No PS1 é uma remoção de slot só; no PS2 a
    "pasta" do jogo não pode ser removida direto (achado em 05/08: o
    -rm de um diretório não-vazio falha com "-6") - precisa esvaziar
    (listar e remover cada arquivo dentro) antes de -rmdir."""
    if console == "PS1":
        _run(console, card_path, ["-rm", item["slot"]])
        return
    path = f"/{item['raw_name']}"
    out = _run(console, card_path, ["-ls", path])
    for line in out.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2 or parts[0] in (".", "..") or parts[0].startswith("--"):
            continue
        _run(console, card_path, ["-rm", f"{path}/{parts[0]}"])
    _run(console, card_path, ["-rmdir", path])


def import_save(console: str, card_path: Path, src_file: Path) -> None:
    """Injeta um arquivo de save (.MCS/.PSV/.PSX/.RAW/.PS1 no PS1,
    .PSU/.PSV no PS2) no card. Não dá pra saber o jogo/slot de destino
    sem abrir o binário do save - deixa a ferramenta decidir e tentar.

    Testado em 05/08: duplicar o MESMO jogo no card funciona
    normalmente (real - hardware de PS1 de verdade permite isso) -
    quem barrou numa primeira tentativa de teste foi falta de espaço
    livre CONTÍGUO (um save de 4 blocos não cabe se só sobra 1 slot
    livre), não duplicação. Por isso o erro traduzido aqui fala em
    espaço, não em "já existe esse jogo"."""
    ext = src_file.suffix.lower()
    if console == "PS1":
        if ext not in (".mcs", ".psv", ".psx", ".raw", ".ps1"):
            raise MemcardError(f"formato não suportado pro PS1: {ext}")
        try:
            _run(console, card_path, ["-in", str(src_file)])
        except MemcardError as e:
            raise MemcardError(
                f"não foi possível importar - provavelmente não há espaço livre "
                f"suficiente no card (detalhe: {e})"
            ) from e
    else:
        if ext not in (".psu", ".psv"):
            raise MemcardError(f"formato não suportado pro PS2: {ext}")
        flag = "-pu" if ext == ".psu" else "-pi"
        try:
            _run(console, card_path, [flag, str(src_file)])
        except MemcardError as e:
            raise MemcardError(
                f"não foi possível importar - provavelmente não há espaço livre "
                f"suficiente no card (detalhe: {e})"
            ) from e


def create_card(console: str, template_path: Path, dest_path: Path) -> None:
    """Cria um card novo, em branco, a partir de um card já existente e
    válido (template_path) usado só de molde.

    Achado real (22/08): --mc-format num arquivo inexistente, ou num
    arquivo já do tamanho certo mas zerado do zero, NÃO produz um card
    válido - os dois binários "salvam" um arquivo de 128 KB/8 MB mas
    sem o cabeçalho certo, e depois -i falha com "no ... Memory Card
    detected". Eles só reformatam em cima de algo que já reconhecem
    como card. Por isso sempre parte de um card configurado existente
    como molde (copia os bytes) e reformata a cópia - isso sim zera de
    verdade os saves (confirmado: Blocks Used 0 / Free 15 no PS1) sem
    precisar reimplementar o parser binário do formato."""
    if dest_path.exists():
        raise MemcardError("já existe um arquivo nesse caminho")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template_path, dest_path)
    try:
        _run(console, dest_path, ["--mc-format"])
    except MemcardError:
        dest_path.unlink(missing_ok=True)
        raise


def transfer_save(console: str, src_card: Path, dest_card: Path, item: dict, tmp_dir: Path) -> None:
    """Move (não copia) um save entre dois cards do MESMO console
    (formatos de PS1 e PS2 são incompatíveis entre si, não faz sentido
    cruzar) - exporta do card origem pro formato portável, injeta no
    destino e só então apaga a origem, pra nunca ficar sem nenhuma
    cópia se o import falhar no meio do caminho (se o import falhar, a
    exceção sobe e a origem não é tocada)."""
    exported = export_save(console, src_card, item, tmp_dir)
    try:
        import_save(console, dest_card, exported)
    finally:
        exported.unlink(missing_ok=True)
    delete_save(console, src_card, item)
