"""Cliente mínimo do IGDB (Twitch app access), com cache em disco e limite de 4 req/s."""
from __future__ import annotations
import json, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

_ULTIMA = [0.0]
_TOKEN = {"v": None, "ate": 0.0}


def _credenciais() -> tuple[str, str]:
    import retrosync
    cfg = retrosync.load_config().get("igdb") or {}
    cid, sec = cfg.get("client_id"), cfg.get("client_secret")
    if not cid or not sec:
        raise RuntimeError("[igdb] client_id/client_secret ausentes no config")
    return cid, sec


def token() -> str:
    if _TOKEN["v"] and time.time() < _TOKEN["ate"]:
        return _TOKEN["v"]
    cid, sec = _credenciais()
    dados = urllib.parse.urlencode({"client_id": cid, "client_secret": sec, "grant_type": "client_credentials"}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://id.twitch.tv/oauth2/token", data=dados), timeout=30) as r:
        j = json.load(r)
    _TOKEN.update(v=j["access_token"], ate=time.time() + j.get("expires_in", 3600) - 120)
    return _TOKEN["v"]


def consulta(endpoint: str, corpo: str, tentativas: int = 5):
    """POST na API v4; espera 0,27 s entre chamadas (4 req/s) e repete em 429/5xx."""
    cid, _ = _credenciais()
    for t in range(tentativas):
        espera = 0.27 - (time.time() - _ULTIMA[0])
        if espera > 0:
            time.sleep(espera)
        _ULTIMA[0] = time.time()
        req = urllib.request.Request(f"https://api.igdb.com/v4/{endpoint}", data=corpo.encode(),
                                     headers={"Client-ID": cid, "Authorization": f"Bearer {token()}", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                _TOKEN["v"] = None
            if e.code in (401, 429, 500, 502, 503, 504):
                time.sleep(1.5 * (t + 1)); continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(1.5 * (t + 1))
    raise RuntimeError(f"IGDB falhou: {endpoint}")


def com_cache(pasta: Path, chave: str, endpoint: str, corpo: str):
    import hashlib
    pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / (hashlib.sha1((endpoint + corpo).encode()).hexdigest() + ".json")
    if arq.exists():
        return json.loads(arq.read_text())
    r = consulta(endpoint, corpo)
    arq.write_text(json.dumps(r, ensure_ascii=False))
    return r
