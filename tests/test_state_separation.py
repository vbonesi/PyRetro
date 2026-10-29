import tempfile
import unittest
from pathlib import Path

from core import cloud, cloud_sync


class TestStateSeparation(unittest.TestCase):
    def test_states_are_private_but_savefiles_remain_shared(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=cloud.MemoryStorage();pc=Path(tmp)/'pc';phone=Path(tmp)/'phone'
            for root in (pc,phone):(root/'states/N64').mkdir(parents=True)
            (pc/'states/N64/A.state.auto').write_bytes(b'pc-core')
            (phone/'states/N64/A.state.auto').write_bytes(b'phone-core')
            (pc/'saves').mkdir();(pc/'saves/A.srm').write_bytes(b'save')
            def cfg(root,device):return {'pc':{'saves_root':str(root/'saves')},'cloud':{'remote':'memory','device':device}}
            cloud_sync.sync(cfg(pc,'pc'),store)
            cloud_sync.sync(cfg(phone,'celular'),store)
            self.assertEqual((phone/'states/N64/A.state.auto').read_bytes(),b'phone-core')
            self.assertEqual((phone/'saves/A.srm').read_bytes(),b'save')
            self.assertIn('states/pc/devices/pc.json',store.files)
            self.assertIn('states/celular/devices/celular.json',store.files)
            self.assertNotIn('states/N64/A.state.auto',str(store.files['saves/devices/pc.json']))


if __name__=='__main__':unittest.main()
