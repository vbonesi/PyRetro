"""Manifestos de discos: dependências explícitas, sem modificar ROMs.

O cliente copia na ordem recebida, conserva os caminhos relativos ao sistema
e só publica o descritor depois das faixas. Não há exclusão automática.
"""
import hashlib
import json
import re
import shlex
from pathlib import PurePosixPath

DESCRIPTORS = {'.cue', '.gdi', '.m3u'}
PAYLOADS = {'.bin', '.wav', '.flac', '.ogg', '.mp3', '.iso', '.chd', '.pbp', '.img', '.raw'}
MAX_TEXT = 1024 * 1024
MAX_FILES = 256
MAX_DEPTH = 16


def relative(value):
    if (not isinstance(value, str) or not value or '\\' in value or ':' in value
            or any(ord(c) < 32 for c in value) or value.startswith('/')
            or any(p in ('', '.', '..') for p in value.split('/'))):
        raise ValueError('referência de disco inválida')
    return PurePosixPath(value)


def references(text, suffix):
    if len(text.encode('utf-8')) > MAX_TEXT:
        raise ValueError('descritor de disco muito grande')
    text = text.lstrip('\ufeff')
    if suffix == '.cue':
        refs = []
        for line in text.splitlines():
            if re.match(r'^\s*FILE\s', line, re.I):
                fields = shlex.split(line.strip())
                if len(fields) != 3:
                    raise ValueError('referência FILE inválida no CUE')
                refs.append(fields[1])
    elif suffix == '.m3u':
        refs = [line.strip() for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith('#')]
    elif suffix == '.gdi':
        lines = [line for line in text.splitlines() if line.strip()]
        try:
            count = int(lines[0]); refs = []
            for line in lines[1:]:
                fields = shlex.split(line)
                if len(fields) != 6:
                    raise ValueError('faixa GDI inválida')
                refs.append(fields[4])
            if count != len(refs):
                raise ValueError('número de faixas GDI inválido')
        except (IndexError, TypeError):
            raise ValueError('GDI inválido') from None
    else:
        return []
    if not refs:
        raise ValueError('descritor de disco sem arquivos associados')
    for ref in refs:
        relative(ref)
    return list(dict.fromkeys(refs))


def manifest(entry, stat, read):
    """Callbacks retornam metadados públicos e texto, nunca caminhos absolutos."""
    relative(entry)
    done, active, files = set(), set(), []

    def visit(name, depth):
        if name in active:
            raise ValueError('referência circular no conjunto de discos')
        if name in done:
            return
        if depth > MAX_DEPTH or len(done) + len(active) >= MAX_FILES:
            raise ValueError('conjunto de discos excede o limite')
        path = relative(name)
        suffix = path.suffix.lower()
        if depth and suffix not in DESCRIPTORS | PAYLOADS:
            raise ValueError('formato de dependência não permitido')
        before = stat(name)
        if before['size'] <= 0:
            raise ValueError('arquivo associado ausente ou vazio')
        active.add(name)
        if suffix in DESCRIPTORS:
            if before['size'] > MAX_TEXT:
                raise ValueError('descritor de disco muito grande')
            refs = references(read(name), suffix)
            if stat(name) != before:
                raise LookupError('descritor mudou durante a análise; tente novamente')
            for ref in refs:
                visit(str(path.parent / relative(ref)), depth + 1)
        active.remove(name); done.add(name)
        files.append({'file': name, 'size': before['size'], 'etag': before['etag'],
                      'source': before['source'], 'descriptor': suffix in DESCRIPTORS})

    visit(entry, 0)
    for row in files:
        if stat(row['file']) != {key: row[key] for key in ('size', 'etag', 'source')}:
            raise LookupError('conjunto mudou durante a análise; tente novamente')
    identity = hashlib.sha256(json.dumps(files, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    return {'version': 1, 'entry': entry, 'id': identity, 'files': files,
            'total_size': sum(f['size'] for f in files)}
