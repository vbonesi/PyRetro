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
