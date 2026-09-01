"""
Fonte de capas ScreenScraper.fr - terceira fonte, além de
libretro-thumbnails e LaunchBox. Credencial de desenvolvedor concedida
em 04/08/2026 (pedida no fórum deles), destravou jeuRecherche.php e
jeuInfos.php (os placeholders xxx/yyy tinham parado de funcionar pra
esses dois em 01/08 - ver docs/changelog.md).

IMPORTANTE - as URLs de mídia que a API devolve (campo "medias" de
cada jogo) já vêm com devid/devpassword/ssid/sspassword embutidos como
parâmetro de URL. Por isso essas URLs NUNCA são expostas direto pro
navegador (nem como "preview" na busca da GUI) - o servidor sempre
baixa a imagem por trás e serve só os bytes, através de um proxy
(/api/cover/ss_preview) e um cache em memória por processo
(gui/server.py _ss_media_cache) que guarda a URL real associada a um
id de busca, nunca grava isso em disco nem manda pro cliente.

SYSTEM_MAP: código do config.toml -> systemeid do ScreenScraper.
Montado cruzando noms.nom_launchbox do systemesListe.php contra
launchbox_mod.PLATFORM_MAP (mesmo texto na maioria dos casos - as duas
fontes usam nomenclatura do LaunchBox). Dois cuidados que já morderam
uma vez cada:
  - a comprehension ingênua {nom_launchbox: id} pega o ÚLTIMO id com
    aquele nome, não o primeiro - "Sega Genesis" aparece em id=1 (Mega
    Drive, certo) E id=203 ("Megadrive - Sonic 2 Hacks", uma
    sub-coleção de hack) - por isso é sempre por PRIMEIRA ocorrência.
  - PCECD tem nom_launchbox com texto levemente diferente do que está
    em launchbox_mod.PLATFORM_MAP ("NEC PC Engine-CD" vs "NEC
    TurboGrafx-CD") - cross-match automático não acha, entra como
    override manual abaixo.
  - ARCADE não tem um systemeid único (o ScreenScraper separa arcade
    por fabricante/placa - Cave, Irem, Capcom Classics, etc, dezenas de
    ids). id=75 ("Mame") é o bucket genérico certo pro nosso caso -
    confirmado via noms_commun incluindo "FBA-LibRetro"/"FBNeo" e
    nom_recalbox incluindo "fbneo", que é exatamente o núcleo/repo que
    o ARCADE do config.toml usa (FBNeo - Arcade Games).
"""
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SYSTEM_MAP = {
    "FC": 3,
    "SFC": 4,
    "GB": 9,
    "GBC": 10,
    "GBA": 12,
    "N64": 14,
    "NDS": 15,
    "MD": 1,
    "SMS": 2,
    "GG": 21,
    "PCE": 31,
    "PCECD": 114,   # override manual - nom_launchbox = "NEC PC Engine-CD"
    "PS": 57,
    "ARCADE": 75,   # bucket genérico "Mame" - ScreenScraper não tem 1 id por FBNeo
    # Sistemas pesados (28/08) - antes a busca de capa deles só tinha
    # libretro-thumbnails + SteamGridDB; o ScreenScraper cobre todos e
    # tem curadoria melhor (é a fonte preferida do usuário, ver
    # search_cover_candidates). Cada id foi CONFERIDO com uma busca
    # real contra a API antes de entrar aqui (PS2->Gran Turismo 4,
    # NGC->Metroid Prime, WII->Super Mario Galaxy, PSP->Daxter,
    # 3DS->Fire Emblem Awakening).
    "PS2": 58,
    "NGC": 13,
    "WII": 16,
    "PSP": 61,
    "3DS": 17,
    # Switch não é sistema de ROM do PyRetro (não roda via RetroArch,
    # ver core/library.read_switch_library) - entra aqui só como fonte
    # de CAPA pros jogos de Switch da Biblioteca, que são 57 dos que
    # ficaram sem capa depois de Steam+SteamGridDB. Id conferido contra
    # a API real (Astral Chain).
    "NSW": 225,
}

API_BASE = "https://api.screenscraper.fr/api2/"

