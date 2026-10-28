"""Sincronização de saves e snapshots pela camada de nuvem, a partir do `config.toml`.

`[cloud]` (opcional; sem ele nada sobe):
    remote   = "drive:Jogos/PyRetro-Nuvem"   # qualquer remoto do rclone ou pasta local
    device   = "pc"                           # nome deste dispositivo
    saves_dir = "~/Games/PyRetro/Saves"       # padrão: a pasta de saves em vigor
"""
from pathlib import Path

from core import cloud as cloud_mod
from core import cloud_saves as cloud_saves_mod

EXCLUDE = ('runtime-logs',)


def enabled(cfg):
    return bool((cfg.get('cloud') or {}).get('remote'))


def storage(cfg):
    if not enabled(cfg):
        raise ValueError('nuvem não configurada: falta [cloud] remote no config.toml')
    return cloud_mod.RcloneStorage(cfg['cloud']['remote'])


def saves_root(cfg):
    section = cfg.get('cloud') or {}
    if section.get('saves_dir'):
        return Path(section['saves_dir']).expanduser()
    return Path(cfg['pc']['saves_root']).expanduser().parent


def saves(cfg, store=None):
    section = cfg.get('cloud') or {}
    return cloud_saves_mod.CloudSaves(store or storage(cfg), section.get('device') or 'pc', saves_root(cfg),
                                      group='saves', exclude=EXCLUDE)


def status(cfg, store=None):
    """Prévia da sincronização: contagem por ação e a lista (conflitos primeiro)."""
    items = saves(cfg, store).plan()
    counts = {}
    for item in items:
        counts[item['action']] = counts.get(item['action'], 0) + 1
    order = {'conflict': 0, 'pull': 1, 'push': 2, 'same': 3}
    return {'counts': counts, 'items': sorted(items, key=lambda i: (order.get(i['action'], 9), i['path']))}


def sync(cfg, store=None):
    """Aplica pulls e pushes; conflitos ficam pendentes para o usuário."""
    engine = saves(cfg, store)
    results = engine.apply()
    return {'results': results, 'conflicts': [r for r in results if r.get('conflict')],
            'errors': [r for r in results if not r['ok'] and not r.get('conflict')]}


def resolve(cfg, path, choice, sha=None, store=None):
    return saves(cfg, store).resolve(path, choice, sha)
