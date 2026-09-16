"""Exclusão mútua entre threads e processos para arquivos do PyRetro.

O lock físico fica em /tmp, não ao lado do arquivo protegido: library.json
mora numa pasta sincronizada e um arquivo auxiliar persistente ali seria
enviado para a nuvem sem oferecer proteção entre máquinas.
"""
from contextlib import contextmanager
import fcntl
import hashlib
from pathlib import Path
import tempfile
import threading


_locks_guard = threading.Lock()
_thread_locks: dict[str, threading.RLock] = {}
_local = threading.local()


def _key(path: Path) -> str:
    return str(Path(path).expanduser().resolve())


def _thread_lock(key: str) -> threading.RLock:
    with _locks_guard:
        return _thread_locks.setdefault(key, threading.RLock())


@contextmanager
def exclusive(path: Path):
    """Serializa um ciclo completo de leitura-modificação-gravação.

    É reentrante na mesma thread, necessário porque um job pode chamar um
    helper que também protege seus checkpoints. Entre processos usa flock;
    entre threads do mesmo processo usa RLock.
    """
    key = _key(path)
    lock = _thread_lock(key)
    with lock:
        depths = getattr(_local, "depths", None)
        if depths is None:
            depths = _local.depths = {}
        depth = depths.get(key, 0)
        depths[key] = depth + 1
        if depth:
            try:
                yield
            finally:
                depths[key] -= 1
            return

        digest = hashlib.sha256(key.encode()).hexdigest()
        lock_dir = Path(tempfile.gettempdir()) / "pyretro-locks"
        lock_dir.mkdir(mode=0o700, exist_ok=True)
        lock_path = lock_dir / f"{digest}.lock"
        try:
            with lock_path.open("a+") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle, fcntl.LOCK_UN)
        finally:
            depths.pop(key, None)
