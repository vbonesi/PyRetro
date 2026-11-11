"""Credencial do Tinfoil gerada pelo PyRetro (substitui o rustfoil `--tinfoil-auth`).

Fluxo de "app instalado" do Google: abre o navegador, recebe o código em `127.0.0.1:<porta livre>`
(com PKCE e `state`) e troca por token. Grava `credentials.json` (o JSON do cliente Desktop, como veio)
e `gdrive.token` (`{"access_token":…, "refresh_token":…}`, o formato que o rustfoil escreve e o Tinfoil
lê) numa pasta fora do repositório, prontos para copiar em `/switch/tinfoil/` do SD. Arquivos 0600; o
token nunca é impresso. Só biblioteca padrão."""
import base64
import hashlib
import json
import os
import secrets
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ESCOPOS = {"readonly": "https://www.googleapis.com/auth/drive.readonly",
           "drive": "https://www.googleapis.com/auth/drive"}
PASTA_PADRAO = "~/Downloads/COPY_TO_SD/switch/tinfoil"
AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def ler_cliente(caminho: Path) -> dict:
    """Lê o JSON do cliente OAuth Desktop e devolve a seção `installed` (ou `web`)."""
    try:
        bruto = json.loads(Path(caminho).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"não consegui ler o JSON do cliente: {e}") from e
    cliente = bruto.get("installed") or bruto.get("web") if isinstance(bruto, dict) else None
    if not cliente or not cliente.get("client_id") or not cliente.get("client_secret"):
        raise ValueError("JSON sem client_id/client_secret (use o cliente OAuth do tipo Desktop)")
    return cliente


def _pkce():
    verificador = secrets.token_urlsafe(64)
    desafio = base64.urlsafe_b64encode(hashlib.sha256(verificador.encode()).digest()).rstrip(b"=").decode()
    return verificador, desafio


def url_de_autorizacao(cliente: dict, redirect: str, escopo: str, state: str, desafio: str) -> str:
    params = {"client_id": cliente["client_id"], "redirect_uri": redirect, "response_type": "code",
              "scope": escopo, "state": state, "access_type": "offline", "prompt": "consent",
              "code_challenge": desafio, "code_challenge_method": "S256"}
    return f"{cliente.get('auth_uri') or AUTH_URI}?{urllib.parse.urlencode(params)}"


def trocar_codigo(cliente: dict, codigo: str, redirect: str, verificador: str, post=None) -> dict:
    """Troca o código por tokens. `post(url, dados) -> dict` é injetável nos testes."""
    dados = {"client_id": cliente["client_id"], "client_secret": cliente["client_secret"], "code": codigo,
             "redirect_uri": redirect, "grant_type": "authorization_code", "code_verifier": verificador}
    return (post or _post)(cliente.get("token_uri") or TOKEN_URI, dados)


def _post(url: str, dados: dict) -> dict:
    req = urllib.request.Request(url, urllib.parse.urlencode(dados).encode(),
                                 {"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            motivo = json.loads(e.read()).get("error", "")
        except ValueError:
            motivo = ""
        raise OSError(f"o Google recusou a troca do código (HTTP {e.code} {motivo})") from None
    except (OSError, ValueError) as e:
        raise OSError(f"falha na troca do código: {e}") from None


def _receber_codigo(state: str, timeout: int, abrir) -> tuple:
    """Sobe o servidor em 127.0.0.1 numa porta livre, chama `abrir(redirect)` e espera o retorno."""
    resultado = {}
    pronto = threading.Event()

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in q or "error" in q:
                resultado.update({k: v[0] for k, v in q.items()})
                ok = resultado.get("state") == state and "code" in resultado
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
                self.wfile.write(("<h3>PyRetro: autorizado. Pode fechar esta aba.</h3>" if ok
                                  else "<h3>PyRetro: autorização recusada ou inválida.</h3>").encode())
                pronto.set()
            else:
                self.send_response(404); self.end_headers()

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    redirect = f"http://127.0.0.1:{srv.server_address[1]}"
    srv.timeout = 1
    try:
        abrir(redirect)
        fim = threading.Event()
        threading.Timer(timeout, fim.set).start()
        while not pronto.is_set() and not fim.is_set():
            srv.handle_request()
    finally:
        srv.server_close()
    if resultado.get("state") != state or "code" not in resultado:
        raise OSError("autorização não concluída (recusada, state inválido ou tempo esgotado)")
    return resultado["code"], redirect


def _gravar_0600(caminho: Path, conteudo: str) -> None:
    fd = os.open(caminho, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(conteudo)
    os.chmod(caminho, 0o600)


def gravar(destino: Path, credenciais_json: str, tokens: dict) -> list:
    if not tokens.get("access_token") or not tokens.get("refresh_token"):
        raise OSError("o Google não devolveu refresh_token; revogue o acesso do app e tente de novo")
    destino = Path(destino).expanduser()
    destino.mkdir(parents=True, exist_ok=True)
    _gravar_0600(destino / "credentials.json", credenciais_json)
    _gravar_0600(destino / "gdrive.token", json.dumps(
        {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"]}, separators=(",", ":")))
    return [destino / "credentials.json", destino / "gdrive.token"]


def login(cliente_json: Path, destino: Path, escopo: str = "readonly", timeout: int = 300,
          abrir=None, post=None) -> Path:
    """Faz o login completo e grava os dois arquivos. Devolve a pasta."""
    cliente = ler_cliente(cliente_json)
    bruto = Path(cliente_json).expanduser().read_text(encoding="utf-8")
    verificador, desafio = _pkce()
    state = secrets.token_urlsafe(24)

    def abrir_padrao(redirect):
        url = url_de_autorizacao(cliente, redirect, ESCOPOS[escopo], state, desafio)
        print("Abrindo o navegador para autorizar. Se não abrir, copie este endereço:\n" + url)
        webbrowser.open(url)

    codigo, redirect = _receber_codigo(state, timeout, abrir or (lambda r: (abrir_padrao(r))))
    tokens = trocar_codigo(cliente, codigo, redirect, verificador, post)
    gravar(destino, bruto, tokens)
    return Path(destino).expanduser()
