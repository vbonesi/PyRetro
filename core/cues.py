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
