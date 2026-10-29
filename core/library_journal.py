"""Diário de mudanças da Biblioteca (SQLite) e sua publicação incremental na nuvem.

A Biblioteca continua sendo o `library.json` (todo o PyRetro lê e grava esse arquivo); o diário registra,
a cada gravação, só o que mudou — jogo novo, jogo removido, campo alterado — com data e dispositivo.
Isso permite:

* enviar à nuvem apenas as mudanças (segmentos pequenos e imutáveis) em vez do arquivo inteiro a cada edição;
* reconstruir a Biblioteca a partir de um snapshot + as mudanças seguintes (restauração em qualquer ponto);
* juntar edições de dois dispositivos campo a campo: vence a mudança mais recente (LWW por jogo e campo).

    journal/<dispositivo>/<de>-<até>.json   segmento imutável: {"device","from","to","changes":[...]}

O diário local é `library-journal.db` ao lado do `library.json`.
"""
import contextlib
import json
import math
import re
import sqlite3
import time

from core import cloud as cloud_mod
from core import journal_rules as rules

SEGMENT_MAX = 2000


def diff(old, new):
    """Mudanças que levam `old` a `new`: [{'op','id','field','value'}]. A ordem dos jogos não conta."""
    old, new = old or {'games': []}, new or {'games': []}
    changes = []
    old_games = {g.get('id'): g for g in old.get('games', [])}
    new_games = {g.get('id'): g for g in new.get('games', [])}
    for game_id, game in new_games.items():
        before = old_games.get(game_id)
        if before is None:
            changes.append({'op': 'add', 'id': game_id, 'value': game}); continue
        for field in sorted(set(before) | set(game)):
            if field == '_play_sessions':
                for event, seconds in game.get(field, {}).items():
                    if event not in before.get(field, {}):
                        changes.append({'op': 'session', 'id': game_id, 'value': {'event': event, 'seconds': seconds}})
                continue
            if before.get(field) != game.get(field) or (field in before) != (field in game):
                if field in game:
                    changes.append({'op': 'set', 'id': game_id, 'field': field, 'value': game[field]})
                else:
                    changes.append({'op': 'unset', 'id': game_id, 'field': field})
    for game_id in old_games:
        if game_id not in new_games:
            changes.append({'op': 'remove', 'id': game_id})
    for key in sorted((set(old) | set(new)) - {'games'}):
        if old.get(key) != new.get(key):
            changes.append({'op': 'meta', 'field': key, 'value': new.get(key)})
    return changes


def apply(base, changes):
    """Reaplica mudanças sobre uma Biblioteca (cópia); jogos novos entram no fim."""
    library = json.loads(json.dumps(base or {'games': []}))
    games = {g.get('id'): g for g in library.setdefault('games', [])}
    for change in changes:
        op, game_id = change['op'], change.get('id')
        if op == 'add':
            if game_id not in games:
                game = json.loads(json.dumps(change['value'])); games[game_id] = game; library['games'].append(game)
        elif op == 'remove':
            if game_id in games:
                library['games'] = [g for g in library['games'] if g.get('id') != game_id]; games.pop(game_id)
        elif op == 'set' and game_id in games:
            games[game_id][change['field']] = change['value']
        elif op == 'unset' and game_id in games:
            games[game_id].pop(change['field'], None)
        elif op == 'meta':
            library[change['field']] = change['value']
        elif op == 'session' and game_id in games:
            game = games[game_id]
            game.setdefault('_play_sessions', {}).setdefault(change['value']['event'], change['value']['seconds'])
    return library


