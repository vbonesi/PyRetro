"""
Biblioteca de jogos "de fora" das ROMs - possuídos em lojas digitais
(Steam/GOG/Epic/Amazon/PSN/Xbox) + acompanhamento pessoal (iniciado/
finalizado/platinado/nota/tempo/observações), migrado da planilha do
Google Sheets que o usuário mantinha na mão. Sai de dentro de
`Drive/Jogos/` de propósito ([pc]/[android] `library_root` no
config.toml) - mesma pasta que o Google Drive Desktop já sincroniza
sozinho pra ROMs/Capas/Saves, então o celular recebe `library.json` de
graça, sem nenhum código de sync novo. O celular só LÊ esse arquivo -
nenhuma função daqui que fala com Heroic/Steam/etc faz sentido rodando
em modo Android (não tem Heroic instalado lá).

Um "jogo" é um registro só (ver `_blank_game`) - campos de
acompanhamento (nota, finalizado, etc) vêm da planilha importada;
`fontes` registra em quais lojas o jogo está confirmado como possuído
(ex: "heroic:epic"). Merge de fonte nova é sempre por nome normalizado
EXATO (`_normalize` - minúsculo, sem acento/pontuação) - quando bate,
entra como fonte a mais no registro existente; sem bater, vira registro novo;
nunca mescla por aproximação sozinho (mesmo cuidado que fetch-covers já
tem com fuzzy match: possíveis duplicatas só entram num relatório pra
revisão manual, ver `merge_owned`).
"""
import csv
import difflib
import http.client
import json
import re
import subprocess
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from core import covers as covers_mod


def _slug(nome: str, plataforma: str) -> str:
    base = unicodedata.normalize("NFKD", f"{nome} {plataforma}").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def _normalize(nome: str) -> str:
    base = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", base.lower()).strip()


def _or_none(v: str | None):
    v = (v or "").strip()
    return v or None


def _to_bool(v: str | None) -> bool:
    return (v or "").strip().upper() == "SIM"


def _to_float(v: str | None):
    v = (v or "").strip().replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


