"""
Backup unidirecional PC -> Drive pros saves que NÃO moram dentro da
árvore Saves/ sincronizada pelo Google Drive.

A maioria dos emuladores (PCSX2, DuckStation, Kronos, RetroArch) já
foi configurada pra escrever direto dentro de Saves/<algo>/ (ver
config.toml [memcards], [pc] saves_root/states_root, e o .ini de cada
emulador) - pra esses o Google Drive já faz o backup sozinho, sem
precisar de nada aqui.

Dolphin (GC/Wii) é o que sobra: guarda save dentro do próprio
diretório de dados do app (sandbox Flatpak), que não dá pra
redirecionar pra dentro do Drive sem risco de quebrar o app (GC
memcard até dá pra apontar por fora, mas o NAND do Wii é uma estrutura
fixa do próprio Dolphin). Então aqui é só uma cópia (nunca corta,
nunca deleta - mesma regra do sync.py) do que mudou pra dentro de
Saves/Dolphin, espelhando a mesma estrutura que emu_saves.py já usa
pro lado Android->PC do Dolphin/PPSSPP.

Tinha uma entrada "flycast" aqui (VMU do Dreamcast standalone,
Saves/Flycast) - removida em 24/08 junto com a mudança de Dreamcast
pra RetroArch (core Flycast escreve save normal em saves_root/
states_root, sem sandbox pra escapar, igual qualquer outro sistema do
RetroArch) - ver docs/changelog.md.

"Mudou" = arquivo novo OU mtime local mais recente que o mtime já
copiado no Drive (compara por caminho relativo dentro de cada fonte).
Como o fluxo é sempre PC->Drive (uma direção só), não existe conceito
de conflito real aqui - diferente do sync.py (PC<->Android), que
decidiu nunca fazer isso pra saves (ver docs/roadmap.md). Se um
arquivo no Drive foi tocado por outro processo, essa cópia atropela
ele mesmo assim; dry-run mostra a lista antes de aplicar.
"""
import shutil
from pathlib import Path

# cfg_key: chave em config.toml [pc] com a raiz de dados do app.
# rel_root: subpasta dentro dela onde os saves ficam.
# dest_name: espelho dentro de Saves/ (Dolphin/PPSSPP já existem por
# causa do emu_saves.py - Flycast é novo, criado do mesmo jeito).
SOURCES = {
    "dolphin_gc": {
        "cfg_key": "dolphin_data_root",
        "rel_root": "GC",
        "dest_name": "Dolphin/GC",
        "glob": "**/*",
    },
    "dolphin_wii": {
        "cfg_key": "dolphin_data_root",
        "rel_root": "Wii/title",
        "dest_name": "Dolphin/Wii/title",
        "glob": "**/*",
    },
}

# Folga de mtime (segundos) pra não marcar "atualizado" por causa de
# arredondamento de timestamp na cópia anterior (mesma cautela do
# MTIME_EPSILON em sync.py, ver docstring lá).
MTIME_EPSILON = 2.0


def _saves_parent(cfg: dict) -> Path:
    return Path(cfg["pc"]["saves_root"]).expanduser().parent


def plan(cfg: dict) -> list[dict]:
    """Lista o que seria copiado, sem escrever nada. Cada item:
    {source, rel_path, src_path, dest_path, action}, action 'novo' ou
    'atualizado'."""
    saves_parent = _saves_parent(cfg)
    items = []
    for key, info in SOURCES.items():
        data_root = cfg["pc"].get(info["cfg_key"])
        if not data_root:
            continue
        src_root = Path(data_root).expanduser() / info["rel_root"]
        if not src_root.is_dir():
            continue
        dest_root = saves_parent / info["dest_name"]
        for src_path in sorted(src_root.glob(info["glob"])):
            if not src_path.is_file():
                continue
            rel = src_path.relative_to(src_root)
            dest_path = dest_root / rel
            if not dest_path.exists():
                action = "novo"
            elif src_path.stat().st_mtime > dest_path.stat().st_mtime + MTIME_EPSILON:
                action = "atualizado"
            else:
                continue
            items.append({
                "source": key, "rel_path": str(rel),
                "src_path": src_path, "dest_path": dest_path, "action": action,
            })
    return items


def apply(items: list[dict]) -> None:
    for item in items:
        item["dest_path"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item["src_path"], item["dest_path"])
