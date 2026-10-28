"""Modelo de armazenamento do PC: onde cada coisa mora hoje e onde passa a morar.

Duas partes, ambas sem escrita:

* `Layout`: resolvedor único de destinos (ROMs por sistema, NSW por título, saves, capas,
  biblioteca, backups). Sem `[storage]` na configuração ele devolve o layout de hoje
  (`~/Drive/Jogos/...`); com `games_root`/`nsw_root` devolve o layout novo. Nada do resto do
  projeto o usa ainda: a migração real (etapa H) liga cada consumidor por categoria.
* `plan`: prévia de uma migração do layout atual para outro, com destinos, tamanhos,
  dependências de disco, colisões, espaço e quem ainda aponta para a pasta antiga.

A migração é SEMPRE cópia verificada, nunca `mv`: apagar de dentro do Insync apaga a cópia da
nuvem. Só depois da verificação o Victor desmarca a pasta no Insync.
"""
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from core import rom_bundles

DEFAULT_GAMES_ROOT = Path.home() / 'Games' / 'PyRetro'
DEFAULT_NSW_ROOT = Path.home() / 'Downloads' / 'NSW'
NSW_CODE = 'NSW'
TAGS = re.compile(r'\s*[\[(][^\])]*[\])]')


def _path(value):
    return Path(value).expanduser()


@dataclass(frozen=True)
class Layout:
    """Destinos de cada categoria. `roms` guarda as ROMs por sistema; NSW tem raiz própria."""
    roms: Path
    nsw: Path
    saves: Path        # contém saves/, states/, runtime-logs/ e as pastas dos emuladores
    capas: Path
    biblioteca: Path
    backups: Path
    bios: Path
    migrated: bool

    @classmethod
    def current(cls, cfg):
        pc = cfg['pc']
        roms = _path(pc['roms_root'])
        return cls(roms=roms, nsw=roms / NSW_CODE, saves=_path(pc['saves_root']).parent, capas=_path(pc['capas_root']),
                   biblioteca=_path(pc['library_root']), backups=_path(pc['backups_root']), bios=roms.parent / 'BIOS',
                   migrated=False)

    @classmethod
    def target(cls, games_root=DEFAULT_GAMES_ROOT, nsw_root=DEFAULT_NSW_ROOT):
        root = _path(games_root)
        return cls(roms=root / 'ROMs', nsw=_path(nsw_root), saves=root / 'Saves', capas=root / 'Capas',
                   biblioteca=root / 'Biblioteca', backups=root / 'Backups', bios=root / 'BIOS', migrated=True)

    @classmethod
    def configured(cls, cfg):
        """Layout em vigor: o novo só quando `[storage] games_root` existe na configuração."""
        storage = cfg.get('storage') or {}
        if storage.get('games_root'):
            return cls.target(storage['games_root'], storage.get('nsw_root') or DEFAULT_NSW_ROOT)
        return cls.current(cfg)

    def rom_dir(self, code):
        return self.nsw if code == NSW_CODE else self.roms / code

    def nsw_title_dir(self, title):
        """Uma pasta por título instalável (base + updates + DLC juntos)."""
        name = nsw_title(title)
        if not name:
            raise ValueError('título NSW inválido')
        return self.nsw / name

    def saves_dir(self, kind='saves'):
        return self.saves / kind


def nsw_title(name):
    """Nome da pasta de um título NSW a partir do nome de um arquivo/pasta: sem extensão, tags
    `[...]`/`(...)` de versão e ID, e sem separadores. Vazio se não sobrar nada."""
    stem = name.rsplit('.', 1)[0] if re.search(r'\.(nsp|nsz|xci|xcz)$', name, re.I) else name
    cleaned = TAGS.sub('', stem).strip(' .-_')
    return re.sub(r'[\\/:*?"<>|\x00-\x1f]', '', cleaned).strip()


def _walk(path):
    """(arquivos, bytes, symlinks) sob `path`, sem seguir links."""
    files = size = 0; links = []
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if entry.is_symlink():
                        links.append(entry.path)
                    elif entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        files += 1; size += entry.stat(follow_symlinks=False).st_size
        except OSError:
            continue
    return files, size, links


def _bundle_problems(folder):
    """Descritores CUE/GDI/M3U de `folder` cujas faixas não existem ou que não dá para ler."""
    problems = []
    for root, _, names in os.walk(folder):
        for name in names:
            suffix = Path(name).suffix.lower()
            if suffix not in rom_bundles.DESCRIPTORS:
                continue
            path = Path(root) / name
            try:
                refs = rom_bundles.references(path.read_text(encoding='utf-8', errors='replace'), suffix)
            except (OSError, ValueError) as error:
                problems.append({'descriptor': str(path.relative_to(folder)), 'problem': f'ilegível: {error}'}); continue
            missing = [r for r in refs if not (path.parent / r).is_file()]
            if missing:
                problems.append({'descriptor': str(path.relative_to(folder)), 'problem': 'faixas ausentes', 'missing': missing})
    return problems


