"""Descritor incompleto e faixa compartilhada não podem parecer um jogo pronto."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from core import mobile_roms, rom_bundles
from test_api import BaseAPI
from test_mobile_roms import config


class TestBundles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ps = self.root / 'PS'; self.ps.mkdir()
        self.cfg = config(self.root)
        self.cfg['heavy_systems']['PS']['exts'].append('m3u')
        (self.ps / 'Album.m3u').write_text('#EXTM3U\nDisc 1.cue\nDisc 2.cue\n')
        (self.ps / 'Disc 1.cue').write_text('FILE "shared.bin" BINARY\n TRACK 01 MODE2/2352')
        (self.ps / 'Disc 2.cue').write_text('FILE "shared.bin" BINARY\n TRACK 01 MODE2/2352')
        (self.ps / 'shared.bin').write_bytes(b'track')

    def bundle(self, entry='Album.m3u'):
        return mobile_roms.bundle(self.cfg, 'PS', entry, set())

    def test_dependency_order_dedup_and_resume_binding(self):
        result = self.bundle()
        self.assertEqual([f['file'] for f in result['files']],
                         ['shared.bin', 'Disc 1.cue', 'Disc 2.cue', 'Album.m3u'])
        member = result['files'][0]
        resolved = mobile_roms.resolve_member(self.cfg, 'PS', 'Album.m3u', member['file'],
                                             result['id'], member['etag'], set())
        self.assertEqual(resolved['path'].read_bytes(), b'track')
        (self.ps / 'Disc 2.cue').write_text('FILE "different.bin" BINARY')
        (self.ps / 'different.bin').write_bytes(b'changed')
        with self.assertRaises(LookupError):
            mobile_roms.resolve_member(self.cfg, 'PS', 'Album.m3u', member['file'],
                                       result['id'], member['etag'], set())

    def test_missing_cycle_escape_and_symlink_refused(self):
        for ref in ['missing.bin', '../private.bin', '/etc/passwd', 'https://x/a.bin', 'Album.m3u']:
            (self.ps / 'Disc 1.cue').write_text(f'FILE "{ref}" BINARY')
            with self.subTest(ref=ref), self.assertRaises(ValueError): self.bundle()
        (self.root / 'private.bin').write_bytes(b'private')
        (self.ps / 'link.bin').symlink_to(self.root / 'private.bin')
        (self.ps / 'Disc 1.cue').write_text('FILE "link.bin" BINARY')
        with self.assertRaises(ValueError): self.bundle()

    def test_member_cannot_fetch_unrelated_file(self):
        result = self.bundle()
        (self.ps / 'Other.bin').write_bytes(b'other')
        with self.assertRaises(ValueError):
            mobile_roms.resolve_member(self.cfg, 'PS', 'Album.m3u', 'Other.bin', result['id'], 'x', set())

    def test_removal_preserves_shared_files_and_never_deletes(self):
        (self.ps / 'Other.cue').write_text('FILE "shared.bin" BINARY')
        plan = mobile_roms.removal_plan(self.cfg, 'PS', 'Album.m3u')
        self.assertEqual(plan['preserve'], ['shared.bin'])
        self.assertEqual(plan['remove'], ['Album.m3u', 'Disc 1.cue', 'Disc 2.cue'])
        self.assertTrue((self.ps / 'shared.bin').exists())
        (self.ps / 'Other.m3u').write_text('Album.m3u')
        self.assertEqual(mobile_roms.removal_plan(self.cfg, 'PS', 'Album.m3u')['remove'], [])

    def test_unreadable_external_descriptor_blocks_removal(self):
        (self.ps / 'Broken.cue').write_text('FILE "missing.bin" BINARY')
        plan = mobile_roms.removal_plan(self.cfg, 'PS', 'Album.m3u')
        self.assertFalse(plan['complete']); self.assertEqual(plan['remove'], [])

    def test_remote_bundle_includes_uncatalogued_explicit_track(self):
        calls = []
        data = {'Game.cue': b'FILE "track.bin" BINARY', 'track.bin': b'abc'}
        def run(args, **kwargs):
            calls.append(args)
            payload = data.get(args[-1].split('/PS/')[-1])
            if payload is None: return subprocess.CompletedProcess(args, 1, b'', b'')
            output = payload if args[1] == 'cat' else json.dumps({'Size': len(payload), 'ModTime': 't', 'IsDir': False})
            return subprocess.CompletedProcess(args, 0, output, '')
        result = mobile_roms.bundle(self.cfg, 'PS', 'Game.cue', {'Game.cue'}, run)
        self.assertEqual([f['file'] for f in result['files']], ['track.bin', 'Game.cue'])
        self.assertTrue(all(f['source'] == 'drive' for f in result['files']))
        self.assertTrue(any(c[1:3] == ['cat', '--count'] for c in calls))

    def test_oversized_descriptor_refused_before_read(self):
        with (self.ps / 'Huge.cue').open('wb') as f: f.truncate(rom_bundles.MAX_TEXT + 1)
        with self.assertRaises(ValueError): self.bundle('Huge.cue')

    def test_change_during_traversal_is_not_published_as_valid_manifest(self):
        counts = {}
        def stat(name):
            counts[name] = counts.get(name, 0) + 1
            return {'size': 30, 'source': 'pc', 'etag': str(counts[name]) if name == 'track.bin' else 'same'}
        with self.assertRaises(LookupError):
            rom_bundles.manifest('disc.cue', stat, lambda _: 'FILE "track.bin" BINARY')


class TestBundleRoutes(BaseAPI):
    def test_manifest_and_member_http(self):
        root = self.raiz / 'ROMs/PS2'
        root.mkdir(exist_ok=True)
        (root / 'Disc.iso').write_bytes(b'disc')
        query = urlencode({'code': 'PS2', 'entry': 'Disc.iso'})
        status, result = self.pedir('/api/mobile/rom/bundle?' + query)
        self.assertEqual(status, 200)
        member = result['files'][0]
        query = urlencode({'code': 'PS2', 'entry': 'Disc.iso', 'file': 'Disc.iso',
                           'bundle': result['id'], 'etag': member['etag']})
        with urlopen(self.url + '/api/mobile/rom/file?' + query, timeout=10) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b'disc')

    def test_stale_manifest_is_conflict(self):
        query = urlencode({'code': 'SFC', 'entry': 'Chrono Trigger.sfc', 'file': 'Chrono Trigger.sfc',
                           'bundle': 'stale', 'etag': 'stale'})
        self.assertEqual(self.pedir('/api/mobile/rom/file?' + query)[0], 409)
