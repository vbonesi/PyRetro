import unittest
from core import cloud,cloud_covers as covers

class TestCovers(unittest.TestCase):
    def test_demand_upload_content_addressing_and_integrity(self):
        store=cloud.MemoryStorage();self.assertEqual(store.list('capas'),[])
        first=covers.publish(store,'água',b'first');covers.publish(store,'água',b'first')
        self.assertEqual(len(store.list('capas')),2);self.assertEqual(covers.get(store,'água'),b'first')
        covers.publish(store,'água',b'second');self.assertEqual(covers.get(store,'água'),b'second')
        self.assertTrue(store.exists('capas/blobs/'+first['sha256']))
        store.put('capas/blobs/'+covers.publish(store,'other',b'bytes')['sha256'],b'wrong',overwrite=True)
        with self.assertRaises(ValueError):covers.get(store,'other')
        with self.assertRaises(cloud.NotFound):covers.get(store,'not-displayed')
