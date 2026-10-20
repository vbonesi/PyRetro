"""TV: presença local real, sem inferir instalação por uma capa/descritor órfão."""
from pathlib import Path
from unittest.mock import patch
from test_api import BaseAPI
from core import pc_games, tv_apps
from core import tv
from core import library


class TestTVCatalog(BaseAPI):
    def setUp(self):
        self.gravar_biblioteca([])

    def test_local_only_complete_roms_and_no_network_refresh(self):
        folder = self.raiz / 'ROMs/PS2'
        folder.mkdir(exist_ok=True)
        (folder / 'Vazia.iso').write_bytes(b'')
        (folder / 'Completa.iso').write_bytes(b'jogo')
        (folder / 'Parcial.iso.part').write_bytes(b'parcial')
        with patch.object(pc_games, 'installed_indexes', return_value={k: {} for k in ('steam', 'legendary', 'gog', 'nile')}):
            status, items = self.pedir('/api/tv/local')
        self.assertEqual(status, 200)
        names = [g['name'] for g in items]
        self.assertIn('Chrono Trigger', names)
        self.assertIn('Final Fantasy VI', names)  # sem capa também aparece
        self.assertIn('Completa', names)
        self.assertNotIn('Vazia', names)
        self.assertFalse(any('Parcial' in n for n in names))

    def test_catalog_includes_cloud_cache_and_cover_without_claiming_installed(self):
        (self.capas_dir / 'Só capa.png').write_bytes(b'imagem')
        with patch.object(pc_games, 'installed_indexes', return_value={k: {} for k in ('steam', 'legendary', 'gog', 'nile')}):
            status, items = self.pedir('/api/tv/catalog')
        self.assertEqual(status, 200)
        cloud = next(g for g in items if g['name'] == 'Bomba Patch')
        self.assertFalse(cloud['local'])
        self.assertEqual(cloud['downloadName'], 'Bomba Patch.iso')
        self.assertFalse(next(g for g in items if g['name'] == 'Só capa')['local'])

    def test_apps_launch_only_registered_id_and_fixed_argv(self):
        apps = {'exemplo': {'nome': 'Exemplo', 'comando': ['/usr/bin/exemplo', '--tv']}}
        with patch.object(tv_apps, 'entries', return_value=apps), patch.object(tv_apps.subprocess, 'Popen') as launch:
            self.assertEqual(self.pedir('/api/tv/apps')[1], [{'id': 'exemplo', 'name': 'Exemplo', 'icon': '▣'}])
            self.assertEqual(self.pedir('/api/tv/apps/launch', {'id': 'exemplo', 'command': 'ignored'})[0], 200)
            self.assertEqual(launch.call_args.args[0], ['/usr/bin/exemplo', '--tv'])
            self.assertNotIn('shell', launch.call_args.kwargs)
            launch.reset_mock()
            self.assertEqual(self.pedir('/api/tv/apps/launch', {'id': 'exemplo;whoami'})[0], 400)
            launch.assert_not_called()

    def test_arcade_unknown_display_name_falls_back_to_romset(self):
        folder = self.raiz / 'ROMs/ARCADE'; folder.mkdir(exist_ok=True)
        (folder / 'unknown.zip').write_bytes(b'rom')
        cfg = {'pc': {'roms_root': str(self.raiz / 'ROMs'), 'capas_root': str(self.raiz / 'Capas')},
               'systems': {'ARCADE': {'exts': ['zip'], 'capas': 'Arcade'}}}
        result = tv.local_roms(cfg, {'games': []}, {'outro': 'Outro'})
        self.assertEqual(result[0]['name'], 'unknown')

    def test_catalog_does_not_promote_wishlist_to_owned(self):
        wish = library._blank_game('Só desejo', 'Steam'); wish['fontes'] = ['wishlist:steam']
        owned = library._blank_game('Possuído e desejado', 'Steam'); owned['fontes'] = ['steam', 'wishlist:xbox']
        self.gravar_biblioteca([wish, owned])
        with patch.object(pc_games, 'installed_indexes', return_value={k: {} for k in ('steam', 'legendary', 'gog', 'nile')}):
            status, items = self.pedir('/api/tv/catalog')
        self.assertEqual(status, 200)
        names = [g['name'] for g in items]
        self.assertNotIn('Só desejo', names)
        self.assertIn('Possuído e desejado', names)