class Journal:
    def __init__(self, path, device, now=time.time):
        self.path, self.device, self.now = path, device, now
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS changes(seq INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL,
                    device TEXT NOT NULL, origin TEXT NOT NULL DEFAULT 'local', op TEXT NOT NULL,
                    game_id TEXT, field TEXT, value TEXT);
                CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
                CREATE INDEX IF NOT EXISTS changes_field ON changes(game_id, field, at);''')

    @contextlib.contextmanager
    def _db(self):
        """Conexão que confirma ao sair e sempre fecha (o `with` do sqlite3 sozinho não fecha)."""
        connection = sqlite3.connect(str(self.path), timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _meta(self, db, key, default=0):
        row = db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
        return json.loads(row['value']) if row else default

    def _set_meta(self, db, key, value):
        db.execute('INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                   (key, json.dumps(value)))

    def _state(self, db):
        state = self._meta(db, 'state', None)
        if state is not None:
            return state
        state = {'versions': {}, 'deleted': {}}
        for row in db.execute('SELECT * FROM changes ORDER BY at,device,seq'):
            op = row['op']
            stamp = [row['at'], row['device'], row['seq']]
            if op == 'add':
                for field in json.loads(row['value'] or '{}'):
                    state['versions'][rules.key(row['game_id'], field)] = stamp
            elif op in ('remove', 'set', 'unset', 'meta'):
                state['versions'][rules.key(row['game_id'], row['field'])] = stamp
        return state

    def record(self, old, new, origin='local', at=None):
        """Registra o que mudou de `old` para `new`. Devolve quantas mudanças entraram."""
        changes = diff(old, new)
        if not changes:
            return 0
        with self._db() as db:
            state_before = self._state(db)
            seen = max(float(self._meta(db, 'last_at')), float(db.execute('SELECT COALESCE(MAX(at),0) FROM changes').fetchone()[0]))
            at = rules.clock(self.now() if at is None else at, seen)
            db.executemany('INSERT INTO changes(at,device,origin,op,game_id,field,value) VALUES(?,?,?,?,?,?,?)',
                           [(c.get('at', at), c.get('device', self.device), origin, c['op'], c.get('id'), c.get('field'),
                             json.dumps(c.get('value'), ensure_ascii=False)) for c in changes])
            last = db.execute('SELECT MAX(seq) FROM changes').fetchone()[0]
            stamped = [{**c, 'at': at, 'device': self.device, 'seq': last-len(changes)+i+1} for i, c in enumerate(changes)]
            _, _, state = rules.merge(old, stamped, state_before, replay_pending=False)
            self._set_meta(db, 'state', state)
            self._set_meta(db, 'last_at', at)
        return len(changes)

    def rows(self, since=0, origin=None, limit=None):
        sql, args = 'SELECT * FROM changes WHERE seq>?', [since]
        if origin:
            sql += ' AND origin=?'; args.append(origin)
        sql += ' ORDER BY seq' + (f' LIMIT {int(limit)}' if limit else '')
        with self._db() as db:
            return [dict(r) for r in db.execute(sql, args)]

    def count(self):
        with self._db() as db:
            return db.execute('SELECT COUNT(*) FROM changes').fetchone()[0]

    def latest_at(self, game_id, field=None):
        """Data da mudança local mais recente do campo; sem `field`, de qualquer campo do jogo."""
        with self._db() as db:
            if field is None:
                row = db.execute('SELECT MAX(at) FROM changes WHERE game_id=? AND origin=?', (game_id, 'local')).fetchone()
            else:
                row = db.execute('SELECT MAX(at) FROM changes WHERE game_id=? AND origin=? AND (field=? OR field IS NULL)',
                                 (game_id, 'local', field)).fetchone()
        return row[0] or 0

    # --- nuvem -------------------------------------------------------------------------------
    @staticmethod
    def _export(row):
        change = {'seq': row['seq'], 'at': row['at'], 'op': row['op']}
        if row['game_id'] is not None:
            change['id'] = row['game_id']
        if row['field'] is not None:
            change['field'] = row['field']
        value = json.loads(row['value']) if row['value'] is not None else None
        if row['op'] in ('add', 'set', 'meta', 'session'):
            change['value'] = value
        return change

    def publish(self, storage):
        """Envia as mudanças locais ainda não publicadas como segmentos imutáveis. Devolve quantas subiram."""
        with self._db() as db:
            done = self._meta(db, 'published_seq')
        sent = 0
        while True:
            rows = self.rows(done, origin='local', limit=SEGMENT_MAX)
            if not rows:
                return sent
            first, last = rows[0]['seq'], rows[-1]['seq']
            segment = {'device': self.device, 'from': first, 'to': last, 'changes': [self._export(r) for r in rows]}
            try:
                storage.put(f'journal/{self.device}/{first:012d}-{last:012d}.json', json.dumps(segment, ensure_ascii=False).encode('utf-8'))
            except cloud_mod.Exists:
                if json.loads(storage.get(f'journal/{self.device}/{first:012d}-{last:012d}.json')) != segment:
                    raise ValueError('segmento do diário diverge da cópia local; nada foi descartado')
            done = last; sent += len(rows)
            with self._db() as db:
                self._set_meta(db, 'published_seq', done)

    def export_state(self):
        with self._db() as db:
            state = self._state(db)
            cursors = {row['device']: row['last'] for row in db.execute('SELECT device,MAX(seq) AS last FROM changes WHERE origin="local" GROUP BY device')}
            for row in db.execute('SELECT key,value FROM meta WHERE key LIKE "remote:%"'):
                cursors[row['key'][7:]] = json.loads(row['value'])
            return {'state': state, 'cursors': cursors, 'last_at': self._meta(db, 'last_at')}

    def fetch(self, storage):
        """Busca a rede antes de adquirir o lock da Biblioteca; somente segmentos ainda não vistos."""
        cache = cloud_mod.MemoryStorage()
        for item in storage.list('journal'):
            match = re.fullmatch(r'journal/([A-Za-z0-9][A-Za-z0-9_.-]{0,127})/(\d+)-(\d+)\.json', item['path'])
            if not match or match[1] == self.device:
                continue
            with self._db() as db:
                seen = self._meta(db, f'remote:{match[1]}')
            if int(match[3]) > seen:
                cache.put(item['path'], storage.get(item['path']))
        return cache

    def pull(self, storage, library, save=None):
        """Aplica à `library` as mudanças de OUTROS dispositivos ainda não vistas; por jogo e campo vence a
        mais recente (inclusive contra edições locais). Devolve (nova biblioteca, quantas mudanças valeram)."""
        applied = 0
        devices = sorted({i['path'].split('/')[1] for i in storage.list('journal') if i['path'].count('/') >= 2
                          and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', i['path'].split('/')[1])} - {self.device})
        for other in devices:
            with self._db() as db:
                seen = self._meta(db, f'remote:{other}')
            segments = sorted(i['path'] for i in storage.list(f'journal/{other}') if i['path'].endswith('.json'))
            for path in segments:
                try:
                    segment = json.loads(storage.get(path))
                    first, last = int(segment['from']), int(segment['to'])
                except (cloud_mod.NotFound, ValueError, KeyError, TypeError):
                    continue
                if last <= seen:
                    continue
                if (first <= 0 or last < first or segment.get('device') != other or not isinstance(segment.get('changes'), list)
                        or len(segment['changes']) > SEGMENT_MAX):
                    raise ValueError('segmento inválido do diário; recibo não avançou')
                changes = []
                sequences = set()
                for change in segment['changes']:
                    if not isinstance(change, dict):
                        raise ValueError('mudança inválida no diário; recibo não avançou')
                    if (not rules.valid(change) or type(change.get('seq')) is not int or not first <= change['seq'] <= last
                            or type(change.get('at')) not in (int, float) or not math.isfinite(change['at']) or change['at'] < 0
                            or change['seq'] in sequences):
                        if change.get('op') not in rules.OPS:
                            continue  # extensão de protocolo desconhecida
                        raise ValueError('mudança inválida no diário; recibo não avançou')
                    sequences.add(change['seq'])
                    if change['seq'] > seen:
                        changes.append({**change, 'device': other})
                with self._db() as db:
                    merged, count, state = rules.merge(library, changes, self._state(db))
                    if count and save is not None:
                        save(merged)  # o recibo só confirma depois de o JSON ser salvo
                    db.executemany('INSERT INTO changes(at,device,origin,op,game_id,field,value) VALUES(?,?,?,?,?,?,?)',
                                   [(c['at'], other, 'remote', c['op'], c.get('id'), c.get('field'), json.dumps(c.get('value'), ensure_ascii=False)) for c in changes])
                    self._set_meta(db, 'state', state)
                    self._set_meta(db, 'last_at', max([float(self._meta(db, 'last_at')), *[float(c['at']) for c in changes]]))
                    seen = max(seen, last)
                    self._set_meta(db, f'remote:{other}', seen)
                library = merged
                applied += count
        with self._db() as db:
            merged, count, state = rules.merge(library, [], self._state(db))
            if count and save is not None:
                save(merged)
            self._set_meta(db, 'state', state)
        return merged, applied + count