def _inside(child, parent):
    child, parent = Path(os.path.abspath(child)), Path(os.path.abspath(parent))
    return child == parent or parent in child.parents


def _free_space(path):
    probe = Path(os.path.abspath(path))
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    return shutil.disk_usage(probe).free, os.stat(probe).st_dev


def _item(category, source, target, walker, check_bundles=False, note=''):
    files, size, links = walker(source)
    item = {'category': category, 'source': str(source), 'target': str(target), 'files': files, 'bytes': size,
            'symlinks': links[:20], 'symlink_count': len(links), 'target_exists': Path(target).exists(), 'note': note}
    if check_bundles:
        item['bundle_problems'] = _bundle_problems(source)
    return item


def _simple_children(path):
    try:
        return sorted(p for p in Path(path).iterdir() if not p.name.startswith('.'))
    except OSError:
        return []


def plan(cfg, games_root=DEFAULT_GAMES_ROOT, nsw_root=DEFAULT_NSW_ROOT, walker=_walk, consumers=None):
    """Prévia (somente leitura) de copiar o acervo do layout atual para o novo.

    `issues` separa o que BLOQUEIA (`blocking`) do que só pede atenção (`warnings`)."""
    current, target = Layout.current(cfg), Layout.target(games_root, nsw_root)
    jogos = current.roms.parent
    items = []
    # ROMs por sistema (NSW tem tratamento próprio logo abaixo).
    for folder in _simple_children(current.roms):
        if folder.name == NSW_CODE or not folder.is_dir() or folder.is_symlink():
            continue
        items.append(_item('roms', folder, target.rom_dir(folder.name), walker, check_bundles=True))
    # NSW: uma pasta por título instalável; arquivos soltos são agrupados por nome sem tags.
    nsw_review = []
    groups = {}
    for child in _simple_children(current.nsw) if current.nsw.is_dir() else []:
        if child.is_dir() and not child.is_symlink():
            items.append(_item('nsw', child, target.nsw / child.name, walker, note='pasta de título'))
        else:
            title = nsw_title(child.name)
            if title:
                groups.setdefault(title, []).append(child)
            else:
                nsw_review.append(str(child))
    for title, members in sorted(groups.items()):
        files = sum(1 for _ in members); size = sum(m.stat().st_size for m in members if m.is_file())
        items.append({'category': 'nsw', 'source': [str(m) for m in members], 'target': str(target.nsw / title),
                      'files': files, 'bytes': size, 'symlinks': [], 'symlink_count': 0,
                      'target_exists': (target.nsw / title).exists(), 'note': 'arquivos soltos agrupados por título'})
    # Demais categorias: a pasta inteira vai para o mesmo nome dentro de Games/PyRetro.
    for category, source, destination in (('saves', current.saves, target.saves), ('capas', current.capas, target.capas),
                                          ('biblioteca', current.biblioteca, target.biblioteca),
                                          ('backups', current.backups, target.backups), ('bios', current.bios, target.bios)):
        if source.is_dir():
            items.append(_item(category, source, destination, walker))

    blocking, warnings = [], []
    games_root, nsw_root = _path(games_root), _path(nsw_root)
    for root, label in ((games_root, 'a raiz de jogos'), (nsw_root, 'a raiz do NSW')):
        if _inside(root, jogos) or _inside(root, Path.home() / 'Drive'):
            blocking.append(f'{label} não pode ficar dentro do Drive (o Insync a sincronizaria)')
    if _inside(nsw_root, games_root) or _inside(games_root, nsw_root):
        blocking.append('as raízes de jogos e NSW não podem se conter')
    seen = {}
    for item in items:
        key = str(item['target']).casefold()
        if key in seen:
            blocking.append(f'dois itens vão para o mesmo destino: {item["target"]}')
        seen[key] = item
        if item['target_exists']:
            warnings.append(f'o destino já existe e será conferido, não sobrescrito: {item["target"]}')
        if item['symlink_count']:
            warnings.append(f'{item["symlink_count"]} link(s) simbólico(s) em {item["source"]} não serão seguidos')
        for problem in item.get('bundle_problems', []):
            warnings.append(f'{item["source"]}/{problem["descriptor"]}: {problem["problem"]}')
    for path in nsw_review:
        warnings.append(f'NSW: sem nome utilizável para a pasta do título: {path}')
    total = sum(i['bytes'] for i in items)
    nsw_bytes = sum(i['bytes'] for i in items if i['category'] == 'nsw')
    games_bytes = total - nsw_bytes
    free, device = _free_space(games_root)
    nsw_free, nsw_device = _free_space(nsw_root)
    if device == nsw_device:
        if int(total * 1.1) > free:
            blocking.append(f'espaço insuficiente: precisa de {humanize(int(total * 1.1))} (com 10% de folga) e há {humanize(free)} livres')
    else:
        if int(games_bytes * 1.1) > free:
            blocking.append(f'espaço insuficiente em {games_root}: precisa de {humanize(int(games_bytes * 1.1))} e há {humanize(free)}')
        if int(nsw_bytes * 1.1) > nsw_free:
            blocking.append(f'espaço insuficiente em {nsw_root}: precisa de {humanize(int(nsw_bytes * 1.1))} e há {humanize(nsw_free)}')
    return {
        'method': 'copiar e verificar (nunca mv: apagar dentro do Insync apaga a nuvem)',
        'current': {k: str(v) for k, v in vars(current).items() if isinstance(v, Path)},
        'target': {k: str(v) for k, v in vars(target).items() if isinstance(v, Path)},
        'items': items, 'bytes': total, 'files': sum(i['files'] for i in items),
        'free_bytes': free, 'same_filesystem': device == nsw_device,
        'consumers': consumers if consumers is not None else find_consumers(jogos),
        'issues': {'blocking': blocking, 'warnings': warnings},
    }


