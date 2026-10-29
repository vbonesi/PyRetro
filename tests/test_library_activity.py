import tempfile
import unittest
from pathlib import Path
from core import library, library_activity as activity


class TestActivity(unittest.TestCase):
    def test_new_sessions_are_immutable_and_union_does_not_repeat_local_time(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'library.json'
            library.save_library(path,{'games':[{'id':'a','tempo':12}]},hooks=False)
            cfg={'pc':{'library_root':directory}}
            activity.update(cfg,'a',favorite=True,event='pc-event',seconds=60)
            self.assertFalse(activity.update(cfg,'a',event='pc-event',seconds=60))
            with self.assertRaises(ValueError):activity.update(cfg,'a',event='pc-event',seconds=120)
            activity.update(cfg,'a',event='phone-event',seconds=120)
            game=library.load_library(path)['games'][0]
            self.assertEqual(game['tempo'],12)
            self.assertTrue(game['favorite'])
            local={'seconds':60,'sessions':1,'automaticSeconds':60,'manualSeconds':0,'_events':['pc-event']}
            self.assertEqual(activity.public_time(game,local)['seconds'],180)
            self.assertEqual(activity.public_time(game,local)['sessions'],2)
            self.assertFalse(activity.update(cfg,'missing',favorite=True))
