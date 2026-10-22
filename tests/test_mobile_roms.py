"""Download de ROM pelo celular (core/mobile_roms.py e rotas /api/mobile/rom).

Origem do problema (22/10/2026): para baixar uma ROM do catálogo, o celular
exigia vincular cada arquivo pelo seletor do Drive em Opções. Agora o
notebook entrega o arquivo que já tem, ou faz streaming do Drive pelo rclone.
O risco é silencioso: uma retomada que junta pedaços de versões diferentes do
arquivo vira ROM corrompida sem erro. Por isso o etag é conferido sempre.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import mobile_roms
from test_api import BaseAPI


def config(root):
    return {'pc': {'roms_root': str(root)},
            'systems': {'SFC': {'exts': ['sfc']}},
            'heavy_systems': {'PS': {'exts': ['cue', 'chd']}, 'PSP': {'exts': ['iso', 'cso']}},
            'rclone': {'remote': 'drive', 'drive_roms_root': 'Jogos/ROMs'}}


class FakeRun:
    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        out = self.answers.get(args[-1])
        if out is None:
            return subprocess.CompletedProcess(args, 3, '', 'not found')
        return subprocess.CompletedProcess(args, 0, json.dumps(out), '')


class TestOptions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        (self.root / 'SFC').mkdir(); (self.root / 'PS').mkdir()
        (self.root / 'SFC/Chrono Trigger.sfc').write_bytes(b'abc')
        (self.root / 'SFC/Super Mario Bros. 3.sfc').write_bytes(b'x')
        (self.root / 'PS/Crash.cue').write_text('FILE "Crash.bin" BINARY')
        (self.root / 'PS/Crash.chd').write_bytes(b'chd')
        self.cfg = config(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_local_por_rotulo_sem_extensao_lista_somente_o_proprio_jogo(self):
        files = mobile_roms.options(self.cfg, 'SFC', 'Chrono Trigger', set())
        self.assertEqual([(f['file'], f['size'], f['source']) for f in files], [('Chrono Trigger.sfc', 3, 'pc')])
        # "Super Mario Bros" não pode puxar o arquivo do "Super Mario Bros. 3".
        self.assertEqual(mobile_roms.options(self.cfg, 'SFC', 'Super Mario Bros', set()), [])

    def test_lista_os_formatos_e_o_celular_escolhe(self):
        names = [f['file'] for f in mobile_roms.options(self.cfg, 'PS', 'Crash', set())]
        self.assertEqual(names, ['Crash.chd', 'Crash.cue'])

    def test_caminho_para_fora_do_sistema_e_recusado(self):
        for name in ('../SFC/Chrono Trigger', '/etc/passwd', 'a/../../x'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                mobile_roms.options(self.cfg, 'PS', name, set())
        with self.assertRaises(ValueError):
            mobile_roms.options(self.cfg, 'XYZ', 'Chrono Trigger', set())

    def test_drive_so_para_nome_do_catalogo_e_sistema_pesado(self):
        run = FakeRun({'drive:Jogos/ROMs/PSP/Patapon.iso': {'Size': 10, 'ModTime': 't1', 'IsDir': False}})
        self.assertEqual(mobile_roms.options(self.cfg, 'PSP', 'Patapon.iso', set(), run), [])
        self.assertEqual(run.calls, [], 'sem nome no catálogo não consulta o Drive')
        files = mobile_roms.options(self.cfg, 'PSP', 'Patapon.iso', {'Patapon.iso'}, run)
        self.assertEqual(files, [{'file': 'Patapon.iso', 'size': 10, 'etag': '10-t1', 'source': 'drive'}])

    def test_pasta_no_drive_lista_os_arquivos_de_dentro(self):
        listing = [{'Path': 'FF7 (Disc 1).chd', 'Size': 5, 'ModTime': 'a'},
                   {'Path': 'leia.txt', 'Size': 1, 'ModTime': 'a'}]
        def fake(args, **kwargs):
            out = {'IsDir': True, 'Size': -1} if '--stat' in args else listing
            return subprocess.CompletedProcess(args, 0, json.dumps(out), '')
        files = mobile_roms.options(self.cfg, 'PS', 'FF7', {'FF7'}, fake)
        self.assertEqual([f['file'] for f in files], ['FF7/FF7 (Disc 1).chd'])

    def test_resolve_confere_etag_local(self):
        path = self.root / 'SFC/Chrono Trigger.sfc'
        item = mobile_roms.resolve(self.cfg, 'SFC', 'Chrono Trigger.sfc', '', set())
        self.assertEqual(item['size'], 3)
        mobile_roms.resolve(self.cfg, 'SFC', 'Chrono Trigger.sfc', item['etag'], set())
        os.utime(path, ns=(1, 1))
        with self.assertRaises(LookupError):
            mobile_roms.resolve(self.cfg, 'SFC', 'Chrono Trigger.sfc', item['etag'], set())
        with self.assertRaises(ValueError):
            mobile_roms.resolve(self.cfg, 'SFC', 'Chrono Trigger.txt', '', set())

    def test_range(self):
        self.assertIsNone(mobile_roms.parse_range(None, 10))
        self.assertEqual(mobile_roms.parse_range('bytes=4-', 10), (4, 9))
        self.assertEqual(mobile_roms.parse_range('bytes=2-99', 10), (2, 9))
        for bad in ('bytes=10-', 'bytes=5-2', 'bytes=1-2,4-5', 'items=0-'):
            with self.subTest(bad=bad), self.assertRaises(IndexError):
                mobile_roms.parse_range(bad, 10)

    def test_drive_envia_trecho_pelo_rclone_cat(self):
        class Process:
            def __init__(self, args, **kwargs):
                Process.args = args; self.stdout = io.BytesIO(b'0123')
            def poll(self): return 0
            def wait(self): return 0
        out = io.BytesIO()
        mobile_roms.send({'source': 'drive', 'remote': 'drive:Jogos/ROMs/PSP/x.iso'}, 6, 9, out, Process)
        self.assertEqual(out.getvalue(), b'0123')
        self.assertEqual(Process.args[:6], ['rclone', 'cat', '--offset', '6', '--count', '4'])
        with self.assertRaises(OSError):  # rclone curto: nunca parece sucesso
            mobile_roms.send({'source': 'drive', 'remote': 'r'}, 0, 9, io.BytesIO(), Process)


class TestRotas(BaseAPI):
    def baixar(self, rota, headers=None):
        req = urllib.request.Request(self.url + rota, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            with e:
                return e.code, dict(e.headers), e.read()

    def test_opcoes_e_download_com_retomada(self):
        status, data = self.pedir('/api/mobile/rom/options?code=SFC&name=Chrono%20Trigger')
        self.assertEqual(status, 200)
        (option,) = data['files']
        self.assertEqual(option['file'], 'Chrono Trigger.sfc')
        rota = '/api/mobile/rom/file?code=SFC&file=Chrono%20Trigger.sfc&etag=' + option['etag']
        status, headers, body = self.baixar(rota)
        self.assertEqual((status, body), (200, b'rom'))
        status, headers, body = self.baixar(rota, {'Range': 'bytes=1-'})
        self.assertEqual((status, body, headers['Content-Range']), (206, b'om', 'bytes 1-2/3'))
        self.assertEqual(self.baixar(rota, {'Range': 'bytes=9-'})[0], 416)
        self.assertEqual(self.baixar('/api/mobile/rom/file?code=SFC&file=Chrono%20Trigger.sfc&etag=0-0')[0], 409)
        self.assertEqual(self.baixar('/api/mobile/rom/file?code=SFC&file=..%2Fconfig.toml')[0], 400)
