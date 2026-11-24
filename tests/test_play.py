"""Abertura segura de ROMs; nenhum teste executa emuladores reais."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, Mock
from core import play


class TestPlay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cfg = {'pc': {'roms_root': str(self.root)},
                    'systems': {'SFC': {'exts': ['sfc', 'smc']}},
                    'heavy_systems': {'PS': {'exts': ['cue', 'chd', 'bin', 'm3u', 'ccd']},
                                      'PS2': {'exts': ['iso']}, '3DS': {'exts': ['3ds']}}}
        self.launcher = self.root / 'launcher'
        self.launcher.write_text('#!/bin/sh\nexit 0\n'); self.launcher.chmod(0o755)
        self.patch = patch.object(play, 'LAUNCHER', self.launcher)
        self.patch.start(); self.addCleanup(self.patch.stop)
        env = patch.object(play, 'session_env', return_value={'WAYLAND_DISPLAY': 'wayland-1'})
        env.start(); self.addCleanup(env.stop)

    def file(self, name, data=b'rom'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_before_and_after_hooks_run_around_the_game_and_never_break_it(self):
        rom = self.file('PS2/Jogo.iso')
        calls = []
        process = Mock(); process.poll.return_value = None
        def boom(*args):
            calls.append('antes'); raise RuntimeError('nuvem fora do ar')
        with patch.object(subprocess, 'Popen', return_value=process), patch.object(play, 'restore_tv_focus'):
            sessions = play.Sessions(before=boom, after=lambda: calls.append('depois'))
            self.assertEqual(sessions.start(self.cfg, 'PS2', rom.name)['status'], 'running')
            self.assertEqual(calls, ['antes'])  # o jogo abriu mesmo com a falha
            process.poll.return_value = 0
            self.assertEqual(sessions.status()['status'], 'finished')
        import time
        for _ in range(50):
            if 'depois' in calls: break
            time.sleep(.02)
        self.assertEqual(calls, ['antes', 'depois'])

    def test_exact_candidates_and_argv_without_shell(self):
        rom = self.file('PS2/Jogo; $(false).iso')
        options = play.candidates(self.cfg, 'PS2', rom.name)
        self.assertEqual(options, [{'name': rom.name, 'error': None}])
        self.assertEqual(play.prepare(self.cfg, 'PS2', rom.name),
                         [str(self.launcher), 'ps2', str(rom)])
        process = Mock(); process.poll.return_value = None
        with patch.object(subprocess, 'Popen', return_value=process) as launch:
            sessions = play.Sessions()
            self.assertEqual(sessions.start(self.cfg, 'PS2', rom.name)['status'], 'running')
            self.assertNotIn('shell', launch.call_args.kwargs)
            # O servidor sobe antes da sessão gráfica: a tela vem do systemd a cada jogo.
            self.assertEqual(launch.call_args.kwargs['env'], {'WAYLAND_DISPLAY': 'wayland-1'})
            with self.assertRaisesRegex(ValueError, 'já existe'):
                sessions.start(self.cfg, 'PS2', rom.name)
            process.poll.return_value = 0
            self.assertEqual(sessions.status()['status'], 'finished')
            self.assertEqual(sessions.status()['returncode'], 0)

    def test_failure_to_start_does_not_leave_session_running(self):
        self.file('PS2/Jogo.iso')
        sessions = play.Sessions()
        with patch.object(subprocess, 'Popen', side_effect=OSError('sem sessão gráfica')):
            with self.assertRaises(OSError): sessions.start(self.cfg, 'PS2', 'Jogo.iso')
        self.assertEqual(sessions.status()['status'], 'idle')

    def test_alternative_requires_known_core_for_system_and_validated_rom(self):
        self.file('MD/Jogo.md')
        self.cfg['systems'] = {'MD': {'exts': ['md']}}
        core = self.file('cores/picodrive_libretro.so')
        with patch.object(play, 'CORE_ROOT', core.parent):
            self.assertEqual(play.prepare(self.cfg, 'MD', 'Jogo.md', 'picodrive')[-2:],
                             [str(core), str(self.root / 'MD/Jogo.md')])
            with self.assertRaises(ValueError): play.prepare(self.cfg, 'MD', 'Jogo.md', '../evil')
            core.unlink()
            with self.assertRaises(ValueError): play.prepare(self.cfg, 'MD', 'Jogo.md', 'picodrive')

    def test_ps1_opens_only_through_the_launcher_system_psx(self):
        """PS1 = SwanStation no RetroArch (o lançador decide); sem alternativa avulsa desde 08/11/2026."""
        self.file('PS/Jogo.chd')
        self.assertEqual(play.prepare(self.cfg, 'PS', 'Jogo.chd'),
                         [str(self.launcher), 'psx', str(self.root / 'PS/Jogo.chd')])
        self.assertEqual([g['id'] for g in play.emulators('PS')], [''])
        for other in ('duckstation', 'swanstation', 'psx-duckstation'):
            with self.assertRaises(ValueError): play.prepare(self.cfg, 'PS', 'Jogo.chd', other)

    def test_emulator_failure_is_visible(self):
        self.file('PS2/Jogo.iso')
        process = Mock(); process.poll.return_value = 2
        with patch.object(subprocess, 'Popen', return_value=process):
            sessions = play.Sessions(); sessions.start(self.cfg, 'PS2', 'Jogo.iso')
            self.assertEqual(sessions.status()['status'], 'error')

    def test_missing_cue_track_and_empty_tracks_are_refused(self):
        self.file('PS/Jogo.cue', b'FILE "Jogo.bin" BINARY\n TRACK 01 MODE2/2352\n')
        self.assertIn('ausente', play.candidates(self.cfg, 'PS', 'Jogo')[0]['error'])
        self.file('PS/Jogo.bin', b'')
        with self.assertRaises(ValueError): play.prepare(self.cfg, 'PS', 'Jogo.cue')
        self.file('PS/Jogo.bin')
        self.assertEqual(play.candidates(self.cfg, 'PS', 'Jogo'), [{'name': 'Jogo.cue', 'error': None}])

    def test_multi_disc_requires_explicit_selection(self):
        self.file('PS/Conjunto/Disco 1.chd'); self.file('PS/Conjunto/Disco 2.chd')
        self.assertEqual(len(play.candidates(self.cfg, 'PS', 'Conjunto')), 2)
        with self.assertRaises(ValueError): play.prepare(self.cfg, 'PS', 'Conjunto')

    def test_path_traversal_and_external_symlinks_are_refused(self):
        self.file('PS2/Jogo.iso')
        outside = self.file('fora.iso')
        (self.root / 'PS2' / 'atalho.iso').symlink_to(outside)
        for name in ('../fora.iso', '/tmp/fora.iso', 'atalho.iso', 'sub/../../fora.iso', 'sub\\fora.iso'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                play.prepare(self.cfg, 'PS2', name)
        (self.root / 'SFC').symlink_to(self.root.parent)
        with self.assertRaises(ValueError): play.candidates(self.cfg, 'SFC', 'fora')

    def test_descriptors_cannot_escape_or_recurse_forever(self):
        self.file('PS/Jogo.cue', b'FILE "../fora.bin" BINARY\n')
        self.file('fora.bin')
        with self.assertRaises(ValueError): play.prepare(self.cfg, 'PS', 'Jogo.cue')
        self.file('PS/Loop.m3u', b'Loop.m3u\n')
        with self.assertRaisesRegex(ValueError, 'circular'): play.prepare(self.cfg, 'PS', 'Loop.m3u')
        self.file('PS/Vazio.m3u', b'# nenhuma faixa\n')
        with self.assertRaises(ValueError): play.prepare(self.cfg, 'PS', 'Vazio.m3u')

    def test_unknown_system_extension_and_launcher_are_refused(self):
        # Switch não tem emulador no lançador (3DS/NDS ganharam em 22/10).
        self.file('NSW/Jogo.nsp'); self.file('PS2/Jogo.exe')
        with self.assertRaises(ValueError): play.prepare(self.cfg, 'NSW', 'Jogo.nsp')
        with self.assertRaises(ValueError): play.prepare(self.cfg, 'PS2', 'Jogo.exe')
        self.file('PS/Jogo.ccd')
        with self.assertRaisesRegex(ValueError, 'CCD'): play.prepare(self.cfg, 'PS', 'Jogo.ccd')
        self.file('PS2/Jogo.iso'); self.launcher.unlink()
        with self.assertRaises(ValueError): play.prepare(self.cfg, 'PS2', 'Jogo.iso')


class TestSwitch2(unittest.TestCase):
    """NSW2 (24/11/2026): sistema pesado padrão, aberto pelo `bonisarch-emulator switch2` (Lichii)."""

    def test_config_sem_secao_ganha_o_nsw2_e_a_do_arquivo_vence(self):
        from core import heavy_roms
        cfg = heavy_roms.with_defaults({'heavy_systems': {'PS2': {'exts': ['iso']}}})
        self.assertEqual(cfg['heavy_systems']['NSW2']['exts'], ['nup', 'nsp', 'xci'])
        self.assertFalse(cfg['heavy_systems']['NSW2']['celular'])
        proprio = heavy_roms.with_defaults({'heavy_systems': {'NSW2': {'exts': ['nup']}}})
        self.assertEqual(proprio['heavy_systems']['NSW2'], {'exts': ['nup']})

    def test_pasta_do_jogo_abre_o_nup_e_ignora_o_resto(self):
        from core import heavy_roms
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            jogo = root / 'NSW2' / 'Zelda'
            (jogo / 'SHADERS').mkdir(parents=True)
            (jogo / 'Zelda [0400486024DEC000][v131072].nup').write_bytes(b'x')
            (jogo / 'SHADERS' / 'vulkan.bin').write_bytes(b'x')
            (jogo / 'README PT-BR.txt').write_text('x')
            cfg = heavy_roms.with_defaults({'pc': {'roms_root': tmp}})
            opcoes = play.candidates(cfg, 'NSW2', 'Zelda')
            self.assertEqual([o['name'] for o in opcoes], ['Zelda/Zelda [0400486024DEC000][v131072].nup'])
            launcher = root / 'launcher'; launcher.write_text('#!/bin/sh\n'); launcher.chmod(0o755)
            with patch.object(play, 'LAUNCHER', launcher):
                cmd = play.prepare(cfg, 'NSW2', opcoes[0]['name'])
            self.assertEqual(cmd[1], 'switch2')

    def test_cadastro_de_switch_2_casa_com_a_pasta_do_nsw2(self):
        from core import library
        idx = library.index_by_rom_name({'games': [
            {'id': 'a', 'nome': 'Zelda', 'plataforma': 'Nintendo Switch 2', 'nomes_alt': []},
            {'id': 'b', 'nome': 'Zelda', 'plataforma': 'Nintendo Switch', 'nomes_alt': []}]})
        self.assertEqual(library.find_for_rom(idx, 'Zelda', 'NSW2')['id'], 'a')
