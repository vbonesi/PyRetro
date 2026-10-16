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
  PS2   textures/<SERIAL>/replacements/     (PCSX2, Flatpak)
  GC/Wii Load/Textures/<ID DE 6 LETRAS>/    (Dolphin, Flatpak)
  PSP   PSP/TEXTURES/<ID DO DISCO>/         (PPSSPP, Flatpak)
O PS1 (DuckStation) não tem substituição de textura estável: fica de fora.

Cada emulador também precisa da opção "carregar texturas" ligada; set_loading
liga, mas só com o emulador fechado (ele regrava o .ini ao sair e desfaria a
mudança)."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

CATALOGO_PATH = Path(__file__).parent / "texturas_catalogo.json"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "texturas"
MANIFESTO = ".pyretro-textura.json"
URL_PERMITIDAS = ("https://archive.org/", "https://github.com/", "https://raw.githubusercontent.com/")
EXTENSOES = (".zip", ".7z", ".rar")

_FLATPAK = Path.home() / ".var/app"
_PADRAO = {
    "PS2": _FLATPAK / "net.pcsx2.PCSX2/config/PCSX2/textures",
    "GC": _FLATPAK / "org.DolphinEmu.dolphin-emu/data/dolphin-emu/Load/Textures",
    "WII": _FLATPAK / "org.DolphinEmu.dolphin-emu/data/dolphin-emu/Load/Textures",
    "PSP": _FLATPAK / "org.ppsspp.PPSSPP/config/ppsspp/PSP/TEXTURES",
}
_PROCESSO = {"PS2": "pcsx2-qt", "GC": "dolphin-emu", "WII": "dolphin-emu", "PSP": "PPSSPPSDL"}
_ID_JOGO = {
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
    return base / "replacements" if sistema == "PS2" else base


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


def _sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def extrair(arquivo: Path, destino: Path) -> None:
    """Extrai .zip/.7z/.rar em `destino` (pasta vazia criada por quem chama).
    zip usa a biblioteca padrão; os outros, 7z ou unrar."""
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
    if sistema == "PS2" and (raiz / "replacements").is_dir():
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
