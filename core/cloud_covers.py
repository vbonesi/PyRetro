"""Capas exibidas: blobs imutáveis e ponteiro por identidade, sem varredura do acervo."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import threading
from core import cloud

MAX_BYTES=8*1024*1024
_pool=ThreadPoolExecutor(max_workers=2,thread_name_prefix='pyretro-cover')
_pending=set()
_completed={}
_lock=threading.Lock()
LAST={}


def item_path(identity):
    if not isinstance(identity,str) or not 0<len(identity)<=1024:
        raise ValueError('identidade de capa inválida')
    return 'capas/items/'+hashlib.sha256(identity.encode()).hexdigest()+'.json'


def publish(storage,identity,data):
    if not 0<len(data)<=MAX_BYTES:
        raise ValueError('capa vazia ou grande demais')
    sha=hashlib.sha256(data).hexdigest();blob='capas/blobs/'+sha
    try:storage.put(blob,data)
    except cloud.Exists:
        if storage.get(blob)!=data:raise ValueError('capa remota divergente')
    pointer={'sha256':sha,'size':len(data)};path=item_path(identity)
    try:previous=json.loads(storage.get(path))
    except cloud.NotFound:previous=None
    if previous!=pointer:storage.put(path,json.dumps(pointer).encode(),overwrite=True)
    return pointer


def get(storage,identity):
    pointer=json.loads(storage.get(item_path(identity)));sha=pointer['sha256']
    if not isinstance(sha,str) or len(sha)!=64 or any(c not in 'abcdef0123456789' for c in sha):raise ValueError('hash de capa inválido')
    data=storage.get('capas/blobs/'+sha)
    if not 0<len(data)<=MAX_BYTES or len(data)!=pointer['size'] or hashlib.sha256(data).hexdigest()!=sha:raise ValueError('capa não confere')
    return data


def displayed(cfg,identity,path):
    """Fila limitada: a requisição de imagem não espera pela rede."""
    from core import cloud_sync
    if not cloud_sync.enabled(cfg) or not Path(path).is_file():return
    stamp=(identity,str(path),Path(path).stat().st_mtime_ns)
    with _lock:
        if stamp in _pending or stamp in _completed or len(_pending)>=100:return
        _pending.add(stamp)
    def run():
        try:
            publish(cloud_sync.storage(cfg),identity,Path(path).read_bytes())
            LAST.update(ok=True)
            with _lock:
                _completed[stamp]=True
                if len(_completed)>2000:_completed.pop(next(iter(_completed)))
        except Exception as error:LAST.update(ok=False,error=str(error))
        finally:
            with _lock:_pending.discard(stamp)
    _pool.submit(run)


def displayed_rom(cfg,code,name,path):
    from core import library, recent, cloud_sync
    lib=library.load_library(cloud_sync.library_file(cfg))
    game=library.find_for_rom(library.index_by_rom_name(lib),name,code)
    identity=game['id'] if game else recent.rom_key(code,name)
    canonical=Path(cfg['pc']['library_root']).expanduser()/game['capa'] if game and game.get('capa') else path
    displayed(cfg,identity,canonical if canonical.is_file() else path)


def displayed_library(cfg,relative,path):
    from core import library, cloud_sync
    for game in library.load_library(cloud_sync.library_file(cfg))['games']:
        if game.get('capa')==relative:displayed(cfg,game['id'],path)