def find_consumers(old_root, home=None):
    """Quem ainda aponta para a pasta antiga: lançador, overrides do Flatpak e configs do RetroArch.
    Só nomes e chaves, nunca conteúdo de save/credencial."""
    home = _path(home or Path.home()); found = []
    old = str(old_root)
    launcher = home / '.local/bin/bonisarch-emulator'
    try:
        text = launcher.read_text(encoding='utf-8', errors='replace')
        if old in text or 'Drive/Jogos' in text:
            found.append({'kind': 'lançador', 'where': str(launcher), 'detail': 'só aceita ROMs dentro da pasta antiga'})
    except OSError:
        pass
    try:
        apps = subprocess.run(['flatpak', 'list', '--app', '--columns=application'], capture_output=True, text=True, timeout=30).stdout.split()
        for app in apps:
            shown = subprocess.run(['flatpak', 'override', '--user', '--show', app], capture_output=True, text=True, timeout=30).stdout
            for line in shown.splitlines():
                if line.startswith('filesystems=') and old in line:
                    found.append({'kind': 'flatpak', 'where': app, 'detail': line.split('=', 1)[1]})
    except (OSError, subprocess.SubprocessError):
        pass
    cfg = home / '.var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg'
    try:
        for line in cfg.read_text(encoding='utf-8', errors='replace').splitlines():
            key, _, value = line.partition('=')
            if old in value:
                found.append({'kind': 'retroarch', 'where': str(cfg), 'detail': key.strip()})
    except OSError:
        pass
    return found


def humanize(size):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024 or unit == 'TB':
            return f'{size:.1f} {unit}' if unit != 'B' else f'{int(size)} B'
        size /= 1024


def report(result):
    lines = [f'Método: {result["method"]}', f'Total: {result["files"]} arquivos, {humanize(result["bytes"])}; livre no destino: {humanize(result["free_bytes"])}']
    for item in sorted(result['items'], key=lambda i: (i['category'], str(i['source']))):
        source = item['source'] if isinstance(item['source'], str) else f'{len(item["source"])} arquivos'
        lines.append(f'  [{item["category"]}] {source} -> {item["target"]}  ({item["files"]} arq., {humanize(item["bytes"])})')
    lines.append('Ainda apontam para a pasta antiga:')
    lines += [f'  - {c["kind"]}: {c["where"]} ({c["detail"]})' for c in result['consumers']] or ['  (nada)']
    for title, key in (('BLOQUEIOS', 'blocking'), ('Avisos', 'warnings')):
        lines.append(f'{title}:')
        lines += [f'  - {m}' for m in result['issues'][key]] or ['  (nenhum)']
    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    import json
    import retrosync
    parser = argparse.ArgumentParser(description='Prévia somente leitura da migração de armazenamento.')
    parser.add_argument('--games-root', default=str(DEFAULT_GAMES_ROOT))
    parser.add_argument('--nsw-root', default=str(DEFAULT_NSW_ROOT))
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    outcome = plan(retrosync.load_config(), args.games_root, args.nsw_root)
    print(json.dumps(outcome, ensure_ascii=False, indent=1) if args.json else report(outcome))
