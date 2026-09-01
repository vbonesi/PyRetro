"""
Fonte de capas alternativa: LaunchBox Games Database, usada como fallback
DEPOIS do libretro-thumbnails (core/covers.py) - só entra em ação pros
itens que já ficaram registrados como "no_match" lá.

Fonte pública, sem necessidade de conta/API key:
    https://gamesdb.launchbox-app.com/Metadata.zip  (~106MB, "Games Database"
    baixado diariamente por eles - Metadata.xml tem ~185k jogos e ~1.3M
    imagens de todas as plataformas que já existiram)
    https://images.launchbox-app.com/<FileName>  (imagem em si, confirmado
    funcionando via teste manual em 31/07)

O Metadata.xml sozinho tem ~500MB descompactado - grande demais pra carregar
inteiro na memória ou reprocessar toda hora. build_index() faz streaming
(xml.etree.ElementTree.iterparse, ~40s por passe) UMA VEZ e salva um índice
filtrado (só as plataformas que interessam, só imagens tipo "Box - Front")
em cache/launchbox_index.json - bem menor, carrega instantâneo depois.

Mapeamento de plataforma (código do config.toml -> nome usado pelo
LaunchBox nos registros <Game>, confirmado em 31/07 direto no XML):
"""
import json
import re
import subprocess
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

METADATA_URL = "https://gamesdb.launchbox-app.com/Metadata.zip"
IMAGE_BASE_URL = "https://images.launchbox-app.com/"
CACHE_DIR = Path(__file__).parent.parent / "cache"
METADATA_ZIP = CACHE_DIR / "launchbox_metadata.zip"
METADATA_XML = CACHE_DIR / "launchbox_metadata" / "Metadata.xml"
INDEX_PATH = CACHE_DIR / "launchbox_index.json"

PLATFORM_MAP = {
    "FC": "Nintendo Entertainment System",
    "SFC": "Super Nintendo Entertainment System",
    "GB": "Nintendo Game Boy",
    "GBC": "Nintendo Game Boy Color",
    "GBA": "Nintendo Game Boy Advance",
    "N64": "Nintendo 64",
    "NDS": "Nintendo DS",
    "MD": "Sega Genesis",
    "SMS": "Sega Master System",
    "GG": "Sega Game Gear",
    "PCE": "NEC TurboGrafx-16",
    "PCECD": "NEC TurboGrafx-CD",
    "PS": "Sony Playstation",
    "ARCADE": "Arcade",
    # Sistemas pesados (28/08) - mesma motivação do SYSTEM_MAP do
    # ScreenScraper: a busca de capa deles só tinha libretro-thumbnails
    # + SteamGridDB. Nome tem que bater EXATO com o campo <Platform> do
    # Metadata.xml (ver build_index) - conferido pela contagem do índice
    # depois do rebuild, nome errado daria 0 jogos.
    "PS2": "Sony Playstation 2",
    "NGC": "Nintendo GameCube",
    "WII": "Nintendo Wii",
    "PSP": "Sony PSP",
    "3DS": "Nintendo 3DS",
}

REGION_PRIORITY = ["North America", "United States", "World", "Europe"]
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10}

_TAG_RE = re.compile(
    r"\((usa|europe|japan|world|en|fr|de|es|it|nl|pt|rev\s*\d+|beta|proto"
    r"|virtual console|sample|disc\s*\d+|disk\s*\d+|track\s*\d+)[^)]*\)",
    re.IGNORECASE,
)
_NONALNUM_RE = re.compile(r"[^a-z0-9]")


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = _TAG_RE.sub("", s)
    s = _NONALNUM_RE.sub("", s)
    return s




def _download_metadata() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["curl", "-sL", "--max-time", "120", "-o", str(METADATA_ZIP), METADATA_URL],
        check=True,
    )
    subprocess.run(
        ["unzip", "-o", "-q", str(METADATA_ZIP), "Metadata.xml", "-d", str(METADATA_XML.parent)],
        check=True,
    )


