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
from test_api import BaseAPI, srv


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

    def test_history_restore_keeps_selected_and_current_versions(self):
        self.put(b'first');self.put(b'second',digest(b'first'))
        versions=sync.history(self.cfg,'retro-saves')['versions'];self.assertEqual(len(versions),1)
        version=versions[0];self.assertEqual(version['current'],digest(b'second'))
        sync.restore(self.cfg,'retro-saves',version['path'],version['version'],version['current'],version['sha256'])
        self.assertEqual((self.root/'Jogo.srm').read_bytes(),b'first')
        self.assertEqual({row['sha256'] for row in sync.history(self.cfg,'retro-saves')['versions']},{digest(b'first'),digest(b'second')})

    def test_history_restore_rejects_stale_destination_source_and_invalid_versions(self):
        self.put(b'first');self.put(b'second',digest(b'first'))
        version=sync.history(self.cfg,'retro-saves')['versions'][0]
        with self.assertRaises(sync.Conflict):sync.restore(self.cfg,'retro-saves','Jogo.srm',version['version'],digest(b'old'),version['sha256'])
        for name in ('../Jogo.srm','1-bad.previous',''):
            with self.assertRaises(ValueError):sync.restore(self.cfg,'retro-saves','Jogo.srm',name,version['current'],version['sha256'])
        path=sync.history_path(self.cfg,'retro-saves','Jogo.srm',version['version']);path.write_bytes(b'altered')
        with self.assertRaises(sync.Conflict):sync.restore(self.cfg,'retro-saves','Jogo.srm',version['version'],version['current'],version['sha256'])
        self.assertEqual((self.root/'Jogo.srm').read_bytes(),b'second')

    def test_history_does_not_follow_symbolic_links(self):
        self.put(b'first');self.put(b'second',digest(b'first'))
        version=sync.history(self.cfg,'retro-saves')['versions'][0]
        path=sync.history_path(self.cfg,'retro-saves','Jogo.srm',version['version']);path.unlink();path.symlink_to(self.root/'Jogo.srm')
        with self.assertRaises(ValueError):sync.history(self.cfg,'retro-saves')


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


    def test_restore_http_requires_fresh_root_and_destination(self):
        cfg=srv.load_config();root=sync.root(cfg,'retro-saves');root.mkdir(parents=True,exist_ok=True)
        (root/'Restore.srm').write_bytes(b'first')
        sync.receive(cfg,'retro-saves','Restore.srm',digest(b'first'),digest(b'second'),io.BytesIO(b'second'),6)
        status,result=self.pedir('/api/mobile/sync/history?group=retro-saves');self.assertEqual(status,200)
        row=next(row for row in result['versions'] if row['path']=='Restore.srm')
        body={'group':'retro-saves','rootTag':result['rootTag'],'path':row['path'],'version':row['version'],'sha256':row['sha256'],'expected':row['current']}
        status,_=self.pedir('/api/mobile/sync/restore',{**body,'rootTag':'0'*64});self.assertEqual(status,409)
        (root/'Restore.srm').write_bytes(b'new external')
        status,_=self.pedir('/api/mobile/sync/restore',body);self.assertEqual(status,409)
        self.assertEqual((root/'Restore.srm').read_bytes(),b'new external')
        body['expected']=digest(b'new external')
        status,_=self.pedir('/api/mobile/sync/restore',body);self.assertEqual(status,200)
        self.assertEqual((root/'Restore.srm').read_bytes(),b'first')