# Ordem de preferência de região pra escolher UMA capa entre as várias
# que o ScreenScraper retorna por jogo (mesma ideia do REGION_PRIORITY
# em launchbox.py). "wor" é "World" quando existe.
_REGION_PRIORITY = ["us", "eu", "wor", "ss"]


def _creds(cfg: dict) -> dict:
    ss = cfg.get("screenscraper", {})
    return {
        "devid": ss.get("dev_id") or "",
        "devpassword": ss.get("dev_password") or "",
        "softname": ss.get("softname") or "PyRetro",
        "ssid": ss.get("member_id") or "",
        "sspassword": ss.get("member_password") or "",
    }


def _best_name(noms: list) -> str:
    if not noms:
        return "(sem nome)"
    by_region = {n.get("region"): n.get("text") for n in noms}
    for region in ("us", "eu", "wor", "ss"):
        if by_region.get(region):
            return by_region[region]
    return noms[0].get("text", "(sem nome)")


def _best_box_media(medias: list) -> str | None:
    """Escolhe UMA mídia "box-2D" entre as várias regiões disponíveis."""
    candidates = {m.get("region"): m.get("url") for m in medias if m.get("type") == "box-2D" and m.get("url")}
    for region in _REGION_PRIORITY:
        if candidates.get(region):
            return candidates[region]
    return next(iter(candidates.values()), None)


def _genero_pt(jeu: dict) -> str | None:
    """Gênero em português DIRETO da API - achado 31/08: o campo
    "genres" de cada jogo já vem com um "noms" multi-idioma que inclui
    "pt" nativo (ex: "Luta", "Plataforma", "Jogos de RPG"), sem precisar
    de nenhum mapeamento manual meu. Prefere o gênero com
    "principale"=="1" (a API marca qual é o principal quando o jogo tem
    mais de um, ex: Super Mario World tem "Plataforma" (principal) E
    "Plataforma / Corre e Pula" (mais específico, não-principal)) - cai
    pro primeiro que tiver tradução pt se nenhum for principal.
    Remove o prefixo "Jogos de " quando presente, pra bater com o
    vocabulário mais enxuto que a Biblioteca já usa ("RPG", não "Jogos
    de RPG")."""
    generos = jeu.get("genres") or []
    if not generos:
        return None

    def pt_de(g):
        return next((n["text"] for n in g.get("noms", []) if n.get("langue") == "pt"), None)

    escolhido = next((pt_de(g) for g in generos if g.get("principale") == "1" and pt_de(g)), None)
    if not escolhido:
        escolhido = next((pt_de(g) for g in generos if pt_de(g)), None)
    if escolhido and escolhido.lower().startswith("jogos de "):
        escolhido = escolhido[len("jogos de "):].strip()
    return escolhido or None


def buscar_genero(code: str, nome: str, cfg: dict) -> str | None:
    """Gênero (em português) pro jogo `nome` dentro do sistema `code`,
    ou None. Mesma regra de match EXATO (nome normalizado) que o resto
    do projeto usa pra capa - nunca aplica gênero de outro jogo por
    aproximação. Reaproveita search_game (já faz a chamada de rede),
    só que olhando "genres" em vez de "medias"."""
    from core import covers as covers_mod

    creds = _creds(cfg)
    if not creds["devid"] or not creds["devpassword"]:
        return None
    systeme_id = SYSTEM_MAP.get(code)
    if systeme_id is None:
        return None

    params = {**creds, "output": "json", "recherche": nome, "systemeid": systeme_id}
    url = API_BASE + "jeuRecherche.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "PyRetro"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except (OSError, ValueError):
        return None

    alvo = covers_mod.normalize(nome)
    for jeu in (data.get("response") or {}).get("jeux") or []:
        if covers_mod.normalize(_best_name(jeu.get("noms", []))) == alvo:
            genero = _genero_pt(jeu)
            if genero:
                return genero
    return None


