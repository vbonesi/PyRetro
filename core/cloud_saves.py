"""Saves na nuvem, sem depender do Insync nem de escrita condicional (plano de 28/10, etapa G).

Funciona sobre qualquer `core.cloud.Storage` (rclone, pasta local, memória). Desenho para provedores
"burros", sem compare-and-swap:

    <grupo>/blobs/<sha256>            conteúdo imutável (nunca sobrescrito, nunca apagado por aqui)
    <grupo>/devices/<dispositivo>.json  manifesto que SÓ aquele dispositivo escreve

Como cada dispositivo escreve só o próprio manifesto, dois aparelhos nunca disputam o mesmo
arquivo. A versão "atual" de um save é o conjunto de cabeças: entradas que nenhuma outra entrada
declara como `base`. Uma única cabeça = sem conflito; várias = conflito, e nada é sobrescrito até
o usuário escolher. Todo conteúdo antigo continua nos blobs (histórico) e, no PC, em
`.pyretro-history/` antes de qualquer substituição local.

O estado local guarda só a linha de base (o hash da última sincronização de cada arquivo).
"""
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from core import cloud as cloud_mod

SKIP_DIRS = {'.pyretro-pending', '.pyretro-history', '.pyretro-cloud', '.pyretro-conflicts'}
PART = '.pyretro-part'
MAX_BYTES = 512 * 1024 * 1024


class Conflict(ValueError):
    pass


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(rel):
    """Caminho relativo aceito (vindo do disco ou, principalmente, de um manifesto remoto)."""
    if (not isinstance(rel, str) or not rel or rel.startswith('/') or '\\' in rel or '\x00' in rel
            or any(part in ('', '.', '..') or part in SKIP_DIRS or part.endswith(PART) for part in rel.split('/'))):
        raise ValueError('caminho de save inválido: ' + repr(rel))
    return rel


def decide(local, baseline, heads):
    """Ação para UM arquivo: 'none' | 'same' | 'push' | 'pull' | 'conflict'.

    `local`: hash do arquivo no disco (None se não existe). `baseline`: hash da última sincronização.
    `heads`: conjunto de hashes atuais na nuvem."""
    heads = set(heads)
    if local is None:
        if not heads:
            return 'none'
        return 'pull' if len(heads) == 1 else 'conflict'  # restaurar o que falta; nunca propaga exclusão
    if not heads:
        return 'push'
    if heads == {local}:
        return 'same'
    if local == baseline:  # não mudei desde a última sincronização
        return 'pull' if len(heads) == 1 else 'conflict'
    if baseline is not None and heads == {baseline}:  # só eu mudei
        return 'push'
    return 'conflict'


