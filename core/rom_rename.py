"""
Renomeia ROM (+ save/state quando existir) junto com o label - o
"rename com cascata" que faltava: antes, só a capa era renomeada pela
GUI e o resto ficava marcado (renamed_pending) pra rodar
aplicar_pendencias.sh depois. Agora cobre ROM/save/state na hora,
pros sistemas leves ([systems]) E pesados ([heavy_systems]).

ROM: se for .cue/.gdi, usa core.cues.rename_disc_set (corrige sidecars
.bin + a referência de texto dentro do arquivo). Senão, rename simples
do arquivo - ou da pasta inteira, pra formatos tipo Switch que usam
pasta por jogo (fora do escopo de [heavy_systems] hoje, mas a função já
suporta).

Save/state: RetroArch guarda tudo achatado (sem subpasta por sistema)
em saves_root/<label>.<ext> e states_root/<label>.state[.auto] - troca
qualquer arquivo cujo nome comece com "<label antigo>." exatamente.
Sistemas com save gerenciado por emulador standalone (PS1/SDC via
DuckStation/Flycast, PS2/etc via seus próprios apps) simplesmente não
têm arquivo nesse padrão - não acha nada, não faz nada, sem tratamento
especial necessário.

Multi-disco (ex: "Final Fantasy VII (Disc 1)/(Disc 2)/(Disc 3)"): se o
label antigo termina em " (Disc N)", procura os outros discos do mesmo
título base e renomeia o grupo inteiro junto, preservando o "(Disc N)"
de cada um (mesma ideia do "(Track N)" nos sidecars .bin, um nível
acima). O `new_label` digitado pode vir com ou sem o próprio "(Disc N)"
- qualquer um dos dois funciona, porque o sufixo de disco é sempre
extraído do nome ANTIGO de cada disco e reaplicado no nome novo.

Nunca usa glob() com o label do usuário como padrão - nomes de jogo
podem ter `[`, `]`, `*` de verdade (tags de ROM hack, por exemplo), que
o glob interpretaria como coringa em vez de texto literal. Sempre
itera e compara string exata.

`delete_with_cascade`: apaga ROM + capa + save/state de um item -
usado pelo botão "🗑 Apagar" (qualquer capa) e pra processar as
marcadas como duplicada. De propósito NÃO agrupa discos múltiplos como
o rename faz - apagar "Jogo (Disc 2)" apaga só o Disc 2 (e seus
sidecars .bin próprios), nunca os outros discos do mesmo jogo. Rename
agrupar faz sentido (manter nomes consistentes); apagar agrupar seria
perigoso demais (clique errado apagaria o jogo inteiro sem querer)."""
import re
import shutil
from pathlib import Path

from core import cues as cues_mod

_DISC_SUFFIX_RE = re.compile(r" \(Disc \d+\)$")


def _find_disc_group(roms_dir: Path, old_label: str, exts_lower: set) -> list | None:
    """Se old_label é um disco de um jogo multi-disco (termina em
    " (Disc N)") E existem outros discos do mesmo título base na
    pasta, retorna a lista de discos (Path), ordenada. Senão, None -
    trata como item único (comportamento de sempre)."""
    m = _DISC_SUFFIX_RE.search(old_label)
    if not m:
        return None
    base_title = old_label[:m.start()]

    discs = []
    for p in roms_dir.iterdir():
        if not p.is_file() or p.suffix.lower().lstrip(".") not in exts_lower:
            continue
        pm = _DISC_SUFFIX_RE.search(p.stem)
        if pm and p.stem[:pm.start()] == base_title:
            discs.append(p)
    return sorted(discs) if len(discs) > 1 else None


def _rename_disc_group(discs: list, old_label: str, new_label: str) -> dict:
    old_base = old_label[:_DISC_SUFFIX_RE.search(old_label).start()]
    new_base = _DISC_SUFFIX_RE.sub("", new_label)  # aceita new_label com ou sem "(Disc N)"

    plans = [(disc, new_base + disc.stem[len(old_base):]) for disc in discs]

    # passe 1: dry-run em TODOS antes de mexer em qualquer um - evita
    # rename parcial do grupo se um dos discos colidir
    for disc, new_stem in plans:
        if disc.suffix.lower() in (".cue", ".gdi"):
            if cues_mod.rename_disc_set(disc, new_stem, apply=False)["status"] == "conflito":
                return {"status": "conflito", "files": []}
        elif disc.with_name(new_stem + disc.suffix).exists():
            return {"status": "conflito", "files": []}

    # passe 2: aplica de verdade
    files = []
    for disc, new_stem in plans:
        if disc.suffix.lower() in (".cue", ".gdi"):
            r = cues_mod.rename_disc_set(disc, new_stem, apply=True)
            files.append(str(r["primary_new"]))
            files += [str(p) for p in r["sidecars_new"]]
        else:
            dest = disc.with_name(new_stem + disc.suffix)
            disc.rename(dest)
            files.append(str(dest))
    return {"status": "renomeado", "files": files}


