"""Sincronização de saves e snapshots pela camada de nuvem, a partir do `config.toml`.

`[cloud]` (opcional; sem ele nada sobe):
    remote   = "drive:Jogos/PyRetro-Nuvem"   # qualquer remoto do rclone ou pasta local
    device   = "pc"                           # nome deste dispositivo
    saves_dir = "~/Games/PyRetro/Saves"       # padrão: a pasta de saves em vigor
"""
import threading
from pathlib import Path

from core import cloud as cloud_mod
from core import cloud_saves as cloud_saves_mod
from core import cloud_snapshots as snapshots_mod

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


def auto(cfg):
    """Sincronizar sozinho ao abrir e ao fechar um jogo (`[cloud] auto = true`; desligado por padrão)."""
    return enabled(cfg) and bool((cfg.get('cloud') or {}).get('auto'))


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


# --- Biblioteca e Backups: snapshot direto na nuvem (sem Insync) --------------------------
LAST_SNAPSHOT = {}
_timer = None
_timer_lock = threading.Lock()


def library_file(cfg):
    return Path(cfg['pc']['library_root']).expanduser() / 'library.json'


def publish_snapshots(cfg, store=None):
    """Envia a Biblioteca (se mudou) e os arquivos novos dos Backups. Devolve o resultado de cada um."""
    store = store or storage(cfg)
    result = {}
    path = library_file(cfg)
    if path.is_file():
        result['library'] = snapshots_mod.publish(store, 'library', path, keep=int((cfg.get('cloud') or {}).get('keep', 30)))
    result['backups'] = snapshots_mod.publish_tree(store, Path(cfg['pc']['backups_root']).expanduser())
    return result


def schedule_library_snapshot(load_config, delay=30):
    """Chamado a cada gravação da Biblioteca: junta várias gravações seguidas em um envio só."""
    global _timer

    def run():
        try:
            cfg = load_config()
            if enabled(cfg):
                LAST_SNAPSHOT.clear(); LAST_SNAPSHOT.update(publish_snapshots(cfg), ok=True)
        except Exception as error:  # noqa: BLE001 - erro de rede não pode derrubar o servidor
            LAST_SNAPSHOT.clear(); LAST_SNAPSHOT.update(ok=False, error=str(error))

    with _timer_lock:
        if _timer is not None:
            _timer.cancel()
        _timer = threading.Timer(delay, run); _timer.daemon = True; _timer.start()


if __name__ == '__main__':
    import argparse
    import json
    import retrosync
    parser = argparse.ArgumentParser(description='Nuvem: saves e snapshots.')
    parser.add_argument('command', choices=['status', 'sync', 'publish', 'versions', 'restore-library'])
    parser.add_argument('--version')
    args = parser.parse_args()
    cfg = retrosync.load_config()
    if args.command == 'status':
        print(json.dumps(status(cfg)['counts']))
    elif args.command == 'sync':
        out = sync(cfg); print(json.dumps({'errors': out['errors'], 'conflitos': len(out['conflicts'])}, ensure_ascii=False))
    elif args.command == 'publish':
        print(json.dumps(publish_snapshots(cfg), ensure_ascii=False))
    elif args.command == 'versions':
        for row in snapshots_mod.versions(storage(cfg), 'library'):
            print(row['stamp'], row['sha12'], row['size'])
    else:
        print(snapshots_mod.restore(storage(cfg), 'library', library_file(cfg), args.version))
