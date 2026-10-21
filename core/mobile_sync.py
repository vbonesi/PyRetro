"""Transferências de saves do cliente Android: hashes, CAS e versões preservadas."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import time
import uuid

from core import file_lock

MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000
GROUPS = {
    'retro-saves': 'RetroArch · saves', 'retro-states': 'RetroArch · estados',
    'retro-runtime': 'RetroArch · runtime', 'psp-saves': 'PPSSPP · saves',
    'psp-states': 'PPSSPP · estados', '3ds-saves': '3DS · saves SDMC',
}


class Conflict(ValueError):
    pass


def root(cfg, group):
    if group not in GROUPS:
        raise ValueError('grupo de sincronização inválido')
    pc = cfg['pc']; saves = Path(pc['saves_root']).expanduser()
    roots = {
        'retro-saves': saves, 'retro-states': Path(pc['states_root']).expanduser(),
        'retro-runtime': Path(pc.get('runtime_logs_root', saves.parent/'runtime-logs')).expanduser(),
        'psp-saves': saves.parent/'PPSSPP'/'SAVEDATA',
        'psp-states': saves.parent/'PPSSPP'/'PPSSPP_STATE',
        '3ds-saves': saves.parent/'Lime3DS'/'sdmc',
    }
    return roots[group].resolve()


def groups(cfg):
    return [{'id': group, 'label': label,
             'rootTag': hashlib.sha256(str(root(cfg, group)).encode()).hexdigest()}
            for group, label in GROUPS.items()]


def accepted(group, relative):
    if group not in GROUPS or not isinstance(relative, str) or not relative or len(relative) > 1024:
        return False
    parts = relative.split('/')
    if (relative.startswith('/') or '\\' in relative or ':' in relative or '\0' in relative or
            any(p in ('', '.', '..') or p.startswith('.pyretro-') for p in parts)):
        return False
    if group == 'retro-saves':
        return PurePosixPath(relative).suffix.lower() in {'.srm','.sav','.rtc','.sra','.eep','.fla','.mcr','.mcd','.dat','.dsv','.nv','.nvm','.mem'}
    if group == 'retro-states':
        return bool(re.search(r'\.state(?:\d+|\.auto)?(?:\.png)?$', relative, re.I))
    if group == 'retro-runtime':
        return relative.lower().endswith('.lrtl')
    if group == 'psp-saves':
        return bool(re.fullmatch(r'[A-Z]{4}\d{5}[^/]*(/[^/]+)+', relative))
    if group == 'psp-states':
        return bool(re.fullmatch(r'[A-Z]{4}\d{5}[^/]*\.(ppst|jpg|png)', relative, re.I))
    return bool(re.fullmatch(r'Nintendo 3DS/[0-9a-f]{32}/[0-9a-f]{32}/(?:title/[0-9a-f]{8}/[0-9a-f]{8}/data|extdata/[0-9a-f]{8}/[0-9a-f]{8})/.+', relative, re.I))


def resolve(cfg, group, relative):
    if not accepted(group, relative):
        raise ValueError('arquivo não pertence ao grupo escolhido')
    base = root(cfg, group); path = base
    for part in relative.split('/'):
        path = path/part
        if path.is_symlink():
            raise ValueError('links não são aceitos na sincronização')
    return path


def fingerprint(path):
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError('o destino não é um arquivo regular')
    before = path.stat()
    if before.st_size > MAX_BYTES:
        raise ValueError('arquivo maior que 512 MB')
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024*1024), b''):
            digest.update(block)
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise Conflict('arquivo mudou durante a leitura; feche o emulador e analise novamente')
    return {'sha256': digest.hexdigest(), 'size': after.st_size, 'mtime': after.st_mtime_ns//1000000}


def manifest(cfg, group):
    base = root(cfg, group); files = []
    if base.exists() and not base.is_dir():
        raise ValueError('pasta de sincronização inválida')
    # Não seguir links nem examinar o histórico das versões anteriores.
    for parent, dirs, names in os.walk(base, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.pyretro-'))
        if any((Path(parent)/d).is_symlink() for d in dirs):
            raise ValueError('link de diretório encontrado; análise cancelada')
        for name in sorted(names):
            relative = (Path(parent)/name).relative_to(base).as_posix()
            if not accepted(group, relative):
                continue
            path = resolve(cfg, group, relative); info = fingerprint(path)
            if info is None:
                raise Conflict('arquivo desapareceu durante a análise')
            files.append({'path': relative, **info})
            if len(files) > MAX_FILES:
                raise ValueError('mais de 20 mil arquivos; selecione um grupo menor')
    return {'group': group, 'rootTag': hashlib.sha256(str(base).encode()).hexdigest(), 'files': files}


def valid_hash(value, missing=False):
    if missing and value == '-':
        return None
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
        raise ValueError('hash de comparação ausente ou inválido')
    return value


def check_tag(cfg, group, tag):
    if valid_hash(tag) != hashlib.sha256(str(root(cfg,group)).encode()).hexdigest():
        raise Conflict('pasta do notebook mudou; analise novamente')


@contextmanager
def snapshot(cfg, group, relative, expected):
    expected = valid_hash(expected); path = resolve(cfg, group, relative)
    info = fingerprint(path)
    if info is None or info['sha256'] != expected:
        raise Conflict('origem mudou depois da análise; nenhuma versão foi substituída')
    with tempfile.TemporaryFile() as target:
        with path.open('rb') as source:
            shutil.copyfileobj(source, target, 1024*1024)
        target.seek(0); digest = hashlib.sha256()
        for block in iter(lambda: target.read(1024*1024), b''):
            digest.update(block)
        if digest.hexdigest() != expected:
            raise Conflict('origem mudou durante a transferência')
        target.seek(0)
        yield target, info


def receive(cfg, group, relative, expected, sha256, stream, length):
    expected = valid_hash(expected, missing=True); sha256 = valid_hash(sha256)
    path = resolve(cfg, group, relative)
    if not 0 <= length <= MAX_BYTES:
        raise ValueError('arquivo maior que 512 MB')
    # Recebe e valida antes de criar qualquer pasta do destino real.
    with tempfile.TemporaryFile() as staged:
        remaining = length; digest = hashlib.sha256()
        while remaining:
            block = stream.read(min(1024*1024, remaining))
            if not block:
                raise ValueError('envio interrompido')
            staged.write(block); digest.update(block); remaining -= len(block)
        if digest.hexdigest() != sha256:
            raise ValueError('checksum do envio não confere')
        with file_lock.exclusive(root(cfg, group)):
            current = fingerprint(path)
            current_hash = current['sha256'] if current else None
            # Resposta perdida após sucesso: retry idempotente.
            if current_hash == sha256:
                return current
            if current_hash != expected:
                raise Conflict('destino mudou depois da análise; conflito preservado')
            path.parent.mkdir(parents=True, exist_ok=True)
            resolve(cfg, group, relative)
            fd, name = tempfile.mkstemp(dir=path.parent, prefix='.pyretro-stage-')
            temporary = Path(name); previous = None
            try:
                staged.seek(0)
                with os.fdopen(fd, 'wb') as output:
                    shutil.copyfileobj(staged, output, 1024*1024); output.flush(); os.fsync(output.fileno())
                latest = fingerprint(path)
                if (latest['sha256'] if latest else None) != expected:
                    raise Conflict('destino mudou durante a transferência')
                if current is not None:
                    history = root(cfg, group)
                    for part in ('.pyretro-history', *relative.split('/')):
                        history = history/part
                        if history.is_symlink():
                            raise ValueError('pasta de histórico inválida')
                        history.mkdir(exist_ok=True)
                    previous = history/(str(time.time_ns())+'-'+uuid.uuid4().hex+'.previous')
                    path.rename(previous)
                    if fingerprint(previous)['sha256'] != expected:
                        raise Conflict('destino mudou ao preservar a versão anterior')
                # Publicação sem substituir um arquivo criado por emulador/Insync.
                try:
                    os.link(temporary, path)
                except FileExistsError:
                    raise Conflict('outro processo criou o destino; versões preservadas') from None
                return {'sha256': sha256, 'size': length, 'mtime': path.stat().st_mtime_ns//1000000}
            except Exception:
                if previous is not None and previous.exists():
                    try:
                        os.link(previous, path)
                    except FileExistsError:
                        pass
                raise
            finally:
                temporary.unlink(missing_ok=True)


VERSION_PATTERN = r'[0-9]+-[0-9a-f]{32}\.previous'


def history_path(cfg, group, relative, version):
    if not accepted(group, relative) or not isinstance(version, str) or not re.fullmatch(VERSION_PATTERN, version):
        raise ValueError('versão inválida')
    path = root(cfg, group)
    for part in ('.pyretro-history', *relative.split('/'), version):
        path = path/part
        if path.is_symlink():
            raise ValueError('links não são aceitos no histórico')
    return path


def history(cfg, group):
    base = root(cfg, group); versions = []; current = {}
    start = base/'.pyretro-history'
    if start.is_symlink():
        raise ValueError('histórico inválido')
    for parent, dirs, names in os.walk(start, followlinks=False):
        if any((Path(parent)/name).is_symlink() for name in dirs):
            raise ValueError('link no histórico')
        for name in names:
            relative = Path(parent).relative_to(start).as_posix()
            if not accepted(group, relative) or not re.fullmatch(VERSION_PATTERN, name):
                continue
            info = fingerprint(history_path(cfg, group, relative, name))
            if info is None:
                raise Conflict('histórico mudou durante a leitura')
            if relative not in current:
                latest = fingerprint(resolve(cfg, group, relative))
                current[relative] = latest['sha256'] if latest else '-'
            versions.append({'path': relative, 'version': name, 'created': int(name.split('-')[0])//1000000, 'current': current[relative], **info})
            if len(versions) > MAX_FILES:
                raise ValueError('histórico excede 20 mil versões')
    versions.sort(key=lambda row: int(row['version'].split('-')[0]), reverse=True)
    return {'rootTag': hashlib.sha256(str(base).encode()).hexdigest(), 'versions': versions}


def restore(cfg, group, relative, version, expected, sha256):
    sha256 = valid_hash(sha256)
    path = history_path(cfg, group, relative, version)
    info = fingerprint(path)
    if info is None or info['sha256'] != sha256:
        raise Conflict('versão anterior mudou ou não está disponível')
    # receive preserva também o save atual. A versão escolhida não é consumida.
    with tempfile.TemporaryFile() as staged:
        with path.open('rb') as source:
            remaining = info['size']
            while remaining:
                block = source.read(min(remaining, 1024*1024))
                if not block:
                    raise Conflict('versão mudou durante a cópia')
                staged.write(block); remaining -= len(block)
            if source.read(1):
                raise Conflict('versão mudou durante a cópia')
        staged.seek(0)
        return receive(cfg, group, relative, expected, sha256, staged, info['size'])