def search_game(code: str, query: str, cfg: dict, limit: int = 20) -> list:
    """Busca jogos no ScreenScraper por nome, dentro do systemeid do
    código dado. Retorna [{"id", "name", "media_url"}] - media_url
    JAMAIS deve ser repassada pro cliente (tem senha embutida, ver
    docstring do módulo) - é pra uso só no backend."""
    creds = _creds(cfg)
    if not creds["devid"] or not creds["devpassword"]:
        raise NotImplementedError(
            "ScreenScraper precisa de credencial de desenvolvedor real "
            "(devid/devpassword) em config.toml [screenscraper]."
        )
    systeme_id = SYSTEM_MAP.get(code)
    if systeme_id is None:
        return []

    params = {**creds, "output": "json", "recherche": query, "systemeid": systeme_id}
    url = API_BASE + "jeuRecherche.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "PyRetro"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except (OSError, ValueError):
        # OSError cobre urllib.error.URLError (falha de conexão) E
        # socket.timeout/TimeoutError (timeout de leitura já com conexão
        # aberta) - achado real: a API do ScreenScraper às vezes aceita a
        # conexão mas demora mais que os 20s pra responder, e
        # socket.timeout NÃO é subclasse de URLError, então antes vazava
        # sem ser pego aqui e derrubava a request inteira sem resposta.
        return []

    jeux = (data.get("response") or {}).get("jeux") or []
    results = []
    for jeu in jeux[:limit]:
        media_url = _best_box_media(jeu.get("medias", []))
        if not media_url:
            continue
        results.append({
            "id": jeu.get("id"), "name": _best_name(jeu.get("noms", [])), "media_url": media_url,
        })
    return results


def fetch_media_bytes(media_url: str) -> bytes | None:
    """Baixa os bytes crus de uma media_url (já vem com credenciais
    embutidas pela própria API). Usado tanto pelo proxy de preview
    quanto pelo download final."""
    req = urllib.request.Request(media_url, headers={"User-Agent": "PyRetro"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except OSError:
        # ver comentário equivalente em search_game - OSError cobre
        # URLError e timeout de leitura (socket.timeout/TimeoutError).
        return None
    return data if len(data) > 500 else None


def download_cover(media_url: str, dest: Path) -> bool:
    """Baixa a capa e grava sempre como PNG de verdade - `convert`
    detecta o formato pelo conteúdo, nunca confia na extensão (mesma
    lição de 02/08, ver core/covers.py PNG_MAGIC)."""
    data = fetch_media_bytes(media_url)
    if not data:
        return False
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    conv = subprocess.run(["convert", str(tmp), str(dest)], capture_output=True, text=True)
    tmp.unlink(missing_ok=True)
    return conv.returncode == 0 and dest.exists() and dest.stat().st_size > 1000


def process_system_fallback(code: str, capas_folder: str, capas_root: Path, registry: dict, cfg: dict,
                             apply: bool, on_progress=None) -> int:
    """Segunda passada, só nos itens que core.covers.process_system já
    marcou como no_match no registry - mesmo papel que
    launchbox.process_system_fallback, botão "🔍 Buscar no
    ScreenScraper" na GUI. Usa o próprio label como termo de busca e
    pega o primeiro resultado (a API já ordena por relevância) - sem
    trava de prefixo como o LaunchBox porque aqui é busca textual da
    API, não índice local exato/prefixo."""
    capas_dir = capas_root / capas_folder / "Named_Boxarts"
    if not capas_dir.is_dir():
        return 0

    reg_sys = registry.setdefault(code, {})
    no_match_labels = sorted(k for k, v in reg_sys.items() if v.get("status") == "no_match")
    found = 0
    total = len(no_match_labels)

    for i, label in enumerate(no_match_labels, 1):
        results = search_game(code, label, cfg, limit=1)
        if not results:
            if on_progress:
                on_progress(label, "no_match", i, total)
            continue
        media_url = results[0]["media_url"]
        if not apply:
            found += 1
            if on_progress:
                on_progress(label, "found", i, total)
            continue
        dest = capas_dir / (label + ".png")
        if download_cover(media_url, dest):
            old_jpg = capas_dir / (label + ".jpg")
            if old_jpg.exists():
                old_jpg.unlink()
            reg_sys[label] = {"status": "replaced_exact", "matched": results[0]["name"], "source": "screenscraper"}
            found += 1
            if on_progress:
                on_progress(label, "downloaded", i, total)
        elif on_progress:
            on_progress(label, "download_failed", i, total)

    return found