class CloudSaves:
    def __init__(self, storage, device, root, group='saves', state_path=None, now=time.time, exclude=(), workers=8, path_filter=None):
        if not device or '/' in device or device.startswith('.'):
            raise ValueError('nome de dispositivo inválido')
        self.storage, self.device, self.root, self.group, self.now = storage, device, Path(root), group, now
        self.workers = workers
        self.exclude = set(exclude)  # pastas de topo que nunca sobem (ex.: runtime-logs)
        self.path_filter = path_filter or (lambda path: True)
        self.state_path = Path(state_path) if state_path else self.root / '.pyretro-cloud' / f'{group}.json'

    # --- estado local -------------------------------------------------------------------
    def _baseline(self):
        try:
            return json.loads(self.state_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}

    def _save_baseline(self, baseline):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_name(self.state_path.name + PART)
        temporary.write_text(json.dumps(baseline, sort_keys=True, indent=1), encoding='utf-8')
        os.replace(temporary, self.state_path)

    def local_files(self):
        """{caminho: sha256} do disco. O hash só é refeito quando tamanho ou data mudam (cache ao lado
        do estado); um save que mudou sem mudar tamanho nem data, caso raro, só é visto na próxima edição."""
        cache_path = self.state_path.with_name(self.state_path.stem + '.hashes.json')
        try:
            cache = json.loads(cache_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            cache = {}
        found, fresh = {}, {}
        for current, dirs, names in os.walk(self.root):
            here = Path(current)
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (here / d).is_symlink()
                       and not (here == self.root and d in self.exclude)]
            for name in names:
                path = here / name
                if path.is_symlink() or name.endswith(PART):
                    continue
                rel = path.relative_to(self.root).as_posix()
                if not self.path_filter(rel):
                    continue
                stat = path.stat()
                known = cache.get(rel)
                if known and known[0] == stat.st_size and known[1] == stat.st_mtime_ns:
                    sha = known[2]
                else:
                    sha = sha256_file(path)
                found[rel] = sha; fresh[rel] = [stat.st_size, stat.st_mtime_ns, sha]
        if fresh != cache:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache_path.with_name(cache_path.name + PART)
            temporary.write_text(json.dumps(fresh, sort_keys=True), encoding='utf-8')
            os.replace(temporary, cache_path)
        return found

    # --- nuvem --------------------------------------------------------------------------
    def _manifest_path(self, device):
        return f'{self.group}/devices/{device}.json'

    def manifests(self):
        out = {}
        for item in self.storage.list(f'{self.group}/devices'):
            name = item['path'].rsplit('/', 1)[-1]
            if not name.endswith('.json'):
                continue
            try:
                data = json.loads(self.storage.get(item['path']))
            except (ValueError, cloud_mod.NotFound):
                continue  # manifesto ilegível não derruba os outros dispositivos
            if isinstance(data, dict) and isinstance(data.get('files'), dict):
                out[name[:-5]] = data
        return out

    @staticmethod
    def heads(manifests):
        """{caminho: {sha: [dispositivos]}} só com as cabeças (versões não substituídas)."""
        entries, written = {}, {}
        for device, manifest in manifests.items():
            for rel, entry in manifest['files'].items():
                try:
                    safe_relative(rel)
                    sha = entry['sha256']
                    if not (isinstance(sha, str) and len(sha) == 64):
                        continue
                    at = float(entry.get('at') or 0)
                except (ValueError, KeyError, TypeError):
                    continue
                entries.setdefault(rel, []).append((device, sha, entry.get('base') or [], at))
                written[(rel, sha)] = max(written.get((rel, sha), 0.0), at)
        # Uma entrada só substitui outra MAIS ANTIGA: duas entradas que citam uma à outra (resolução de
        # conflito a favor de um lado enquanto o outro enviava) não podem se anular e sumir com o save.
        superseded = set()
        for rel, rows in entries.items():
            for _device, _sha, base, at in rows:
                for b in base:
                    if isinstance(b, str) and (rel, b) not in superseded and written.get((rel, b), 0.0) <= at:
                        superseded.add((rel, b))
        result = {}
        for rel, rows in entries.items():
            heads = {}
            for device, sha, _base, _at in rows:
                if (rel, sha) not in superseded:
                    heads.setdefault(sha, []).append(device)
            if heads:
                result[rel] = heads
        return result

    # --- planejar e aplicar -------------------------------------------------------------
    def plan(self):
        local, baseline, heads = self.local_files(), self._baseline(), self.heads(self.manifests())
        items = []
        for rel in sorted(set(local) | set(heads)):
            if not self.path_filter(rel):
                continue
            action = decide(local.get(rel), baseline.get(rel), heads.get(rel, {}))
            if action == 'same' and baseline.get(rel) == local.get(rel):
                continue  # já sincronizado: nada a fazer
            if action != 'none':
                items.append({'path': rel, 'action': action, 'local': local.get(rel), 'baseline': baseline.get(rel),
                              'heads': {sha: sorted(devs) for sha, devs in heads.get(rel, {}).items()}})
        return items

    def apply(self, items=None):
        """Executa a prévia. Conflitos não são resolvidos aqui (ver `resolve`). Devolve um resultado por
        arquivo; um erro num arquivo não interrompe os demais."""
        items = self.plan() if items is None else items
        baseline, manifests = self._baseline(), self.manifests()
        own = manifests.get(self.device) or {'version': 1, 'device': self.device, 'generation': 0, 'files': {}}
        results, wrote = [], False
        pushes = []
        for item in items:
            rel, action = item['path'], item['action']
            try:
                safe_relative(rel)
                if action == 'push':
                    pushes.append(item); continue  # o envio dos blobs roda em paralelo, logo abaixo
                if action == 'pull':
                    self._pull(rel, next(iter(item['heads'])), baseline)
                elif action == 'same':
                    baseline[rel] = item['local']
                results.append({'path': rel, 'action': action, 'ok': action != 'conflict',
                                **({'conflict': item['heads']} if action == 'conflict' else {})})
            except (OSError, ValueError, cloud_mod.NotFound, Conflict) as error:
                results.append({'path': rel, 'action': action, 'ok': False, 'error': str(error)})
        if pushes:
            # Cada chamada ao Drive leva segundos; vários blobs ao mesmo tempo (o manifesto só sai depois).
            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                outcomes = list(pool.map(self._upload_blob, pushes))
            for item, (entry, error) in zip(pushes, outcomes):
                if error:
                    results.append({'path': item['path'], 'action': 'push', 'ok': False, 'error': error})
                else:
                    own['files'][item['path']] = entry; baseline[item['path']] = entry['sha256']; wrote = True
                    results.append({'path': item['path'], 'action': 'push', 'ok': True})
        if wrote:
            own['generation'] = int(own.get('generation', 0)) + 1
            own['updated'] = self.now()
            self.storage.put(self._manifest_path(self.device), json.dumps(own, sort_keys=True).encode('utf-8'), overwrite=True)
        self._save_baseline(baseline)
        return results

    def _upload_blob(self, item):
        """Envia o blob de um arquivo e devolve (entrada do manifesto, erro)."""
        rel = item['path']
        try:
            path = self.root / rel
            size = path.stat().st_size
            if size > MAX_BYTES:
                raise ValueError(f'{rel}: maior que o limite de {MAX_BYTES} bytes')
            data = path.read_bytes()
            sha = sha256_bytes(data)
            if sha != item['local']:
                raise Conflict(f'{rel}: o arquivo mudou durante a sincronização; tente de novo')
            try:
                self.storage.put(f'{self.group}/blobs/{sha}', data)
            except cloud_mod.Exists:
                pass  # mesmo hash = mesmo conteúdo
            return {'sha256': sha, 'size': size, 'base': sorted(item['heads']), 'at': self.now()}, None
        except (OSError, ValueError, Conflict) as error:
            return None, str(error)

    def _pull(self, rel, sha, baseline):
        data = self.storage.get(f'{self.group}/blobs/{sha}')
        if sha256_bytes(data) != sha:
            raise ValueError(f'{rel}: o conteúdo baixado não confere com o hash; nada foi alterado')
        target = self.root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file():  # a versão local vai para o histórico antes de ser substituída
            history = self.root / '.pyretro-history' / rel
            history.mkdir(parents=True, exist_ok=True)
            os.replace(target, history / f'{time.time_ns()}.previous')
        temporary = target.with_name(target.name + PART)
        temporary.write_bytes(data)
        os.replace(temporary, target)
        baseline[rel] = sha

    def resolve(self, rel, choice, sha=None):
        """Resolve um conflito. `choice='local'`: a versão deste dispositivo vence e passa a substituir
        todas as cabeças. `choice='remote'`: baixa a cabeça `sha` (obrigatória se houver mais de uma) e a
        local vai para o histórico. Nada é apagado nos dois casos."""
        safe_relative(rel)
        manifests = self.manifests()
        heads = self.heads(manifests).get(rel, {})
        local = self.local_files().get(rel)
        if choice == 'local':
            if local is None:
                raise ValueError('não há versão local para manter')
            item = {'path': rel, 'action': 'push', 'local': local, 'baseline': None, 'heads': heads}
            return self.apply([item])[0]
        if choice == 'remote':
            if sha is None and len(heads) == 1:
                sha = next(iter(heads))
            if sha not in heads:
                raise ValueError('escolha uma das versões da nuvem')
            return self.apply([{'path': rel, 'action': 'pull', 'local': local, 'baseline': None, 'heads': {sha: heads[sha]}}])[0]
        raise ValueError('escolha desconhecida: ' + str(choice))
