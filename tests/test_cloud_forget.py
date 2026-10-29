import tempfile
import unittest
import json
from pathlib import Path
from core.cloud import MemoryStorage
from core.cloud_saves import CloudSaves,Conflict
from test_api import BaseAPI
from unittest.mock import patch
import server

class TestForget(unittest.TestCase):
    def test_shared_kotlin_python_tombstone_fixture(self):
        data=json.loads((Path(__file__).resolve().parents[1]/'android/app/src/test/resources/save-tombstone.json').read_text())
        self.store.put('saves/devices/pc.json',json.dumps(data['pc']).encode(),overwrite=True)
        self.store.put('saves/devices/phone.json',json.dumps(data['phone']).encode(),overwrite=True)
        item=self.b.plan()[0];self.assertEqual(item['action'],'forget');self.assertEqual(item['deletedHeads'],[data['marker']])
        self.b.apply();self.assertEqual(self.b.plan(),[])
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.pc=root/'pc';self.phone=root/'phone';self.pc.mkdir();self.phone.mkdir();self.store=MemoryStorage()
        self.a=CloudSaves(self.store,'pc',self.pc,now=lambda:1000);self.b=CloudSaves(self.store,'phone',self.phone,now=lambda:1)
        (self.pc/'Game.srm').write_bytes(b'original');self.a.apply();self.b.apply()
    def forget(self):
        item=self.a.plan(include_same=True)[0];return self.a.forget(item['path'],item['local'],item['heads'])
    def test_explicit_deletion_is_not_restored_and_history_and_blobs_remain(self):
        self.assertTrue(self.forget()['ok']);self.assertFalse((self.pc/'Game.srm').exists())
        self.assertEqual(self.b.plan()[0]['action'],'forget');self.b.apply()
        self.assertFalse((self.phone/'Game.srm').exists());self.assertEqual(self.a.plan(),[]);self.assertEqual(self.b.plan(),[])
        self.assertEqual(next((self.phone/'.pyretro-history').rglob('*.previous')).read_bytes(),b'original')
        self.assertEqual(len(self.store.list('saves/blobs')),1)
        (self.pc/'Game.srm').write_bytes(b'restored');self.assertTrue(self.a.apply()[0]['ok']);self.b.apply()
        self.assertEqual((self.phone/'Game.srm').read_bytes(),b'restored')
    def test_offline_edit_is_a_conflict_and_stale_confirmation_is_refused(self):
        item=self.a.plan(True)[0];(self.pc/'Game.srm').write_bytes(b'new')
        with self.assertRaises(Conflict):self.a.forget(item['path'],item['local'],item['heads'])
        self.assertEqual((self.pc/'Game.srm').read_bytes(),b'new')
        (self.pc/'Game.srm').write_bytes(b'original');self.forget();(self.phone/'Game.srm').write_bytes(b'changed offline')
        self.assertEqual(self.b.plan()[0]['action'],'conflict');self.b.apply();self.assertTrue((self.phone/'Game.srm').exists())
        self.b.resolve('Game.srm','local');self.a.apply();self.assertEqual((self.pc/'Game.srm').read_bytes(),b'changed offline')

class TestForgetHTTP(BaseAPI):
    def test_exact_confirmation_is_required_before_mutating_a_save(self):
        cfg=server.load_config();cfg['cloud']={'remote':'memory','device':'pc'};store=MemoryStorage()
        target=Path(cfg['pc']['saves_root'])/'Synthetic.srm';target.write_bytes(b'fixture')
        with patch.object(server,'load_config',return_value=cfg),patch.object(server.cloud_sync_mod,'storage',return_value=store):
            status,data=self.pedir('/api/cloud/saves/status?all=1');self.assertEqual(status,200)
            item=next(i for i in data['items'] if i['path']=='saves/Synthetic.srm')
            body={'path':item['path'],'group':item['group'],'expectedLocal':item['local'],'expectedHeads':list(item['heads']),'confirm':'sim'}
            self.assertEqual(self.pedir('/api/cloud/saves/forget',body)[0],400);self.assertTrue(target.exists())
            body['confirm']='Esquecer este save: '+body['path'];self.assertEqual(self.pedir('/api/cloud/saves/forget',body)[0],200)
            self.assertFalse(target.exists())
