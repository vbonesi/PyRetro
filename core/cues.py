"""
Correção de .cue (e no futuro .gdi) e normalização de nomes de disco.

Regra central: o nome do .cue é a fonte da verdade. O(s) arquivo(s)
FILE referenciado(s) devem se chamar:
    - single-track: "<nome do cue>.bin"
    - multi-track:  "<nome do cue> (Track N).bin"
      (respeitando o padrão de zero-padding - "Track 1" vs "Track 01"
      - já usado pelos arquivos existentes na pasta; The Legend of
      Oasis foi normalizado hoje pra 1 dígito pra bater com o resto
      do acervo)

Nunca mexe em folhas .ccd/.img (formato diferente, CCD/IMG, não .bin;
Mega Man X6 e Parasite Eve usam esse formato de propósito).

Nunca deleta .cue sem .bin correspondente - isso é uma ROM que o
usuário ainda vai baixar, não lixo (erro cometido e corrigido hoje).

Funções previstas (ainda não implementadas):
    parse_cue(path: Path) -> list[str]
        Extrai os nomes de arquivo FILE "..." na ordem.

    expected_names(cue_path: Path, existing_files: list[str]) -> list[str]
        Calcula os nomes esperados dado o padrão de dígito já em uso.

    fix_cue(path: Path, rename_bin=False, dry_run=True) -> FixReport
        Corrige a(s) referência(s) FILE dentro do .cue. Se rename_bin
        for True, também renomeia o(s) .bin físico(s) - off por
        padrão, é mais arriscado com o Insync sincronizando junto.
        Sempre faz backup do .cue original antes de escrever.

    scan_folder(path: Path) -> ScanReport
        Classifica cada .cue em: ok | fora_do_padrao | sem_bin (aguardando
        download) | formato_especial (ccd/img, ignorado).

    fix_all(root: Path, dry_run=True) -> ScanReport
"""
import re
from pathlib import Path

_TRACK_SUFFIX_RE = re.compile(r" \(Track \d+\)$")


def find_bin_sidecars(primary: Path) -> list:
    """.bin com o mesmo nome base do .cue/.gdi, ou "<nome> (Track N).bin"
    - não impõe um padrão de zero-padding, só reconhece o que já existe
    na pasta (o texto do sufixo é preservado literal, nunca regerado)."""
    sidecars = []
    for sib in primary.parent.iterdir():
        if sib == primary or not sib.is_file() or sib.suffix.lower() != ".bin":
            continue
        if _TRACK_SUFFIX_RE.sub("", sib.stem) == primary.stem:
            sidecars.append(sib)
    return sorted(sidecars)


def rename_disc_set(primary: Path, new_stem: str, apply: bool = False) -> dict:
    """Renomeia um .cue/.gdi (e no futuro qualquer coisa com FILE "...")
    junto com os .bin sidecars, e reescreve a referência de nome de
    arquivo DENTRO do texto do .cue/.gdi pra apontar pros nomes novos -
    achado em 02/08 durante o desenho do rename com cascata: só
    renomear os arquivos sem atualizar essa referência deixa o .cue
    apontando pro nome velho do .bin, e o emulador não acha mais a
    faixa (jogo não abre). Não mexe em .ccd/.img nem .chd (formatos sem
    essa referência de texto pra corrigir).

    Confere conflito em TODOS os destinos antes de mexer em qualquer
    arquivo - nunca faz rename parcial. Retorna {"status":
    "renomeado"|"conflito"|"seria_renomeado"|"sem_referencia_de_texto",
    "primary_new": Path|None, "sidecars_new": [Path, ...]}."""
    has_text_ref = primary.suffix.lower() in (".cue", ".gdi")
    sidecars = find_bin_sidecars(primary) if has_text_ref else []

    renames = [(primary, primary.with_name(new_stem + primary.suffix))]
    for sc in sidecars:
        track_part = sc.stem[len(primary.stem):]  # "" ou " (Track N)"
        renames.append((sc, sc.with_name(new_stem + track_part + sc.suffix)))

    for _, dst in renames:
        if dst.exists():
            return {"status": "conflito", "primary_new": None, "sidecars_new": []}

    primary_new = renames[0][1]
    sidecars_new = [dst for _, dst in renames[1:]]

    if not apply:
        status = "seria_renomeado" if has_text_ref or not sidecars else "seria_renomeado"
        return {"status": status, "primary_new": primary_new, "sidecars_new": sidecars_new}

    content = primary.read_text(encoding="utf-8", errors="replace") if has_text_ref else None
    if content is not None:
        for (src, dst) in renames[1:]:
            content = content.replace(f'"{src.name}"', f'"{dst.name}"')

    for src, dst in renames:
        src.rename(dst)
    if content is not None:
        primary_new.write_text(content, encoding="utf-8")

    return {"status": "renomeado", "primary_new": primary_new, "sidecars_new": sidecars_new}
