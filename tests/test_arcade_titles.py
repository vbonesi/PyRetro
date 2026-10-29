"""ROM de Arcade (arquivo = código do set) reconhecida na Biblioteca pelo título completo do DAT."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import arcade, library

DAT = '''<?xml version="1.0"?><datafile>
<game name="kof97" romof="neogeo"><description>The King of Fighters '97 (NGM-2320)</description></game>
<game name="neogeo" isbios="yes"><description>Neo Geo</description></game>
</datafile>'''


def lib(*games):
    return {'games': [{'id': n, 'nome': n, 'plataforma': p, 'fontes': [], 'nomes_alt': []} for n, p in games]}


class ArcadeTitles(unittest.TestCase):
    def test_load_titles_reads_description_of_each_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'FinalBurn Neo (ClrMame Pro XML, Arcade only).dat').write_text(DAT)
            self.assertEqual(arcade.load_titles(tmp)['kof97'], "The King of Fighters '97 (NGM-2320)")
        self.assertEqual(arcade.load_titles('/nao/existe'), {})

    def test_set_code_resolves_to_the_registered_game_ignoring_revision_code(self):
        index = library.index_by_rom_name(lib(("The King of Fighters '97", 'FBNeo - Arcade Games')))
        with mock.patch.object(library, '_arcade_titles', return_value={'kof97': ["The King of Fighters '97 (NGM-2320)"]}):
            self.assertEqual(library.find_for_rom(index, 'kof97', 'ARCADE')['id'], "The King of Fighters '97")
            self.assertEqual([g['id'] for g in library.records_for_rom(index, 'KOF97', 'ARCADE')], ["The King of Fighters '97"])
            self.assertIsNone(library.find_for_rom(index, 'kof97', 'FC'))  # outro sistema nunca herda o título
            self.assertIsNone(library.find_for_rom(index, 'kof98', 'ARCADE'))

    def test_other_systems_keep_matching_only_by_name_and_edition_stays_separate(self):
        index = library.index_by_rom_name(lib(('Game', 'Nintendo - Super Nintendo Entertainment System')))
        with mock.patch.object(library, '_arcade_titles', return_value={'game': ['Other Title']}):
            self.assertEqual(library.rom_name_keys('Game', 'SFC'), ['game'])
            self.assertEqual(library.find_for_rom(index, 'Game (USA)', 'SFC')['id'], 'Game')

    def test_unreadable_titles_never_break_matching(self):
        index = library.index_by_rom_name(lib(('kof97', 'FBNeo - Arcade Games')))
        with mock.patch.object(library, '_arcade_titles', return_value={}):
            self.assertEqual(library.find_for_rom(index, 'kof97', 'ARCADE')['id'], 'kof97')

    def test_add_mobile_rom_reuses_the_record_found_by_title(self):
        library_ = lib(("The King of Fighters '97", 'FBNeo - Arcade Games'))
        cfg = {'systems': {'ARCADE': {'nome': 'FBNeo - Arcade Games'}}}
        with mock.patch.object(library, '_arcade_titles', return_value={'kof97': ["The King of Fighters '97 (NGM-2320)"]}):
            game, created = library.add_mobile_rom(library_, cfg, {'nome': 'kof97', 'code': 'ARCADE'})
        self.assertFalse(created)
        self.assertEqual(len(library_['games']), 1)
        self.assertIn('rom:ARCADE', game['fontes'])


if __name__ == '__main__':
    unittest.main()
