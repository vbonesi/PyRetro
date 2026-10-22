"""
Pacotes de texturas HD para os emuladores do PC (substituição de textura).

PCSX2, Dolphin e PPSSPP carregam PNG/DDS de uma pasta por jogo; este módulo
baixa um pacote do catálogo (core/texturas_catalogo.json, gerado por
tools/gerar_catalogo_texturas.py a partir do Internet Archive) ou importa um
arquivo local, confere o SHA-1, extrai para uma pasta temporária e copia
para a pasta certa do emulador. Cada instalação grava um manifesto
(.pyretro-textura.json) com os arquivos copiados, então remover só apaga o que
o PyRetro instalou (dumps e pacotes manuais ficam intactos).

Pastas de destino (confirmadas em 16/10/2026 só para o PCSX2 - NFS Underground 2,
SLUS-21065, com troca de textura vista em jogo; Dolphin e PPSSPP seguem a
convenção documentada deles e ainda NÃO foram testados aqui):
  PS1   textures/<SERIAL>/replacements/     (DuckStation; troca "vram-write-<hash>.png")
  PS2   textures/<SERIAL>/replacements/     (PCSX2, Flatpak)
  GC/Wii Load/Textures/<ID DE 6 LETRAS>/    (Dolphin, Flatpak)
  PSP   PSP/TEXTURES/<ID DO DISCO>/         (PPSSPP, Flatpak)

Cada emulador também precisa da opção "carregar texturas" ligada; set_loading
liga, mas só com o emulador fechado (ele regrava o .ini ao sair e desfaria a
mudança)."""
import hashlib
import ipaddress
import json
import os
import re
import shutil
import subprocess
import tempfile
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CATALOGO_PATH = Path(__file__).parent / "texturas_catalogo.json"
FONTES_PATH = Path(__file__).parent / "texturas_fontes.json"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "texturas"
MANIFESTO = ".pyretro-textura.json"
URL_PERMITIDAS = ("https://archive.org/", "https://github.com/", "https://raw.githubusercontent.com/")
EXTENSOES = (".zip", ".7z", ".rar")

_FLATPAK = Path.home() / ".var/app"
_PADRAO = {
    "PS1": Path.home() / ".local/share/duckstation/textures",
    "PS2": _FLATPAK / "net.pcsx2.PCSX2/config/PCSX2/textures",
    "GC": _FLATPAK / "org.DolphinEmu.dolphin-emu/data/dolphin-emu/Load/Textures",
    "WII": _FLATPAK / "org.DolphinEmu.dolphin-emu/data/dolphin-emu/Load/Textures",
    "PSP": _FLATPAK / "org.ppsspp.PPSSPP/config/ppsspp/PSP/TEXTURES",
}
_PROCESSO = {"PS1": "DuckStation-x64", "PS2": "pcsx2-qt", "GC": "dolphin-emu", "WII": "dolphin-emu", "PSP": "PPSSPPSDL"}
_ID_JOGO = {
    "PS1": re.compile(r"^[A-Z]{4}-\d{5}$"),
    "PS2": re.compile(r"^[A-Z]{4}-\d{5}$"),
    "GC": re.compile(r"^[A-Z0-9]{6}$"),
    "WII": re.compile(r"^[A-Z0-9]{6}$"),
    "PSP": re.compile(r"^[A-Z]{4}\d{5}$"),
}


class TexturaErro(Exception):
    pass


def sistemas_suportados() -> list[str]:
    return list(_PADRAO)


def carregar_catalogo(path: Path = CATALOGO_PATH) -> list[dict]:
    pacotes = json.loads(path.read_text(encoding="utf-8"))["pacotes"]
    return [p for p in pacotes if p.get("sistema") in _PADRAO]


def achar_pacote(pacote_id: str, catalogo: list[dict] | None = None) -> dict:
    for p in catalogo if catalogo is not None else carregar_catalogo():
        if p["id"] == pacote_id:
            return p
    raise TexturaErro(f"pacote desconhecido: {pacote_id}")


