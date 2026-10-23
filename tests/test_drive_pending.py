"""Pendências de saves enviadas pelo celular ao Drive, aplicadas no PC com histórico."""
import hashlib
import shutil

from test_api import BaseAPI


def sha(data):
    return hashlib.sha256(data).hexdigest()


class TestDrivePending(BaseAPI):
    def setUp(self):
        self.saves = self.raiz / 'Saves/saves'
        shutil.rmtree(self.raiz / 'Saves', ignore_errors=True)
        (self.saves / 'SFC').mkdir(parents=True)
        (self.saves / 'SFC/Jogo.srm').write_bytes(b'pc antigo')

    def pending(self, data, base):
        folder = self.saves / '.pyretro-pending/SFC/Jogo.srm'
        folder.mkdir(parents=True, exist_ok=True)
        name = f"1700000000000-{base or 'none'}.pending"
        (folder / name).write_bytes(data)
        return name

    def listing(self):
        status, data = self.pedir('/api/drive_pending')
        self.assertEqual(status, 200)
        return data['items']

    def test_apply_when_pc_is_still_the_version_the_phone_saw(self):
        name = self.pending(b'do celular', sha(b'pc antigo'))
        [item] = self.listing()
        self.assertEqual(item['status'], 'apply')
        status, _ = self.pedir('/api/drive_pending/apply', {'group': 'retro-saves', 'path': 'SFC/Jogo.srm', 'pending': name})
        self.assertEqual(status, 200)
        self.assertEqual((self.saves / 'SFC/Jogo.srm').read_bytes(), b'do celular')
        history = list((self.saves / '.pyretro-history/SFC/Jogo.srm').iterdir())
        self.assertEqual(sorted(p.suffix for p in history), ['.applied', '.previous'])
        self.assertEqual(self.listing(), [])

    def test_conflict_keeps_pc_until_user_chooses(self):
        name = self.pending(b'do celular', sha(b'outra versao'))
        [item] = self.listing()
        self.assertEqual(item['status'], 'conflict')
        status, _ = self.pedir('/api/drive_pending/apply', {'group': 'retro-saves', 'path': 'SFC/Jogo.srm', 'pending': name})
        self.assertEqual(status, 409)
        self.assertEqual((self.saves / 'SFC/Jogo.srm').read_bytes(), b'pc antigo')
        status, _ = self.pedir('/api/drive_pending/reject', {'group': 'retro-saves', 'path': 'SFC/Jogo.srm', 'pending': name})
        self.assertEqual(status, 200)
        self.assertEqual((self.saves / 'SFC/Jogo.srm').read_bytes(), b'pc antigo')
        self.assertEqual(self.listing(), [])

    def test_force_uses_phone_version_and_preserves_pc(self):
        name = self.pending(b'do celular', sha(b'outra versao'))
        status, _ = self.pedir('/api/drive_pending/apply', {'group': 'retro-saves', 'path': 'SFC/Jogo.srm', 'pending': name, 'force': True})
        self.assertEqual(status, 200)
        self.assertEqual((self.saves / 'SFC/Jogo.srm').read_bytes(), b'do celular')
        previous = [p for p in (self.saves / '.pyretro-history/SFC/Jogo.srm').iterdir() if p.suffix == '.previous']
        self.assertEqual(previous[0].read_bytes(), b'pc antigo')

    def test_invalid_names_and_paths_are_ignored(self):
        folder = self.saves / '.pyretro-pending/SFC/Jogo.srm'
        folder.mkdir(parents=True)
        (folder / 'qualquer.pending').write_bytes(b'x')
        self.assertEqual(self.listing(), [])
        status, _ = self.pedir('/api/drive_pending/apply', {'group': 'retro-saves', 'path': 'SFC/Jogo.srm', 'pending': 'qualquer.pending'})
        self.assertEqual(status, 404)
