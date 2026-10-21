"""Sincronização móvel com acervo sintético; sem adb, nuvem ou saves reais."""
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
import urllib.parse
import urllib.request
from unittest.mock import patch

from core import mobile_sync as sync
from test_api import BaseAPI


def digest(data):return hashlib.sha256(data).hexdigest()


class MobileSyncFiles(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.cfg={'pc':{'saves_root':str(self.base/'saves'),'states_root':str(self.base/'states')}}
        self.root=sync.root(self.cfg,'retro-saves');self.root.mkdir()

    def put(self,data,expected='-',relative='Jogo.srm'):
        return sync.receive(self.cfg,'retro-saves',relative,expected,digest(data),io.BytesIO(data),len(data))

    def test_first_upload_retry_and_previous_version_are_preserved(self):
        self.put(b'old');self.put(b'old')
        result=self.put(b'new',digest(b'old'))
        self.assertEqual(result['sha256'],digest(b'new'))
        self.assertEqual((self.root/'Jogo.srm').read_bytes(),b'new')
        history=list((self.root/'.pyretro-history').rglob('*.previous'))
        self.assertEqual(len(history),1);self.assertEqual(history[0].read_bytes(),b'old')
        manifest=sync.manifest(self.cfg,'retro-saves')
        self.assertEqual([row['path'] for row in manifest['files']],['Jogo.srm'])

    def test_conflict_missing_expected_truncated_and_bad_checksum_never_change_destination(self):
        self.put(b'original')
        with self.assertRaises(sync.Conflict):self.put(b'new',digest(b'outdated'))
        with self.assertRaises(ValueError):self.put(b'new','')
        with self.assertRaises(ValueError):sync.receive(self.cfg,'retro-saves','Jogo.srm',digest(b'original'),digest(b'x'),io.BytesIO(b'x'),2)
        with self.assertRaises(ValueError):sync.receive(self.cfg,'retro-saves','Jogo.srm',digest(b'original'),digest(b'other'),io.BytesIO(b'x'),1)
        self.assertEqual((self.root/'Jogo.srm').read_bytes(),b'original')
        self.assertFalse((self.root/'.pyretro-history').exists())

    def test_path_symlink_and_rom_uploads_are_refused(self):
        outside=self.base/'outside.srm';outside.write_bytes(b'outside')
        (self.root/'link.srm').symlink_to(outside)
        for path in ('../outside.srm','/outside.srm','folder/../Jogo.srm','folder\\Jogo.srm','.pyretro-history/Jogo.srm','ROM.nes','link.srm'):
            with self.subTest(path=path),self.assertRaises(ValueError):self.put(b'x',relative=path)
        self.assertEqual(outside.read_bytes(),b'outside')

    def test_snapshot_is_checked_before_sending(self):
        self.put(b'original')
        with sync.snapshot(self.cfg,'retro-saves','Jogo.srm',digest(b'original')) as (file,info):
            self.assertEqual(file.read(),b'original');self.assertEqual(info['size'],8)
        with self.assertRaises(sync.Conflict):
            with sync.snapshot(self.cfg,'retro-saves','Jogo.srm',digest(b'old')):pass

    def test_external_file_created_during_publish_is_preserved_alongside_previous(self):
        self.put(b'previous');real_link=sync.os.link
        def race(source,dest):
            if str(source).split('/')[-1].startswith('.pyretro-stage-'):
                Path(dest).write_bytes(b'external')
            return real_link(source,dest)
        with patch.object(sync.os,'link',side_effect=race),self.assertRaises(sync.Conflict):self.put(b'incoming',digest(b'previous'))
        self.assertEqual((self.root/'Jogo.srm').read_bytes(),b'external')
        self.assertEqual(next((self.root/'.pyretro-history').rglob('*.previous')).read_bytes(),b'previous')

    def test_sdmc_filter_only_includes_game_data_and_extdata(self):
        prefix='Nintendo 3DS/'+'0'*32+'/'+'1'*32+'/'
        self.assertTrue(sync.accepted('3ds-saves',prefix+'title/00040000/00123400/data/00000001/main'))
        self.assertTrue(sync.accepted('3ds-saves',prefix+'extdata/00000000/00123400/00000001'))
        for rest in ('title/00040000/00123400/content/game.app','dbs/title.db','sysdata/movable.sed'):
            self.assertFalse(sync.accepted('3ds-saves',prefix+rest))
        self.assertFalse(sync.accepted('psp-saves','SYSTEM/ppsspp.ini'))
        self.assertTrue(sync.accepted('psp-saves','ULUS12345DATA/DATA.BIN'))


class MobileSyncHTTP(BaseAPI):
    def test_raw_transfer_manifest_download_and_compare_and_swap(self):
        _,groups=self.pedir('/api/mobile/sync/groups');tag=next(g['rootTag'] for g in groups if g['id']=='retro-saves')
        data=b'mobile save';query=urllib.parse.urlencode({'group':'retro-saves','path':'Mobile.srm','expected':'-','sha256':digest(data),'rootTag':tag})
        req=urllib.request.Request(self.url+'/api/mobile/sync/file?'+query,data=data,headers={'X-PyRetro-CSRF':self.csrf_token})
        with urllib.request.urlopen(req) as response:self.assertEqual(response.status,200)
        status,manifest=self.pedir('/api/mobile/sync/manifest?group=retro-saves');self.assertEqual(status,200)
        self.assertIn('Mobile.srm',[row['path'] for row in manifest['files']])
        get=urllib.parse.urlencode({'group':'retro-saves','path':'Mobile.srm','hash':digest(data),'rootTag':tag})
        with urllib.request.urlopen(self.url+'/api/mobile/sync/file?'+get) as response:self.assertEqual(response.read(),data)
        req=urllib.request.Request(self.url+'/api/mobile/sync/file?'+query,data=b'bad')
        with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(req)
        self.assertEqual(error.exception.code,403)
        error.exception.close()
        self.assertEqual((self.raiz/'Saves/saves/Mobile.srm').read_bytes(),data)
