"""Remoção local/Drive: prévia, proteção, revalidação por token e resultado por item."""
import unittest

from core import removal

LOCAL = {"remove": ["PS/Jogo.cue", "PS/Jogo.bin"], "preserve": ["PS/Faixa compartilhada.bin"], "complete": True}
DRIVE = [{"path": "Jogos/ROMs/PS/Jogo.cue", "id": "a1", "size": 10}, {"path": "Jogos/ROMs/PS/Jogo.bin", "id": "b2", "size": 900}]


def make(scope, **kw):
    args = dict(local_plan=LOCAL, drive_list=DRIVE, can_write_drive=True)
    args.update(kw)
    return removal.plan(scope, "PS", "Jogo.cue", **args)


class TestRemoval(unittest.TestCase):
    def test_local_only_touches_pc_and_preserves_shared_tracks(self):
        plan = make("local")
        self.assertEqual((plan["local"], plan["drive"]), (["PS/Jogo.bin", "PS/Jogo.cue"], []))
        self.assertEqual(plan["preserved"], ["PS/Faixa compartilhada.bin"])
        self.assertTrue(any("outro conjunto" in w for w in plan["warnings"]))
        self.assertEqual(plan["blocked"], [])
        self.assertIn("saves e estados", plan["keeps"])

    def test_drive_scope_needs_write_permission_and_a_listing(self):
        self.assertTrue(any("só para leitura" in b for b in make("drive", can_write_drive=False)["blocked"]))
        self.assertTrue(any("consultar o Drive" in b for b in make("drive", drive_list=None)["blocked"]))
        plan = make("drive")
        self.assertEqual((len(plan["drive"]), plan["bytes_drive"], plan["local"]), (2, 910, []))

    def test_both_lists_each_side_and_last_copy_warnings(self):
        plan = make("both")
        self.assertEqual((len(plan["local"]), len(plan["drive"])), (2, 2))
        self.assertTrue(any("última cópia" in w for w in make("local", drive_list=[])["warnings"]))
        self.assertTrue(any("última cópia" in w for w in make("drive", local_plan=None)["warnings"]))

    def test_started_pinned_or_running_games_are_blocked(self):
        plan = make("local", protected=["jogo iniciado e não finalizado", "fixado neste dispositivo"], running=True)
        self.assertEqual(len(plan["blocked"]), 3)
        with self.assertRaises(removal.Blocked):
            removal.apply(plan, plan["token"], plan["confirm_text"], trash=lambda p: None, drive_trash=lambda i: None)

    def test_uncertain_local_plan_blocks(self):
        plan = make("local", local_plan={**LOCAL, "complete": False})
        self.assertTrue(any("exclusivos" in b for b in plan["blocked"]))

    def test_apply_requires_same_token_and_exact_confirmation(self):
        plan = make("both")
        done = []
        kw = dict(trash=done.append, drive_trash=lambda i: done.append(i["path"]))
        with self.assertRaisesRegex(removal.Blocked, "mudou"):
            removal.apply(plan, "outro-token", plan["confirm_text"], **kw)
        with self.assertRaisesRegex(removal.Blocked, "confirmação"):
            removal.apply(plan, plan["token"], "sim", **kw)
        self.assertEqual(done, [])
        outcome = removal.apply(plan, plan["token"], plan["confirm_text"], **kw)
        self.assertTrue(outcome["ok"])
        self.assertEqual(len(done), 4)

    def test_token_changes_when_the_remote_listing_changes(self):
        a = make("both"); b = make("both", drive_list=DRIVE + [{"path": "Jogos/ROMs/PS/extra.bin", "id": "c3", "size": 1}])
        self.assertNotEqual(a["token"], b["token"])
        self.assertEqual(a["token"], make("both")["token"])

    def test_partial_failure_is_reported_per_item_and_does_not_stop_the_batch(self):
        plan = make("both")
        def drive_trash(item):
            if item["id"] == "a1":
                raise OSError("sem rede")
        outcome = removal.apply(plan, plan["token"], plan["confirm_text"], trash=lambda p: None, drive_trash=drive_trash)
        self.assertFalse(outcome["ok"])
        failed = [r for r in outcome["results"] if not r["ok"]]
        self.assertEqual((len(outcome["results"]), len(failed), failed[0]["error"]), (4, 1, "sem rede"))

    def test_unknown_scope_is_rejected(self):
        with self.assertRaises(ValueError):
            make("tudo")


