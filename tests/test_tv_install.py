"""Preservação de atalhos Steam: somente VDF fictício em memória."""
from pathlib import Path
import unittest
from tools import install_tv


class TestTVInstall(unittest.TestCase):
    def test_rename_preserves_id_artwork_tags_and_all_other_fields(self):
        launcher, home = Path('/home/test/.local/bin/pyretro-tv'), Path('/home/test')
        data, _ = install_tv.add_shortcut(b'', launcher, home)
        nodes = install_tv.decode(data)
        fields = nodes[0][2][0][2]
        fields[:] = [(t, k, install_tv.LEGACY_NAME if k == 'AppName' else v) for t, k, v in fields]
        old = install_tv.encode(nodes)
        new, changed = install_tv.add_shortcut(old, launcher, home)
        self.assertTrue(changed)
        self.assertEqual(new, data)
        self.assertFalse(install_tv.add_shortcut(new, launcher, home)[1])

    def test_addition_preserves_unknown_fields_and_existing_shortcut_bytes(self):
        # Um atalho com campos e tags que o instalador não deve editar.
        existing = b'\x000\0\x01AppName\0Meu jogo\0\x02appid\0\x01\x00\x00\x80\x00tags\0\x010\0Favoritos\0\x08\x08'
        data = b'\x00shortcuts\0' + existing + b'\x08\x08'
        new, changed = install_tv.add_shortcut(data, Path('/home/test/.local/bin/pyretro-tv'), Path('/home/test'))
        self.assertTrue(changed)
        self.assertEqual(new[:len(data)-2], data[:-2])
        self.assertIn(install_tv.NAME.encode(), new)
        self.assertIn(b'--host "/home/test/.local/bin/pyretro-tv"', new)
        self.assertIn(existing, new)
        again, changed = install_tv.add_shortcut(new, Path('/home/test/.local/bin/pyretro-tv'), Path('/home/test'))
        self.assertFalse(changed)
        self.assertEqual(again, new)

    def test_unknown_or_truncated_vdf_is_refused(self):
        for data in (b'\x00shortcuts\0', b'\x00shortcuts\0\x090\0\x08\x08', b'\x08extras'):
            with self.subTest(data=data), self.assertRaises((ValueError, IndexError)):
                install_tv.add_shortcut(data, Path('/launcher'), Path('/home/test'))
