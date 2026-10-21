"""Catálogo local da TV: somente disco, sem refresh remoto ou escrita no acervo."""
from pathlib import Path
from urllib.parse import quote

from core import covers, library, pc_games, play


def local_roms(cfg, lib, arcade_names=None):
    root = Path(cfg['pc']['roms_root']).expanduser()
    cover_root = Path(cfg['pc']['capas_root']).expanduser()
    index = library.index_by_rom_name(lib)
    out = []
    for code, info in {**cfg.get('systems', {}), **cfg.get('heavy_systems', {})}.items():
        folder = root / code
        if not folder.is_dir() or not folder.resolve().is_relative_to(root.resolve()):
            continue
        exts = {'.' + e.lower().lstrip('.') for e in info.get('exts', [])}
        seen = set()
        for path in sorted(folder.iterdir()):
            if path.name.startswith('.') or (not path.is_dir() and path.suffix.lower() not in exts):
                continue
            label = path.name if path.is_dir() else path.stem
            if label in seen:
                continue
            # Capas e descritores órfãos não são jogos instalados.
            try:
                if path.is_dir():
                    options = [p for p in path.rglob('*') if p.is_file() and p.suffix.lower() in exts]
                else:
                    if path.suffix.lower() == '.bin' and path.with_suffix('.cue').is_file():
                        continue
                    options = [path]
                valid = False
                for option in options:
                    try:
                        play.validate_bundle(folder, str(option.relative_to(folder)))
                        valid = True
                        break
                    except (OSError, ValueError):
                        continue
            except (OSError, ValueError):
                continue
            if not valid:
                continue
            seen.add(label)
            name = (covers.arcade_display_name(label, arcade_names) or label) if code == 'ARCADE' and arcade_names else label
            tracking = library.rom_tracking_info(index, name, code) or {}
            registered = library.find_for_rom(index, name, code)
            cover = None
            for ext in ('.png', '.jpg'):
                found = cover_root / info.get('capas', '') / 'Named_Boxarts' / (label + ext)
                if found.is_file():
                    cover = _versioned(f'/images/{quote(code)}/{quote(label + ext)}', found)
                    break
            out.append({'name': name, 'platform': info.get('nome') or info.get('capas') or code,
                        'code': code, 'romName': label, 'cover': cover,
                        'tracking': tracking, 'local': True, **({'id': registered['id']} if registered else {})})
    return out


def _versioned(url, path):
    """Capa com ?v=<mtime>: o app Android guarda capas por URL; sem versão, uma capa
    trocada no PC nunca era baixada de novo no celular (mesmo motivo do com_versao)."""
    try:
        return f'{url}?v={int(path.stat().st_mtime)}'
    except OSError:
        return url


def _library_cover(cfg, game):
    if not game.get('capa'):
        return None
    return _versioned('/library-images/' + quote(game['capa']), Path(cfg['pc']['library_root']).expanduser() / game['capa'])


def local_pc(cfg, lib):
    indexes = pc_games.installed_indexes(cfg)
    out = []
    for g in lib['games']:
        if g.get('oculto') or not pc_games.find(cfg, g, indexes):
            continue
        out.append({'id': g['id'], 'name': g['nome'], 'platform': g['plataforma'],
                    'cover': _library_cover(cfg, g),
                    'tracking': g, 'local': True})
    return out


def catalog(cfg, lib, cached, arcade_names=None):
    """Catálogo para busca/sistemas, inclusive capas sem ROM e cache da nuvem."""
    local = local_roms(cfg, lib, arcade_names)
    by_key = {(g['code'], g['romName']): g for g in local}
    index = library.index_by_rom_name(lib)
    for code, info in {**cfg.get('systems', {}), **cfg.get('heavy_systems', {})}.items():
        cover_dir = Path(cfg['pc']['capas_root']).expanduser() / info.get('capas', '') / 'Named_Boxarts'
        names = {p.stem: p.name for p in cover_dir.glob('*') if p.suffix.lower() in ('.png', '.jpg')}
        drive = {g['name']: g for g in cached.get(code, [])}
        exts = {'.' + e.lower().lstrip('.') for e in info.get('exts', [])}
        # Sistemas pesados usam o catálogo, não a coleção maior de capas.
        labels = set(drive) | {g['romName'] for g in local if g['code'] == code} if code in cfg.get('heavy_systems', {}) else set(names)
        for name in sorted(labels):
            label = Path(name).stem if name in drive and not drive[name].get('is_dir') and Path(name).suffix.lower() in exts else name
            key = (code, label)
            if key in by_key:
                continue
            shown = (covers.arcade_display_name(label, arcade_names) or label) if code == 'ARCADE' and arcade_names else label
            registered = library.find_for_rom(index, shown, code)
            by_key[key] = {'name': shown, 'platform': info.get('nome') or info.get('capas') or code,
                           'code': code, 'romName': name, 'cover': _versioned(f'/images/{quote(code)}/{quote(names[label])}', cover_dir / names[label]) if label in names else None,
                           'tracking': library.rom_tracking_info(index, shown, code) or {}, 'local': False,
                           'downloadName': name if name in drive else None, 'driveName': name if name in drive else None,
                           **({'id': registered['id']} if registered else {})}
    pc_local = {g['id'] for g in local_pc(cfg, lib)}
    out = list(by_key.values())
    represented = {g['id'] for x in out if (g := library.find_for_rom(index, x['name'], x['code']))}
    for g in lib['games']:
        sources = g.get('fontes', [])
        if g.get('oculto') or (sources and all(f.startswith('wishlist:') for f in sources)):
            continue
        if g['id'] in represented:
            continue
        out.append({'id': g['id'], 'name': g['nome'], 'platform': g['plataforma'],
                    'cover': _library_cover(cfg, g),
                    'tracking': g, 'local': g['id'] in pc_local})
    return sorted(out, key=lambda g: g['name'].lower())
