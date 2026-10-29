"""Regras do diário compartilhadas com o Android: LWW determinístico e sessões imutáveis."""
import copy
import json
import math

OPS = {'add', 'remove', 'set', 'unset', 'meta', 'session'}


def valid(change):
    if not isinstance(change, dict) or change.get('op') not in OPS:
        return False
    op = change['op']
    if op != 'meta' and (not isinstance(change.get('id'), str) or not 0 < len(change['id']) <= 512):
        return False
    if op in ('set', 'unset', 'meta') and (not isinstance(change.get('field'), str) or not change['field'] or change['field'] in ('id', 'games', '_play_sessions')):
        return False
    if op == 'add' and (not isinstance(change.get('value'), dict) or change['value'].get('id') != change['id']):
        return False
    if op == 'session':
        value = change.get('value')
        return (isinstance(value, dict) and isinstance(value.get('event'), str) and 0 < len(value['event']) <= 256
                and type(value.get('seconds')) is int and 0 < value['seconds'] <= 365 * 86400)
    return True


def clock(now, seen):
    """HLC escalar: estritamente maior que tudo já observado, mesmo se o relógio recuar."""
    return max(float(now), math.nextafter(float(seen), math.inf))


def key(game, field):
    return json.dumps([game, field], ensure_ascii=False, separators=(',', ':'))


def merge(base, changes, state=None, replay_pending=True):
    """Aplica eventos em qualquer ordem. `state` contém versões e tombstones, separado dos jogos."""
    library = copy.deepcopy(base or {'games': []})
    state = copy.deepcopy(state or {})
    versions = state.setdefault('versions', {})
    deleted = state.setdefault('deleted', {})
    games = {g['id']: g for g in library.setdefault('games', [])}
    applied = 0
    minimum = (-1, '', 0)
    waiting = [] if replay_pending else list(state.get('pending', []))
    changes = (list(state.get('pending', [])) if replay_pending else []) + list(changes)

    def version(game, field):
        return tuple(versions.get(key(game, field), minimum))

    for change in changes:
        if not valid(change):
            continue
        try:
            stamp = (float(change['at']), str(change['device']), int(change['seq']))
            if not math.isfinite(stamp[0]) or stamp[0] < 0 or stamp[2] <= 0:
                continue
        except (KeyError, ValueError, TypeError, OverflowError):
            continue
        op, game_id, field = change['op'], change.get('id'), change.get('field')
        broad = version(game_id, None)
        if op == 'meta':
            if stamp <= version(None, field):
                continue
            library[field] = copy.deepcopy(change.get('value'))
            versions[key(None, field)] = stamp
        elif op == 'remove':
            known = [tuple(v) for k, v in versions.items() if json.loads(k)[0] == game_id]
            if stamp <= max(known, default=minimum):
                continue
            if game_id in games:
                deleted[game_id] = games.pop(game_id)
            versions[key(game_id, None)] = stamp
        elif op == 'add':
            if stamp <= broad:
                deleted.setdefault(game_id, copy.deepcopy(change['value']))
                continue
            game = games.setdefault(game_id, {'id': game_id})
            for name, value in change['value'].items():
                if name == '_play_sessions':
                    game.setdefault(name, {}).update(copy.deepcopy(value))
                elif stamp > max(broad, version(game_id, name)):
                    game[name] = copy.deepcopy(value)
                    versions[key(game_id, name)] = stamp
            deleted.pop(game_id, None)
        else:
            if op != 'session' and stamp <= max(broad, version(game_id, field)):
                continue
            if game_id not in games:
                if stamp <= broad or game_id not in deleted:
                    if stamp > broad:
                        waiting.append(change)
                    continue
                games[game_id] = copy.deepcopy(deleted[game_id])
            game = games[game_id]
            if op == 'session':
                event = change['value']['event']
                seconds = change['value']['seconds']
                sessions = game.setdefault('_play_sessions', {})
                if event in sessions:
                    if sessions[event] != seconds:
                        raise ValueError('sessão com conteúdo divergente; diário preservado')
                    continue
                sessions[event] = seconds
                versions[key(game_id, '_play_sessions:' + event)] = stamp
            elif op == 'set':
                game[field] = copy.deepcopy(change.get('value'))
                versions[key(game_id, field)] = stamp
            else:
                game.pop(field, None)
                versions[key(game_id, field)] = stamp
        applied += 1
    library['games'] = list(games.values())
    unique = {(c['device'], c['seq']): c for c in waiting}
    if len(unique) > 10000:
        raise ValueError('muitas mudanças sem cadastro; diário preservado')
    ready = [c for c in unique.values() if c['id'] in games or c['id'] in deleted]
    state['pending'] = [c for c in unique.values() if c not in ready] if replay_pending else waiting
    if replay_pending and ready:
        library, count, state = merge(library, ready, state)
        applied += count
    return library, applied, state
