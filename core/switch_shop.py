"""Índice de "shop" do Tinfoil para o Switch: lista os dumps de `<drive_roms_root>/NSW/` com UMA
chamada `rclone lsjson -R` e grava `PyRetro-Nuvem/switch/shop.json` no Drive. Cada arquivo vira
`gdrive:/<ID do arquivo>#<nome>`, que o Tinfoil (OAuth somente leitura) baixa direto do Google.

O índice carrega nomes e IDs do acervo: fica só no Drive, nunca no Git. Se o rclone falhar, nada
é gravado (a versão anterior continua valendo)."""
import json
import subprocess
from datetime import datetime

from core import heavy_roms as heavy_mod
from core import switch_upload as upload_mod

NOME_INDICE = "shop.json"
PASTA_NUVEM = "switch"
EXTS = upload_mod.EXTS
PARCIAIS = upload_mod.PARCIAIS


def _destino(cfg: dict) -> str:
    """Pasta `switch/` dentro da nuvem do PyRetro (`[cloud].remote`, senão o padrão do rclone)."""
    base = (cfg.get("cloud") or {}).get("remote")
    if not base:
        base = f"{heavy_mod._rclone_cfg(cfg)['remote']}:Jogos/PyRetro-Nuvem"
    return f"{base.rstrip('/')}/{PASTA_NUVEM}"


def montar(entradas: list, agora: datetime | None = None) -> dict:
    """Converte a saída do `lsjson -R` no JSON do Tinfoil. Ignora pastas, parciais, itens sem ID
    e extensões não suportadas; ordena pelo caminho para o índice ser estável."""
    arquivos = []
    for e in sorted(entradas, key=lambda x: str(x.get("Path") or x.get("Name") or "").casefold()):
        nome = str(e.get("Name") or "")
        baixo = nome.lower()
        if e.get("IsDir") or not e.get("ID") or baixo.endswith(PARCIAIS) or not baixo.endswith(EXTS):
            continue
        arquivos.append({"url": f"gdrive:/{e['ID']}#{nome}", "size": max(int(e.get("Size") or 0), 0)})
    quando = (agora or datetime.now()).strftime("%d/%m/%Y %H:%M")
    return {"files": arquivos, "success": f"PyRetro Shop: {len(arquivos)} arquivo(s), atualizado em {quando}"}


def gerar(cfg: dict, run=subprocess.run, emit=lambda e: None, agora: datetime | None = None) -> dict:
    """Lê a pasta NSW do Drive, monta o índice e o sobe. Levanta OSError sem gravar nada se o
    rclone falhar ou devolver lixo. Devolve {"arquivos": N, "destino": "<pasta>"}."""
    rc = heavy_mod._rclone_cfg(cfg)
    origem = f"{rc['remote']}:{rc['drive_roms_root']}/{upload_mod.CODIGO}"
    emit({"type": "progress", "status": "listando a pasta NSW do Drive"})
    try:
        r = run(["rclone", "lsjson", "-R", "--files-only", origem], capture_output=True, text=True, timeout=600)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        raise OSError(f"rclone indisponível: {e}") from e
    if r.returncode != 0:
        raise OSError(f"rclone não listou a pasta NSW: {(r.stderr or '').strip()[-200:]}")
    try:
        entradas = json.loads(r.stdout)
        if not isinstance(entradas, list):
            raise ValueError("resposta inesperada")
    except ValueError as e:
        raise OSError(f"resposta do rclone ilegível: {e}") from e
    indice = montar(entradas, agora)
    destino = _destino(cfg)
    emit({"type": "progress", "status": "enviando o índice"})
    conteudo = json.dumps(indice, ensure_ascii=False, indent=1)
    try:
        w = run(["rclone", "rcat", f"{destino}/{NOME_INDICE}"], input=conteudo, capture_output=True, text=True, timeout=120)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        raise OSError(f"rclone indisponível: {e}") from e
    if w.returncode != 0:
        raise OSError(f"não consegui gravar o índice no Drive: {(w.stderr or '').strip()[-200:]}")
    return {"arquivos": len(indice["files"]), "destino": destino}


def main(cfg: dict) -> int:
    try:
        r = gerar(cfg)
    except OSError as e:
        print(f"erro: {e}")
        return 1
    print(f"índice do Switch atualizado: {r['arquivos']} arquivo(s) em {r['destino']}/{NOME_INDICE}")
    return 0
