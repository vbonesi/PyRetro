"""
Mapeamento serial -> nome de jogo pra PS1/PS2, usado pela tela de Saves
(ver core/memcard.py e docs/memory_card_editor.md). Os slots/pastas
dentro de um memory card real são nomeados pelo serial do disco (ex:
pasta "BASLUS-21672" no PS2, slot "BASCUS-9424400000000" no PS1), não
pelo nome do jogo - sem esse cruzamento a tela só mostraria códigos
ilegíveis.

Fonte: os DATs de redump em libretro/libretro-database
(metadat/redump/Sony - PlayStation{,  2}.dat), que já trazem
"serial" no nível do jogo (não só por ROM/track). Escolhido em vez de
uma base própria porque já é a mesma fonte de dados curada que o
projeto usa pra .cue/nomeação (libretro), evitando outra dependência.
Confirmado manualmente contra saves reais do usuário (Crash Bandicoot
- Warped/SCUS-94244, Gran Turismo 2/SCUS-94455, Guitar Hero III/
SLUS-21672, Need for Speed Underground 2/SLUS-21065, entre outros).

Cacheia em cache/serials_index.json (baixa de novo só se não existir
ou com force=True) - os DATs são ~80k linhas cada, não vale reparsear
toda hora.
"""
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache"
INDEX_PATH = CACHE_DIR / "serials_index.json"

DAT_URLS = {
    "PS1": "https://raw.githubusercontent.com/libretro/libretro-database/master/metadat/redump/Sony%20-%20PlayStation.dat",
    "PS2": "https://raw.githubusercontent.com/libretro/libretro-database/master/metadat/redump/Sony%20-%20PlayStation%202.dat",
}

_GAME_BLOCK_RE = re.compile(
    r'name\s+"(?P<name>[^"]+)"\s*\n\s*region\s+"[^"]*"\s*\n\s*serial\s+"(?P<serial>[^"]+)"',
)

# Slots/pastas de memory card codificam o serial junto com o código de
# região da Sony ("BA"/"BI"/"BE" pra América/Japão/Europa) e, no caso
# do PS1, um sufixo de save colado direto sem separador. Normaliza pra
# bater com o formato "XXXX-NNNNN" usado nos DATs.
_SLOT_SERIAL_RE = re.compile(r"^B[AIE]([A-Z]{4})-?(\d{3,5})")


def normalize_slot_serial(raw: str) -> str | None:
    """"BASCUS-9424400000000" -> "SCUS-94244"; "BASLUS-21672" ->
    "SLUS-21672". Retorna None se não bater com o padrão esperado."""
    m = _SLOT_SERIAL_RE.match(raw)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}"


def _parse_dat(text: str) -> dict:
    out = {}
    for m in _GAME_BLOCK_RE.finditer(text):
        out.setdefault(m.group("serial"), m.group("name"))
    return out


def build_index(force: bool = False) -> dict:
    """{"PS1": {serial: nome}, "PS2": {serial: nome}} - baixa e parseia
    os DATs de redump na primeira vez, depois só lê o cache."""
    if INDEX_PATH.exists() and not force:
        return json.loads(INDEX_PATH.read_text())

    index = {}
    for console, url in DAT_URLS.items():
        req = urllib.request.Request(url, headers={"User-Agent": "PyRetro"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                text = resp.read().decode("utf-8", errors="replace")
        except urllib.error.URLError:
            index[console] = {}
            continue
        index[console] = _parse_dat(text)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index))
    return index


def lookup(console: str, raw_slot_name: str, index: dict) -> str | None:
    """Resolve o nome do jogo pra um nome de slot/pasta cru do memory
    card, ou None se o serial não bater com nenhum jogo conhecido."""
    serial = normalize_slot_serial(raw_slot_name)
    if not serial:
        return None
    return index.get(console, {}).get(serial)