class TestRemovalServer(unittest.TestCase):
    """Rotas de remoção: prévia pelo acervo de mentira e aplicação com lixeira simulada."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); ps = self.root / "ROMs" / "PS"; ps.mkdir(parents=True)
        (ps / "Disco.cue").write_text('FILE "Disco.bin" BINARY\n TRACK 01 MODE2/2352')
        (ps / "Disco.bin").write_bytes(b"x" * 20)
        (ps / "Outro.cue").write_text('FILE "Outro.bin" BINARY\n TRACK 01 MODE2/2352')
        (ps / "Outro.bin").write_bytes(b"y" * 20)
        (self.root / "Biblioteca").mkdir()
        self.cfg = {"pc": {"roms_root": str(self.root / "ROMs"), "library_root": str(self.root / "Biblioteca"),
                           "backups_root": str(self.root / "Backups")},
                    "systems": {}, "heavy_systems": {"PS": {"exts": ["cue", "chd"]}},
                    "rclone": {"remote": "drive", "drive_roms_root": "Jogos/ROMs"}}

    def test_local_plan_then_apply_sends_only_this_game_to_the_trash(self):
        import sys
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "gui"))
        import server as srv
        from unittest import mock
        plan = srv._removal_plan(self.cfg, "local", "PS", "Disco.cue")
        self.assertEqual(sorted(plan["local"]), ["Disco.bin", "Disco.cue"])
        self.assertEqual(plan["blocked"], [])
        trashed = []
        with mock.patch.object(srv, "_organize_trash", return_value=lambda p: trashed.append(p.name)):
            outcome = srv._removal_apply(self.cfg, {"scope": "local", "code": "PS", "entry": "Disco.cue",
                                                    "token": plan["token"], "confirm": plan["confirm_text"]})
        self.assertTrue(outcome["ok"])
        self.assertEqual(sorted(trashed), ["Disco.bin", "Disco.cue"])

    def test_catalog_style_stem_resolves_to_the_descriptor_file(self):
        import sys
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "gui"))
        import server as srv
        self.assertEqual(srv._removal_entry(self.cfg, "PS", "Disco"), "Disco.cue")
        self.assertEqual(srv._removal_entry(self.cfg, "PS", "Disco.cue"), "Disco.cue")
        self.assertEqual(srv._removal_entry(self.cfg, "PS", "Nada"), "Nada")
        plan = srv._removal_plan(self.cfg, "local", "PS", "Disco")
        self.assertEqual(sorted(plan["local"]), ["Disco.bin", "Disco.cue"])

    def test_drive_scope_is_blocked_while_rclone_is_read_only_and_wrong_token_is_refused(self):
        import sys
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "gui"))
        import server as srv
        from unittest import mock
        plan = srv._removal_plan(self.cfg, "both", "PS", "Disco.cue")
        self.assertTrue(any("só para leitura" in b for b in plan["blocked"]))
        local = srv._removal_plan(self.cfg, "local", "PS", "Disco.cue")
        with mock.patch.object(srv, "_organize_trash", return_value=lambda p: self.fail("não devia apagar")):
            with self.assertRaises(removal.Blocked):
                srv._removal_apply(self.cfg, {"scope": "local", "code": "PS", "entry": "Disco.cue",
                                              "token": "errado", "confirm": local["confirm_text"]})


if __name__ == "__main__":
    unittest.main()
