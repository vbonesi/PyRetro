"""
Fonte de capas ScreenScraper.fr - BLOQUEADA por enquanto, ver abaixo.

A API tem dois níveis de credencial: a conta pessoal do usuário
(ssid/sspassword, já configurada em config.toml [screenscraper]) e uma
credencial de "desenvolvedor" (devid/devpassword) que identifica o
PyRetro como aplicação - essa precisa ser pedida no fórum do
ScreenScraper, não é self-service.

Em 31/07 os placeholders devid=xxx&devpassword=yyy pareciam funcionar
contra jeuInfos.php e systemesListe.php (testado direto). Em 01/08,
retestando pra construir esse módulo, jeuInfos.php e jeuRecherche.php
(os dois endpoints que realmente importam - busca e info de jogo)
passaram a recusar esse placeholder:

    "Erreur de login : Vérifier vos identifiants développeur !" (HTTP 403)

só systemesListe.php (usado abaixo pra montar o SYSTEM_MAP) continua
aceitando. Ou seja: dá pra descobrir o mapeamento de sistemas, mas NÃO
dá pra buscar/baixar capa de jogo nenhuma sem devid/devpassword de
verdade. search_game/download_cover ficam propositalmente não
implementadas (levantam NotImplementedError) até isso ser resolvido -
nada de fingir que funciona com um placeholder que a própria API já
rejeitou uma vez.

Próximo passo pra desbloquear: pedir credencial de desenvolvedor no
fórum do ScreenScraper (https://www.screenscraper.fr, seção
Contribuer/Développeurs) usando a conta "bonis" já configurada.

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


def _creds(cfg: dict) -> dict:
    ss = cfg.get("screenscraper", {})
    return {
        "devid": ss.get("dev_id") or "",
        "devpassword": ss.get("dev_password") or "",
        "softname": ss.get("softname") or "PyRetro",
        "ssid": ss.get("member_id") or "",
        "sspassword": ss.get("member_password") or "",
    }


def search_game(code: str, query: str, cfg: dict) -> list:
    creds = _creds(cfg)
    if not creds["devid"] or not creds["devpassword"]:
        raise NotImplementedError(
            "ScreenScraper precisa de credencial de desenvolvedor real "
            "(devid/devpassword) - o placeholder xxx/yyy foi testado em "
            "01/08 e a API recusou pra busca de jogo (jeuRecherche.php). "
            "Peça a credencial no fórum do ScreenScraper e preencha "
            "config.toml [screenscraper] antes de usar esta função."
        )
    raise NotImplementedError("busca ainda não implementada - ver bloqueio acima")


def download_cover(*args, **kwargs) -> bool:
    raise NotImplementedError(
        "download ainda não implementado - depende de search_game, "
        "que está bloqueada por falta de devid/devpassword real"
    )
