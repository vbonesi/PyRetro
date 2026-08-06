"""
Busca e substituição de capas via libretro-thumbnails.

Regra central, aprendida com um incidente real: fuzzy match NUNCA é
aplicado automaticamente. Só entra na pasta o que bateu exato (depois
de normalizar tags de região/revisão). Fuzzy vira uma lista pra
revisão humana - correspondência de sequência (ex: "Dragon Quest" vs
"Dragon Quest II") pode ter similaridade > 90% e ainda assim ser um
jogo errado, então dígitos/numerais romanos finais são comparados à
parte e bloqueiam o match se divergirem.

Nunca apaga uma capa existente por falta de ROM correspondente - o
usuário mantém mais capas do que roms de propósito (sincroniza sob
demanda).
"""
import base64
import difflib
import json
import re
import subprocess
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TREE_CACHE_DIR = Path("/tmp/lt_trees")
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10}

# PS1 e Dreamcast saíram da biblioteca de capas (os standalones DuckStation/
# Flycast baixam capa sozinhos agora - ver docs/capas_sem_correspondencia.md).
# Continuam no config.toml normalmente pra quando ROMs/Saves existirem na
# GUI - essa exclusão é só da tela de capas / sync de capas, não do projeto
# como um todo. Definido aqui (não em gui/server.py) porque core/sync.py
# também precisa dele e core não deveria importar de gui.
COVERS_EXCLUDED = {"SDC", "PS"}

_TAG_RE = re.compile(
    r"\((usa|europe|japan|world|en|fr|de|es|it|nl|pt|rev\s*\d+|beta|proto"
    r"|virtual console|sample|disc\s*\d+|disk\s*\d+|track\s*\d+)[^)]*\)",
    re.IGNORECASE,
)
_BRACKET_RE = re.compile(r"\[[^\]]*\]")
_ARTICLE_RE = re.compile(r"\b(the|a|an|of|and|de|da|do|le|la)\b")
_NONALNUM_RE = re.compile(r"[^a-z0-9]")


def _strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def normalize(s: str, loose: bool = False) -> str:
    """loose=True também remove QUALQUER parêntese (pega códigos tipo
    "(NGM-007)(NGH-007)" que a lista de tags conhecidas não cobre)."""
    s = _strip_accents(s).lower()
    if loose:
        s = re.sub(r"\([^)]*\)", "", s)
    else:
        s = _TAG_RE.sub("", s)
    s = _BRACKET_RE.sub("", s)
    s = _ARTICLE_RE.sub("", s)
    s = _NONALNUM_RE.sub("", s)
    return s


def trailing_sequence_marker(label: str):
    """Extrai o "número de sequência" no final de um título (dígitos
    ou numeral romano), pra impedir que "Dragon Quest" combine com
    "Dragon Quest II" só por similaridade textual."""
    core = re.sub(r"\s*\([^)]*\)\s*$", "", label).strip()
    m = re.search(r"(\d+|[ivx]+)$", core, re.IGNORECASE)
    if not m:
        return None
    tok = m.group(1).lower()
    if tok.isdigit():
        return tok
    return str(ROMAN.get(tok, tok))


