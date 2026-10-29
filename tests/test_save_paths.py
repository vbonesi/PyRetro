import unittest
from core.save_paths import accepted
from test_api import BaseAPI

class TestPaths(unittest.TestCase):
    def test_title_data_and_extdata_only(self):
        prefix='Nintendo 3DS/'+'a'*32+'/'+'b'*32+'/'
        self.assertTrue(accepted('3ds-saves',prefix+'title/00040000/00123400/data/00000001/main'))
        self.assertTrue(accepted('3ds-saves',prefix+'extdata/00000000/00123400/00000001'))
        for rest in ('title/00040000/00123400/content/game.app','../secret','nand/file'):
            self.assertFalse(accepted('3ds-saves',prefix+rest))
        self.assertTrue(accepted('psp-saves','ULUS12345DATA/DATA.BIN'))
        for path in ('SYSTEM/ppsspp.ini','../a.sav','/a.sav','a//b.sav','a/.pyretro-history/b.sav'):
            self.assertFalse(accepted('psp-saves',path))

class TestRetiredRoutes(BaseAPI):
    def test_old_read_and_write_return_gone(self):
        for path in ('groups','history','manifest','file','restore'):
            self.assertEqual(self.pedir('/api/mobile/sync/'+path)[0],410)
            self.assertEqual(self.pedir('/api/mobile/sync/'+path,{})[0],410)
