"""Tempo local de sessões: processo de emulador ou duração informada pelo usuário."""
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import tempfile
import uuid

from core import file_lock


def load(path):
    try:
        data = json.loads(Path(path).read_text())
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict) or not isinstance(data.get('games'), dict):
        raise ValueError('histórico de tempo inválido; arquivo preservado')
    for value in data['games'].values():
        if not isinstance(value, dict) or any(type(value.get(k)) is not int or value[k] < 0 for k in ('seconds','sessions','automaticSeconds','manualSeconds')) or not isinstance(value.get('_events'),list):
            raise ValueError('histórico de tempo inválido; arquivo preservado')
    return data['games']


def record(path, key, seconds, source='manual', event=None):
    if not isinstance(key, str) or not key or len(key) > 512:
        raise ValueError('jogo inválido')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 1 <= seconds <= 365 * 86400:
        raise ValueError('duração inválida')
    if source not in ('emulator', 'manual', 'android'):
        raise ValueError('origem inválida')
    event = str(event or uuid.uuid4())
    if len(event) > 128:
        raise ValueError('identificador da sessão inválido')
    path = Path(path)
    with file_lock.exclusive(path):
        games = load(path)
        game = games.setdefault(key, {'seconds': 0, 'sessions': 0, 'automaticSeconds': 0, 'manualSeconds': 0, '_events': []})
        if event in game['_events']:
            return game
        duration = int(seconds)
        game['seconds'] += duration; game['sessions'] += 1
        game['automaticSeconds' if source == 'emulator' else 'manualSeconds'] += duration
        game['lastSession'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
        # Uma fila offline antiga pode ser reenviada depois de muitas sessões.
        # Não expirar IDs já confirmados: o retry continua sendo idempotente.
        game['_events'].append(event)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=path.parent, prefix='.playtime-')
        try:
            with os.fdopen(fd, 'w') as output:
                json.dump({'version': 1, 'games': games}, output, ensure_ascii=False)
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)
        return game


def public(game):
    return {key: game.get(key, 0) for key in ('seconds', 'sessions', 'automaticSeconds', 'manualSeconds')}
