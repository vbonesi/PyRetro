"""Sugestões de abertura usam instalação/plataforma, sem executar a ação."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core import game_actions, pc_games, play, tv_apps, library
from test_api import BaseAPI


class TestSuggestions(unittest.TestCase):
    def setUp(self):
        self.apps = [{'id': name, 'name': name, 'icon': ''} for name in ('chiaki', 'sysdvr', 'greenlight', 'steam', 'heroic')]
        patched = patch.object(tv_apps, 'catalog', return_value=self.apps)
        patched.start(); self.addCleanup(patched.stop)

    def game(self, platform='Steam', **extra):
        record = library._blank_game('Mesmo nome', platform)
        return {'id': record['id'], 'name': record['nome'], 'platform': platform, 'tracking': record, **extra}

    def test_remote_requires_supported_generation_and_installed_client(self):
        for platform, app in (('PlayStation 4', 'chiaki'), ('Nintendo Switch', 'sysdvr'), ('Xbox One', 'greenlight')):
            suggestion = game_actions.suggest({}, self.game(platform))
            self.assertEqual((suggestion['kind'], suggestion['app']['id']), ('remote', app))
        for platform in ('PlayStation 3', 'Xbox 360', 'PSN'):
            self.assertIsNone(game_actions.remote_option(platform, self.apps))
        self.assertIsNone(game_actions.remote_option('PlayStation 4', []))

    def test_installed_pc_and_store_fallback_are_distinguished(self):
        with patch.object(pc_games, 'find', return_value={'store': 'steam', 'id': '10'}):
            self.assertEqual(game_actions.suggest({}, self.game())['kind'], 'pc')
        with patch.object(pc_games, 'find', return_value=None):
            self.assertEqual(game_actions.suggest({}, self.game())['kind'], 'app')

    def test_rom_options_download_and_missing_launcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            launcher = Path(tmp) / 'launcher'; launcher.touch()
            game = self.game('PlayStation 2', code='PS2', romName='Jogo', driveName='Jogo.iso')
            with patch.object(play, 'LAUNCHER', launcher), patch.object(play, 'candidates', return_value=[{'name': 'Jogo.iso', 'error': None}]) as candidates:
                self.assertEqual(game_actions.suggest({}, game)['kind'], 'rom')
                candidates.return_value = [{'name': 'Jogo.cue', 'error': 'faixa ausente'}]
                suggestion = game_actions.suggest({}, game)
                self.assertEqual(suggestion['kind'], 'download')
                self.assertTrue(suggestion['url'].startswith('/tv?game='))
                launcher.unlink()
                self.assertEqual(game_actions.suggest({}, game)['kind'], 'none')


class TestDrawActionsHTTP(BaseAPI):
    def setUp(self):
        self.pc = library._blank_game('Mesmo nome', 'Steam'); self.pc.update(fontes=['steam'], genero='Ação')
        self.ps4 = library._blank_game('Mesmo nome', 'PlayStation 4'); self.ps4.update(fontes=['psn'], genero='RPG')
        self.gravar_biblioteca([self.pc, self.ps4])
        apps = patch.object(tv_apps, 'catalog', return_value=[{'id': 'chiaki', 'name': 'PS4 remoto', 'icon': 'PS'}])
        apps.start(); self.addCleanup(apps.stop)

    def test_draw_homonyms_preserves_id_platform_and_genre_without_launching(self):
        with patch.object(pc_games, 'find', return_value={'store': 'steam', 'id': '10'}), patch('subprocess.Popen') as launch:
            status, result = self.pedir('/api/sortear?system=biblioteca&genero=A%C3%A7%C3%A3o')
        self.assertEqual(status, 200)
        self.assertEqual(result['game']['id'], self.pc['id'])
        self.assertEqual(result['plataforma'], 'Steam')
        self.assertTrue(result['game']['local'])
        self.assertEqual(result['suggestion']['kind'], 'pc')
        launch.assert_not_called()

    def test_draw_and_details_offer_ps4_remote_without_pc_launch(self):
        with patch.object(pc_games, 'find', return_value=None), patch('subprocess.Popen') as launch:
            result = self.pedir('/api/sortear?system=biblioteca&genero=RPG')[1]
            detail = self.pedir('/api/pc/options?id=' + self.ps4['id'])[1]
        self.assertEqual(result['game']['id'], self.ps4['id'])
        self.assertEqual(result['suggestion']['app']['id'], 'chiaki')
        self.assertFalse(detail['available'])
        self.assertEqual(detail['remote']['label'], 'Transmitir do PS4')
        launch.assert_not_called()
