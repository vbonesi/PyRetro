"""Dependências de fliperama: cadeia de romof, download do pai e proteção na remoção."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core import arcade, heavy_roms as heavy

DAT = """<datafile>
<game name="pai" romof="neogeo"><rom name="a"/></game>
<game name="filho" cloneof="pai" romof="pai"><rom name="b"/></game>
<game name="neto" cloneof="pai" romof="filho"><rom name="c"/></game>
<game name="sozinho"><rom name="d"/></game>
<game name="ciclo1" romof="ciclo2"/><game name="ciclo2" romof="ciclo1"/>
</datafile>"""


class TestArcade(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        folder = self.base / "BIOS/RetroArch/fbneo"; folder.mkdir(parents=True)
        (folder / "FinalBurn Neo (ClrMame Pro XML, Arcade only).dat").write_text(DAT)
        self.cfg = {"pc": {"roms_root": str(self.base / "ROMs")}, "systems": {"ARCADE": {"exts": ["zip"]}},
                    "rclone": {"staging_dir": str(self.base / "staging")}}

    def test_chain_stops_at_cycles_and_unknown_sets(self):
        parents = arcade.load_dat(arcade.dat_dir(self.cfg))
        self.assertEqual(arcade.chain("neto", parents), ["filho", "pai", "neogeo"])
        self.assertEqual(arcade.chain("sozinho", parents), [])
        self.assertEqual(sorted(arcade.chain("ciclo1", parents)), ["ciclo2"])
        self.assertEqual(arcade.required_zips("filho.zip", parents), ["pai.zip", "neogeo.zip"])
        self.assertEqual(arcade.load_dat(self.base / "nao-existe"), {})

    def test_dependents_tell_which_local_zips_still_need_a_parent(self):
        parents = arcade.load_dat(arcade.dat_dir(self.cfg))
        self.assertEqual(arcade.dependents("pai.zip", ["pai.zip", "filho.zip", "neto.zip", "sozinho.zip"], parents), ["filho.zip", "neto.zip"])
        self.assertEqual(arcade.dependents("sozinho.zip", ["sozinho.zip", "filho.zip"], parents), [])

    def test_downloading_a_clone_also_downloads_missing_parents_but_ignores_bios(self):
        calls = []
        def rclone(args, **kwargs):
            calls.append(args)
            if args[1] == "lsjson":
                return SimpleNamespace(returncode=0, stdout=json.dumps({"IsDir": False}), stderr="")
            name = args[2].rsplit("/", 1)[-1]
            if name == "neogeo.zip":
                return SimpleNamespace(returncode=1, stdout="", stderr="not found")  # BIOS não está na pasta de ROMs
            dest = Path(args[3]); dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(name.encode())
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with patch.object(heavy.subprocess, "run", side_effect=rclone):
            ok, _ = heavy.download_from_drive("ARCADE", "neto.zip", self.base / "ROMs", self.cfg)
        self.assertTrue(ok)
        got = sorted(p.name for p in (self.base / "ROMs/ARCADE").glob("*.zip"))
        self.assertEqual(got, ["filho.zip", "neto.zip", "pai.zip"])


if __name__ == "__main__":
    unittest.main()
