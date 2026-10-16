"""Modo TV: rota pública e gravação atômica do progresso de uma ROM fictícia."""
import urllib.request
from test_api import BaseAPI
from core import library as lm


class TestTV(BaseAPI):
    def setUp(self):
        self.gravar_biblioteca([])

    def test_tv_served_with_csp_and_scripts_external(self):
        with urllib.request.urlopen(self.url + '/tv') as response:
            self.assertEqual(response.status, 200)
            self.assertIn('text/html', response.headers['Content-Type'])
            self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
            self.assertIn('/static/tv.js', response.read().decode())

    def track(self, campos):
        return self.pedir('/api/library/track', {
            'nome': 'Jogo TV', 'code': 'PS2', 'plataforma': 'PlayStation 2',
            'fonte': 'rom:PS2', 'campos': campos,
        })

    def test_rom_progress_batch_preserves_existing_fields(self):
        self.assertEqual(self.track({'iniciado': True, 'observacoes': 'Preservar'})[0], 200)
        self.assertEqual(self.track({'iniciado': True, 'finalizado': True,
                                     'platinado': False, 'nota': 8.1})[0], 200)
        games = lm.load_library(self.lib_path)['games']
        self.assertEqual(len(games), 1)
        self.assertTrue(games[0]['finalizado'])
        self.assertEqual(games[0]['nota'], 8.1)
        self.assertEqual(games[0]['observacoes'], 'Preservar')

    def test_invalid_batch_does_not_create_or_partially_modify_rom(self):
        self.assertEqual(self.track({'iniciado': True, 'nota': 99})[0], 400)
        self.assertEqual(lm.load_library(self.lib_path)['games'], [])
        self.track({'iniciado': False})
        before = self.lib_path.read_bytes()
        for campos in ({'iniciado': True, 'nota': 99}, {'iniciado': True, 'inexistente': 1}, [], {}):
            self.assertEqual(self.track(campos)[0], 400)
            self.assertEqual(self.lib_path.read_bytes(), before)

    def test_play_options_validate_local_rom_without_launching(self):
        from unittest.mock import patch
        from core import play
        rom = self.raiz / 'ROMs/PS2/Teste.iso'
        rom.parent.mkdir(parents=True, exist_ok=True)
        rom.write_bytes(b'iso ficticio')
        with patch.object(play, 'LAUNCHER', rom):
            status, data = self.pedir('/api/play/options?code=PS2&name=Teste.iso')
        self.assertEqual(status, 200)
        self.assertEqual(data['options'], [{'name': 'Teste.iso', 'error': None}])
        status, _ = self.pedir('/api/play/options?code=PS2&name=../fora.iso')
        self.assertEqual(status, 400)

    def test_play_start_uses_csrf_and_only_starts_validated_request(self):
        from unittest.mock import patch
        with patch.object(__import__('server').PLAY_SESSIONS, 'start', return_value={'status': 'running'}) as start:
            status, data = self.pedir('/api/play/start', {'code': 'PS2', 'name': 'Teste.iso'})
            self.assertEqual(status, 200)
            self.assertEqual(data['status'], 'running')
            self.assertEqual(start.call_args.args[1:], ('PS2', 'Teste.iso'))
        import urllib.error
        req = urllib.request.Request(self.url + '/api/play/start', data=b'{}', headers={'Content-Type': 'application/json'})
        with self.assertRaises(urllib.error.HTTPError) as response:
            urllib.request.urlopen(req)
        self.assertEqual(response.exception.code, 403)
        response.exception.close()