# Tradução do gênero (LaunchBox só tem em inglês, ao contrário do
# ScreenScraper que já vem em pt nativo - ver core/screenscraper.
# _genero_pt). Cobre os ~28 valores mais comuns do Metadata.xml
# (conferido em 31/08: soma 99%+ das 187mil entradas com gênero
# preenchido). Jogo com mais de um gênero (separado por ";") usa só o
# PRIMEIRO - mesmo critério de "um gênero só" que a Biblioteca já usa.
# Valor sem tradução mapeada aqui fica em inglês mesmo (melhor que
# perder o dado).
MAPA_GENERO_EN_PT = {
    "Action": "Ação", "Adventure": "Aventura", "Shooter": "Tiro",
    "Platform": "Plataforma", "Puzzle": "Puzzle", "Role-Playing": "RPG",
    "Strategy": "Estratégia", "Sports": "Esporte", "Racing": "Corrida",
    "Education": "Educação", "Fighting": "Luta", "Board Game": "Jogo de Tabuleiro",
    "Construction and Management Simulation": "Simulação",
    "Visual Novel": "Visual Novel", "Casino": "Cassino", "Horror": "Terror",
    "Compilation": "Coletânea", "Life Simulation": "Simulação",
    "Beat 'em Up": "Luta", "Pinball": "Pinball", "Music": "Música",
    "Flight Simulator": "Simulação", "Quiz": "Quiz",
    "Vehicle Simulation": "Simulação", "Sandbox": "Sandbox", "Party": "Festa",
    "Stealth": "Furtividade", "MMO": "MMO", "Card Game": "Card Game",
    "Simulation": "Simulação",
}


def traduzir_genero(genero_en: str | None) -> str | None:
    if not genero_en:
        return None
    primeiro = genero_en.split(";")[0].strip()
    return MAPA_GENERO_EN_PT.get(primeiro, primeiro)


def build_index(force: bool = False) -> dict:
    """Faz o streaming parse do Metadata.xml (três passes: Game duas
    vezes - nome/gênero e depois GameImage) e monta {plataforma_config:
    {nome_normalizado: [filename, nome_original, genero_en]}}. Cacheia
    em INDEX_PATH - só reprocessa se force=True ou não existir.

    Gênero (31/08) entra pra TODA plataforma querida, inclusive
    "Windows" (jogos de PC - usado só pelo preenchimento de gênero da
    Biblioteca, `find_cover` continua sem cobertura de PC de propósito,
    capa de Steam/Epic/GOG já vem de outra fonte) - por isso o critério
    de "tem gênero" é mais solto que o de "tem capa" (`best`, que exige
    ter achado imagem Box-Front): um jogo pode ter gênero sem ter capa
    catalogada, e vice-versa."""
    if INDEX_PATH.exists() and not force:
        return json.loads(INDEX_PATH.read_text())

    if not METADATA_XML.exists() or force:
        _download_metadata()

    wanted_platforms = set(PLATFORM_MAP.values()) | {"Windows"}

    # passe 1: DatabaseID -> (nome_normalizado, nome_original, plataforma_lb, genero_en)
    games: dict[str, tuple[str, str, str, str | None]] = {}
    for event, elem in ET.iterparse(METADATA_XML, events=("end",)):
        if elem.tag == "Game":
            plat = elem.findtext("Platform")
            if plat in wanted_platforms:
                dbid = elem.findtext("DatabaseID")
                name = elem.findtext("Name")
                if dbid and name:
                    games[dbid] = (normalize(name), name, plat, elem.findtext("Genres"))
            elem.clear()

    # passe 2: pra cada DatabaseID relevante, pega a melhor imagem "Box - Front"
    # (prioriza regiao North America > United States > World > Europe > qualquer)
    best: dict[str, tuple[int, str]] = {}  # dbid -> (prioridade, filename)
    for event, elem in ET.iterparse(METADATA_XML, events=("end",)):
        if elem.tag == "GameImage":
            dbid = elem.findtext("DatabaseID")
            if dbid in games and elem.findtext("Type") == "Box - Front":
                region = elem.findtext("Region") or ""
                prio = REGION_PRIORITY.index(region) if region in REGION_PRIORITY else len(REGION_PRIORITY)
                filename = elem.findtext("FileName")
                if dbid not in best or prio < best[dbid][0]:
                    best[dbid] = (prio, filename)
            elem.clear()

    # index[code][nome_normalizado] = [filename_ou_null, nome_original, genero_en_ou_null]
    index: dict = {code: {} for code in (set(PLATFORM_MAP) | {"PC"})}
    code_by_platform = {v: k for k, v in PLATFORM_MAP.items()}
    code_by_platform["Windows"] = "PC"
    for dbid, (norm_name, orig_name, plat, genero_en) in games.items():
        code = code_by_platform[plat]
        filename = best[dbid][1] if dbid in best else None
        index[code][norm_name] = [filename, orig_name, genero_en]

    INDEX_PATH.write_text(json.dumps(index))
    return index


def find_genero(code: str, label: str, index: dict) -> str | None:
    """Gênero (já traduzido) pro jogo `label` dentro do sistema `code`
    (ou "PC" pra jogo de Biblioteca Steam/Epic/GOG/etc) - mesmo match
    EXATO de `find_cover`, sem o fallback por prefixo (gênero errado por
    semelhança de nome é pior que não preencher)."""
    entry = index.get(code, {}).get(normalize(label))
    return traduzir_genero(entry[2]) if entry else None