def _to_iso_date(v: str | None):
    v = (v or "").strip()
    if not v:
        return None
    try:
        return datetime.strptime(v, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


_TEMPO_RE = re.compile(r"^(\d+):(\d{2})(?::(\d{2}))?$")


def tempo_para_horas(valor: str | None) -> float:
    """`tempo` é texto livre digitado na tela ("31:40:00", HH:MM:SS) -
    converte pra horas (float) pra dar pra somar. Aceita também HH:MM
    sem segundos (achado 31/08 ao somar o campo pra estatística: 93 dos
    94 preenchidos eram HH:MM:SS exato, 1 só tinha HH:MM). Formato que
    não bate nenhum dos dois vira 0 - preferível a travar a soma inteira
    por um valor digitado errado."""
    if not valor:
        return 0.0
    m = _TEMPO_RE.match(valor.strip())
    if not m:
        return 0.0
    h, mi, s = m.group(1), m.group(2), m.group(3) or "0"
    return int(h) + int(mi) / 60 + int(s) / 3600


def _blank_game(nome: str, plataforma: str) -> dict:
    return {
        "id": _slug(nome, plataforma),
        "nome": nome,
        "plataforma": plataforma,
        "subgenero": None,
        "genero": None,
        "iniciado": False,
        "finalizado": False,
        "platinado": False,
        "nota": None,
        "savestate": False,
        "data_final": None,
        "tempo": None,
        "meta": None,
        "observacoes": None,
        "lancamento": None,
        "desenvolvedora": None,
        "capa": None,
        "fontes": [],
        # Nomes que este jogo JÁ TEVE (ver update_game) - a fonte
        # externa continua mandando o nome antigo, e o merge casa por
        # nome, então sem isso renomear pela tela faria o jogo voltar
        # como registro NOVO na próxima sincronização (achado do
        # usuário 28/08: "tem que manter de alguma maneira que o jogo
        # foi renomeado, para ele não aparecer de novo em novas
        # verificações").
        "nomes_alt": [],
        # Esconder da listagem sem apagar o registro (pedido do usuário
        # 28/08: jogo online tipo Black Desert, que está na conta mas
        # não faz sentido acompanhar). Nunca some do arquivo - mesmo
        # princípio de "nunca apaga nada sozinho" do resto do projeto.
        "oculto": False,
    }


def load_library(path: Path) -> dict:
    if not path.exists():
        return {"games": []}
    return json.loads(path.read_text())


def save_library(path: Path, library: dict) -> None:
    """Grava de forma ATÔMICA: escreve num temporário do lado e só
    então troca pelo arquivo final (`os.replace`, que é atômico no
    mesmo sistema de arquivos). Achado 28/08: com `write_text` direto,
    qualquer leitura que caísse no meio da escrita pegava um JSON pela
    metade - e isso é fácil de acontecer aqui, porque a GUI é
    multi-thread (ThreadingHTTPServer) e ainda por cima costuma ter job
    de fundo gravando (library-refresh, fetch-covers) enquanto o
    usuário mexe na tela pelo celular. O sintoma seria exatamente
    "cliquei em finalizado e não consigo mais acessar": o GET seguinte
    estoura no json.loads e a tela não carrega. Com a troca atômica,
    quem lê sempre vê a versão inteira - a antiga ou a nova, nunca um
    pedaço."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(library, indent=1, ensure_ascii=False))
    tmp.replace(path)


def import_sheet_csv(library: dict, csv_path: Path) -> dict:
    """Lê o CSV exportado do Google Sheets (Arquivo > Fazer download >
    CSV) e faz upsert em library["games"] pelo id (nome+plataforma) -
    rodar de novo com um CSV mais recente atualiza os campos de
    acompanhamento de quem já existe em vez de duplicar. Cabeçalho
    esperado: Nome do Jogo, Plataforma, Subgenero, Genero, Iniciado,
    Finalizado, Platinado, Nota, Savestate, Data Final, Tempo, Meta,
    Observações, Lançamento, Desenvolvedora ('Capa' é ignorada - a
    planilha usava =IMAGE() sobre busca do Bing, nunca uma capa de
    verdade; capa de verdade é buscada à parte, ver fetch_covers)."""
    by_id = {g["id"]: g for g in library["games"]}
    added, updated = 0, 0

    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            nome = (row.get("Nome do Jogo") or "").strip()
            if not nome:
                continue
            plataforma = (row.get("Plataforma") or "").strip()
            fields = {
                "nome": nome,
                "plataforma": plataforma,
                "subgenero": _or_none(row.get("Subgenero")),
                "genero": _or_none(row.get("Genero")),
                "iniciado": _to_bool(row.get("Iniciado")),
                "finalizado": _to_bool(row.get("Finalizado")),
                "platinado": _to_bool(row.get("Platinado")),
                "nota": _to_float(row.get("Nota")),
                "savestate": _to_bool(row.get("Savestate")),
                "data_final": _to_iso_date(row.get("Data Final")),
                "tempo": _or_none(row.get("Tempo")),
                "meta": _or_none(row.get("Meta")),
                "observacoes": _or_none(row.get("Observações")),
                "lancamento": _to_iso_date(row.get("Lançamento")),
                "desenvolvedora": _or_none(row.get("Desenvolvedora")),
            }
            game_id = _slug(nome, plataforma)
            if game_id in by_id:
                by_id[game_id].update(fields)
                updated += 1
            else:
                game = _blank_game(nome, plataforma)
                game.update(fields)
                library["games"].append(game)
                by_id[game_id] = game
                added += 1

    return {"added": added, "updated": updated}


_HEROIC_SOURCES = [
    ("legendary_library.json", "library", "Epic Games Store", "heroic:epic"),
    ("gog_library.json", "games", "GOG", "heroic:gog"),
    ("nile_library.json", "library", "Amazon Games", "heroic:amazon"),
]


def read_heroic_libraries(heroic_cfg: dict) -> list:
    """[{"nome", "plataforma", "fonte"}] de tudo que o Heroic Games
    Launcher já tem cacheado localmente pra Epic (legendary)/GOG
    (gogdl)/Amazon (nile) - sem nenhuma chamada de rede, só lê os 3
    JSON que o próprio Heroic mantém atualizado sozinho
    (store_cache/<loja>_library.json). Pula DLC/redistribuível
    (`install.is_dlc`, ex: "Galaxy Common Redistributables" da GOG)."""
    config_dir = Path(heroic_cfg.get("config_dir") or "~/.config/heroic").expanduser()
    cache_dir = config_dir / "store_cache"

    owned = []
    for filename, key, plataforma, fonte in _HEROIC_SOURCES:
        path = cache_dir / filename
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for g in data.get(key, []):
            if g.get("install", {}).get("is_dlc"):
                continue
            owned.append({"nome": g["title"], "plataforma": plataforma, "fonte": fonte})
    return owned


def read_steam_library(steam_cfg: dict) -> list:
    """[{"nome", "plataforma": "Steam", "fonte": "steam"}] via API Web
    oficial (IPlayerService/GetOwnedGames) - precisa de `api_key` +
    `steamid64` em [steam] no config.toml. Levanta ValueError se
    faltar alguma das duas (config incompleta) ou RuntimeError se a
    API responder sem 'games' (perfil com "Detalhes do jogo" fora de
    Público - a API não erra, só devolve biblioteca vazia)."""
    api_key = steam_cfg.get("api_key")
    steamid64 = steam_cfg.get("steamid64")
    if not api_key or not steamid64:
        raise ValueError("faltando api_key/steamid64 em [steam] no config.toml")

    params = urllib.parse.urlencode({
        "key": api_key,
        "steamid": steamid64,
        "format": "json",
        "include_appinfo": 1,
        "include_played_free_games": 1,
    })
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?{params}"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read())

    games = data.get("response", {}).get("games")
    if not games:
        raise RuntimeError(
            "API respondeu sem nenhum jogo - confira se \"Detalhes do jogo\" está "
            "Público no perfil Steam (Editar perfil > Privacidade), ou se o "
            "steamid64 está certo"
        )
    return [{"nome": g["name"], "plataforma": "Steam", "fonte": "steam", "appid": g["appid"]} for g in games]


def steam_appid_index(steam_cfg: dict) -> dict:
    """{nome normalizado: appid} da biblioteca Steam do usuário - usado
    só pra achar capa (ver find_cover_steam_cdn). Falha de rede/config
    devolve {} em vez de levantar: capa da Steam é um ATALHO (fonte
    oficial, melhor qualidade), não a única - sem ela o fetch cai no
    SteamGridDB normalmente."""
    try:
        owned = read_steam_library(steam_cfg)
    except (ValueError, RuntimeError, OSError):
        return {}
    return {covers_mod.normalize(g["nome"]): g["appid"] for g in owned if g.get("appid")}


# Arte de biblioteca oficial da Steam (mesma imagem retrato que o
# cliente da Steam mostra), servida pelo CDN público - não precisa de
# chave nem de login, só do appid. `_2x` é a versão maior; nem todo
# jogo tem, por isso a lista tem fallback pra resolução normal.
_STEAM_CDN_TEMPLATES = [
    "https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900_2x.jpg",
    "https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
]


def find_cover_steam_cdn(appid) -> str | None:
    """URL da capa oficial da Steam pro `appid`, ou None se o jogo não
    tiver arte de biblioteca publicada (acontece com jogo antigo/
    removido - aí quem chama cai pro SteamGridDB)."""
    for template in _STEAM_CDN_TEMPLATES:
        url = template.format(appid=appid)
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": _BROWSER_USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                if r.status == 200:
                    return url
        except OSError:
            continue
    return None


_PSN_CLIENT_ID = "09515159-7237-4370-9b40-3806e67c0891"
_PSN_REDIRECT_URI = "com.scee.psxandroid.scecompcall://redirect"
# client_id:client_secret fixos da API oficial da Sony (públicos - usados
# por qualquer app que fala com essa API, não é credencial nossa nem do
# usuário) codificados em Basic auth, mesmo valor usado pelo psn-api.
_PSN_TOKEN_BASIC = "Basic MDk1MTUxNTktNzIzNy00MzcwLTliNDAtMzgwNmU2N2MwODkxOnVjUGprYTV0bnRCMktxc1A="
# Hash SHA256 da query GraphQL "getPurchasedGameList" ("persisted
# query" - a API recusa a query em texto puro, só aceita o hash de uma
# query já conhecida do lado do servidor). Reverso-engenheiro pela
# comunidade (psn-api), não documentado pela Sony.
_PSN_PURCHASED_GAMES_HASH = "827a423f6a8ddca4107ac01395af2ec0eafd8396fc7fa204aaf9b7ed2eefa168"


def _psn_access_token(npsso: str) -> str:
    """Troca o npsso (token manual do usuário, ver read_psn_library) por
    um access_token de curta duração (~1h) - fluxo reverso-engenheirado
    documentado pela comunidade (psn-api/PSNAWP), não existe API oficial
    de app registrado pra isso:
    1) chama o /authorize da Sony com o npsso como cookie, SEM seguir o
       redirect (por isso http.client cru em vez de urllib.request, que
       seguiria sozinho) - o "code" vem na query string do header
       Location da resposta 302, não no corpo.
    2) troca esse code por um access_token via POST com a Basic auth
       fixa acima."""
    params = urllib.parse.urlencode({
        "access_type": "offline",
        "client_id": _PSN_CLIENT_ID,
        "redirect_uri": _PSN_REDIRECT_URI,
        "response_type": "code",
        "scope": "psn:mobile.v2.core psn:clientapp",
    })
    conn = http.client.HTTPSConnection("ca.account.sony.com", timeout=30)
    try:
        conn.request("GET", f"/api/authz/v3/oauth/authorize?{params}", headers={"Cookie": f"npsso={npsso}"})
        location = conn.getresponse().getheader("Location")
    finally:
        conn.close()

    if not location or "code=" not in location:
        raise RuntimeError(
            "npsso inválido ou expirado - gere um novo visitando "
            "https://ca.account.sony.com/api/v1/ssocookie logado no PSN pelo navegador"
        )
    code = urllib.parse.parse_qs(urllib.parse.urlparse(location).query).get("code", [None])[0]
    if not code:
        raise RuntimeError("não encontrei o 'code' no redirect da Sony - npsso inválido ou expirado")

    body = urllib.parse.urlencode({
        "code": code,
        "redirect_uri": _PSN_REDIRECT_URI,
        "grant_type": "authorization_code",
        "token_format": "jwt",
    }).encode()
    req = urllib.request.Request(
        "https://ca.account.sony.com/api/authz/v3/oauth/token",
        data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded", "Authorization": _PSN_TOKEN_BASIC},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        token_data = json.loads(r.read())

    access_token = token_data.get("access_token")
    if not access_token:
        raise RuntimeError(f"Sony não devolveu access_token: {token_data}")
    return access_token


def read_psn_trophy_titles(psn_cfg: dict) -> list:
    """[{"nome", "plataforma": "PSN", "fonte": "psn"}] via troféus
    (trophyTitles, paginado de 800 em 800). NÃO é a biblioteca possuída
    - é histórico de jogo: só aparece título que já foi ABERTO pelo
    menos uma vez (troféu sincroniza no primeiro launch), comprado e
    nunca aberto não entra. Mantido à parte de `read_psn_library`
    (biblioteca de verdade) porque cobre coisa que ela não cobre -
    jogo físico jogado, por exemplo - mas não é usado por
    `library-refresh psn` por padrão. Mesma autenticação de
    `read_psn_library`, ver docstring de lá pro `npsso`."""
    npsso = psn_cfg.get("npsso")
    if not npsso:
        raise ValueError("faltando npsso em [psn] no config.toml")
    access_token = _psn_access_token(npsso)

    games, offset = [], 0
    while True:
        req = urllib.request.Request(
            f"https://m.np.playstation.com/api/trophy/v1/users/me/trophyTitles?limit=800&offset={offset}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        games += [
            {"nome": t["trophyTitleName"], "plataforma": "PSN", "fonte": "psn"}
            for t in data.get("trophyTitles", [])
        ]
        offset = data.get("nextOffset")
        if not offset:
            break

    if not games:
        raise RuntimeError("nenhum jogo com troféu encontrado - conta nova, ou privacidade de troféus restrita?")
    return games


# Entitlements que aparecem junto na biblioteca de compras mas não são
# jogo (apps pré-instalados/parceiros) - lista pequena e best-effort,
# baseada só no que apareceu numa conta real (Spotify, PS4 Media
# Player); outra conta pode ter Netflix/YouTube/etc que não estão
# aqui - filtro incompleto de propósito, não dá pra saber os IDs de
# apps que nunca vimos.
_PSN_NON_GAME_ENTITLEMENT_PREFIXES = {
    "EP4950-CUSA01780_00",  # Spotify
    "IP9100-CUSA02012_00",  # PS4 Media Player (Reprodutor de mídia)
}


def read_psn_library(psn_cfg: dict) -> list:
    """[{"nome", "plataforma": "PSN", "fonte": "psn"}] via biblioteca de
    compras de verdade (GraphQL `getPurchasedGameList`, endpoint interno
    do site library.playstation.com) - PS4/PS5 apenas, `isActive: true`
    (não lista o que foi removido/reembolsado da conta). Igual ao caso
    do Xbox (ver read_xbox_library), é um endpoint reverso-engenheiro
    (query "persisted" via hash SHA256, não documentado publicamente) -
    se a Sony mudar o schema, o hash `_PSN_PURCHASED_GAMES_HASH` para de
    bater e isso quebra com um erro claro (não silencioso).

    Precisa de `apollo-require-preflight: true` no header - sem isso a
    API recusa com 400 "potential CSRF" (achado testando ao vivo, não
    documentado em lugar nenhum).

    Precisa de `npsso` em [psn] no config.toml - token manual, válido
    por ~2 meses, obtido visitando
    https://ca.account.sony.com/api/v1/ssocookie logado no PSN pelo
    navegador (copia o valor de "npsso" do JSON que a página devolve)."""
    npsso = psn_cfg.get("npsso")
    if not npsso:
        raise ValueError("faltando npsso em [psn] no config.toml")
    access_token = _psn_access_token(npsso)

    games, start, size = [], 0, 100
    while True:
        params = urllib.parse.urlencode({
            "operationName": "getPurchasedGameList",
            "variables": json.dumps({
                "isActive": True, "platform": ["ps4", "ps5"], "size": size, "start": start,
                "sortBy": "ACTIVE_DATE", "sortDirection": "desc",
            }),
            "extensions": json.dumps({
                "persistedQuery": {"version": 1, "sha256Hash": _PSN_PURCHASED_GAMES_HASH},
            }),
        })
        req = urllib.request.Request(
            f"https://web.np.playstation.com/api/graphql/v1/op?{params}",
            headers={"Authorization": f"Bearer {access_token}", "apollo-require-preflight": "true"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())

        page = data.get("data", {}).get("purchasedTitlesRetrieve", {}).get("games")
        if page is None:
            raise RuntimeError(f"resposta inesperada da Sony (schema mudou?): {data}")
        for g in page:
            prefix = "-".join(g["entitlementId"].split("-")[:2])
            if prefix in _PSN_NON_GAME_ENTITLEMENT_PREFIXES:
                continue
            games.append({"nome": g["name"], "plataforma": f"PSN ({g['platform']})", "fonte": "psn"})

        if len(page) < size:
            break
        start += size

    if not games:
        raise RuntimeError("biblioteca de compras vazia - conta nova, ou só tem jogo físico/via PS Plus?")
    return games


def read_xbox_library(xbox_cfg: dict) -> list:
    """[{"nome", "plataforma": "Xbox", "fonte": "xbox:jogado"}] via
    OpenXBL (xbl.io), API não-oficial mantida pela comunidade - a
    Microsoft não tem API pública equivalente à da Steam (nem de
    biblioteca comprada, nem community-maintained como a do PSN acima).

    Fonte deliberadamente "xbox:jogado", não "xbox" - o único endpoint
    disponível (`/titles`) é histórico de jogo, não biblioteca: mistura
    comprado + Game Pass + disco de era 360 sem separação confiável
    (`gamePass.isGamePass` testado contra a conta real e não bate com
    jogos que sabidamente são Game Pass - ex: Victoria 3/EU4/HoI4 vêm
    com `isGamePass: false`, não dá pra confiar nesse campo). Decisão do
    usuário (27/08): importar tudo mesmo assim, mas com essa fonte
    marcada como "jogado" pra ficar explícito que não é o mesmo que
    "possuído" nas outras fontes - revisão de quais fazem sentido manter
    é manual, no library.json.

    Precisa de `api_key` em [xbox] no config.toml - grátis, gerada
    logando com a conta Microsoft/Xbox em https://xbl.io. Resposta vem
    envelopada em {"content": {...}, "code": ...} (formato do gateway do
    OpenXBL, não da Microsoft direto)."""
    api_key = xbox_cfg.get("api_key")
    if not api_key:
        raise ValueError("faltando api_key em [xbox] no config.toml")

    req = urllib.request.Request(
        "https://api.xbl.io/v2/titles",
        headers={
            "X-Authorization": api_key,
            "Accept": "application/json",
            # O Cloudflare na frente do xbl.io bloqueia a assinatura padrão
            # do urllib ("Python-urllib/x.y", 403 "browser_signature_banned")
            # mesmo com a chave certa - user-agent de navegador comum resolve.
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())

    content = data.get("content", data)
    titles = content.get("titles") or []
    if not titles:
        raise RuntimeError("API respondeu sem nenhum jogo - confira se a chave do OpenXBL (xbl.io) está certa")
    return [{"nome": t["name"], "plataforma": "Xbox", "fonte": "xbox:jogado"} for t in titles]


def nomes_para_match(game: dict) -> list:
    """Nome atual + todos os nomes anteriores (`nomes_alt`) - é por
    esses que uma fonte externa pode reconhecer o registro. Ver
    update_game/merge_owned."""
    return [game["nome"], *game.get("nomes_alt", [])]


def merge_owned(library: dict, owned: list) -> dict:
    """Cruza `owned` (jogos possuídos, vindos de alguma fonte externa)
    com library["games"]: nome normalizado IGUAL só anota a fonte a
    mais no registro existente (nunca mexe em nota/finalizado/etc);
    sem batida exata vira registro novo (possuído mas ainda sem
    acompanhamento). `possible_dupes` é só um alerta (difflib, corte
    0.8) pra revisão manual - nunca mescla sozinho por aproximação,
    pra não arriscar juntar dois jogos diferentes por engano."""
    # Indexa nome atual e apelidos, mas o atual tem PRIORIDADE: se dois
    # registros disputam o mesmo texto (um pelo nome vigente, outro por
    # um apelido antigo), o do nome vigente ganha - senão um rename
    # desfeito poderia sequestrar o jogo homônimo de verdade.
    by_norm = {}
    for g in library["games"]:
        by_norm.setdefault(_normalize(g["nome"]), []).append(g)
    for g in library["games"]:
        for apelido in g.get("nomes_alt", []):
            chave = _normalize(apelido)
            if chave not in by_norm:
                by_norm[chave] = [g]
    all_names = [g["nome"] for g in library["games"]]

    added = merged = 0
    possible_dupes = []

    for item in owned:
        norm = _normalize(item["nome"])
        existing = by_norm.get(norm)
        if existing:
            for g in existing:
                if item["fonte"] not in g["fontes"]:
                    g["fontes"].append(item["fonte"])
            merged += 1
            continue

        close = difflib.get_close_matches(item["nome"], all_names, n=1, cutoff=0.8)
        if close:
            possible_dupes.append((item["nome"], close[0]))

        game = _blank_game(item["nome"], item["plataforma"])
        game["fontes"].append(item["fonte"])
        library["games"].append(game)
        by_norm.setdefault(norm, []).append(game)
        all_names.append(item["nome"])
        added += 1

    return {"added": added, "merged": merged, "possible_dupes": possible_dupes}


# Mapeia plataforma (texto livre gravado em library.json - planilha ou
# fonte de loja) pro código de sistema ROM equivalente, só quando dá
# pra afirmar isso com segurança - cobre os rótulos que
# core/heavy_roms.py e o config.toml usam pra cada sistema (ver
# `capas`/`nome` em [systems]/[heavy_systems], é o texto que
# `get_or_create_for_rom` grava em registro novo) mais os que já
# apareceram de verdade na planilha do usuário (SNES, "Game Boy
# Advanced" com "d" a mais, etc). Achado 27/08: cruzar ROM<->Biblioteca
# só por nome (sem checar isso) misturava jogos DIFERENTES que só têm
# o nome igual - "Celeste" comprado no Xbox e um "Celeste.gba" (quase
# certamente ROM-hack/demake amador) viraram um registro só, ou
# "Chrono Trigger"/"Final Fantasy VII"/"IX" catalogados como "Steam" na
# planilha "roubavam" o card da ROM de SNES/PS1 mesmo o usuário
# querendo ver os dois separados (pedido explícito do usuário: "por
# isso deve se separar jogo/plataforma"). Texto de plataforma que não
# aparece aqui simplesmente nunca cruza com ROM nenhuma - fica sempre
# separado, o oposto do fuzzy match (aqui o erro seguro é NÃO unir).
PLATAFORMA_ROM_CODES = {
    "nintendo nintendo entertainment system": "FC", "nes": "FC", "famicom": "FC",
    "nintendo super nintendo entertainment system": "SFC", "snes": "SFC", "super nintendo": "SFC",
    "nintendo game boy": "GB", "game boy": "GB",
    "nintendo game boy color": "GBC", "game boy color": "GBC",
    "nintendo game boy advance": "GBA", "game boy advance": "GBA", "game boy advanced": "GBA",
    "nintendo nintendo 64": "N64", "nintendo 64": "N64",
    "nintendo nintendo ds": "NDS", "nintendo ds": "NDS",
    "sega mega drive genesis": "MD", "mega drive": "MD", "genesis": "MD", "sega genesis": "MD",
    "sega master system mark iii": "SMS", "master system": "SMS",
    "sega game gear": "GG", "game gear": "GG",
    "nec pc engine turbografx 16": "PCE", "pc engine": "PCE", "turbografx 16": "PCE", "turbografx": "PCE",
    "nec pc engine cd turbografx cd": "PCECD", "pc engine cd": "PCECD", "turbografx cd": "PCECD",
    "fbneo arcade games": "ARCADE", "arcade": "ARCADE",
    "sony playstation": "PS", "playstation": "PS", "ps1": "PS", "psx": "PS", "psone": "PS",
    "sony playstation 2": "PS2", "playstation 2": "PS2", "ps2": "PS2",
    "nintendo gamecube": "NGC", "gamecube": "NGC", "game cube": "NGC",
    "nintendo wii": "WII", "wii": "WII",
    "sony psp": "PSP", "psp": "PSP", "playstation portable": "PSP",
    "nintendo 3ds": "3DS", "3ds": "3DS",
}


def rom_code_for_plataforma(plataforma: str) -> str | None:
    return PLATAFORMA_ROM_CODES.get(_normalize(plataforma or ""))


def index_by_rom_name(library: dict) -> dict:
    """{covers_mod.normalize(nome): [registros]} - TODOS os jogos com
    esse nome, não só um: pode haver mais de um jogo DIFERENTE com o
    mesmo nome em plataformas diferentes de verdade (ver
    PLATAFORMA_ROM_CODES acima) - quem usa filtra pelo código certo via
    find_for_rom, nunca assume que nome igual = mesmo jogo sozinho."""
    # Mesma prioridade de merge_owned: nome vigente antes de apelido.
    by_norm = {}
    for g in library["games"]:
        by_norm.setdefault(covers_mod.normalize(g["nome"]), []).append(g)
    for g in library["games"]:
        for apelido in g.get("nomes_alt", []):
            chave = covers_mod.normalize(apelido)
            if chave not in by_norm:
                by_norm[chave] = [g]
    return by_norm


def find_for_rom(rom_index: dict, nome: str, code: str) -> dict | None:
    """Acha, dentro de um índice já construído por index_by_rom_name,
    o registro que representa a MESMA ROM: nome normalizado igual E
    plataforma gravada mapeando pro mesmo `code` (via
    rom_code_for_plataforma) - nunca só nome (ver PLATAFORMA_ROM_CODES).
    Sem bater nenhum (nome não existe, ou existe só em plataforma(s)
    diferente(s) desse `code`), devolve None."""
    for g in rom_index.get(covers_mod.normalize(nome), []):
        if rom_code_for_plataforma(g["plataforma"]) == code:
            return g
    return None


def get_or_create_for_rom(library: dict, nome: str, code: str, plataforma: str, fonte: str) -> dict:
    """Acha (via find_for_rom - nome E plataforma compatível com
    `code`) ou cria um registro pra ROM leve/pesada. `plataforma` aqui
    é o rótulo que vai ser GRAVADO num registro novo (mesmo texto que
    `capas`/`nome` do sistema em config.toml, já coberto por
    PLATAFORMA_ROM_CODES, então um registro criado agora casa
    corretamente com uma edição futura na mesma ROM). Sempre garante
    `fonte` na lista de fontes do registro (novo ou já existente).
    Usado pelo tracking universal (iniciado/finalizado/platinado/nota)
    em ROM leve/pesada: a primeira edição feita na tela "cria" o
    registro sozinha, sem precisar de import de planilha nem de fonte
    de loja - por isso `fonte` aqui é sempre "rom:<CODIGO>", nunca uma
    loja de verdade. Diferente do antigo get_or_create_by_name (27/08):
    esse cruzava só por nome, misturando jogo diferente com nome igual
    em plataforma diferente - ver PLATAFORMA_ROM_CODES."""
    game = find_for_rom(index_by_rom_name(library), nome, code)
    if game is None:
        game = _blank_game(nome, plataforma)
        library["games"].append(game)
    if fonte not in game["fontes"]:
        game["fontes"].append(fonte)
    return game


def _limpa_nome_switch(nome: str) -> str:
    """Nome da pasta sem as tags entre colchetes do formato do dump
    ("[NSP]"/"[NSZ]"/"[XCI]") - elas não fazem parte do nome do jogo."""
    return re.sub(r"\s*\[[^\]]*\]", "", nome).strip()


_EXTENSOES_SWITCH = (".nsp", ".nsz", ".xci")


def nomes_dentro_da_colecao(entradas: list) -> list:
    """Sugestão de quais jogos uma coletânea contém, a partir dos nomes
    dos arquivos/pastas DE DENTRO dela. É só um chute pra pré-preencher
    a tela de decompor - quem decide é o usuário, que corrige na mão.

    Os três formatos que aparecem de verdade na coleção (conferidos no
    Drive em 29/08):
      "Portal", "Portal 2"                          -> subpasta por jogo, já limpo
      "Pikmin 1 [0100AA...][v0].nsp"                -> arquivo com title-id e versão
      "Castlevania Dominus Collection [ID][v0].nsp" -> só o nome da própria
                                                       coletânea (base + update)
    Tira extensão de dump, tira TODO grupo entre colchetes (title-id,
    versão, região) e deduplica preservando a ordem - o caso do
    Castlevania cai pra uma sugestão só (a própria coletânea), que é
    honesto: não dá pra adivinhar os jogos de dentro pelo nome do
    arquivo, e o usuário completa na mão."""
    vistos, saida = set(), []
    for entrada in entradas:
        nome = entrada.get("name", "") if isinstance(entrada, dict) else str(entrada)
        if nome.lower().endswith(_EXTENSOES_SWITCH):
            nome = nome.rsplit(".", 1)[0]
        nome = re.sub(r"\s*\[[^\]]*\]", "", nome)
        # Anotação de tamanho que aparece em pasta baixada por torrent
        # ("Demonschool (0.89 GB)") - é do arquivo, não do jogo, e sem
        # tirar isso o mesmo jogo apareceria duas vezes na sugestão.
        nome = re.sub(r"\s*\(\s*\d+([.,]\d+)?\s*(GB|MB|KB)\s*\)", "", nome, flags=re.I).strip()
        # Numeração de ordem que o usuário escreve na subpasta pra deixar a
        # série na sequência certa ("1. Demons of Asteborg", "2. Astebros").
        # É organização da pasta, não nome do jogo. Exige o ponto/parêntese
        # E o espaço depois de propósito: assim "1979 Revolution" e
        # "13 Sentinels" passam intactos.
        nome = re.sub(r"^\d{1,2}[.)]\s+", "", nome).strip()
        chave = _normalize(nome)
        if nome and chave not in vistos:
            vistos.add(chave)
            saida.append(nome)
    return saida


def mapa_pastas_switch(roms_root: Path, cfg: dict | None = None) -> dict:
    """{nome limpo: nome real da pasta} - ex: {"Portal Companion
    Collection": "Portal Companion Collection [NSP]"}. Precisa existir
    porque a Biblioteca guarda o nome LIMPO, mas pra olhar dentro da
    pasta é preciso o nome real (com a tag do dump). Cobre local e
    Drive, com a local ganhando quando o mesmo jogo está nos dois."""
    mapa = {}
    if cfg:
        from core import heavy_roms as _heavy
        for item in _heavy.list_drive_items("NSW", cfg):
            if item["is_dir"]:
                mapa[_limpa_nome_switch(item["name"])] = item["name"]
    switch_dir = roms_root / "NSW"
    if switch_dir.is_dir():
        for entrada in switch_dir.iterdir():
            if entrada.is_dir():
                mapa[_limpa_nome_switch(entrada.name)] = entrada.name
    return mapa


def conteudo_da_pasta_switch(pasta_real: str, roms_root: Path, cfg: dict | None = None) -> list:
    """Nomes dos itens DENTRO de uma pasta de jogo do Switch (local se
    existir, senão Drive). Uma chamada só de rclone, na pasta
    específica - listar a NSW inteira leva minutos e não serve aqui."""
    local = roms_root / "NSW" / pasta_real
    if local.is_dir():
        return [{"name": e.name} for e in sorted(local.iterdir())]
    if not cfg:
        return []
    import json as _json
    import subprocess as _sp
    from core import heavy_roms as _heavy
    rc = _heavy._rclone_cfg(cfg)
    alvo = f"{rc['remote']}:{rc['drive_roms_root']}/NSW/{pasta_real}"
    try:
        r = _sp.run(["rclone", "lsjson", alvo], capture_output=True, text=True, timeout=90)
        if r.returncode != 0:
            return []
        return [{"name": i["Name"]} for i in _json.loads(r.stdout)]
    except (OSError, ValueError, _sp.SubprocessError):
        return []


def read_switch_library(roms_root: Path, cfg: dict | None = None) -> list:
    """[{"nome", "plataforma": "Nintendo Switch", "fonte": "switch"}] a
    partir da pasta NSW - cada jogo é uma pasta (dump NSP/NSZ/XCI, ex:
    "Nine Sols [NSZ]"), mesma convenção de "pasta = 1 item" que
    core/heavy_roms.py já usa pros consoles pesados, só que aqui é só
    leitura de nome (sem gestão de arquivo - Switch não roda via
    RetroArch, enviar/baixar/renomear não fazem sentido e arriscariam
    mexer em jogo de verdade à toa).

    Junta as DUAS pontas (correção 28/08): a pasta local
    (`roms_root/NSW/`) E a do Google Drive (via rclone, mesma função que
    os sistemas pesados usam). Ler só a local estava perdendo quase tudo
    - o usuário mantém o grosso da coleção no Drive e só puxa pro PC o
    que vai jogar, então a pasta local varia de tamanho o tempo todo
    (tinha 22 num dia e 4 no outro) enquanto o Drive segue crescendo.
    Sem `cfg`, lê só a local (o lado do Drive precisa de [rclone]).

    Cruzamento com o que já existe na planilha (nota/observações
    preservadas) é feito por `merge_owned`, igual Heroic/Steam - jogo
    que faz parte de uma coletânea/bundle sem nome exato igual ao da
    planilha não é forçado a casar (fica como possível duplicata só
    reportada, ou vira registro novo separado - aceito por decisão do
    usuário, "não daria pra separar, paciência")."""
    nomes = set()

    switch_dir = roms_root / "NSW"
    if switch_dir.is_dir():
        for entry in switch_dir.iterdir():
            if entry.is_dir():
                nomes.add(_limpa_nome_switch(entry.name))

    if cfg:
        from core import heavy_roms as _heavy
        for item in _heavy.list_drive_items("NSW", cfg):
            if item["is_dir"]:
                nomes.add(_limpa_nome_switch(item["name"]))

    return [{"nome": n, "plataforma": "Nintendo Switch", "fonte": "switch"}
            for n in sorted(nomes) if n]


def read_manual_list(path: Path, plataforma: str, fonte: str) -> list:
    """[{"nome", "plataforma", "fonte"}] a partir de um arquivo texto,
    um jogo por linha (linha vazia ou começando com # é ignorada) - pra
    fonte sem API confiável (PSN/Xbox, ver docs/changelog.md 27/08) ou
    qualquer lista avulsa que o usuário levantar na mão."""
    games = []
    for line in path.read_text(encoding="utf-8").splitlines():
        nome = line.strip()
        if not nome or nome.startswith("#"):
            continue
        games.append({"nome": nome, "plataforma": plataforma, "fonte": fonte})
    return games


# Campos de acompanhamento editáveis pela GUI (edição inline, ver
# gui/server.py "/api/library/update") - só esses; nome/plataforma/
# fontes continuam só via CLI (library-import-sheet/refresh/add), pra
# não arriscar quebrar o "id" (slug de nome+plataforma) editando pela
# tela. Diferente das fontes que só o PC fala com (Heroic/Steam/etc),
# isso aqui é leitura+escrita de arquivo local só - funciona igual
# rodando em modo Android (Termux), sem precisar de nada PC-only.
# Campos booleanos e de texto livre editáveis pela tela. `nome` e
# `plataforma` entraram em 28/08 (pedido: "estender o editar nome para
# todos os campos" - o gatilho foi um nome errado vindo da planilha,
# "Where's is my water?"). Editar os dois é seguro porque o `id` NÃO é
# recalculado: ele é gerado uma vez na criação e daí em diante é só uma
# chave opaca (é assim que /api/library/update e o tracking já
# funcionam). O que continua fora: `id` (chave) e `fontes` (é registro
# de posse confirmada por API, não opinião do usuário - muda via
# library-refresh/library-add).
_CAMPOS_BOOL = {"iniciado", "finalizado", "platinado", "savestate", "oculto"}
_CAMPOS_TEXTO = {"tempo", "observacoes", "nome", "plataforma", "genero",
                 "subgenero", "desenvolvedora", "meta"}
_CAMPOS_DATA = {"lancamento", "data_final"}
_CAMPOS_OBRIGATORIOS = {"nome", "plataforma"}
EDITABLE_FIELDS = {"nota"} | _CAMPOS_BOOL | _CAMPOS_TEXTO | _CAMPOS_DATA


def update_game(library: dict, game_id: str, field: str, value) -> bool:
    """Atualiza UM campo de um jogo já cadastrado. Retorna False (não
    levanta erro) se o jogo ou o campo não existir - quem chama decide o
    que fazer (ver uso em gui/server.py). Levanta ValueError se o valor
    for inválido (nota fora de faixa, data em formato errado, ou
    nome/plataforma vazios)."""
    if field not in EDITABLE_FIELDS:
        return False
    game = next((g for g in library["games"] if g["id"] == game_id), None)
    if game is None:
        return False

    if field == "nota":
        value = None if value in (None, "") else float(value)
        if value is not None and not (0 <= value <= 11):
            raise ValueError("nota precisa estar entre 0 e 11")
    elif field in _CAMPOS_DATA:
        value = (str(value).strip() or None) if value is not None else None
        if value is not None:
            # Aceita tanto ISO (que é como guardamos) quanto dd/mm/aaaa
            # (como o usuário escrevia na planilha).
            iso = _to_iso_date(value)
            if iso is None:
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                    iso = value
                except ValueError:
                    raise ValueError(f"data inválida: {value!r} (use aaaa-mm-dd ou dd/mm/aaaa)")
            value = iso
    elif field in _CAMPOS_TEXTO:
        value = (str(value).strip() or None) if value is not None else None
        if field in _CAMPOS_OBRIGATORIOS and not value:
            raise ValueError(f"{field} não pode ficar vazio")
    else:
        value = bool(value)

    # Renomear guarda o nome antigo como apelido, senão a próxima
    # sincronização (que casa por nome, ver merge_owned) não reconhece
    # mais este registro e recria o jogo do zero.
    if field == "nome" and value != game["nome"]:
        anteriores = game.setdefault("nomes_alt", [])
        if _normalize(game["nome"]) not in {_normalize(n) for n in anteriores}:
            anteriores.append(game["nome"])
        # O nome ATUAL nunca fica na lista de apelidos: além de
        # redundante, um apelido que na verdade é o nome vigente de
        # outro jogo causaria merge errado (renomear "Portal" pra
        # "Portal 2" por engano e voltar deixaria "Portal 2" como
        # apelido, e aí o "Portal 2" de verdade da loja cairia neste
        # registro).
        game["nomes_alt"] = [n for n in anteriores if _normalize(n) != _normalize(value)]

    game[field] = value
    return True


# Mesmo user-agent "de navegador" do read_xbox_library - o Cloudflare
# na frente do steamgriddb.com bloqueia a assinatura padrão do urllib
# (403 "error code: 1010") do mesmo jeito que faz com o xbl.io.
_BROWSER_USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")


def search_covers_steamgriddb(termo: str, api_key: str, max_jogos: int = 6,
                              por_jogo: int = 3) -> list:
    """[{"nome", "url"}] de capas CANDIDATAS pro termo buscado - pra
    escolha manual na tela, não pra aplicação automática. Diferente de
    `find_cover_steamgriddb` (que exige match exato justamente pra
    nunca aplicar capa de outro jogo sozinho), aqui volta tudo que a
    busca achou: quem decide é o humano olhando a prévia, mesmo
    princípio da busca de capa que os sistemas leves já tinham
    (search_cover_candidates em gui/server.py). Pedido do usuário
    28/08: "não consigo buscar nem alterar capa [na Biblioteca]...
    quero ir capeando todos os jogos de todas as abas".

    Devolve várias artes por jogo (`por_jogo`) porque o SteamGridDB
    costuma ter fan-art alternativa - útil quando a primeira não é a
    capa "oficial" que o usuário quer."""
    headers = {"Authorization": f"Bearer {api_key}", "User-Agent": _BROWSER_USER_AGENT}
    search_url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{urllib.parse.quote(termo)}"
    with urllib.request.urlopen(urllib.request.Request(search_url, headers=headers), timeout=15) as r:
        jogos = (json.loads(r.read()).get("data") or [])[:max_jogos]

    out = []
    for jogo in jogos:
        grids_url = f"https://www.steamgriddb.com/api/v2/grids/game/{jogo['id']}?dimensions=600x900"
        try:
            with urllib.request.urlopen(urllib.request.Request(grids_url, headers=headers), timeout=15) as r:
                grids = json.loads(r.read()).get("data") or []
        except (OSError, json.JSONDecodeError):
            continue
        for grid in grids[:por_jogo]:
            out.append({"nome": jogo["name"], "url": grid["url"]})
    return out


def find_cover_steamgriddb(nome: str, api_key: str) -> str | None:
    """URL da melhor capa (grid 600x900, estilo "alternate" - o mesmo
    formato retrato que Steam/Heroic usam pra biblioteca) pro jogo
    `nome`, via SteamGridDB (steamgriddb.com/api/v2, chave gratuita em
    Preferences > API). Só devolve em MATCH EXATO (nome normalizado
    igual ao primeiro resultado da busca) - a API de busca não garante
    que o 1º resultado seja o jogo certo (ex: "Mario" pode devolver
    spin-off antes do principal), e mesmo cuidado do resto do projeto
    com fuzzy match vale aqui: melhor não achar capa nenhuma do que
    aplicar a de outro jogo sozinho. Devolve None sem levantar erro se
    não achar (sem jogo, sem grid, ou sem match exato)."""
    headers = {"Authorization": f"Bearer {api_key}", "User-Agent": _BROWSER_USER_AGENT}

    search_url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{urllib.parse.quote(nome)}"
    with urllib.request.urlopen(urllib.request.Request(search_url, headers=headers), timeout=15) as r:
        results = json.loads(r.read()).get("data") or []
    if not results:
        return None

    # Varre TODOS os resultados atrás de um match exato, não só o
    # primeiro (mudança 28/08: a busca da API não ordena por
    # relevância de forma confiável - "Portal" podia devolver "Portal
    # Knights" na frente e o jogo certo em 3º, e a versão antiga
    # desistia no 1º). Continua sendo match EXATO (nome normalizado
    # igual), só que agora considerando a lista inteira - o cuidado de
    # nunca aplicar capa de outro jogo sozinho fica intacto.
    # Segunda passada com `loose=True` (tira parênteses também) pega
    # coisas tipo "FINAL FANTASY VII (2013)" -> "Final Fantasy VII".
    for use_loose in (False, True):
        alvo = covers_mod.normalize(nome, loose=use_loose)
        for r in results:
            if covers_mod.normalize(r["name"], loose=use_loose) == alvo:
                grids_url = f"https://www.steamgriddb.com/api/v2/grids/game/{r['id']}?dimensions=600x900"
                with urllib.request.urlopen(urllib.request.Request(grids_url, headers=headers), timeout=15) as gr:
                    grids = json.loads(gr.read()).get("data") or []
                if grids:
                    return grids[0]["url"]
    return None


# Plataforma da Biblioteca -> código que o core/screenscraper.py
# entende (ver SYSTEM_MAP lá). Só o que tem equivalente de verdade -
# loja de PC (Steam/Epic/GOG/Amazon) não entra, o ScreenScraper é
# catálogo de console.
def _find_cover_screenscraper(nome: str, ss_code: str, cfg: dict) -> str | None:
    """URL da capa no ScreenScraper pro jogo `nome` dentro do sistema
    `ss_code`, ou None. Mesma regra de match EXATO das outras fontes
    (nome normalizado igual ao do resultado) - nunca aplica capa de
    outro jogo sozinho. Import local pra não criar dependência circular
    no topo do módulo (screenscraper importa covers, que é vizinho
    daqui). Devolve a `media_url` COM credencial embutida, que é o
    formato que o download entende - por isso nunca deve vazar pro
    cliente (ver docstring de core/screenscraper.py)."""
    from core import screenscraper as _ss
    try:
        resultados = _ss.search_game(ss_code, nome, cfg, limit=10)
    except (OSError, NotImplementedError, json.JSONDecodeError, KeyError):
        return None
    alvo = covers_mod.normalize(nome)
    for r in resultados:
        if covers_mod.normalize(r["name"]) == alvo:
            return r["media_url"]
    return None


# Selo da linha de relançamento que vem GRUDADO no título oficial do
# jogo na eShop. "ACA NEOGEO METAL SLUG" é o Metal Slug de Neo Geo
# publicado pela Hamster; "SEGA AGES Out Run" é o Out Run. O selo é do
# programa de relançamento, não do jogo.
_SELOS_DE_RELANCAMENTO = ("ACA NEOGEO ", "SEGA AGES ", "SEGA Ages ")


def gravar_png(data: bytes, dest: Path) -> bool:
    """Grava `data` em `dest` (sempre .png) garantindo que o CONTEÚDO
    seja PNG de verdade, não só a extensão.

    Achado em 29/08, depois de baixar 116 capas de coletânea decomposta:
    20 tinham bytes JPEG dentro de um arquivo .png. O bug já era
    conhecido do projeto - `core/launchbox.download_cover` converte por
    isso desde 02/08 ("o metadado da fonte não é garantia do conteúdo
    real") e existe até um `retrosync validate-covers` pra caçar o
    estrago - mas o caminho da Biblioteca nunca tinha recebido a
    correção, porque grava direto o que a URL devolve.

    Navegador tolera (fareja o conteúdo), mas RetroArch só exibe PNG de
    verdade e o `validate-covers` acusa - deixar os dois lados com a
    mesma regra é mais barato que lembrar da exceção depois.
    `convert` detecta o formato pelo conteúdo, então é idempotente e
    barato pra quem já veio PNG. Sem ImageMagick, grava o que veio (é
    melhor ter a capa do que não ter)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if data[:8].startswith(b"\x89PNG\r\n\x1a\n"):
        dest.write_bytes(data)
        return True

    tmp = dest.with_suffix(".origem.tmp")
    tmp.write_bytes(data)
    try:
        r = subprocess.run(["convert", str(tmp), str(dest)], capture_output=True, text=True)
        # O que prova a conversão é o CONTEÚDO ser PNG, não o tamanho.
        # (Copiei de início o `st_size > 1000` do launchbox e um teste
        # com imagem de cor sólida derrubou: lá a checagem é de
        # download vazio, aqui um PNG legítimo comprime pra 300 bytes.)
        convertido = (r.returncode == 0 and dest.exists()
                      and dest.read_bytes()[:8].startswith(b"\x89PNG\r\n\x1a\n"))
    except (OSError, subprocess.SubprocessError):
        convertido = False
    finally:
        tmp.unlink(missing_ok=True)

    if not convertido:
        dest.write_bytes(data)
    return True


def nomes_alternativos_de_capa(nome: str) -> list:
    """Outros nomes pelos quais o MESMO jogo pode estar catalogado nas
    fontes de capa. Só entra em ação depois que o nome de verdade não
    achou nada (ver fetch_covers) - nunca substitui a busca principal,
    porque as duas formas aparecem no acervo: "SEGA AGES Out Run" tem
    capa própria no SteamGridDB (a arte do relançamento) e "Out Run"
    sozinho não tem; já "ACA NEOGEO METAL SLUG" não tem e "Metal Slug"
    tem. Tentar só uma das duas perderia metade (conferido em 29/08 na
    API: 99 dos 108 ACA NEOGEO ficaram sem capa por causa do selo).

    Continua valendo a regra do projeto de nunca aplicar capa por
    aproximação: quem casa é o `find_cover_*`, sempre em match EXATO -
    aqui só se tira um prefixo conhecido e fixo, o que é uma reescrita
    do título, não um chute de semelhança."""
    alternativos = []
    for selo in _SELOS_DE_RELANCAMENTO:
        if nome.startswith(selo) and len(nome) > len(selo):
            alternativos.append(nome[len(selo):].strip())
    return alternativos


PLATAFORMA_SCREENSCRAPER = {
    "Nintendo Switch": "NSW",
    "PlayStation 4": "PS",     # ScreenScraper não separa PS4; PS1 é o mais próximo
    "PlayStation 3": "PS",
    "PlayStation 2": "PS2",
    "Nintendo 3DS": "3DS",
}


def fetch_covers(library: dict, capas_dir: Path, api_key: str, on_progress=None,
                 steam_appids: dict | None = None, cfg: dict | None = None) -> dict:
    """Busca capa pra todo jogo em library["games"] que ainda não tem
    `capa` - baixa em `capas_dir/<id>.png` e grava o caminho relativo
    (`capas/<id>.png`) no registro. `on_progress`, se passado, é
    chamado a cada jogo como on_progress(nome, status) - usado pela GUI
    pra progresso ao vivo, mesmo padrão de covers.process_system
    (opcional, não quebra quem chama sem isso).

    Três fontes, nessa ordem (28/08 - antes era só SteamGridDB):
    1. CDN oficial da Steam, quando o jogo está na biblioteca Steam do
       usuário (`steam_appids`, ver steam_appid_index) - é a mesma arte
       que o cliente da Steam mostra, sem depender de curadoria de
       terceiro, então vem primeiro por qualidade/confiabilidade.
    2. ScreenScraper, quando a plataforma do jogo tem equivalente lá
       (`PLATAFORMA_SCREENSCRAPER` + `cfg`) - curadoria melhor que o
       SteamGridDB, e cobre bem o que mais faltava: jogo de Switch.
    3. SteamGridDB (`api_key`), o mais genérico, pro que sobrou.
    Jogo oculto (`oculto`) é pulado - não faz sentido gastar rede com
    o que o usuário escondeu de propósito."""
    pending = [g for g in library["games"] if not g["capa"] and not g.get("oculto")]
    result = {"baixado": 0, "sem_match": 0, "erro": 0, "via_steam": 0, "via_ss": 0,
              "via_alias": 0, "aliases": []}
    steam_appids = steam_appids or {}

    for game in pending:
        url, via_steam, via_ss, alias_usado = None, False, False, None
        try:
            appid = steam_appids.get(covers_mod.normalize(game["nome"]))
            if appid:
                url = find_cover_steam_cdn(appid)
                via_steam = url is not None
            # O nome de verdade primeiro, sempre; só depois o título sem
            # o selo de relançamento (ver nomes_alternativos_de_capa).
            for i, nome in enumerate([game["nome"], *nomes_alternativos_de_capa(game["nome"])]):
                if url:
                    break
                if cfg:
                    ss_code = PLATAFORMA_SCREENSCRAPER.get(game["plataforma"])
                    if ss_code:
                        url = _find_cover_screenscraper(nome, ss_code, cfg)
                        via_ss = url is not None
                if not url:
                    url = find_cover_steamgriddb(nome, api_key)
                if url and i > 0:
                    alias_usado = nome
        except (OSError, json.JSONDecodeError, KeyError):
            result["erro"] += 1
            if on_progress:
                on_progress(game["nome"], "erro")
            continue

        if not url:
            result["sem_match"] += 1
            if on_progress:
                on_progress(game["nome"], "sem_match")
            continue

        capas_dir.mkdir(parents=True, exist_ok=True)
        dest = capas_dir / f"{game['id']}.png"
        req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
        except OSError:
            result["erro"] += 1
            if on_progress:
                on_progress(game["nome"], "erro")
            continue
        if not gravar_png(data, dest):
            result["erro"] += 1
            if on_progress:
                on_progress(game["nome"], "erro")
            continue
        game["capa"] = f"capas/{game['id']}.png"
        result["baixado"] += 1
        if via_steam:
            result["via_steam"] += 1
        if via_ss:
            result["via_ss"] += 1
        if alias_usado:
            # Registrado nominalmente, não só contado: a capa veio de uma
            # busca por um título diferente do que está no registro, então
            # é o lote que mais merece uma conferida de olho.
            result["via_alias"] += 1
            result["aliases"].append((game["nome"], alias_usado))
        if on_progress:
            fonte = "steam" if via_steam else ("screenscraper" if via_ss else "steamgriddb")
            if alias_usado:
                fonte += f", buscado como {alias_usado!r}"
            on_progress(game["nome"], f"baixado ({fonte})")

    return result
