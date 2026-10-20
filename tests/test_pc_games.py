"""Último jogado e abertura de jogos de PC; nenhum teste abre loja ou jogo reais."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_api import BaseAPI

from core import library as lm
from core import pc_games, recent
import server as srv


class TestPcGames(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        steamapps = self.root / 'steam/steamapps'
        steamapps.mkdir(parents=True)
        (steamapps / 'appmanifest_10.acf').write_text('"AppState"\n{\n\t"appid"\t\t"10"\n\t"name"\t\t"Hollow Knight"\n}')
        (steamapps / 'appmanifest_11.acf').write_text('"AppState"\n{\n\t"appid"\t\t"11"\n\t"name"\t\t"Steam Linux Runtime 3"\n}')
        (steamapps / 'appmanifest_12.acf').write_text('"AppState"\n{\n\t"appid"\t\t"12"\n\t"name"\t\t"The Sims\u2122 4"\n}')
        (steamapps / 'appmanifest_x.acf').write_text('"AppState"\n{\n\t"appid"\t\t"1;rm"\n\t"name"\t\t"Mau"\n}')
        heroic = self.root / 'heroic/legendaryConfig/legendary'
        heroic.mkdir(parents=True)
        (heroic / 'installed.json').write_text(json.dumps({
            'abc123': {'title': 'Alien: Isolation', 'is_dlc': False},
            'bad id;': {'title': 'Perigoso', 'is_dlc': False}}))
        self.cfg = {'heroic': {'config_dir': str(self.root / 'heroic')}}
        p = patch.object(pc_games, 'STEAM_ROOTS', (str(self.root / 'steam'),)); p.start(); self.addCleanup(p.stop)

    def test_installed_only_and_runtime_or_unsafe_ids_ignored(self):
        self.assertEqual(pc_games.steam_installed(), {'hollowknight': '10', 'sims4': '12'})
        self.assertEqual(pc_games.heroic_installed(self.cfg['heroic'], 'legendary'), {'alienisolation': 'abc123'})

    def test_find_requires_matching_source(self):
        game = {'nome': 'Hollow Knight', 'nomes_alt': [], 'fontes': ['steam']}
        self.assertEqual(pc_games.find(self.cfg, game), {'store': 'steam', 'id': '10'})
        self.assertIsNone(pc_games.find(self.cfg, {**game, 'fontes': ['heroic:gog']}))
        self.assertIsNone(pc_games.find(self.cfg, {**game, 'plataforma': 'Super Nintendo'}))
        self.assertEqual(pc_games.find(self.cfg, {'nome': 'The Sims 4', 'nomes_alt': [], 'fontes': ['steam']}), {'store': 'steam', 'id': '12'})
        self.assertEqual(pc_games.find(self.cfg, {'nome': 'Alien: Isolation', 'nomes_alt': [], 'fontes': ['heroic:epic']}),
                         {'store': 'legendary', 'id': 'abc123'})

    def test_commands_are_fixed_argv_and_reject_unsafe_ids(self):
        self.assertEqual(pc_games.command({'store': 'steam', 'id': '10'})[-1], 'steam://rungameid/10')
        self.assertEqual(pc_games.command({'store': 'legendary', 'id': 'abc'})[-1], 'heroic://launch/legendary/abc')
        for bad in ({'store': 'steam', 'id': '1 2'}, {'store': 'legendary', 'id': 'a/b'}):
            with self.assertRaises(ValueError): pc_games.command(bad)

    def test_amazon_nile_uses_installed_ids_and_cached_titles(self):
        base = self.root / 'heroic'
        (base / 'nile_config/nile').mkdir(parents=True)
        (base / 'store_cache').mkdir(exist_ok=True)
        app = 'amzn1.adg.product.abc-123'
        installed = self.root / 'Games/amazon'; installed.mkdir(parents=True)
        (base / 'nile_config/nile/installed.json').write_text(json.dumps([{'id': app, 'path': str(installed)}]))
        (base / 'store_cache/nile_library.json').write_text(json.dumps({'library': [
            {'app_name': app, 'title': 'Amazon instalado'},
            {'app_name': 'nao-instalado', 'title': 'Só possuído'}]}))
        self.assertEqual(pc_games.heroic_installed(self.cfg['heroic'], 'nile'), {'amazoninstalado': app})
        found = pc_games.find(self.cfg, {'nome': 'Amazon instalado', 'fontes': ['heroic:amazon']})
        self.assertEqual(pc_games.command(found)[-1], 'heroic://launch/nile/' + app)

    def test_steam_download_incomplete_is_not_installed(self):
        p = self.root / 'steam/steamapps/appmanifest_20.acf'
        p.write_text('\"appid\" \"20\"\n\"name\" \"Incompleto\"\n\"StateFlags\" \"1026\"')
        self.assertNotIn('incompleto', pc_games.steam_installed())

    def test_recent_keys_and_touch(self):
        self.assertEqual(recent.rom_key('PS2', 'Jogo X.iso'), recent.rom_key('PS2', 'Jogo X.iso'))
        self.assertEqual(recent.rom_key('PS', 'Pasta Jogo/disc.cue'), recent.rom_key('PS', 'Pasta Jogo/outro.cue'))
        path = self.root / 'cache/last.json'
        recent.touch(path, 'pc:a'); self.assertIn('pc:a', recent.load(path))
        path.write_text('lixo'); self.assertEqual(recent.load(path), {})


class TestPcHTTP(BaseAPI):
    def setUp(self):
        self.a = lm._blank_game('Antigo', 'Steam'); self.a.update(iniciado=True, fontes=['steam'])
        self.b = lm._blank_game('Recente', 'Steam'); self.b.update(iniciado=True, fontes=['steam'])
        self.c = lm._blank_game('Nunca', 'Steam'); self.c.update(iniciado=True)
        self.gravar_biblioteca([self.a, self.b, self.c])
        srv.LAST_PLAYED_PATH.unlink(missing_ok=True)

    def test_iniciados_ordered_by_last_played(self):
        recent.touch(srv.LAST_PLAYED_PATH, recent.pc_key(self.a['id']), now=__import__('datetime').datetime(2026, 1, 1))
        recent.touch(srv.LAST_PLAYED_PATH, recent.pc_key(self.b['id']), now=__import__('datetime').datetime(2026, 2, 1))
        status, data = self.pedir('/api/iniciados')
        self.assertEqual(status, 200)
        self.assertEqual([g['nome'] for g in data], ['Recente', 'Antigo', 'Nunca'])

    def test_pc_options_and_launch(self):
        found = {'store': 'steam', 'id': '10'}
        with patch.object(pc_games, 'find', return_value=found):
            self.assertEqual(self.pedir('/api/pc/options?id=' + self.a['id'])[1], {'available': True, 'store': 'steam'})
            with patch.object(pc_games, 'launch') as launch:
                status, data = self.pedir('/api/pc/launch', {'id': self.a['id']})
            self.assertEqual((status, data['status']), (200, 'launched'))
            launch.assert_called_once_with(found)
        self.assertIn(recent.pc_key(self.a['id']), recent.load(srv.LAST_PLAYED_PATH))

    def test_launch_refuses_not_installed_unknown_and_missing_id(self):
        with patch.object(pc_games, 'find', return_value=None), patch.object(pc_games, 'launch') as launch:
            self.assertEqual(self.pedir('/api/pc/launch', {'id': self.a['id']})[0], 400)
            self.assertEqual(self.pedir('/api/pc/launch', {'id': 'inexistente'})[0], 400)
            self.assertEqual(self.pedir('/api/pc/launch', {})[0], 400)
            launch.assert_not_called()