_WORD_RE = re.compile(r"[a-z0-9]+")


def _words(s: str) -> list:
    return _WORD_RE.findall(s.lower())


def find_cover(code: str, label: str, index: dict) -> str | None:
    """Retorna o FileName da imagem no LaunchBox, ou None.

    Exato primeiro. Se não achar, tenta por PREFIXO de palavras - comum
    o arquivo local não ter o subtítulo que o LaunchBox guarda por
    extenso (ex: local "Zool" vs LaunchBox "Zool: Ninja of the 'Nth'
    Dimension"). A trava de segurança: as primeiras N palavras do
    candidato (N = número de palavras do label) têm que ser IDÊNTICAS
    às do label, E a palavra seguinte (se houver) não pode ser um
    número/numeral romano sozinho - senão "Contra" casaria com
    "Contra III" (a palavra extra "iii" logo depois do prefixo é
    exatamente o tipo de vazamento de sequência que isso bloqueia)."""
    sysidx = index.get(code, {})

    k = normalize(label)
    if k in sysidx and sysidx[k][0]:
        return sysidx[k][0]

    label_words = _words(label)
    if not label_words:
        return None
    n = len(label_words)

    for norm_name, entry in sysidx.items():
        filename, orig_name = entry[0], entry[1]
        if not filename:
            continue  # entrada só de gênero (31/08), sem imagem catalogada
        cand_words = _words(orig_name)
        if len(cand_words) <= n or cand_words[:n] != label_words:
            continue
        next_word = cand_words[n]
        if next_word.isdigit() or next_word in ROMAN:
            continue  # "Contra" não pode casar com "Contra III"
        return filename
    return None


def download_cover(filename: str, dest: Path) -> bool:
    """dest é sempre o caminho final em .png - RetroArch só exibe
    thumbnail nesse formato (confirmado em 01/08/2026). Baixa num
    temporário e SEMPRE passa pelo `convert` do ImageMagick antes de
    gravar em dest, mesmo quando a extensão declarada no filename do
    LaunchBox já é ".png" - achado em 02/08: confiar nessa extensão
    deixou capas reais da coleção com bytes JPEG dentro de um arquivo
    .png (o metadado do LaunchBox não é garantia do conteúdo real).
    `convert` detecta o formato pelo conteúdo, não pelo nome -
    idempotente e barato pra um PNG de verdade."""
    src_ext = Path(filename).suffix or ".jpg"
    tmp = dest.with_suffix(src_ext + ".tmp")
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "20", "-o", str(tmp), "-w", "%{http_code}", IMAGE_BASE_URL + filename],
        capture_output=True, text=True,
    )
    if not (r.stdout.strip() == "200" and tmp.exists() and tmp.stat().st_size > 1000):
        tmp.unlink(missing_ok=True)
        return False

    conv = subprocess.run(["convert", str(tmp), str(dest)], capture_output=True, text=True)
    tmp.unlink(missing_ok=True)
    return conv.returncode == 0 and dest.exists() and dest.stat().st_size > 1000


def process_system_fallback(code: str, capas_folder: str, capas_root: Path, registry: dict, index: dict,
                             apply: bool, on_progress=None) -> int:
    """Segunda passada, só nos itens que core.covers.process_system já
    marcou como no_match no registry. Usado tanto pela CLI (retrosync.py
    fetch-covers-fallback) quanto pela GUI - mesma lógica, sem duplicar.
    Retorna quantos achou (baixados ou, em modo simulação, encontrados)."""
    capas_dir = capas_root / capas_folder / "Named_Boxarts"
    if not capas_dir.is_dir():
        return 0

    reg_sys = registry.setdefault(code, {})
    no_match_labels = sorted(k for k, v in reg_sys.items() if v.get("status") == "no_match")
    found = 0
    total = len(no_match_labels)

    for i, label in enumerate(no_match_labels, 1):
        filename = find_cover(code, label, index)
        if not filename:
            if on_progress:
                on_progress(label, "no_match", i, total)
            continue
        if not apply:
            found += 1
            if on_progress:
                on_progress(label, "found", i, total)
            continue
        dest = capas_dir / (label + ".png")
        if download_cover(filename, dest):
            old_jpg = capas_dir / (label + ".jpg")
            if old_jpg.exists():
                old_jpg.unlink()
            reg_sys[label] = {"status": "replaced_exact", "matched": filename, "source": "launchbox"}
            found += 1
            if on_progress:
                on_progress(label, "downloaded", i, total)
        elif on_progress:
            on_progress(label, "download_failed", i, total)

    return found