def load_tree(repo: str) -> list:
    """Retorna a lista de nomes de arquivo REAIS (sem extensão)
    disponíveis no repo - cada entrada é exatamente o que existe no
    servidor, pronta pra baixar."""
    tree_path = TREE_CACHE_DIR / f"{repo}.json"
    if not tree_path.exists():
        TREE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        url = f"https://api.github.com/repos/libretro-thumbnails/{repo}/git/trees/master?recursive=1"
        req = urllib.request.Request(url, headers={"User-Agent": "PyRetro"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            tree_path.write_bytes(resp.read())

    data = json.loads(tree_path.read_text())
    names = []
    for entry in data.get("tree", []):
        path = entry.get("path", "")
        if path.startswith("Named_Boxarts/") and path.endswith(".png"):
            names.append(path[len("Named_Boxarts/"):-4])
    return names


def build_index(names: list, loose: bool = False) -> dict:
    """Indexa cada nome real pela sua forma normalizada - e, quando o
    nome combina "Titulo A _ Titulo B" (comum no Neo Geo, ingles e
    japones juntos), indexa CADA PEDAÇO separadamente também, mas
    sempre apontando pro nome de arquivo REAL (combinado), nunca pro
    pedaço isolado (que não existe como arquivo no servidor)."""
    idx = {}
    for n in names:
        idx.setdefault(normalize(n, loose=loose), []).append(n)
        if " _ " in n:
            for part in n.split(" _ "):
                part = part.strip()
                idx.setdefault(normalize(part, loose=loose), []).append(n)
    return idx


def pick_best(candidates: list) -> str:
    for pref in ("(USA)", "(USA, Europe)", "(World)", "(Europe)", "(Japan)"):
        for c in candidates:
            if pref in c and not any(bad in c for bad in ("Beta", "Proto", "Sample")):
                return c
    for c in candidates:
        if not any(bad in c for bad in ("Beta", "Proto", "Sample")):
            return c
    return candidates[0]


def load_romname_dat(url: str, cache_name: str) -> dict:
    """Baixa (e cacheia) um .dat estilo ClrMamePro do libretro-database
    e retorna {nome_curto_da_rom: nome_completo_do_jogo}. Usado pro
    Arcade, onde o arquivo local se chama tipo "bjourney" e o jogo de
    verdade é "Blue's Journey / Raguy" - resolver isso ANTES de tentar
    casar contra o libretro-thumbnails evita fuzzy match perigoso
    comparando um código curto contra título comprido (foi assim que
    "bjourney" virou "Journey" e "karnovr" virou "Karnov" - ambos
    errados, achados por revisão manual)."""
    dat_path = TREE_CACHE_DIR / f"{cache_name}.dat"
    if not dat_path.exists():
        TREE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "PyRetro"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dat_path.write_bytes(resp.read())
    content = dat_path.read_text(encoding="utf-8", errors="replace")
    games = re.findall(r'game \(\s*name "([^"]+)".*?rom \( name (\S+?)\.zip', content, re.DOTALL)
    return {rom.lower(): name for name, rom in games}


def _try_match(name: str, exact_idx: dict, loose_idx: dict, norm_keys: list):
    """Tenta casar UM nome (exato -> loose -> fuzzy). Não sabe nada
    sobre DAT de romname, só faz a comparação normal."""
    k = normalize(name)
    if k in exact_idx:
        return pick_best(exact_idx[k]), "exact"

    k_loose = normalize(name, loose=True)
    if k_loose in loose_idx:
        return pick_best(loose_idx[k_loose]), "exact"

    close = difflib.get_close_matches(k, norm_keys, n=3, cutoff=0.90)
    label_seq = trailing_sequence_marker(name)
    for cand_key in close:
        cand_names = exact_idx.get(cand_key) or []
        if not cand_names:
            continue
        cand_name = cand_names[0]
        cand_seq = trailing_sequence_marker(cand_name)
        if label_seq != cand_seq:
            continue  # "Dragon Quest" != "Dragon Quest II" mesmo com >90% de similaridade
        return pick_best(cand_names), "fuzzy"
    return None, None


def _clean_dat_name(real_name: str) -> str:
    """"Puzzled / Joy Joy Kid (NGM-021 ~ NGH-021)" -> "Puzzled" - pega só o
    título principal. Precisa de espaço nos dois lados da barra - "/" sem
    espaço aparece dentro de datas ("1994/09/19") e sufixos ("Vehicle-001/II"),
    cortar nesses casos quebra o nome no meio (bug achado com dariusg/mslug2)."""
    primary = re.split(r"\s+/\s+", real_name)[0]
    return re.sub(r"\s*\([^)]*\)\s*$", "", primary).strip()


def arcade_display_name(label: str, romname_dat: dict) -> str | None:
    """Nome de exibição pro Arcade - o label/arquivo real continua sendo o
    nome curto do romset (ex: "mslug2"), isso aqui é só pra GUI mostrar
    "Metal Slug 2" na tela em vez do código. Puramente cosmético - nunca
    usado pra rename/apagar/renomear ROM (ver core/rom_rename.py, que
    sempre opera no label curto de verdade)."""
    real_name = romname_dat.get(label.lower())
    return _clean_dat_name(real_name) if real_name else None


def find_match(label: str, exact_idx: dict, loose_idx: dict, norm_keys: list, romname_dat: dict | None = None):
    """Retorna (nome_remoto, tipo) onde tipo é 'exact' ou 'fuzzy'.

    Se romname_dat for passado e o label bater com um nome curto de
    rom conhecido (ex: Arcade), tenta casar pelo nome COMPLETO
    resolvido primeiro - é bem mais confiável que comparar o código
    curto direto contra o índice de capas."""
    if romname_dat:
        real_name = romname_dat.get(label.lower())
        if real_name:
            primary = _clean_dat_name(real_name)
            remote, kind = _try_match(primary, exact_idx, loose_idx, norm_keys)
            if remote:
                return remote, kind

    return _try_match(label, exact_idx, loose_idx, norm_keys)


class RateLimited(Exception):
    """A API do GitHub recusou por cota (403/429) - não é a mesma coisa
    que "capa não existe". Ver process_system: isso NUNCA vira no_match,
    fica sem registrar pra tentar de novo na próxima rodada. Já aconteceu
    duas vezes de eu confundir os dois e precisar limpar o registro na mão."""


def _download_via_api(repo: str, remote_name: str) -> bytes | None:
    """Fallback pro cache do raw.githubusercontent.com às vezes servir
    uma resposta velha/quebrada (HTTP 200 com poucos bytes) pra um
    arquivo que existe normalmente no repo. A API do GitHub busca o
    blob direto (base64), infraestrutura diferente, sem esse cache.

    Levanta RateLimited se for cota (não confundir com 404 = arquivo
    realmente não existe nesse nome)."""
    path = urllib.parse.quote(f"Named_Boxarts/{remote_name}.png")
    url = f"https://api.github.com/repos/libretro-thumbnails/{repo}/contents/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "PyRetro", "Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise RateLimited from e
        return None
    except urllib.error.URLError:
        return None
    content = data.get("content")
    if not content:
        return None
    return base64.b64decode(content)


ROMNAME_DATS = {
    "ARCADE": (
        "https://raw.githubusercontent.com/libretro/libretro-database/master/"
        "metadat/fbneo-split/FBNeo%20-%20Arcade%20Games.dat",
        "fbneo",
    ),
}


def process_system(code: str, capas_folder: str, repo: str, capas_root: Path, registry: dict, apply: bool,
                    on_progress=None) -> dict:
    """Varre uma pasta de capas local, tenta casar cada capa existente
    (que ainda não está no registry) contra o repo remoto. Exato é
    baixado (se apply=True); fuzzy só entra no relatório.

    on_progress, se passado, é chamado a cada item processado como
    on_progress(label, status) - usado pela GUI pra mostrar progresso
    ao vivo, opcional pra não quebrar quem chama sem isso (a CLI)."""
    capas_dir = capas_root / capas_folder / "Named_Boxarts"
    result = {"exact": 0, "fuzzy": [], "no_match": 0, "cached": 0, "rate_limited": 0}
    if not capas_dir.is_dir():
        return result

    names = load_tree(repo)
    exact_idx = build_index(names, loose=False)
    loose_idx = build_index(names, loose=True)
    norm_keys = list(exact_idx.keys())

    romname_dat = None
    if code in ROMNAME_DATS:
        dat_url, dat_cache_name = ROMNAME_DATS[code]
        romname_dat = load_romname_dat(dat_url, dat_cache_name)

    reg_sys = registry.setdefault(code, {})
    base_url = f"https://raw.githubusercontent.com/libretro-thumbnails/{repo}/master/Named_Boxarts/"

    existing = sorted({p.stem for p in capas_dir.iterdir() if p.suffix.lower() in (".png", ".jpg")})

    total = len(existing)
    for i, label in enumerate(existing, 1):
        if label in reg_sys:
            result["cached"] += 1
            if on_progress:
                on_progress(label, "cached", i, total)
            continue

        remote, kind = find_match(label, exact_idx, loose_idx, norm_keys, romname_dat)

        if remote is None:
            reg_sys[label] = {"status": "no_match"}
            result["no_match"] += 1
            if on_progress:
                on_progress(label, "no_match", i, total)
            continue

        if kind == "fuzzy":
            result["fuzzy"].append((label, remote))
            if on_progress:
                on_progress(label, "fuzzy", i, total)
            continue  # não baixa, não registra - fica pendente pra próxima rodada até humano decidir

        if not apply:
            result["exact"] += 1
            if on_progress:
                on_progress(label, "exact", i, total)
            continue

        url = base_url + urllib.parse.quote(remote + ".png")
        dest = capas_dir / (label + ".png")
        tmp = dest.with_suffix(".png.tmp")
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "20", "-o", str(tmp), "-w", "%{http_code}", url],
            capture_output=True, text=True,
        )
        ok = r.stdout.strip() == "200" and tmp.exists() and tmp.stat().st_size > 1000

        if not ok:
            tmp.unlink(missing_ok=True)
            try:
                data = _download_via_api(repo, remote)
            except RateLimited:
                # cota da API acabou - não é "sem_match", é "não tentado
                # ainda". Não registra (fica pendente pra próxima rodada)
                # e para a varredura desse sistema aqui, sem gastar mais
                # chamada à toa nos itens restantes.
                result["rate_limited"] += 1
                break
            if data and len(data) > 1000:
                tmp.write_bytes(data)
                ok = True

        if ok:
            tmp.replace(dest)
            jpg = capas_dir / (label + ".jpg")
            if jpg.exists():
                jpg.unlink()
            reg_sys[label] = {"status": "replaced_exact", "matched": remote}
            result["exact"] += 1
            if on_progress:
                on_progress(label, "downloaded", i, total)
        else:
            tmp.unlink(missing_ok=True)
            reg_sys[label] = {"status": "no_match"}
            result["no_match"] += 1
            if on_progress:
                on_progress(label, "no_match", i, total)

    return result