def pasta_base(sistema: str, cfg: dict | None = None) -> Path:
    if sistema not in _PADRAO:
        raise TexturaErro(f"sistema sem suporte a texturas: {sistema}")
    custom = ((cfg or {}).get("texturas") or {}).get(sistema.lower())
    return Path(custom).expanduser() if custom else _PADRAO[sistema]


def pasta_jogo(sistema: str, id_jogo: str, cfg: dict | None = None) -> Path:
    """Pasta onde o emulador procura as texturas do jogo. Valida o formato do
    ID: ele vira nome de pasta, nunca pode carregar '/' ou '..'."""
    if not _ID_JOGO[sistema].match(id_jogo or ""):
        raise TexturaErro(f"ID de jogo inválido para {sistema}: {id_jogo!r}")
    return pasta_base(sistema, cfg) / id_jogo


def _destino_arquivos(sistema: str, id_jogo: str, cfg: dict | None) -> Path:
    base = pasta_jogo(sistema, id_jogo, cfg)
    return base / "replacements" if sistema in ("PS1", "PS2") else base


def estado(pacote: dict, cfg: dict | None = None) -> dict:
    """{'instalado': bool, 'arquivos': int} lendo o manifesto do pacote."""
    man = _ler_manifesto(_destino_arquivos(pacote["sistema"], pacote["id_jogo"], cfg))
    if man and man.get("pacote") == pacote["id"]:
        return {"instalado": True, "arquivos": len(man["arquivos"])}
    return {"instalado": False, "arquivos": 0}


