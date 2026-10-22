"""ROMs do acervo para o app Android: somente leitura, um arquivo por pedido.

O celular baixa pelo notebook (Tailscale) o que o PC já tem na pasta
sincronizada. O que só existe no Drive (sistemas pesados) vem do rclone em
streaming, sem gravar nada no PC nem no staging. A versão do arquivo (etag:
tamanho + data) é conferida em cada pedido: uma retomada nunca junta pedaços
de dois arquivos diferentes. Escolha do jogo e da fila continua no celular.
"""
import json
import re
import subprocess
from pathlib import Path

from core import heavy_roms, play

MAX_FILES = 64


def _system(cfg, code):
    info = cfg.get('systems', {}).get(code) or cfg.get('heavy_systems', {}).get(code)
    if not isinstance(code, str) or not info:
        raise ValueError('sistema desconhecido')
    root = Path(cfg['pc']['roms_root']).expanduser() / code
    if root.exists() and not root.resolve().is_relative_to(root.parent.resolve()):
        raise ValueError('pasta do sistema fora do acervo')
    exts = {'.' + e.lower().lstrip('.') for e in info.get('exts', [])}
    return root, exts, code in cfg.get('heavy_systems', {})


def _local_etag(path):
    stat = path.stat()
    return f'{stat.st_size}-{stat.st_mtime_ns}'


def _drive_remote(cfg, code, relative):
    rc = heavy_roms._rclone_cfg(cfg)
    return f"{rc['remote']}:{rc['drive_roms_root']}/{code}/{relative}"


def _rclone_json(args, run=subprocess.run):
    try:
        result = run(['rclone', *args], capture_output=True, text=True, timeout=120)
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        raise ValueError('rclone indisponível no notebook') from error
    if result.returncode:
        raise ValueError('arquivo não encontrado no Drive')
    return json.loads(result.stdout or 'null')


def _drive_etag(entry):
    return f"{max(int(entry.get('Size', 0)), 0)}-{entry.get('ModTime', '')}"


def local_options(cfg, code, name):
    root, exts, _ = _system(cfg, code)
    item = root / play.safe_relative(name)
    if not item.resolve().is_relative_to(root.resolve()):
        raise ValueError('ROM fora da pasta do sistema')
    if item.is_file():
        found = [item]
    elif item.is_dir():
        found = sorted(p for p in item.rglob('*') if p.is_file())
    elif item.parent.is_dir():
        found = sorted(p for p in item.parent.iterdir() if p.is_file() and p.stem == item.name)
    else:
        found = []
    out = []
    for path in found:
        if path.suffix.lower() not in exts or path.is_symlink() or path.name.startswith('.'):
            continue
        if not path.resolve().is_relative_to(root.resolve()) or path.stat().st_size == 0:
            continue
        out.append({'file': str(path.relative_to(root)), 'size': path.stat().st_size,
                    'etag': _local_etag(path), 'source': 'pc'})
    return out[:MAX_FILES]


def drive_options(cfg, code, name, drive_names, run=subprocess.run):
    """Só nomes do catálogo do Drive em cache: nada de busca aproximada."""
    root, exts, heavy = _system(cfg, code)
    if not heavy or name not in drive_names:
        return []
    play.safe_relative(name)
    if '/' in name:
        raise ValueError('selecione um item do catálogo, sem subpastas')
    entry = _rclone_json(['lsjson', '--stat', _drive_remote(cfg, code, name)], run)
    if not isinstance(entry, dict):
        return []
    if entry.get('IsDir'):
        rows = _rclone_json(['lsjson', '-R', '--files-only', _drive_remote(cfg, code, name)], run) or []
        found = [(f"{name}/{row['Path']}", row) for row in rows if isinstance(row, dict) and 'Path' in row]
    else:
        found = [(name, entry)]
    out = []
    for relative, row in sorted(found):
        try:
            play.safe_relative(relative)
        except ValueError:
            continue
        if Path(relative).suffix.lower() in exts and int(row.get('Size', 0)) > 0:
            out.append({'file': relative, 'size': int(row['Size']), 'etag': _drive_etag(row), 'source': 'drive'})
    return out[:MAX_FILES]


def options(cfg, code, name, drive_names, run=subprocess.run):
    local = local_options(cfg, code, name)
    return local or drive_options(cfg, code, name, drive_names, run)


def resolve(cfg, code, relative, etag, drive_names, run=subprocess.run):
    """Arquivo pedido pelo celular, conferido de novo. Etag diferente = origem mudou."""
    root, exts, heavy = _system(cfg, code)
    rel = play.safe_relative(relative)
    if rel.suffix.lower() not in exts:
        raise ValueError('formato não pertence a este sistema')
    path = root / rel
    if path.exists():
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('ROM fora da pasta do sistema')
        current = _local_etag(path)
        if etag and etag != current:
            raise LookupError('ROM mudou no notebook; descarte a cópia parcial e baixe de novo')
        return {'source': 'pc', 'path': path, 'size': path.stat().st_size, 'etag': current}
    if not heavy or rel.parts[0] not in drive_names:
        raise ValueError('ROM não encontrada no notebook nem no catálogo do Drive')
    entry = _rclone_json(['lsjson', '--stat', _drive_remote(cfg, code, str(rel))], run)
    if not isinstance(entry, dict) or entry.get('IsDir'):
        raise ValueError('arquivo não encontrado no Drive')
    current = _drive_etag(entry)
    if etag and etag != current:
        raise LookupError('ROM mudou no Drive; descarte a cópia parcial e baixe de novo')
    return {'source': 'drive', 'remote': _drive_remote(cfg, code, str(rel)),
            'size': int(entry.get('Size', 0)), 'etag': current}


def parse_range(header, size):
    """(início, fim) inclusivos; None sem Range. Só um intervalo, como o celular pede."""
    if not header:
        return None
    match = re.fullmatch(r'bytes=(\d+)-(\d*)', header.strip())
    if not match or int(match[1]) >= size:
        raise IndexError('intervalo inválido')
    start = int(match[1])
    end = min(int(match[2]) if match[2] else size - 1, size - 1)
    if end < start:
        raise IndexError('intervalo inválido')
    return start, end


def send(item, start, end, output, popen=subprocess.Popen):
    """Copia [start, end] para output. Drive: rclone cat com offset, sem arquivo local."""
    remaining = end - start + 1
    if item['source'] == 'pc':
        with item['path'].open('rb') as source:
            source.seek(start)
            while remaining:
                data = source.read(min(1024 * 1024, remaining))
                if not data:
                    raise OSError('ROM ficou menor durante o envio')
                output.write(data)
                remaining -= len(data)
        return
    process = popen(['rclone', 'cat', '--offset', str(start), '--count', str(remaining), item['remote']],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        while remaining:
            data = process.stdout.read(min(1024 * 1024, remaining))
            if not data:
                raise OSError('rclone encerrou antes do fim do arquivo')
            output.write(data)
            remaining -= len(data)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
