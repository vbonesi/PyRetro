"""Identidade de saves por jogo, somente evidência local e DAT já em cache."""
import os
from pathlib import Path
import re
import unicodedata
from core import covers, library, mobile_sync, serials


def exact_name(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def read_3ds_id(path):
    """Lê só NCCH/NCSD headers; não descriptografa nem infere extdata."""
    with path.open('rb') as source:
        before = os.fstat(source.fileno())
        if before.st_size < 512: raise ValueError('cabeçalho truncado')
        header = source.read(512)
        available = before.st_size
        if header[0x100:0x104] == b'NCSD':
            offset = int.from_bytes(header[0x120:0x124], 'little') * 512
            size = int.from_bytes(header[0x124:0x128], 'little') * 512
            if offset < 512 or size < 512 or offset + size > before.st_size:
                raise ValueError('partição NCSD inválida')
            source.seek(offset); header = source.read(512); available = size
        if header[0x100:0x104] != b'NCCH': raise ValueError('formato não suportado')
        size = int.from_bytes(header[0x104:0x108], 'little') * (512 << header[0x18e])
        if size < 512 or size > available: raise ValueError('conteúdo NCCH truncado')
        title = int.from_bytes(header[0x118:0x120], 'little')
        if title >> 32 != 0x00040000 or title & 0xffffffff == 0:
            raise ValueError('não é aplicação 3DS base')
        after = os.fstat(source.fileno())
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('ROM mudou durante leitura')
        return f'{title:016x}'


def _local_3ds(cfg, names):
    base = Path(cfg['pc']['roms_root']).expanduser()
    root = base / '3DS'
    if root.is_symlink() or not root.resolve().is_relative_to(base.resolve()): return []
    exact, fuzzy = [], []
    keys = {exact_name(n) for n in names}
    norms = {covers.normalize(n) for n in names}
    # Top-level files or explicitly named game directories, no arbitrary full-ROM scan.
    if not root.is_dir(): return []
    for path in root.iterdir():
        if path.is_symlink(): continue
        label = path.name if path.is_dir() else path.stem
        if exact_name(label) not in keys and covers.normalize(label) not in norms: continue
        if path.is_dir():
            files = []
            for parent, dirs, entries in os.walk(path, followlinks=False):
                dirs[:] = [d for d in dirs if not (Path(parent)/d).is_symlink()]
                files.extend(Path(parent)/n for n in entries)
                if len(files) > 256: raise ValueError('muitas ROMs candidatas')
        else: files = [path]
        for candidate in files:
            if candidate.is_symlink() or not candidate.is_file(): continue
            if candidate.suffix.lower() not in ('.3ds', '.cci', '.cxi'): continue
            if not candidate.resolve().is_relative_to(root.resolve()): continue
            (exact if exact_name(label) in keys else fuzzy).append(candidate)
    return exact or fuzzy


def mapping(cfg, game, index=None):
    code = library.rom_code_for_plataforma(game['plataforma'])
    out = {'schema': 1, 'id': game['id'], 'code': code, 'status': 'unknown',
           'titleIds': [], 'candidates': [], 'filters': [], 'extdataStatus': 'not-applicable'}
    names = [game['nome'], *game.get('nomes_alt', [])]
    if code == 'PSP':
        data = (serials.cached_index() if index is None else index).get('PSP', {})
        keys = {exact_name(n) for n in names}; norms = {covers.normalize(n) for n in names}
        exact, near = {}, {}
        for raw, title in data.items() if isinstance(data, dict) else []:
            if not isinstance(title, str) or not isinstance(raw, str) or not re.fullmatch(r'[A-Z]{4}-?\d{5}', raw): continue
            ident = raw.replace('-', '')
            record = {'titleId': ident, 'name': title, 'source': 'redump-psp'}
            if exact_name(title) in keys: exact[ident] = record
            elif covers.normalize(title) in norms: near[ident] = record
        out['candidates'] = sorted((exact or near).values(), key=lambda c: c['titleId'])
        if len(exact) == 1: out['titleIds'] = list(exact)
        out['source'] = serials.DAT_URLS['PSP']
    elif code == '3DS':
        out['extdataStatus'] = 'unknown'
        out['source'] = 'ncch-program-id'
        identified, failed = {}, False
        try:
            paths = _local_3ds(cfg, names)
            for path in paths:
                try:
                    ident = read_3ds_id(path)
                    identified[ident] = {'titleId': ident, 'name': path.stem, 'source': 'ncch-program-id'}
                except (OSError, ValueError): failed = True
        except (OSError, ValueError): failed = True
        out['candidates'] = sorted(identified.values(), key=lambda c: c['titleId'])
        if len(identified) == 1 and not failed: out['titleIds'] = list(identified)
        out['incomplete'] = failed
    else:
        out['status'] = 'unsupported'
        return out
    out['status'] = 'identified' if out['titleIds'] else 'needs-choice' if out['candidates'] else 'unknown'
    for ident in out['titleIds']:
        if code == 'PSP':
            out['filters'].extend({'group': group, 'kind': 'psp-serial', 'titleId': ident}
                                  for group in ('psp-saves', 'psp-states'))
        else:
            out['filters'].append({'group': '3ds-saves', 'kind': '3ds-title', 'titleId': ident,
                                   'high': ident[:8], 'low': ident[8:]})
    return out


def matches(group, path, title_id):
    """Filtro após identificação/escolha explícita. Nunca seleciona extdata por chute."""
    if not mobile_sync.accepted(group, path) or not isinstance(title_id, str): return False
    if group in ('psp-saves', 'psp-states'):
        return bool(re.fullmatch(r'[A-Z]{4}\d{5}', title_id) and path[:9].upper() == title_id)
    if group == '3ds-saves' and re.fullmatch(r'00040000[0-9a-f]{8}', title_id):
        parts = path.lower().split('/')
        return parts[3:7] == ['title', title_id[:8], title_id[8:], 'data']
    return False
