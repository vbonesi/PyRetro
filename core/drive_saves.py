"""Contrato puro de saves no Drive; sem OAuth, rede ou escrita no acervo.

Espelhar no Android junto com docs/drive-saves.md. Não confundir verificação
de metadados com compare-and-swap remoto: o adaptador precisa garantir publicação.
"""
import hashlib
import json
from core import mobile_sync

GROUP_PATHS = {
    'retro-saves': 'saves', 'retro-states': 'states', 'retro-runtime': 'runtime-logs',
    'psp-saves': 'PPSSPP/SAVEDATA', 'psp-states': 'PPSSPP/PPSSPP_STATE',
    '3ds-saves': 'Lime3DS/sdmc',
}


def layout():
    return [{'group': group, 'path': 'Jogos/Saves/' + path,
             'label': mobile_sync.GROUPS[group]} for group, path in GROUP_PATHS.items()]


def identity(account_id, saves_folder_id, group, local_tree):
    if group not in GROUP_PATHS or any(not isinstance(v, str) or not v for v in
                                     (account_id, saves_folder_id, local_tree)):
        raise ValueError('identidade de sincronização inválida')
    # Array JSON compacto com escapes ASCII: mesma serialização no cliente.
    encoded = json.dumps([1, account_id, saves_folder_id, group, local_tree],
                         ensure_ascii=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def direction(local, remote, baseline):
    for value in (local, remote, baseline):
        if value is not None:
            mobile_sync.valid_hash(value)
    if local == remote: return 'same'
    if local is None: return 'download' if baseline is None else 'conflict'
    if remote is None: return 'upload' if baseline is None else 'conflict'
    if baseline is None: return 'conflict'
    if local == baseline: return 'download'
    if remote == baseline: return 'upload'
    return 'conflict'


def version(row, remote=False):
    if row is None: return None
    if not isinstance(row, dict): raise ValueError('metadados inválidos')
    digest = mobile_sync.valid_hash(row.get('sha256'))
    size = row.get('size')
    if type(size) is not int or not 0 <= size <= mobile_sync.MAX_BYTES:
        raise ValueError('tamanho inválido')
    out = {'sha256': digest, 'size': size}
    if remote:
        for key in ('id', 'version'):
            value = row.get(key)
            if not isinstance(value, str) or not value:
                raise ValueError('id/version do Drive ausente')
            out[key] = value
    return out


def index(group, rows, remote=False):
    if group not in GROUP_PATHS: raise ValueError('grupo inválido')
    out, ids = {}, set()
    for row in rows:
        path = row.get('path') if isinstance(row, dict) else None
        if not mobile_sync.accepted(group, path): raise ValueError('caminho fora do grupo')
        if path in out: raise mobile_sync.Conflict('nomes duplicados; escolha a origem explicitamente')
        out[path] = version(row, remote)
        if remote:
            if out[path]['id'] in ids: raise ValueError('mesmo objeto em caminhos diferentes')
            ids.add(out[path]['id'])
        if len(out) > mobile_sync.MAX_FILES: raise ValueError('mais de 20 mil arquivos')
    return out


def analyze(group, local_rows, remote_rows, baseline, scope):
    mobile_sync.valid_hash(scope)
    left, right = index(group, local_rows), index(group, remote_rows, True)
    if not isinstance(baseline, dict): raise ValueError('baseline inválida')
    for path, digest in baseline.items():
        if not mobile_sync.accepted(group, path): raise ValueError('baseline fora do grupo')
        mobile_sync.valid_hash(digest)
    paths = sorted(left.keys() | right.keys() | baseline.keys())
    if len(paths) > mobile_sync.MAX_FILES: raise ValueError('mais de 20 mil arquivos')
    return {'schema': 1, 'identity': scope, 'group': group, 'rows': [
        {'path': path, 'local': left.get(path), 'remote': right.get(path),
         'baseline': baseline.get(path),
         'direction': direction((left.get(path) or {}).get('sha256'),
                                (right.get(path) or {}).get('sha256'), baseline.get(path))}
        for path in paths]}


def prepare(row, choice, local_now, remote_now):
    """Revalida após escolha humana; nunca traduz ausência em exclusão."""
    if choice not in ('upload', 'download', 'skip'): raise ValueError('escolha inválida')
    if choice == 'skip': return {'action': 'skip'}
    left, right = version(local_now), version(remote_now, True)
    if left != row['local'] or right != row['remote']:
        raise mobile_sync.Conflict('uma ponta mudou; analise e confirme novamente')
    source, target = (left, right) if choice == 'upload' else (right, left)
    if source is None: raise ValueError('não há versão na origem escolhida')
    return {'action': choice, 'path': row['path'], 'source': source, 'expected': target,
            'preserve': target if target and target['sha256'] != source['sha256'] else None}


def confirm(transfer, local_after, remote_after, preserved_hash=None, *, published=False):
    """Retorna hash para baseline só após publicação/recibo verificados.

    `published` não é inferido de HTTP 200: inclui enumeração sem duplicatas,
    checksum nas duas pontas, histórico e confirmação pelo adaptador transacional.
    """
    if not published or transfer.get('action') not in ('upload', 'download'):
        raise mobile_sync.Conflict('transferência ainda não confirmada')
    left, right = version(local_after), version(remote_after, True)
    expected = transfer['source']
    if any(v is None or v['sha256'] != expected['sha256'] or v['size'] != expected['size']
           for v in (left, right)):
        raise mobile_sync.Conflict('conteúdo não confirmado nas duas pontas')
    previous = transfer['preserve']
    if previous and preserved_hash != previous['sha256']:
        raise mobile_sync.Conflict('versão anterior não preservada')
    return expected['sha256']
