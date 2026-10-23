"""Relatório compartilhável por lista permitida; não inclui logs nem inventário.

Só verifica presença de diretórios e executáveis. Não lê biblioteca, credenciais,
ROMs ou saves, não consulta rede nem executa os programas encontrados.
"""
import shutil
import sys
from pathlib import Path

ROOTS = {
    'roms_root': ('roms', 'Confira a pasta de ROMs nas configurações do PC.'),
    'saves_root': ('saves', 'Confira a pasta de saves nas configurações do PC.'),
    'states_root': ('states', 'Confira a pasta de estados nas configurações do PC.'),
    'backups_root': ('backups', 'Confira a pasta de backups antes de restaurar saves.'),
}


def report(cfg, play_state=None, which=shutil.which):
    checks = []
    for key, (label, action) in ROOTS.items():
        value = cfg.get('pc', {}).get(key)
        try:
            present = isinstance(value, str) and bool(value) and Path(value).expanduser().is_dir()
            status = 'present' if present else 'missing'
        except (OSError, ValueError, RuntimeError):
            status = 'unavailable'
        checks.append({'id': label, 'status': status, 'action': '' if status == 'present' else action})
    for binary, action in [('rclone', 'Instale o rclone para acessar ROMs que estão somente na nuvem.'),
                           ('bonisarch-emulator', 'Instale o lançador do setup para abrir jogos no PC.')]:
        present = bool(which(binary))
        checks.append({'id': binary, 'status': 'present' if present else 'missing',
                       'action': '' if present else action})
    state = play_state if play_state in ('idle', 'running', 'starting', 'error') else 'unknown'
    return {'schema': 1, 'application': 'PyRetro', 'python': f'{sys.version_info.major}.{sys.version_info.minor}',
            'play_state': state, 'checks': checks,
            'limits': ['Presença não comprova permissão de escrita, login, conexão ou funcionamento.',
                       'Rede, Android, controle e consoles não foram testados por este relatório.'],
            'privacy': 'Sem caminhos, nomes de jogos, contas, endereços de rede, tokens ou logs.'}
