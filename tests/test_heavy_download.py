"""Download fictício: staging, faixas e recusa de sobrescrita."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from core import heavy_roms as heavy


class TestHeavyDownload(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name); self.root = self.base / 'ROMs'
        self.cfg = {'heavy_systems': {'PS': {'exts': ['cue', 'chd']}, 'PS2': {'exts': ['iso']}},
                    'rclone': {'staging_dir': str(self.base / 'staging')}}
        self.remote = {'Jogo.cue': b'FILE "Faixa 1.bin" BINARY\nFILE "Faixa 2.bin" BINARY\n',
                       'Faixa 1.bin': b'faixa 1', 'Faixa 2.bin': b'faixa 2', 'Jogo.iso': b'iso novo'}
        self.calls = []
        self.mock = patch.object(heavy.subprocess, 'run', side_effect=self.rclone)
        self.mock.start(); self.addCleanup(self.mock.stop)

    def rclone(self, args, **kwargs):
        self.calls.append(args)
        if args[1] == 'lsjson':
            return SimpleNamespace(returncode=0, stdout=json.dumps({'IsDir': False}), stderr='')
        name = args[2].split('/', 3)[-1]  # drive:Jogos/ROMs/PS/nome
        dest = Path(args[3]); dest.parent.mkdir(parents=True, exist_ok=True)
        if name not in self.remote:
            return SimpleNamespace(returncode=1, stdout='', stderr='arquivo ausente')
        dest.write_bytes(self.remote[name])
        return SimpleNamespace(returncode=0, stdout='', stderr='')

    def download(self, name, code='PS'):
        return heavy.download_from_drive(code, name, self.root, self.cfg)

    def test_light_systems_download_too_and_unknown_systems_are_refused(self):
        self.cfg['systems'] = {'SFC': {'exts': ['sfc', 'smc']}}
        self.remote['Jogo Leve.sfc'] = b'rom leve'
        self.assertTrue(self.download('Jogo Leve.sfc', code='SFC')[0])
        self.assertEqual((self.root / 'SFC' / 'Jogo Leve.sfc').read_bytes(), b'rom leve')
        ok, message = self.download('x.sfc', code='NAOEXISTE')
        self.assertFalse(ok); self.assertIn('desconhecido', message)

    def test_staging_goes_inside_games_root_when_storage_is_configured(self):
        self.assertEqual(heavy.download_staging(self.cfg), self.base / 'staging')
        self.cfg['storage'] = {'games_root': str(self.base / 'Games')}
        self.assertEqual(heavy.download_staging(self.cfg), self.base / 'Games' / '.pyretro' / 'staging')

    def test_cue_download_includes_referenced_tracks(self):
        self.assertTrue(self.download('Jogo.cue')[0])
        for name, data in self.remote.items():
            if name.endswith('.iso'): continue
            self.assertEqual((self.root / 'PS' / name).read_bytes(), data)
        self.assertEqual(list((self.base / 'staging').iterdir()), [])

    def test_existing_cue_is_preserved_and_missing_tracks_are_downloaded(self):
        dest = self.root / 'PS'; dest.mkdir(parents=True)
        (dest / 'Jogo.cue').write_bytes(self.remote['Jogo.cue'])
        (dest / 'Faixa 1.bin').write_bytes(b'minha faixa existente')
        self.assertTrue(self.download('Jogo.cue')[0])
        self.assertEqual((dest / 'Faixa 1.bin').read_bytes(), b'minha faixa existente')
        self.assertEqual((dest / 'Faixa 2.bin').read_bytes(), b'faixa 2')

    def test_missing_track_failure_does_not_publish_primary(self):
        del self.remote['Faixa 2.bin']
        self.assertFalse(self.download('Jogo.cue')[0])
        self.assertFalse((self.root / 'PS' / 'Jogo.cue').exists())
        self.assertFalse((self.root / 'PS' / 'Faixa 1.bin').exists())

    def test_existing_iso_and_staging_files_are_preserved(self):
        dest = self.root / 'PS2'; dest.mkdir(parents=True)
        (dest / 'Jogo.iso').write_bytes(b'original')
        staging = self.base / 'staging'; staging.mkdir(); (staging / 'Jogo.iso').write_bytes(b'antigo')
        self.assertFalse(self.download('Jogo.iso', 'PS2')[0])
        self.assertEqual((dest / 'Jogo.iso').read_bytes(), b'original')
        self.assertEqual((staging / 'Jogo.iso').read_bytes(), b'antigo')

    def test_regular_file_uses_copyto_and_unique_staging(self):
        self.assertTrue(self.download('Jogo.iso', 'PS2')[0])
        self.assertEqual((self.root / 'PS2' / 'Jogo.iso').read_bytes(), b'iso novo')
        command = next(c for c in self.calls if c[1] == 'copyto')
        self.assertIn('pyretro-rom-', command[3])

    def test_download_rejects_paths_before_running_rclone(self):
        for name in ('../Jogo.iso', '/tmp/Jogo.iso', 'pasta/Jogo.iso'):
            self.assertFalse(self.download(name, 'PS2')[0])
        self.assertEqual(self.calls, [])

    def test_destination_appearing_during_download_is_never_overwritten(self):
        original = self.rclone
        def concurrent(args, **kwargs):
            result = original(args, **kwargs)
            if args[1] == 'copyto':
                dest = self.root / 'PS2' / 'Jogo.iso'; dest.parent.mkdir(parents=True)
                dest.write_bytes(b'chegou pelo Insync')
            return result
        with patch.object(heavy.subprocess, 'run', side_effect=concurrent):
            self.assertFalse(self.download('Jogo.iso', 'PS2')[0])
        self.assertEqual((self.root / 'PS2/Jogo.iso').read_bytes(), b'chegou pelo Insync')

    def test_directory_download_preserves_item_folder(self):
        def folder(args, **kwargs):
            if args[1] == 'lsjson':
                return SimpleNamespace(returncode=0, stdout=json.dumps({'IsDir': True}), stderr='')
            dest = Path(args[3]); dest.mkdir(parents=True)
            (dest / 'Disco.chd').write_bytes(b'jogo')
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        with patch.object(heavy.subprocess, 'run', side_effect=folder):
            self.assertTrue(self.download('Conjunto')[0])
        self.assertEqual((self.root / 'PS/Conjunto/Disco.chd').read_bytes(), b'jogo')

    def test_directory_missing_track_is_not_published(self):
        def folder(args, **kwargs):
            if args[1] == 'lsjson':
                return SimpleNamespace(returncode=0, stdout=json.dumps({'IsDir': True}), stderr='')
            dest = Path(args[3]); dest.mkdir(parents=True)
            (dest / 'Disco.cue').write_bytes(b'FILE "Ausente.bin" BINARY\n')
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        with patch.object(heavy.subprocess, 'run', side_effect=folder):
            self.assertFalse(self.download('Conjunto')[0])
        self.assertFalse((self.root / 'PS/Conjunto').exists())
