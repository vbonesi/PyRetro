"""Favoritos e novas sessões no cadastro canônico, sem importar totais históricos."""
import math
from pathlib import Path
from core import file_lock, library


def update(cfg, game_id, *, favorite=None, event=None, seconds=None):
    if not game_id:
        return False
    if event is not None:
        if not isinstance(event, str) or not 0 < len(event) <= 200 or type(seconds) not in (int, float) or not math.isfinite(seconds) or not 1 <= seconds <= 365 * 86400:
            raise ValueError('sessão inválida')
    path = Path(cfg['pc']['library_root']).expanduser() / 'library.json'
    with file_lock.exclusive(path):
        data = library.load_library(path)
        game = next((g for g in data['games'] if g['id'] == game_id), None)
        if game is None:
            return False
        changed = False
        if favorite is not None:
            if type(favorite) is not bool:
                raise ValueError('favorito inválido')
            changed = game.get('favorite') != favorite
            game['favorite'] = favorite
        if event is not None:
            sessions = game.setdefault('_play_sessions', {})
            if event in sessions and sessions[event] != int(seconds):
                raise ValueError('sessão divergente; duração original preservada')
            changed |= event not in sessions
            sessions[event] = int(seconds)
        if changed:
            library.save_library(path, data)
        return changed


def public_time(tracking, local):
    """União das sessões locais e remotas; eventos já contados no PC não somam duas vezes."""
    from core.playtime import public
    out = public(local)
    known = set(local.get('_events', []))
    extra = {event: seconds for event, seconds in tracking.get('_play_sessions', {}).items()
             if event not in known and isinstance(seconds, int) and seconds > 0}
    out['seconds'] += sum(extra.values())
    out['manualSeconds'] += sum(extra.values())
    out['sessions'] += len(extra)
    return out
