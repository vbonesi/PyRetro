"""Armazenamento em nuvem independente de provedor (plano de 28/10: PyRetro como app local-first).

Uma interface pequena (`Storage`) que o resto do PyRetro usa para falar com "a nuvem", sem saber se
é Drive, OneDrive, S3, WebDAV ou uma pasta local:

* `RcloneStorage`: qualquer remoto do rclone (`drive:PyRetro`) ou uma pasta local (que o rclone trata
  como remoto `local`, ótimo para testar sem rede).
* `MemoryStorage`: em memória, para testes rápidos.

Regras da interface, pensadas para provedores "burros" (sem escrita condicional):

* `put(path, data)` recusa sobrescrever (`Exists`) a menos que `overwrite=True`; blobs de conteúdo
  endereçado por hash nunca precisam sobrescrever.
* `trash` manda para a lixeira do provedor quando ele tem (Drive: recuperável por 30 dias).
* Nada aqui apaga em massa nem sincroniza pastas inteiras: só operações por arquivo.
"""
import json
import posixpath
import subprocess
import tempfile
from pathlib import Path
import hashlib
from core import file_lock


class Exists(FileExistsError):
    """O destino já existe e `overwrite` não foi pedido."""


class NotFound(FileNotFoundError):
    pass


def _clean(path):
    if (not isinstance(path, str) or not path or path.startswith('/') or '\\' in path or '\x00' in path
            or any(part in ('', '.', '..') for part in path.split('/'))):
        raise ValueError('caminho remoto inválido: ' + repr(path))
    return path


class Storage:
    """Contrato. `list` devolve [{'path','size'}] de tudo sob `prefix` (recursivo, só arquivos)."""

    def list(self, prefix=''):
        raise NotImplementedError

    def exists(self, path):
        raise NotImplementedError

    def get(self, path):
        raise NotImplementedError

    def put(self, path, data, overwrite=False):
        raise NotImplementedError

    def trash(self, path):
        raise NotImplementedError


class MemoryStorage(Storage):
    def __init__(self):
        self.files = {}
        self.trashed = []

    def list(self, prefix=''):
        prefix = prefix.rstrip('/') + '/' if prefix else ''
        return [{'path': p, 'size': len(d)} for p, d in sorted(self.files.items()) if p.startswith(prefix)]

    def exists(self, path):
        return _clean(path) in self.files

    def get(self, path):
        try:
            return self.files[_clean(path)]
        except KeyError:
            raise NotFound(path) from None

    def put(self, path, data, overwrite=False):
        _clean(path)
        if path in self.files and not overwrite:
            raise Exists(path)
        self.files[path] = bytes(data)

    def trash(self, path):
        self.trashed.append((_clean(path), self.files.pop(path, None)))


class RcloneStorage(Storage):
    """`base` é um remoto do rclone com pasta (`drive:PyRetro`) ou um caminho local."""

    def __init__(self, base, run=subprocess.run, timeout=600):
        self.base, self.run, self.timeout = base.rstrip('/'), run, timeout
        self._ready_parents=set()

    def _write_lock(self,path):
        digest=hashlib.sha256((self.base+'\0'+path).encode()).hexdigest()
        return file_lock.exclusive(Path(tempfile.gettempdir())/('pyretro-cloud-write-'+digest))

    def _ensure_dir(self,path):
        parent=posixpath.dirname(path)
        if parent in self._ready_parents:return
        # mkdir recursivo no Drive não é único por nome. Serializar a criação da árvore,
        # inclusive entre processos, antes dos uploads paralelos evita pastas duplicadas.
        with self._write_lock(''):
            if parent not in self._ready_parents:
                self._rclone('mkdir',self._remote(parent));self._ready_parents.add(parent)

    def _remote(self, path=''):
        return self.base + ('/' + path if path else '')

    def _rclone(self, *args, input=None, check=True):
        done = self.run(['rclone', *args], capture_output=True, input=input, timeout=self.timeout)
        if check and done.returncode != 0:
            message = (done.stderr or b'').decode('utf-8', 'replace').strip()
            if done.returncode == 3 or 'not found' in message.lower():
                raise NotFound(message)
            raise OSError(message or f'rclone falhou ({done.returncode})')
        return done

    def list(self, prefix=''):
        if prefix:
            _clean(prefix.rstrip('/'))
        done = self._rclone('lsjson', '-R', '--files-only', '--no-mimetype', '--no-modtime', self._remote(prefix.rstrip('/')), check=False)
        if done.returncode == 3:  # pasta inexistente = vazio
            return []
        if done.returncode != 0:
            raise OSError((done.stderr or b'').decode('utf-8', 'replace').strip())
        base = prefix.rstrip('/')
        return [{'path': posixpath.join(base, row['Path']) if base else row['Path'], 'size': int(row['Size'])}
                for row in json.loads(done.stdout or b'[]') if not row.get('IsDir')]

    def exists(self, path):
        done = self._rclone('lsjson', '--stat', '--no-mimetype', '--no-modtime', self._remote(_clean(path)), check=False)
        return done.returncode == 0 and not json.loads(done.stdout or b'null').get('IsDir', False)

    def get(self, path):
        return self._rclone('cat', self._remote(_clean(path))).stdout

    def put(self, path, data, overwrite=False):
        _clean(path)
        with self._write_lock(path):
            self._ensure_dir(path)
            return self._put(path,data,overwrite)

    def _put(self,path,data,overwrite):
        if not overwrite and self.exists(path):
            raise Exists(path)
        with tempfile.TemporaryDirectory(prefix='pyretro-cloud-') as tmp:
            source = Path(tmp) / 'dados'
            source.write_bytes(data)
            if overwrite and self.exists(path):
                # Troca por renomeação no próprio destino: quem lê vê o arquivo antigo ou o novo inteiro.
                staging = path + '.pyretro-novo'
                self._rclone('copyto', str(source), self._remote(staging))
                self._rclone('moveto', self._remote(staging), self._remote(path))
            else:
                self._rclone('copyto', str(source), self._remote(path))

    def trash(self, path):
        self._rclone('deletefile', self._remote(_clean(path)))
