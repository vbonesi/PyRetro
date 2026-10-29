import tempfile
import unittest
import json
from pathlib import Path
from core import cloud,cloud_catalog
class TestCloudCatalog(unittest.TestCase):
    def test_only_cached_dependencies_are_published_without_rom_or_bios(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);folder=root/'BIOS/RetroArch/fbneo';folder.mkdir(parents=True)
            (folder/'Arcade only.dat').write_text('<game name="clone" romof="parent"><game name="parent"><game name="../invalid">')
            store=cloud.MemoryStorage();cloud_catalog.publish_arcade({'pc':{'roms_root':str(root/'ROMs')}},store)
            self.assertEqual(json.loads(store.get('catalog/arcade.json'))['parents'],{'clone':'parent','parent':''})
            self.assertEqual(len(store.files),1)
    def test_arcade_names_come_from_dat_descriptions(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);folder=root/'BIOS/RetroArch/fbneo';folder.mkdir(parents=True)
            (folder/'Arcade only.dat').write_text('<datafile><game name="kof97"><description>The King of Fighters &apos;97</description></game></datafile>')
            store=cloud.MemoryStorage();cloud_catalog.publish_arcade({'pc':{'roms_root':str(root/'ROMs')}},store)
            self.assertEqual(json.loads(store.get('catalog/arcade.json'))['names'],{'kof97':"The King of Fighters '97"})
