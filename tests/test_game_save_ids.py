import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote
from core import game_save_ids as ids, library, serials
from test_api import BaseAPI


def ncch(title='0004000000123400'):
    data = bytearray(512)
    data[0x100:0x104] = b'NCCH'
    data[0x104:0x108] = (1).to_bytes(4, 'little')
    data[0x118:0x120] = int(title, 16).to_bytes(8, 'little')
    return data


class SaveIdTests(unittest.TestCase):
    def test_psp_region_requires_exact_match_or_user_choice(self):
        game = library._blank_game('Game', 'Sony - PSP')
        index = {'PSP': {'ULUS-12345': 'Game (USA)', 'ULES-12345': 'Game (Europe)'}}
        result = ids.mapping({}, game, index)
        self.assertEqual(result['status'], 'needs-choice')
        self.assertEqual(result['titleIds'], [])
        self.assertEqual(result['filters'], [])
        self.assertEqual(len(result['candidates']), 2)
        game['nome'] = 'Game (USA)'
        result = ids.mapping({}, game, index)
        self.assertEqual(result['titleIds'], ['ULUS12345'])
        self.assertEqual(len(result['filters']), 2)
        game['plataforma'] = 'Super Nintendo'
        self.assertEqual(ids.mapping({}, game, index)['status'], 'unsupported')

    def test_alias_can_identify_but_multiple_exact_aliases_are_ambiguous(self):
        game = library._blank_game('Localized name', 'PSP')
        game['nomes_alt'] = ['Game (USA)']
        index = {'PSP': {'ULUS12345': 'Game (USA)', 'ULES12345': 'Game (Europe)'}}
        self.assertEqual(ids.mapping({}, game, index)['status'], 'identified')
        game['nomes_alt'].append('Game (Europe)')
        self.assertEqual(ids.mapping({}, game, index)['status'], 'needs-choice')

    def test_3ds_ncch_ncsd_bounds_and_base_title(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'test.3ds'
            path.write_bytes(ncch())
            self.assertEqual(ids.read_3ds_id(path), '0004000000123400')
            container = bytearray(1024)
            container[0x100:0x104] = b'NCSD'
            container[0x120:0x124] = (1).to_bytes(4, 'little')
            container[0x124:0x128] = (1).to_bytes(4, 'little')
            container[512:] = ncch()
            path.write_bytes(container)
            self.assertEqual(ids.read_3ds_id(path), '0004000000123400')
            for data in (b'NCCH', container[:-1], ncch('0004000e00123400'), ncch('0000000000000000')):
                path.write_bytes(data)
                with self.assertRaises(ValueError): ids.read_3ds_id(path)

    def test_filters_do_not_cross_title_extdata_content_or_history(self):
        root = 'Nintendo 3DS/' + '0'*32 + '/' + '1'*32 + '/'
        title = '0004000000123400'
        self.assertTrue(ids.matches('3ds-saves', root+'title/00040000/00123400/data/00000001/main', title))
        for suffix in ('title/00040000/00123401/data/main', 'title/00040000/00123400/content/main',
                       'extdata/00000000/00123400/main', 'title/00040000/00123400/data/../main'):
            self.assertFalse(ids.matches('3ds-saves', root+suffix, title))
        self.assertTrue(ids.matches('psp-saves', 'ULUS12345DATA00/DATA.BIN', 'ULUS12345'))
        self.assertTrue(ids.matches('psp-states', 'ULUS12345_1.00_0.ppst', 'ULUS12345'))
        self.assertFalse(ids.matches('psp-saves', 'ULES12345DATA00/DATA.BIN', 'ULUS12345'))
        self.assertFalse(ids.matches('psp-saves', 'ULUS12345DATA00/.pyretro-history/x', 'ULUS12345'))

    def test_local_mapping_never_follows_symlinks_and_does_not_guess_extdata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/'3DS').mkdir()
            cfg = {'pc': {'roms_root': temp}}
            game = library._blank_game('Game', '3DS')
            outside = root/'outside.cxi'; outside.write_bytes(ncch())
            (root/'3DS/Game.cxi').symlink_to(outside)
            self.assertEqual(ids.mapping(cfg, game)['status'], 'unknown')
            (root/'3DS/Game.cxi').unlink()
            (root/'3DS/Game.cxi').write_bytes(ncch())
            result = ids.mapping(cfg, game)
            self.assertEqual(result['titleIds'], ['0004000000123400'])
            self.assertEqual(result['extdataStatus'], 'unknown')
            (root/'3DS/Game.cci').write_bytes(b'invalid')
            self.assertEqual(ids.mapping(cfg, game)['titleIds'], [])

    def test_missing_or_corrupt_cache_does_not_fetch(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(serials, 'INDEX_PATH', Path(temp)/'cache.json'), \
                patch.object(serials.urllib.request, 'urlopen', side_effect=AssertionError('no network')):
            self.assertEqual(serials.cached_index(), {})
            serials.INDEX_PATH.write_text('not json')
            self.assertEqual(serials.cached_index(), {})


class SaveIdRouteTests(BaseAPI):
    def setUp(self):
        self.game = library._blank_game('Game (USA)', 'PSP')
        self.gravar_biblioteca([self.game])

    def test_lookup_by_library_id_without_reading_saves_or_network(self):
        with patch.object(serials, 'cached_index', return_value={'PSP': {'ULUS-12345': 'Game (USA)'}}):
            status, result = self.pedir('/api/mobile/saves/game?id='+quote(self.game['id']))
        self.assertEqual(status, 200)
        self.assertEqual(result['id'], self.game['id'])
        self.assertEqual(result['titleIds'], ['ULUS12345'])
        self.assertEqual(self.pedir('/api/mobile/saves/game')[0], 400)
        self.assertEqual(self.pedir('/api/mobile/saves/game?id=missing')[0], 404)
