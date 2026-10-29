"""Sincronização de saves e snapshots pela camada de nuvem, a partir do `config.toml`.

`[cloud]` (opcional; sem ele nada sobe):
    remote   = "drive:Jogos/PyRetro-Nuvem"   # qualquer remoto do rclone ou pasta local
    device   = "pc"                           # nome deste dispositivo
    saves_dir = "~/Games/PyRetro/Saves"       # padrão: a pasta de saves em vigor
"""
import threading
import time
from pathlib import Path

from core import cloud as cloud_mod
from core import cloud_saves as cloud_saves_mod
from core import cloud_snapshots as snapshots_mod
from core import library_journal as journal_mod
from core import file_lock

EXCLUDE = ('runtime-logs',)


def is_state(path):
    return bool({'states', 'sstates', 'savestates', 'statesaves', 'ppsspp_state'} & set(path.lower().split('/')[:-1]))


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
                                      group='saves', exclude=EXCLUDE, path_filter=lambda path: not is_state(path))


def engines(cfg, store=None):
    store = store or storage(cfg)
    device = (cfg.get('cloud') or {}).get('device') or 'pc'
    return [saves(cfg, store), cloud_saves_mod.CloudSaves(store, device, saves_root(cfg), group=f'states/{device}',
                                                        exclude=EXCLUDE, path_filter=is_state)]


def status(cfg, store=None):
    """Prévia da sincronização: contagem por ação e a lista (conflitos primeiro)."""
    items = [{**item, 'group': engine.group} for engine in engines(cfg, store) for item in engine.plan()]
    counts = {}
    for item in items:
        counts[item['action']] = counts.get(item['action'], 0) + 1
    order = {'conflict': 0, 'pull': 1, 'push': 2, 'same': 3}
    return {'counts': counts, 'items': sorted(items, key=lambda i: (order.get(i['action'], 9), i['path']))}


def sync(cfg, store=None):
    """Aplica pulls e pushes; conflitos ficam pendentes para o usuário."""
    results = [{**row, 'group': engine.group} for engine in engines(cfg, store) for row in engine.apply()]
    return {'results': results, 'conflicts': [r for r in results if r.get('conflict')],
            'errors': [r for r in results if not r['ok'] and not r.get('conflict')]}


def resolve(cfg, path, choice, sha=None, store=None, group='saves'):
    engine = next((e for e in engines(cfg, store) if e.group == group), None)
    if engine is None:
        raise ValueError('grupo de saves inválido')
    return engine.resolve(path, choice, sha)


# --- Biblioteca e Backups: snapshot direto na nuvem (sem Insync) --------------------------
LAST_SNAPSHOT = {}
_timer = None
_timer_lock = threading.Lock()


def library_file(cfg):
    return Path(cfg['pc']['library_root']).expanduser() / 'library.json'


def journal(cfg):
    """Diário de mudanças da Biblioteca (SQLite ao lado do library.json)."""
    return journal_mod.Journal(library_file(cfg).with_name('library-journal.db'), (cfg.get('cloud') or {}).get('device') or 'pc')


def record_library_change(cfg, before, after):
    """Chamado a cada gravação da Biblioteca: registra o que mudou no diário local (sem rede)."""
    if enabled(cfg):
        journal(cfg).record(before, after)


def publish_snapshots(cfg, store=None):
    """Envia as mudanças novas da Biblioteca (diário) e os arquivos novos dos Backups. O arquivo inteiro só
    vai como snapshot de compactação: o primeiro, a cada 24 h ou depois de muitas mudanças."""
    store = store or storage(cfg)
    result = publish_library(cfg, store)
    result['backups'] = snapshots_mod.publish_tree(store, Path(cfg['pc']['backups_root']).expanduser())
    return result


def publish_library(cfg, store=None):
    store = store or storage(cfg)
    result = {}
    path = library_file(cfg)
    if path.is_file():
        diary = journal(cfg)
        result['journal'] = diary.publish(store)
        latest = snapshots_mod.latest(store, 'library')
        stale = latest is None or 'journal' not in latest or (time.time() - float(latest.get('at', 0))) > 24 * 3600 or diary.count() - int(latest.get('journal_count', 0)) > 2000
        if stale:
            with file_lock.exclusive(path):
                data = path.read_bytes()
                checkpoint = {'journal_count': diary.count(), 'journal': diary.export_state()}
            result['library'] = snapshots_mod.publish_bytes(store, 'library', data, keep=int((cfg.get('cloud') or {}).get('keep', 30)), extra=checkpoint)
    return result


def pull_library(cfg, store=None):
    """Junta na Biblioteca local as mudanças de outros dispositivos (por jogo e campo, vence a mais recente)."""
    from core import library as library_mod
    path = library_file(cfg)
    diary = journal(cfg)
    fetched = diary.fetch(store or storage(cfg))
    with file_lock.exclusive(path):
        _, applied = diary.pull(fetched, library_mod.load_library(path),
                                      save=lambda merged: library_mod.save_library(path, merged, hooks=False))
    return {'applied': applied}


LAST_LIBRARY = {}
_library_sync_lock = threading.Lock()


def sync_library(cfg, store=None):
    """Rotina leve: diário e compactação, sem varrer Backups nem transportar saves."""
    if not _library_sync_lock.acquire(blocking=False):
        return {'busy': True}
    try:
        store = store or storage(cfg)
        out = {**pull_library(cfg, store), **publish_library(cfg, store), 'at': time.time(), 'ok': True}
        LAST_LIBRARY.clear(); LAST_LIBRARY.update(out)
        return out
    except Exception as error:
        LAST_LIBRARY.clear(); LAST_LIBRARY.update(ok=False, error=str(error), at=time.time())
        raise
    finally:
        _library_sync_lock.release()


class LibraryPoller:
    """Uma rotina do servidor: início, pós-jogo e a cada cinco minutos; sem jobs do Codex."""
    def __init__(self, load_config, interval=300):
        self.load_config, self.interval = load_config, interval
        self.stopped, self.wake = threading.Event(), threading.Event()
        self.thread = None

    def start(self):
        if self.thread is not None:
            return
        def run():
            while not self.stopped.is_set():
                try:
                    cfg = self.load_config()
                    if enabled(cfg):
                        sync_library(cfg)
                except Exception:
                    pass  # LAST_LIBRARY guarda erro; a próxima tentativa preserva a fila
                self.wake.wait(self.interval); self.wake.clear()
        self.thread = threading.Thread(target=run, daemon=True, name='pyretro-library')
        self.thread.start()

    def trigger(self):
        self.wake.set()

    def stop(self):
        self.stopped.set(); self.wake.set()


def schedule_library_snapshot(load_config, delay=30):
    """Chamado a cada gravação da Biblioteca: junta várias gravações seguidas em um envio só."""
    global _timer

    def run():
        try:
            cfg = load_config()
            if enabled(cfg):
                LAST_SNAPSHOT.clear(); LAST_SNAPSHOT.update(sync_library(cfg), ok=True)
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