def convert_jpg_to_png(capas_dir: Path, apply: bool = False) -> list:
    """RetroArch só exibe thumbnail em PNG - .jpg na pasta Named_Boxarts
    fica invisível pro menu do RetroArch mesmo com o nome certo, mesmo
    que apareça normal em qualquer visualizador (inclusive aqui na GUI,
    que não faz essa distinção). Usa o `convert` do ImageMagick (não é
    stdlib, mas já é uma dependência externa aceita no projeto, igual
    o curl).

    Só apaga o .jpg original depois de confirmar que o .png novo existe
    e tem tamanho razoável - nunca perde a capa se a conversão falhar.

    Se o .png já existe (achado em 01/08: acontecia quando um .jpg novo
    chegava - upload manual, fallback do LaunchBox - depois que essa
    função já tinha rodado uma vez), o .jpg velho é só lixo (RetroArch
    não olha pra ele de jeito nenhum com o .png presente) - apaga direto,
    sem converter de novo."""
    results = []
    if not capas_dir.is_dir():
        return results
    for jpg in sorted(list(capas_dir.glob("*.jpg")) + list(capas_dir.glob("*.jpeg"))):
        png = jpg.with_suffix(".png")
        if png.exists():
            if apply:
                jpg.unlink()
                results.append({"file": jpg.name, "status": "jpg_orfao_removido"})
            else:
                results.append({"file": jpg.name, "status": "jpg_orfao_seria_removido"})
            continue
        if not apply:
            results.append({"file": jpg.name, "status": "seria_convertido"})
            continue
        r = subprocess.run(["convert", str(jpg), str(png)], capture_output=True, text=True)
        if r.returncode == 0 and png.exists() and png.stat().st_size > 1000:
            jpg.unlink()
            results.append({"file": jpg.name, "status": "convertido"})
        else:
            png.unlink(missing_ok=True)
            results.append({"file": jpg.name, "status": "falhou", "erro": r.stderr.strip()[:200]})
    return results


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def validate_png_content(capas_dir: Path, apply: bool = False) -> list:
    """Confere se cada `.png` em Named_Boxarts é PNG DE VERDADE (pelos
    primeiros bytes do arquivo, não pela extensão) - achado em 02/08:
    5 capas reais da coleção tinham bytes JPEG salvos com nome .png
    (vieram de curadoria manual antiga, ou de um upload/download que
    confiou na extensão declarada em vez do conteúdo - motivo pelo qual
    download_cover/download_selected_cover/o upload da GUI agora sempre
    passam por `convert`, independente da extensão declarada).
    RetroArch não mostra nada pra esses arquivos - fica com o ícone
    genérico de "sem capa" mesmo com o nome certo, sem erro visível.

    Com apply=True, corrige no lugar via `convert` (detecta o formato
    real e regrava como PNG de verdade, mesma imagem, só troca o
    container). Vale rodar esse comando de vez em quando, principalmente
    depois de uploads manuais."""
    results = []
    if not capas_dir.is_dir():
        return results
    for png in sorted(capas_dir.glob("*.png")):
        with open(png, "rb") as f:
            header = f.read(8)
        if header.startswith(PNG_MAGIC):
            continue
        if not apply:
            results.append({"file": png.name, "status": "seria_corrigido"})
            continue
        r = subprocess.run(["convert", str(png), str(png)], capture_output=True, text=True)
        if r.returncode == 0 and png.stat().st_size > 1000:
            with open(png, "rb") as f:
                ok = f.read(8).startswith(PNG_MAGIC)
            results.append({"file": png.name, "status": "corrigido" if ok else "falhou"})
        else:
            results.append({"file": png.name, "status": "falhou", "erro": r.stderr.strip()[:200]})
    return results