def _rename_rom(roms_dir: Path, old_label: str, new_label: str, exts: list) -> dict:
    exts_lower = {e.lower().lstrip(".") for e in exts}
    if not roms_dir.is_dir():
        return {"status": "nao_encontrado", "files": []}

    disc_group = _find_disc_group(roms_dir, old_label, exts_lower)
    if disc_group:
        return _rename_disc_group(disc_group, old_label, new_label)

    matches = [
        p for p in roms_dir.iterdir()
        if p.is_file() and p.stem == old_label and p.suffix.lower().lstrip(".") in exts_lower
    ]
    dir_match = roms_dir / old_label
    if not matches and dir_match.is_dir():
        matches = [dir_match]

    if not matches:
        return {"status": "nao_encontrado", "files": []}
    if len(matches) > 1:
        return {"status": "ambiguo", "files": [str(m) for m in matches]}

    rom = matches[0]
    if rom.is_dir():
        dest = roms_dir / new_label
        if dest.exists():
            return {"status": "conflito", "files": [str(dest)]}
        rom.rename(dest)
        return {"status": "renomeado", "files": [str(dest)]}

    if rom.suffix.lower() in (".cue", ".gdi"):
        r = cues_mod.rename_disc_set(rom, new_label, apply=True)
        if r["status"] == "conflito":
            return {"status": "conflito", "files": []}
        files = [str(r["primary_new"])] + [str(p) for p in r["sidecars_new"]]
        return {"status": "renomeado", "files": files}

    dest = rom.with_name(new_label + rom.suffix)
    if dest.exists():
        return {"status": "conflito", "files": [str(dest)]}
    rom.rename(dest)
    return {"status": "renomeado", "files": [str(dest)]}


def _rename_flat_matches(folder: Path, old_label: str, new_label: str) -> list:
    """saves/states não têm subpasta por sistema - só troca o que
    começar exatamente com "<old_label>." (comparação de string, nunca
    glob - ver docstring do módulo)."""
    if not folder.is_dir():
        return []
    prefix = old_label + "."
    renamed = []
    for p in sorted(folder.iterdir()):
        if not p.is_file() or not p.name.startswith(prefix):
            continue
        rest = p.name[len(old_label):]  # ex: ".srm", ".state.auto"
        dest = p.with_name(new_label + rest)
        if dest.exists():
            continue  # nunca sobrescreve - deixa esse sem renomear
        p.rename(dest)
        renamed.append(str(dest))
    return renamed


def rename_with_cascade(roms_dir: Path, saves_dir: Path, states_dir: Path,
                         old_label: str, new_label: str, exts: list) -> dict:
    """Retorna {"rom": {"status": ..., "files": [...]}, "saves": [...],
    "states": [...]}. Só mexe em save/state se a ROM foi renomeada com
    sucesso (senão ficaria com save/state apontando pra uma ROM que
    ainda tem o nome velho)."""
    rom_result = _rename_rom(roms_dir, old_label, new_label, exts)
    if rom_result["status"] != "renomeado":
        return {"rom": rom_result, "saves": [], "states": []}
    saves = _rename_flat_matches(saves_dir, old_label, new_label)
    states = _rename_flat_matches(states_dir, old_label, new_label)
    return {"rom": rom_result, "saves": saves, "states": states}


def _delete_rom(roms_dir: Path, label: str, exts: list) -> dict:
    """Apaga só O ITEM (arquivo/pasta) que bate exato com label - não
    agrupa discos múltiplos (ver docstring do módulo). Se for .cue/.gdi,
    apaga os sidecars .bin próprios dele junto."""
    exts_lower = {e.lower().lstrip(".") for e in exts}
    if not roms_dir.is_dir():
        return {"status": "nao_encontrado", "files": []}

    matches = [
        p for p in roms_dir.iterdir()
        if p.is_file() and p.stem == label and p.suffix.lower().lstrip(".") in exts_lower
    ]
    dir_match = roms_dir / label
    if not matches and dir_match.is_dir():
        matches = [dir_match]

    if not matches:
        return {"status": "nao_encontrado", "files": []}
    if len(matches) > 1:
        return {"status": "ambiguo", "files": [str(m) for m in matches]}

    rom = matches[0]
    deleted = []
    if rom.is_dir():
        shutil.rmtree(rom)
        deleted.append(str(rom))
    else:
        if rom.suffix.lower() in (".cue", ".gdi"):
            for sc in cues_mod.find_bin_sidecars(rom):
                sc.unlink()
                deleted.append(str(sc))
        rom.unlink()
        deleted.append(str(rom))
    return {"status": "apagado", "files": deleted}


def find_flat_matches(folder: Path, label: str) -> list:
    """Lista (sem apagar) os arquivos de saves_root/states_root que
    pertencem a um label - mesma comparação exata por prefixo (nunca
    glob) do resto do módulo. Usado tanto pela galeria de capas (pra
    mostrar se o jogo tem save/state) quanto pelo delete abaixo."""
    if not folder.is_dir():
        return []
    prefix = label + "."
    return [p for p in sorted(folder.iterdir()) if p.is_file() and p.name.startswith(prefix)]


def delete_flat_matches(folder: Path, label: str) -> list:
    matches = find_flat_matches(folder, label)
    for p in matches:
        p.unlink()
    return [str(p) for p in matches]


def delete_with_cascade(roms_dir: Path, capas_dir: Path | None, saves_dir: Path, states_dir: Path,
                         label: str, exts: list) -> dict:
    """Apaga ROM + capa (se capas_dir for passado - sistemas pesados não
    têm capa, passa None) + save/state de um item. Retorna {"rom":
    {...}, "capa": [...], "saves": [...], "states": [...]}. Sempre
    tenta os quatro, mesmo se a ROM não for encontrada - o item pode já
    ter sido removido de um lado e não do outro, e o usuário quer
    limpar o que sobrou."""
    rom_result = _delete_rom(roms_dir, label, exts)
    capa_deleted = []
    if capas_dir is not None:
        for ext in (".png", ".jpg", ".jpeg"):
            p = capas_dir / (label + ext)
            if p.exists():
                p.unlink()
                capa_deleted.append(str(p))
    saves = delete_flat_matches(saves_dir, label)
    states = delete_flat_matches(states_dir, label)
    return {"rom": rom_result, "capa": capa_deleted, "saves": saves, "states": states}
