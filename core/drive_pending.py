"""Saves que o celular enviou ao Drive sem poder sobrescrever (ver docs/drive-saves.md).

O app grava `<grupo>/.pyretro-pending/<caminho>/<ms>-<base>.pending`, onde base é o
SHA-256 da versão do Drive que ele viu (ou `none`). O Insync traz esses arquivos para o
PC, e aqui eles são aplicados por `mobile_sync.receive`: gravação condicional com a
versão anterior em `.pyretro-history`. Se o arquivo do PC mudou desde então, é conflito
e nada é substituído; o usuário escolhe usar o do celular ou manter o do PC.
"""
import hashlib
import re
import time
import uuid
from pathlib import Path

from core import mobile_sync

PENDING = '.pyretro-pending'
NAME = re.compile(r'([0-9]{13})-([0-9a-f]{64}|none)\.pending')


def _sha(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _items(cfg, group):
    base = mobile_sync.root(cfg, group) / PENDING
    if not base.is_dir() or base.is_symlink():
        return
    for file in sorted(base.rglob('*.pending')):
        match = NAME.fullmatch(file.name)
        relative = file.parent.relative_to(base).as_posix()
        if not match or file.is_symlink() or not file.is_file() or not mobile_sync.accepted(group, relative):
            continue
        yield file, relative, int(match[1]), (None if match[2] == 'none' else match[2])


def scan(cfg):
    """Pendências de todos os grupos, com o que aconteceria ao aplicar."""
    out = []
    for group in mobile_sync.GROUPS:
        for file, relative, at, base in _items(cfg, group):
            current = mobile_sync.fingerprint(mobile_sync.resolve(cfg, group, relative))
            now = current['sha256'] if current else None
            sha = _sha(file)
            status = 'same' if now == sha else 'apply' if now == base else 'conflict'
            out.append({'group': group, 'path': relative, 'pending': file.name, 'at': at,
                        'size': file.stat().st_size, 'sha256': sha, 'base': base, 'current': now, 'status': status})
    return sorted(out, key=lambda item: (item['group'], item['path'], item['at']))


def _find(cfg, group, relative, pending):
    for file, rel, at, base in _items(cfg, group):
        if rel == relative and file.name == pending:
            return file, base
    raise LookupError('pendência não encontrada; atualize a lista')


def _archive(cfg, group, relative, file, suffix):
    history = mobile_sync.root(cfg, group)
    for part in ('.pyretro-history', *relative.split('/')):
        history = history / part
        if history.is_symlink():
            raise ValueError('pasta de histórico inválida')
        history.mkdir(exist_ok=True)
    file.rename(history / f'{time.time_ns()}-{uuid.uuid4().hex}.{suffix}')
    try:
        file.parent.rmdir()  # pasta vazia da pendência; outras pendências do mesmo arquivo ficam
    except OSError:
        pass


def apply(cfg, group, relative, pending, force=False):
    """Aplica uma pendência. `force` usa a versão do celular mesmo em conflito (a do PC vai
    para o histórico). Devolve o novo estado do arquivo no PC."""
    file, base = _find(cfg, group, relative, pending)
    sha = _sha(file)
    if force:
        current = mobile_sync.fingerprint(mobile_sync.resolve(cfg, group, relative))
        base = current['sha256'] if current else None
    with open(file, 'rb') as stream:
        result = mobile_sync.receive(cfg, group, relative, base, sha, stream, file.stat().st_size)
    _archive(cfg, group, relative, file, 'applied')
    return result


def reject(cfg, group, relative, pending):
    """Mantém o arquivo do PC; a versão do celular vai para o histórico (não é apagada)."""
    file, _ = _find(cfg, group, relative, pending)
    _archive(cfg, group, relative, file, 'rejected')
