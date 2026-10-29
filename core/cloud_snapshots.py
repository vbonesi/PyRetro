"""Snapshots versionados na nuvem para a Biblioteca (`library.json`) e cópias novas dos Backups.

Substitui a sincronização direta do Insync: o arquivo vivo mora no PC; a cada atualização o PyRetro
envia uma versão nova e imutável, e o Drive (ou qualquer remoto) guarda o histórico.

    snapshots/<nome>/<AAAAmmdd-HHMMSS>-<sha12>   cada versão, nunca sobrescrita
    snapshots/<nome>/latest.json                   ponteiro da versão mais recente (só este PC escreve)
    backups/<caminho>                              arquivos dos Backups, enviados uma vez, sem apagar nada

A retenção manda as versões velhas para a lixeira do provedor (Drive: recuperável por 30 dias).
"""
import hashlib
import json
import os
import time
from pathlib import Path

from core import cloud as cloud_mod


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _stamp(now):
    return time.strftime('%Y%m%d-%H%M%S', time.localtime(now))


def latest(storage, name):
    try:
        return json.loads(storage.get(f'snapshots/{name}/latest.json'))
    except (cloud_mod.NotFound, ValueError):
        return None


def versions(storage, name):
    """Versões guardadas, da mais nova para a mais antiga: [{'path','size','stamp','sha12'}]."""
    rows = []
    for item in storage.list(f'snapshots/{name}'):
        leaf = item['path'].rsplit('/', 1)[-1]
        if leaf == 'latest.json' or '-' not in leaf:
            continue
        stamp, _, sha12 = leaf.rpartition('-')
        rows.append({'path': item['path'], 'size': item['size'], 'stamp': stamp, 'sha12': sha12})
    return sorted(rows, key=lambda r: r['stamp'], reverse=True)


def publish(storage, name, path, keep=30, now=time.time, extra=None):
    """Envia `path` como nova versão se o conteúdo mudou. Devolve {'state': 'enviado'|'igual', ...}."""
    return publish_bytes(storage, name, Path(path).read_bytes(), keep=keep, now=now, extra=extra)


def publish_bytes(storage, name, data, keep=30, now=time.time, extra=None):
    """Publica bytes capturados junto com o checkpoint do diário, sem reler um JSON em alteração."""
    json.loads(data)  # só publica JSON válido: um arquivo pela metade nunca vira "versão atual"
    sha = _sha(data)
    current = latest(storage, name)
    if current and current.get('sha256') == sha:
        if extra and any(current.get(key) != value for key, value in extra.items()):
            storage.put(f'snapshots/{name}/latest.json', json.dumps({**current, **extra}).encode(), overwrite=True)
        return {'state': 'igual', 'sha256': sha}
    leaf = f'{_stamp(now())}-{sha[:12]}'
    try:
        storage.put(f'snapshots/{name}/{leaf}', data)
    except cloud_mod.Exists:
        pass
    pointer = {'file': leaf, 'sha256': sha, 'size': len(data), 'at': now(), **(extra or {})}
    storage.put(f'snapshots/{name}/latest.json', json.dumps(pointer).encode(), overwrite=True)
    trimmed = 0
    for old in versions(storage, name)[keep:]:
        storage.trash(old['path']); trimmed += 1
    return {'state': 'enviado', 'sha256': sha, 'file': leaf, 'trimmed': trimmed}


def restore(storage, name, dest, version=None):
    """Baixa uma versão (a mais recente por padrão) para `dest`, conferindo o hash. A cópia local
    que existia vai para `<dest>.antes-<AAAAmmdd-HHMMSS>` antes de ser substituída."""
    dest = Path(dest)
    if version is None:
        current = latest(storage, name)
        if not current:
            raise cloud_mod.NotFound('não há snapshot na nuvem')
        version = current['file']
    data = storage.get(f'snapshots/{name}/{version}')
    if not version.endswith(_sha(data)[:12]):
        raise ValueError('o snapshot baixado não confere com o hash; nada foi alterado')
    json.loads(data)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        os.replace(dest, dest.with_name(f'{dest.name}.antes-{_stamp(time.time())}'))
    temporary = dest.with_name(dest.name + '.pyretro-part')
    temporary.write_bytes(data)
    os.replace(temporary, dest)
    return {'restored': version, 'bytes': len(data)}


def publish_tree(storage, root, prefix='backups', max_file=256 * 1024 * 1024, workers=8):
    """Envia arquivos novos de `root` para `<prefix>/...` (em paralelo; cada chamada ao Drive leva segundos).
    Nunca sobrescreve nem apaga na nuvem; arquivos maiores que `max_file` e symlinks são ignorados e contados."""
    from concurrent.futures import ThreadPoolExecutor
    root = Path(root)
    if not root.is_dir():
        return {'sent': 0, 'skipped': 0, 'present': 0}
    skipped, wanted = 0, []
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
        for leaf in names:
            path = Path(current) / leaf
            if path.is_symlink() or leaf.endswith(('.part', '.tmp', '.pyretro-part')):
                continue
            if path.stat().st_size > max_file:
                skipped += 1; continue
            wanted.append((f'{prefix}/{path.relative_to(root).as_posix()}', path))

    def send(item):
        rel, path = item
        if storage.exists(rel):
            return 'present'
        try:
            storage.put(rel, path.read_bytes())
        except cloud_mod.Exists:
            return 'present'
        return 'sent'

    with ThreadPoolExecutor(max_workers=workers) as pool:
        outcomes = list(pool.map(send, wanted))
    return {'sent': outcomes.count('sent'), 'skipped': skipped, 'present': outcomes.count('present')}
