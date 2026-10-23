"""Saves pelo modo TV: guardar, apagar e restaurar sempre deixam cópia."""
import shutil
from unittest.mock import patch

from test_api import BaseAPI


class TestTVSaves(BaseAPI):
    def setUp(self):
        self.saves = self.raiz / 'Saves/saves/SFC'
        self.states = self.raiz / 'Saves/states/SFC'
        shutil.rmtree(self.raiz / 'Saves', ignore_errors=True)
        shutil.rmtree(self.raiz / 'Backups', ignore_errors=True)
        self.saves.mkdir(parents=True); self.states.mkdir(parents=True)
        (self.saves / 'Jogo.srm').write_bytes(b'save original')
        (self.states / 'Jogo.state.auto').write_bytes(b'estado')
        (self.saves / 'Outro Jogo.srm').write_bytes(b'nao mexer')

    def acao(self, nome, **extra):
        return self.pedir(f'/api/tv/saves/{nome}', {'code': 'SFC', 'label': 'Jogo', **extra})

    def copias(self):
        status, data = self.pedir('/api/tv/saves/backups?code=SFC&label=Jogo')
        self.assertEqual(status, 200)
        return data['items']

    def test_backup_copies_only_this_game(self):
        status, data = self.acao('backup')
        self.assertEqual(status, 200)
        self.assertEqual(data['files'], 2)
        [copia] = self.copias()
        self.assertEqual(sorted(a['name'] for a in copia['arquivos']), ['Jogo.srm', 'Jogo.state.auto'])
        self.assertTrue((self.saves / 'Jogo.srm').exists())

    def test_remove_keeps_copy_and_restore_brings_it_back(self):
        status, _ = self.acao('remove', name='Jogo.srm', kind='save', legado=False)
        self.assertEqual(status, 200)
        self.assertFalse((self.saves / 'Jogo.srm').exists())
        self.assertTrue((self.saves / 'Outro Jogo.srm').exists())
        [copia] = self.copias()
        (self.states / 'Jogo.state.auto').write_bytes(b'estado novo')
        status, data = self.acao('restore', stamp=copia['stamp'])
        self.assertEqual(status, 200)
        self.assertEqual((self.saves / 'Jogo.srm').read_bytes(), b'save original')
        # O que estava em uso antes de restaurar também foi guardado.
        self.assertIsNotNone(data['safety'])
        self.assertEqual(len(self.copias()), 2)

    def test_refuses_other_files_paths_and_running_game(self):
        self.assertEqual(self.acao('remove', name='Outro Jogo.srm', kind='save', legado=False)[0], 404)
        self.assertEqual(self.acao('restore', stamp='../x')[0], 400)
        self.assertEqual(self.pedir('/api/tv/saves/backup', {'code': 'SFC', 'label': '../Jogo'})[0], 400)
        self.assertEqual(self.pedir('/api/tv/saves/backup', {'code': 'XYZ', 'label': 'Jogo'})[0], 404)
        server = __import__('server')
        with patch.object(server.PLAY_SESSIONS, 'status', return_value={'status': 'running'}):
            self.assertEqual(self.acao('backup')[0], 409)
        self.assertTrue((self.saves / 'Jogo.srm').exists())