def _ler_manifesto(destino: Path) -> dict | None:
    try:
        return json.loads((destino / MANIFESTO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def baixar(pacote: dict, emit=None, cache_dir: Path = CACHE_DIR) -> Path:
    """Baixa o arquivo do pacote para o cache e confere o SHA-1. Reaproveita o
    arquivo já baixado quando o hash bate."""
    url = pacote["url"]
    if not url.startswith(URL_PERMITIDAS):
        raise TexturaErro("origem do download não permitida")
    nome = re.sub(r"[^A-Za-z0-9._-]", "_", pacote["arquivo"])
    cache_dir.mkdir(parents=True, exist_ok=True)
    final = cache_dir / nome
    if final.is_file() and _sha1(final) == pacote["sha1"]:
        return final
    parcial = cache_dir / (nome + ".part")
    total = pacote.get("tamanho") or 0
    feito = 0
    h = hashlib.sha1()
    req = urllib.request.Request(url, headers={"User-Agent": "PyRetro"})
    with urllib.request.urlopen(req, timeout=60) as r, open(parcial, "wb") as f:
        if not url.startswith(URL_PERMITIDAS) or not r.geturl().startswith("https://"):
            raise TexturaErro("redirecionamento inseguro")
        while chunk := r.read(1 << 20):
            f.write(chunk)
            h.update(chunk)
            feito += len(chunk)
            if emit:
                emit({"type": "progress", "status": "baixando", "feito": feito, "total": total})
    if h.hexdigest() != pacote["sha1"]:
        parcial.unlink(missing_ok=True)
        raise TexturaErro("o SHA-1 do arquivo baixado não bate com o do catálogo; download descartado")
    parcial.replace(final)
    return final


LIMITE_URL = 12 * 1024 ** 3  # bytes; configurável em [texturas] limite_gb


def validar_url(url: str) -> str:
    """Aceita só https para um host público (sem usuário/senha na URL, porta 443).
    Impede que um link vire acesso a serviços da rede local (localhost, 192.168.x, tailnet...).
    Devolve o host."""
    try:
        u = urllib.parse.urlsplit(url)
        porta = u.port
    except ValueError:
        raise TexturaErro("link inválido") from None
    if u.scheme != "https" or not u.hostname:
        raise TexturaErro("o link precisa ser https://")
    if u.username or u.password:
        raise TexturaErro("link com usuário/senha não é aceito")
    if porta not in (None, 443):
        raise TexturaErro("só a porta 443 é aceita")
    try:
        enderecos = {i[4][0] for i in socket.getaddrinfo(u.hostname, 443, proto=socket.IPPROTO_TCP)}
    except OSError as e:
        raise TexturaErro(f"não consegui resolver {u.hostname}: {e}") from None
    for a in enderecos:
        if not ipaddress.ip_address(a.split("%")[0]).is_global:
            raise TexturaErro("o link aponta para um endereço que não é público")
    return u.hostname


class _RedirectSeguro(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validar_url(newurl)  # cada salto passa pela mesma validação
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _nome_do_link(url: str, cabecalhos) -> str:
    nome = ""
    cd = cabecalhos.get("Content-Disposition") or ""
    m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", cd, re.I)
    if m:
        nome = urllib.parse.unquote(m.group(1))
    if not nome:
        nome = urllib.parse.unquote(Path(urllib.parse.urlsplit(url).path).name)
    return nome


def baixar_url(url: str, emit=None, cache_dir: Path = CACHE_DIR, limite: int = LIMITE_URL) -> tuple[Path, str]:
    """Baixa um pacote de um link direto escolhido pelo usuário. Sem hash de referência: devolve
    (arquivo, sha1 calculado) para o usuário registrar. O arquivo precisa ser .zip/.7z/.rar."""
    validar_url(url)
    cache_dir.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(_RedirectSeguro)
    req = urllib.request.Request(url, headers={"User-Agent": "PyRetro"})
    parcial = None
    try:
        with opener.open(req, timeout=60) as r:
            if not r.geturl().startswith("https://"):
                raise TexturaErro("redirecionamento inseguro")
            tipo = (r.headers.get("Content-Type") or "").lower()
            if tipo.startswith("text/html"):
                raise TexturaErro("o link abre uma página, não o arquivo; use o link direto do .zip/.7z/.rar")
            nome = _nome_do_link(r.geturl(), r.headers)
            ext = Path(nome).suffix.lower()
            if ext not in EXTENSOES:
                raise TexturaErro("o link precisa apontar direto para um .zip, .7z ou .rar")
            total = int(r.headers.get("Content-Length") or 0)
            if total > limite:
                raise TexturaErro(f"arquivo grande demais ({total // 1024 ** 2} MB; limite {limite // 1024 ** 2} MB)")
            fd, tmp = tempfile.mkstemp(dir=cache_dir, prefix="link-", suffix=ext)
            parcial = Path(tmp)
            h = hashlib.sha1()
            feito = 0
            with os.fdopen(fd, "wb") as f:
                while chunk := r.read(1 << 20):
                    feito += len(chunk)
                    if feito > limite:
                        raise TexturaErro("o arquivo passou do limite de tamanho; download cancelado")
                    f.write(chunk)
                    h.update(chunk)
                    if emit:
                        emit({"type": "progress", "status": "baixando", "feito": feito, "total": total})
        return parcial, h.hexdigest()
    except (TexturaErro, urllib.error.URLError, OSError):
        if parcial is not None:
            parcial.unlink(missing_ok=True)
        raise


def _sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def validar_arquivo(arquivo: Path) -> None:
    """Valida caminhos, links e tamanho declarado antes de extrair uploads locais."""
    import zipfile
    import stat
    entries=[]
    if arquivo.suffix.lower()=='.zip':
        with zipfile.ZipFile(arquivo) as archive:
            for info in archive.infolist():
                if stat.S_ISLNK(info.external_attr >> 16):raise TexturaErro('links não são aceitos no pacote')
                entries.append((info.filename,info.file_size))
    else:
        if not shutil.which('7z'):raise TexturaErro('7z é necessário para validar RAR/7z antes de extrair')
        listing=subprocess.run(['7z','l','-slt','-ba',str(arquivo)],capture_output=True,text=True,timeout=60,check=False)
        if listing.returncode:raise TexturaErro('não foi possível conferir o arquivo compactado')
        for block in listing.stdout.split('\n\n'):
            fields=dict(line.split(' = ',1) for line in block.splitlines() if ' = ' in line)
            if fields.get('Symbolic Link') or fields.get('Hard Link') or re.search(r'(?:^|\s)l\S{9}(?:\s|$)', fields.get('Attributes','')):
                raise TexturaErro('links não são aceitos no pacote')
            if fields.get('Path'):entries.append((fields['Path'],int(fields.get('Size','0'))))
    if len(entries)>50000 or sum(size for _,size in entries)>LIMITE_URL:raise TexturaErro('pacote extraído grande demais')
    for name,_ in entries:
        normalized=name.replace('\\','/')
        if normalized.startswith('/') or re.match(r'^[A-Za-z]:',normalized) or '..' in normalized.split('/'):
            raise TexturaErro('o arquivo tenta escrever fora da pasta de extração')


def extrair(arquivo: Path, destino: Path) -> None:
    """Extrai .zip/.7z/.rar em `destino` (pasta vazia criada por quem chama).
    zip usa a biblioteca padrão; os outros, 7z ou unrar."""
    validar_arquivo(arquivo)
    ext = arquivo.suffix.lower()
    if ext == ".zip":
        import zipfile
        raiz = destino.resolve()
        with zipfile.ZipFile(arquivo) as z:
            for info in z.infolist():
                alvo = (destino / info.filename).resolve()
                if raiz != alvo and raiz not in alvo.parents:
                    raise TexturaErro("o arquivo tenta escrever fora da pasta de extração")
            z.extractall(destino)
        return
    if ext not in EXTENSOES:
        raise TexturaErro(f"formato não suportado: {ext}")
    for cmd in (["7z", "x", "-y", f"-o{destino}", str(arquivo)],
                ["unrar", "x", "-y", str(arquivo), str(destino) + "/"]):
        if shutil.which(cmd[0]):
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                return
            erro = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["falha"]
            raise TexturaErro(f"{cmd[0]} falhou: {erro[0]}")
    raise TexturaErro("instale p7zip (7z) ou unrar para extrair este pacote")


def _achar_raiz(extraido: Path, id_jogo: str) -> Path:
    """Pasta do pacote que contém as texturas: a pasta chamada como o ID do
    jogo (até 4 níveis), senão a pasta extraída inteira."""
    for nivel in range(5):
        for p in extraido.glob("/".join(["*"] * (nivel + 1))):
            if p.is_dir() and not p.is_symlink() and p.name.upper() == id_jogo.upper():
                return p
    return extraido


def instalar_de_pasta(extraido: Path, sistema: str, id_jogo: str, pacote_id: str,
                      cfg: dict | None = None) -> int:
    """Copia as texturas de uma pasta já extraída para a pasta do emulador.
    Devolve quantos arquivos foram copiados."""
    destino = _destino_arquivos(sistema, id_jogo, cfg)
    raiz = _achar_raiz(extraido, id_jogo)
    if sistema in ("PS1", "PS2") and (raiz / "replacements").is_dir():
        raiz = raiz / "replacements"
    copiados = []
    destino.mkdir(parents=True, exist_ok=True)
    for f in sorted(raiz.rglob("*")):
        if f.is_symlink() or not f.is_file() or f.name == MANIFESTO:
            continue
        rel = f.relative_to(raiz)
        alvo = destino / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, alvo)
        copiados.append(rel.as_posix())
    if not copiados:
        raise TexturaErro("o pacote não trouxe nenhum arquivo de textura")
    (destino / MANIFESTO).write_text(
        json.dumps({"pacote": pacote_id, "arquivos": copiados}), encoding="utf-8")
    return len(copiados)


def instalar(pacote: dict, cfg: dict | None = None, emit=None, arquivo: Path | None = None) -> int:
    """Baixa (ou usa `arquivo` local), extrai e instala. Devolve o nº de arquivos."""
    sistema, id_jogo = pacote["sistema"], pacote["id_jogo"]
    _destino_arquivos(sistema, id_jogo, cfg)  # valida antes de baixar GB
    baixado = arquivo is None
    if baixado:
        arquivo = baixar(pacote, emit)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(dir=CACHE_DIR, prefix="extr-") as tmp:
            if emit:
                emit({"type": "progress", "status": "extraindo"})
            extrair(arquivo, Path(tmp))
            if emit:
                emit({"type": "progress", "status": "instalando"})
            return instalar_de_pasta(Path(tmp), sistema, id_jogo, pacote["id"], cfg)
    finally:
        # cache/ mora dentro do ~/Drive sincronizado: um .rar de centenas de MB
        # subiria para a nuvem à toa. Falhou? Baixa de novo na próxima tentativa.
        if baixado:
            arquivo.unlink(missing_ok=True)


def remover(pacote: dict, cfg: dict | None = None) -> int:
    """Apaga só os arquivos que o manifesto registrou. Devolve quantos."""
    destino = _destino_arquivos(pacote["sistema"], pacote["id_jogo"], cfg)
    man = _ler_manifesto(destino)
    if not man or man.get("pacote") != pacote["id"]:
        raise TexturaErro("este pacote não está instalado pelo PyRetro")
    raiz = destino.resolve()
    n = 0
    for rel in man["arquivos"]:
        f = (destino / rel).resolve()
        if raiz in f.parents and f.is_file():
            f.unlink()
            n += 1
    (destino / MANIFESTO).unlink(missing_ok=True)
    for d in sorted((p for p in destino.rglob("*") if p.is_dir()), reverse=True):
        try:
            d.rmdir()
        except OSError:
            pass
    # pasta do pacote (e a do jogo, quando há "replacements/") só somem se ficaram vazias
    for d in (destino, destino.parent if destino.name == "replacements" else None):
        if d is not None:
            try:
                d.rmdir()
            except OSError:
                pass
    return n


def emulador_aberto(sistema: str) -> bool:
    nome = _PROCESSO[sistema]
    for p in Path("/proc").glob("[0-9]*/comm"):
        try:
            if p.read_text().strip() == nome[:15]:
                return True
        except OSError:
            continue
    return False


_CHAVES = {
    "PS1": ("~/.local/share/duckstation/settings.ini", "TextureReplacements",
            "EnableVRAMWriteReplacements", "true"),
    "PS2": ("~/.var/app/net.pcsx2.PCSX2/config/PCSX2/inis/PCSX2.ini", "EmuCore/GS",
            "LoadTextureReplacements", "true"),
    "GC": ("~/.var/app/org.DolphinEmu.dolphin-emu/config/dolphin-emu/GFX.ini", "Settings",
           "HiresTextures", "True"),
    "WII": ("~/.var/app/org.DolphinEmu.dolphin-emu/config/dolphin-emu/GFX.ini", "Settings",
            "HiresTextures", "True"),
    "PSP": ("~/.var/app/org.ppsspp.PPSSPP/config/ppsspp/PSP/SYSTEM/ppsspp.ini", "Graphics",
            "ReplaceTextures", "True"),
}


def set_loading(sistema: str) -> str:
    """Liga a opção de carregar texturas no .ini do emulador. Devolve
    'ligado', 'ja_ligado' ou levanta TexturaErro (emulador aberto/arquivo ausente)."""
    caminho, secao, chave, valor = _CHAVES[sistema]
    ini = Path(caminho).expanduser()
    if emulador_aberto(sistema):
        raise TexturaErro("feche o emulador antes: ele regrava o .ini ao sair e desfaria a mudança")
    if not ini.is_file():
        raise TexturaErro(f"configuração do emulador não encontrada: {ini}")
    linhas = ini.read_text(encoding="utf-8").splitlines(keepends=True)
    atual, achou = None, False
    for i, l in enumerate(linhas):
        s = l.strip()
        if s.startswith("["):
            atual = s.strip("[]")
        elif atual == secao and re.match(rf"^{re.escape(chave)}\s*=", s):
            if s.split("=", 1)[1].strip().lower() == valor.lower():
                return "ja_ligado"
            linhas[i] = f"{chave} = {valor}\n"
            achou = True
            break
    if not achou:
        for i, l in enumerate(linhas):
            if l.strip() == f"[{secao}]":
                linhas.insert(i + 1, f"{chave} = {valor}\n")
                achou = True
                break
    if not achou:
        linhas += [f"\n[{secao}]\n", f"{chave} = {valor}\n"]
    tmp = ini.with_suffix(ini.suffix + ".pyretro-tmp")
    tmp.write_text("".join(linhas), encoding="utf-8")
    os.replace(tmp, ini)
    return "ligado"


def _normalizar(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", re.sub(r"\(.*?\)|\[.*?\]", "", s.lower())))


def tem_rom(pacote: dict, nomes_rom: list[str]) -> bool:
    """Heurística: o título do pacote tem as mesmas palavras que o nome de
    alguma ROM do mesmo sistema (ignora região/versão entre parênteses e
    pontuação). Igualdade, não "contém": senão "NFS Underground" casaria com
    a ROM de "NFS Underground 2"."""
    alvo = _normalizar(pacote["nome"])
    return bool(alvo) and any(alvo == _normalizar(Path(n).stem) for n in nomes_rom)


# ---------------------------------------------------------------------------
# Índice de fontes externas (core/texturas_fontes.json, gerado por
# tools/gerar_fontes_texturas.py a partir da planilha "Texture Packs Archive").
# São páginas de fórum, não arquivos: o PyRetro só mostra o link para os jogos
# da Biblioteca, e a instalação vai pela importação local (arquivo baixado à mão).
# ---------------------------------------------------------------------------
PLATAFORMAS = {
    "PS1": ("Sony - PlayStation", "PlayStation"),
    "PS2": ("Sony - PlayStation 2", "PlayStation 2"),
    "PSP": ("Sony - PSP",),
    "GC": ("Nintendo - GameCube",),
    "WII": ("Nintendo - Wii",),
    "3DS": ("Nintendo - 3DS",),
}


def carregar_fontes(path: Path = FONTES_PATH) -> list[dict]:
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))["fontes"]


def _chave_nome(s: str) -> frozenset:
    return frozenset(_normalizar(s.replace("&", " and ")))


def fontes_da_biblioteca(jogos: list[dict], sistemas: list[str], fontes: list[dict] | None = None,
                         catalogo: list[dict] | None = None) -> list[dict]:
    """Fontes cujo título é igual (mesma regra de tem_rom) ao nome, ou a um
    nome alternativo, de um jogo da Biblioteca do mesmo sistema. O ID do jogo
    vem do serial da planilha ou, sem ele, do pacote de mesmo nome no catálogo."""
    fontes = carregar_fontes() if fontes is None else fontes
    catalogo = carregar_catalogo() if catalogo is None else catalogo
    nomes = {s: {} for s in sistemas if s in PLATAFORMAS}
    for g in jogos:
        for sis, plats in PLATAFORMAS.items():
            if sis in nomes and g.get("plataforma") in plats:
                for n in [g.get("nome") or "", *(g.get("nomes_alt") or [])]:
                    if _chave_nome(n):
                        nomes[sis].setdefault(_chave_nome(n), g.get("nome"))
    no_cat = {(p["sistema"], _chave_nome(p["nome"])): p["id_jogo"] for p in catalogo}
    out = []
    for f in fontes:
        chave = _chave_nome(f["nome"])
        jogo = nomes.get(f["sistema"], {}).get(chave)
        if not jogo:
            continue
        id_cat = no_cat.get((f["sistema"], chave), "")
        id_jogo = f.get("serial") or id_cat
        if id_jogo and not _CEL_ID[f["sistema"]].match(id_jogo):
            id_jogo = ""
        out.append({**f, "jogo": jogo, "id_jogo": id_jogo, "no_catalogo": bool(id_cat)})
    return out


# ---------------------------------------------------------------------------
# Celular (Android, via adb). Mesma ideia do PC: copia as texturas para a pasta
# do emulador e grava um manifesto. Pastas confirmadas por `adb shell ls` em
# 16/10/2026; a troca de textura em jogo no celular AINDA NÃO foi testada.
#   PS1  DuckStation  Android/data/com.github.stenzek.duckstation/files/textures/<SERIAL>/replacements
#   PSP  PPSSPP Gold  /sdcard/Jogos/PSP/PSP/TEXTURES/<ID>
#   3DS  Lime3DS      /sdcard/Jogos/3DS/load/textures/<TITLE ID DE 16 HEX>
# O DuckStation do Android guarda o settings.ini na área privada do app, então a
# opção "trocar texturas" vai por jogo, em gamesettings/<SERIAL>.ini.
# ---------------------------------------------------------------------------
_CEL_DUCK = "/sdcard/Android/data/com.github.stenzek.duckstation/files"
_CELULAR = {
    "PS1": _CEL_DUCK + "/textures",
    "PSP": "/sdcard/Jogos/PSP/PSP/TEXTURES",
    "3DS": "/sdcard/Jogos/3DS/load/textures",
}
_CEL_ID = dict(_ID_JOGO, **{"3DS": re.compile(r"^[0-9A-F]{16}$")})
_CEL_INI_PSP = "/sdcard/Jogos/PSP/PSP/SYSTEM/ppsspp.ini"
_CEL_INI_3DS = "/sdcard/Jogos/3DS/config/config.ini"


def sistemas_celular() -> list[str]:
    return list(_CELULAR)


def _cel_destino(sistema: str, id_jogo: str) -> str:
    if sistema not in _CELULAR:
        raise TexturaErro(f"sistema sem suporte a texturas no celular: {sistema}")
    if not _CEL_ID[sistema].match(id_jogo or ""):
        raise TexturaErro(f"ID de jogo inválido para {sistema}: {id_jogo!r}")
    base = f"{_CELULAR[sistema]}/{id_jogo}"
    return base + "/replacements" if sistema == "PS1" else base


def estado_celular(pacote: dict, serial: str | None = None) -> dict:
    from core import adb as adb_mod
    destino = _cel_destino(pacote["sistema"], pacote["id_jogo"])
    try:
        bruto = adb_mod.shell(f"cat {adb_mod.shquote(destino + '/' + MANIFESTO)} 2>/dev/null", serial)
        man = json.loads(bruto)
    except (adb_mod.AdbError, ValueError):
        return {"instalado": False, "arquivos": 0}
    if man.get("pacote") == pacote["id"]:
        return {"instalado": True, "arquivos": len(man["arquivos"])}
    return {"instalado": False, "arquivos": 0}


def instalar_celular(pacote: dict, serial: str | None = None, emit=None, arquivo: Path | None = None) -> int:
    """Baixa (ou usa `arquivo`), extrai no PC e envia por adb para o emulador do celular."""
    from core import adb as adb_mod
    sistema, id_jogo = pacote["sistema"], pacote["id_jogo"]
    destino = _cel_destino(sistema, id_jogo)
    baixado = arquivo is None
    if baixado:
        arquivo = baixar(pacote, emit)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(dir=CACHE_DIR, prefix="extr-") as tmp:
            if emit:
                emit({"type": "progress", "status": "extraindo"})
            extrair(arquivo, Path(tmp))
            raiz = _achar_raiz(Path(tmp), id_jogo)
            if sistema == "PS1" and (raiz / "replacements").is_dir():
                raiz = raiz / "replacements"
            arquivos = [f.relative_to(raiz).as_posix() for f in sorted(raiz.rglob("*"))
                        if f.is_file() and not f.is_symlink() and f.name != MANIFESTO]
            if not arquivos:
                raise TexturaErro("o pacote não trouxe nenhum arquivo de textura")
            if emit:
                emit({"type": "progress", "status": "enviando"})
            adb_mod.shell(f"mkdir -p {adb_mod.shquote(destino)}", serial)
            # "dir/." (string): o Path descartaria o ".", e o adb criaria destino/<nome-da-pasta>
            if not adb_mod.push(f"{raiz}/.", destino, serial):
                raise TexturaErro("o adb falhou ao enviar as texturas")
            man = Path(tmp) / MANIFESTO
            man.write_text(json.dumps({"pacote": pacote["id"], "arquivos": arquivos}), encoding="utf-8")
            if not adb_mod.push(man, destino + "/" + MANIFESTO, serial):
                raise TexturaErro("o adb falhou ao gravar o manifesto")
            return len(arquivos)
    except adb_mod.AdbError as e:
        raise TexturaErro(f"celular indisponível: {e}") from e
    finally:
        if baixado:
            arquivo.unlink(missing_ok=True)


def remover_celular(pacote: dict, serial: str | None = None) -> int:
    from core import adb as adb_mod
    destino = _cel_destino(pacote["sistema"], pacote["id_jogo"])
    try:
        man = json.loads(adb_mod.shell(f"cat {adb_mod.shquote(destino + '/' + MANIFESTO)} 2>/dev/null", serial))
    except (adb_mod.AdbError, ValueError):
        raise TexturaErro("este pacote não está instalado pelo PyRetro no celular") from None
    if man.get("pacote") != pacote["id"]:
        raise TexturaErro("este pacote não está instalado pelo PyRetro no celular")
    n = 0
    for rel in man["arquivos"]:
        if ".." in Path(rel).parts or rel.startswith("/"):
            continue
        adb_mod.shell(f"rm -f {adb_mod.shquote(destino + '/' + rel)}", serial)
        n += 1
    adb_mod.shell(f"rm -f {adb_mod.shquote(destino + '/' + MANIFESTO)}; "
                  f"find {adb_mod.shquote(destino)} -depth -type d -empty -delete", serial)
    return n


def _ini_valor(texto: str, secao: str, chave: str, valor: str) -> tuple[str, bool]:
    """Define chave = valor dentro de [secao] num texto .ini; devolve (texto, mudou)."""
    linhas = texto.splitlines(keepends=True)
    atual = None
    for i, l in enumerate(linhas):
        s = l.strip().lstrip("\ufeff")
        if s.startswith("["):
            atual = s.strip("[]")
        elif atual == secao and re.match(rf"^{re.escape(chave)}\s*=", s):
            if s.split("=", 1)[1].strip().lower() == valor.lower():
                return texto, False
            linhas[i] = f"{chave} = {valor}\n"
            return "".join(linhas), True
    for i, l in enumerate(linhas):
        if l.strip().lstrip("\ufeff") == f"[{secao}]":
            linhas.insert(i + 1, f"{chave} = {valor}\n")
            return "".join(linhas), True
    sep = "" if texto.endswith("\n") or not texto else "\n"
    return texto + f"{sep}\n[{secao}]\n{chave} = {valor}\n", True


def set_loading_celular(sistema: str, id_jogo: str, serial: str | None = None) -> str:
    """Liga a troca de textura no emulador do celular. Devolve 'ligado' ou 'ja_ligado'.
    PS1: gamesettings/<SERIAL>.ini do DuckStation; PSP: ppsspp.ini; 3DS: config.ini do Lime3DS."""
    from core import adb as adb_mod
    _cel_destino(sistema, id_jogo)
    if sistema == "PS1":
        remoto, secao, chave, valor = f"{_CEL_DUCK}/gamesettings/{id_jogo}.ini", "TextureReplacements", "EnableVRAMWriteReplacements", "true"
    elif sistema == "PSP":
        remoto, secao, chave, valor = _CEL_INI_PSP, "Graphics", "ReplaceTextures", "True"
    else:
        remoto, secao, chave, valor = _CEL_INI_3DS, "Utility", "custom_textures", "1"
    try:
        # "; true": arquivo ainda inexistente (ex.: gamesettings do jogo) não é erro
        atual = adb_mod.shell(f"cat {adb_mod.shquote(remoto)} 2>/dev/null; true", serial)
        novo, mudou = _ini_valor(atual, secao, chave, valor)
        if not mudou:
            return "ja_ligado"
        with tempfile.TemporaryDirectory(dir=CACHE_DIR if CACHE_DIR.is_dir() else None) as tmp:
            f = Path(tmp) / "ini"
            f.write_text(novo, encoding="utf-8")
            if not adb_mod.push(f, remoto, serial):
                raise TexturaErro("o adb falhou ao gravar a configuração do emulador")
    except adb_mod.AdbError as e:
        raise TexturaErro(f"celular indisponível: {e}") from e
    return "ligado"
