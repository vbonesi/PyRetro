from concurrent.futures import ThreadPoolExecutor
import urllib.request
import urllib.error
from test_api import BaseAPI
from core import library as lm


class MobileLibraryTests(BaseAPI):
    def setUp(self):
        self.gravar_biblioteca([])

    def add(self, nome='Somente celular', code='SFC'):
        return self.pedir('/api/library/add-rom', {'nome': nome, 'code': code})

    def test_phone_only_rom_is_idempotent_and_present_in_catalog(self):
        status, first = self.add()
        self.assertEqual(status, 201)
        self.assertTrue(first['created'])
        status, again = self.add()
        self.assertEqual(status, 200)
        self.assertEqual(first['id'], again['id'])
        self.assertFalse(again['created'])
        status, catalog = self.pedir('/api/tv/catalog')
        games = catalog if isinstance(catalog, list) else catalog['games']
        game = next(g for g in games if g.get('id') == first['id'])
        self.assertEqual((game['code'], game['romName'], game['local']), ('SFC', 'Somente celular', False))
        self.assertFalse((self.raiz / 'ROMs/SFC/Somente celular.sfc').exists())

    def test_reuse_preserves_history_and_separates_platform(self):
        game = lm._blank_game('Mesmo nome', 'Super Nintendo')
        game.update(iniciado=True, nota=9, tempo=125, observacoes='manter', nomes_alt=['Alias'])
        self.gravar_biblioteca([game])
        self.assertEqual(self.add('Alias')[1]['id'], game['id'])
        self.assertEqual(self.add('Mesmo nome', 'PS2')[0], 201)
        stored = lm.load_library(self.lib_path)['games'][0]
        self.assertEqual(stored, {**game, 'fontes': ['rom:SFC']})

    def test_bad_bodies_never_write(self):
        before = self.lib_path.read_bytes()
        for body in ([], {'nome': [], 'code': 'SFC'}, {'nome': '../fora', 'code': 'SFC'},
                     {'nome': '\0x', 'code': 'SFC'}, {'nome': 'Game', 'code': 'UNK'},
                     {'nome': 'Game', 'code': 'SFC', 'iniciado': True}, {'nome': ' ', 'code': 'SFC'}):
            self.assertEqual(self.pedir('/api/library/add-rom', body)[0], 400, body)
            self.assertEqual(self.lib_path.read_bytes(), before)

    def test_ambiguity_does_not_choose_first(self):
        a = lm._blank_game('Duplicado', 'Super Nintendo', 'one')
        b = lm._blank_game('Duplicado', 'Super Nintendo', 'two')
        self.gravar_biblioteca([a, b]); before = self.lib_path.read_bytes()
        self.assertEqual(self.add('Duplicado')[0], 409)
        self.assertEqual(self.lib_path.read_bytes(), before)

    def test_parallel_requests_create_one_and_csrf_is_required(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.add(), range(4)))
        self.assertEqual(sorted(r[0] for r in results), [200, 200, 200, 201])
        self.assertEqual(len({r[1]['id'] for r in results}), 1)
        req = urllib.request.Request(self.url + '/api/library/add-rom', data=b'{}')
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(req)
        self.assertEqual(error.exception.code, 403)
        error.exception.close()
