"""Sugestão de abertura do jogo, sem iniciar processos ou downloads."""
from urllib.parse import urlencode

from core import pc_games, play, tv_apps


REMOTE_PLATFORMS = {
    'Nintendo Switch': ('sysdvr', 'Transmitir do Switch Lite'),
    'Switch': ('sysdvr', 'Transmitir do Switch Lite'),
    'PlayStation 4': ('chiaki', 'Transmitir do PS4'),
    'Xbox': ('greenlight', 'Transmitir do Xbox'),
    'Xbox One': ('greenlight', 'Transmitir do Xbox'),
    'Xbox Series S': ('greenlight', 'Transmitir do Xbox'),
    'Xbox Series X': ('greenlight', 'Transmitir do Xbox'),
}
STORE_PLATFORMS = {'Steam': 'steam', 'Epic Games Store': 'heroic', 'GOG': 'heroic', 'Amazon Games': 'heroic'}


def remote_option(platform, apps):
    remote = REMOTE_PLATFORMS.get(platform)
    if remote is None:
        return None
    app = next((app for app in apps if app['id'] == remote[0]), None)
    if not app:
        return None
    hint = ('Abra o jogo no Switch e ative TCP Bridge no SysDVR. Use os controles do console.'
            if remote[0] == 'sysdvr' else
            'Abre o cliente remoto. Escolha este jogo no console; o jogo não é iniciado automaticamente.')
    return {'kind': 'remote', 'app': app, 'label': remote[1], 'hint': hint}


def store_option(platform, apps):
    store = STORE_PLATFORMS.get(platform)
    app = next((app for app in apps if app['id'] == store), None)
    if app:
        return {'kind': 'app', 'app': app, 'label': 'Abrir ' + app['name'],
                'hint': 'Não instalado neste PC. Abra a loja para instalar ou escolher o jogo.'}
    return None


def suggest(cfg, game):
    from core import tv_home
    url = '/tv?' + urlencode({'game': tv_home.item_key(game)})
    result = {'kind': 'none', 'url': url, 'hint': 'Consulte os detalhes no modo TV.'}
    if game.get('code'):
        try:
            options = play.candidates(cfg, game['code'], game['romName'])
        except (OSError, ValueError) as error:
            return {**result, 'hint': str(error)}
        if not play.LAUNCHER.is_file():
            return {**result, 'hint': 'O lançador de emuladores precisa estar instalado.'}
        valid = [option for option in options if not option.get('error')]
        if valid:
            return {**result, 'kind': 'rom', 'code': game['code'], 'options': valid,
                    'hint': 'Escolha o disco/formato para jogar.' if len(valid) > 1 else 'Pronto para abrir o emulador.'}
        if game.get('driveName') or game.get('downloadName'):
            return {**result, 'kind': 'download', 'label': 'Baixar e jogar no modo TV',
                    'hint': 'Confira os arquivos e confirme o download no modo TV.'}
        return {**result, 'hint': 'A ROM precisa estar completa neste PC para jogar.'}
    apps = tv_apps.catalog(cfg)
    remote = remote_option(game['platform'], apps)
    if remote:
        return {**result, **remote}
    found = pc_games.find(cfg, game.get('tracking', {}))
    if found:
        return {**result, 'kind': 'pc', 'id': game['id'], 'store': found['store'],
                'label': 'Jogar (' + ('Steam' if found['store'] == 'steam' else 'Heroic') + ')',
                'hint': 'Abre o jogo instalado neste PC pela loja.'}
    store = store_option(game['platform'], apps)
    if store:
        return {**result, **store}
    return {**result, 'hint': 'Sem lançamento disponível neste PC para essa plataforma.'}
