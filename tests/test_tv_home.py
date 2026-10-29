"""Início, favoritos, temas e aplicativos remotos com dados isolados."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from core import tv_home, tv_apps, pc_games, library, recent
from test_api import BaseAPI
import server as srv


class TestTVPreferences(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'prefs.json'

    def test_concurrent_favorites_preserve_each_other_and_theme(self):
        tv_home.update(self.path, theme='light')
        threads = [threading.Thread(target=tv_home.update, args=(self.path,), kwargs={'key': 'pc:' + str(i), 'favorite': True}) for i in range(12)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(len(tv_home.load(self.path)['favorites']), 12)
        self.assertEqual(tv_home.load(self.path)['theme'], 'light')
        tv_home.update(self.path, key='pc:4', favorite=False)
        self.assertNotIn('pc:4', tv_home.load(self.path)['favorites'])

    def test_invalid_update_does_not_write_and_corrupt_shape_is_tolerated(self):
        for kwargs in ({'theme': 'bad'}, {'key': 'pc:one', 'favorite': 1}):
            with self.assertRaises(ValueError): tv_home.update(self.path, **kwargs)
        self.assertFalse(self.path.exists())
        self.path.write_text('{"favorites": "bad", "theme": null}')
        self.assertEqual(tv_home.load(self.path), {'favorites': [], 'theme': 'dark'})

    def test_rom_identity_matches_history_with_dot_in_title(self):
        game = {'code': 'PS', 'romName': 'Mr. Driller'}
        self.assertEqual(tv_home.item_key(game), recent.rom_key('PS', 'Mr. Driller.chd'))
        self.assertNotEqual(tv_home.item_key(game), tv_home.item_key({'code': 'PS2', 'romName': 'Mr. Driller'}))

    def test_sysdvr_command_uses_validated_address_and_no_shell(self):
        self.path.write_text(json.dumps({'switch_ip': '192.0.2.20'}))
        with patch.object(tv_apps, 'REMOTES_PATH', self.path), patch.object(tv_apps.shutil, 'which', return_value='/bin/flatpak'), patch.object(tv_apps.subprocess, 'run') as run:
            run.return_value.stdout = 'com.github.exelix11.sysdvr\n'
            cmd = tv_apps.entries({})['sysdvr']['comando']
            self.assertEqual(cmd, ['flatpak', 'run', 'com.github.exelix11.sysdvr', 'bridge', '192.0.2.20', '--fullscreen'])
            self.path.write_text(json.dumps({'switch_ip': 'host;whoami'}))
            self.assertEqual(tv_apps.entries({})['sysdvr']['comando'][-2:], ['bridge', '--fullscreen'])

    def test_chiaki_uses_registered_nickname_and_validated_ip(self):
        self.path.write_text(json.dumps({'ps4_ip': '192.0.2.45', 'ps4_nickname': 'PS4 de teste'}))
        with patch.object(tv_apps, 'REMOTES_PATH', self.path), patch.object(tv_apps.shutil, 'which', return_value='/bin/flatpak'), patch.object(tv_apps.subprocess, 'run') as run:
            run.return_value.stdout = 'io.github.streetpea.Chiaki4deck\n'
            self.assertEqual(tv_apps.entries({})['chiaki']['comando'], ['flatpak', 'run', 'io.github.streetpea.Chiaki4deck', '--fullscreen', '--exit-app-on-stream-exit', 'stream', 'PS4 de teste', '192.0.2.45'])
            self.path.write_text(json.dumps({'ps4_ip': 'host;whoami', 'ps4_nickname': 'PS4 de teste'}))
            self.assertEqual(tv_apps.entries({})['chiaki']['comando'], ['flatpak', 'run', 'io.github.streetpea.Chiaki4deck'])


class TestTVHomeHTTP(BaseAPI):
    def setUp(self):
        self.game = library._blank_game('Meu jogo', 'Steam'); self.game['fontes'] = ['steam']; self.game['iniciado'] = True
        self.gravar_biblioteca([self.game]); srv.TV_PREFS_PATH.unlink(missing_ok=True); srv.LAST_PLAYED_PATH.unlink(missing_ok=True)
        self.patch_pc = patch.object(pc_games, 'installed_indexes', return_value={'steam': {'meujogo': '10'}, 'legendary': {}, 'gog': {}, 'nile': {}})
        self.patch_pc.start(); self.addCleanup(self.patch_pc.stop)
        self.patch_apps = patch.object(tv_apps, 'catalog', return_value=[{'id': 'chiaki', 'name': 'PS4 remoto', 'icon': 'PS'}])
        self.patch_apps.start(); self.addCleanup(self.patch_apps.stop)

    def test_home_tracks_unmarked_recent_games_and_local_pc(self):
        self.game['iniciado'] = False; self.gravar_biblioteca([self.game])
        recent.touch(srv.LAST_PLAYED_PATH, recent.pc_key(self.game['id']))
        status, home = self.pedir('/api/tv/home')
        self.assertEqual(status, 200)
        self.assertEqual(home['recent'][0]['id'], self.game['id'])
        self.assertEqual(home['continue'], [])
        self.assertEqual(home['counts']['pc'], 1)
        self.assertEqual(home['apps'][0]['id'], 'chiaki')

    def test_favorite_is_shared_and_theme_stays_local(self):
        before = self.lib_path.read_bytes()
        key = recent.pc_key(self.game['id'])
        self.assertEqual(self.pedir('/api/tv/favorite', {'key': key, 'favorite': True})[0], 200)
        self.assertEqual(self.pedir('/api/tv/preferences', {'theme': 'light'})[0], 200)
        home = self.pedir('/api/tv/home')[1]
        self.assertEqual(home['favorites'][0]['id'], self.game['id'])
        self.assertEqual(home['preferences']['theme'], 'light')
        expected=json.loads(before);expected['games'][0]['favorite']=True
        self.assertEqual(json.loads(self.lib_path.read_bytes()), expected)
        self.assertEqual(self.pedir('/api/tv/favorite', {'id': self.game['id'], 'favorite': False})[0], 200)
        self.assertEqual(self.pedir('/api/tv/home')[1]['favorites'], [])

    def test_missing_unknown_and_non_boolean_favorites_are_rejected(self):
        for body in ({'favorite': True}, {'key': 'pc:missing', 'favorite': True}, {'id': self.game['id'], 'favorite': 'true'}):
            self.assertEqual(self.pedir('/api/tv/favorite', body)[0], 400)
        self.assertFalse(srv.TV_PREFS_PATH.exists())
