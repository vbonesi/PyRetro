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
  - PCECD e NEOGEO têm nom_launchbox com texto levemente diferente do
    que está em launchbox_mod.PLATFORM_MAP ("NEC PC Engine-CD" vs "NEC
    TurboGrafx-CD"; "SNK Neo Geo" vs "SNK Neo Geo AES") - cross-match
    automático não acha, entram como override manual abaixo.
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
    "SS": 22,
    "SDC": 23,
    "PCE": 31,
    "PCECD": 114,   # override manual - nom_launchbox = "NEC PC Engine-CD"
    "PS": 57,
    "NEOGEO": 142,  # override manual - nom_launchbox = "SNK Neo Geo" (sem "AES")
    "NEOGEOCD": 70,
    "ARCADE": 75,   # bucket genérico "Mame" - ScreenScraper não tem 1 id por FBNeo
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
    except (urllib.error.URLError, ValueError):
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
    except urllib.error.URLError:
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
