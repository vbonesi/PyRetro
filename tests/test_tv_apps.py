"""Clientes remotos: pedidos repetidos não criam players extras."""
import subprocess
import threading
import unittest
from unittest.mock import patch

from core import tv_apps


class TestRemoteLaunch(unittest.TestCase):
    def setUp(self):
        self.command = ['flatpak', 'run', 'io.github.unknownskl.greenlight']
        for target, kwargs in (
                ('entries', {'return_value': {'greenlight': {'comando': self.command}}}),
                ('subprocess.run', {}), ('subprocess.Popen', {}), ('session_env', {'return_value': {}})):
            mock = patch('core.tv_apps.' + target, **kwargs)
            setattr(self, target.split('.')[-1] + '_mock', mock.start())
            self.addCleanup(mock.stop)
        self.run_mock.return_value.stdout = ''
        self.Popen_mock.return_value.poll.return_value = None
        cleared = patch.dict(tv_apps._remote_processes, {}, clear=True)
        cleared.start(); self.addCleanup(cleared.stop)

    def test_concurrent_requests_create_only_one_player(self):
        barrier = threading.Barrier(8)
        results = []

        def open_remote():
            barrier.wait()
            results.append(tv_apps.launch({}, 'greenlight'))

        threads = [threading.Thread(target=open_remote) for _ in range(8)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=5)
        self.assertEqual(len(results), 8)
        self.assertEqual(sum(not result['already_running'] for result in results), 1)
        self.Popen_mock.assert_called_once()
        self.assertEqual(self.Popen_mock.call_args.args[0], self.command)
        self.assertNotIn('shell', self.Popen_mock.call_args.kwargs)

    def test_existing_flatpak_after_service_restart_is_preserved(self):
        self.run_mock.return_value.stdout = 'io.github.unknownskl.greenlight\n'
        self.assertTrue(tv_apps.launch({}, 'greenlight')['already_running'])
        self.Popen_mock.assert_not_called()

    def test_closed_player_can_be_opened_again(self):
        self.run_mock.return_value.stdout = 'io.github.unknownskl.greenlight.other\n'
        self.assertFalse(tv_apps.launch({}, 'greenlight')['already_running'])
        self.Popen_mock.return_value.poll.return_value = 0
        self.assertFalse(tv_apps.launch({}, 'greenlight')['already_running'])
        self.assertEqual(self.Popen_mock.call_count, 2)

    def test_failed_instance_check_does_not_launch_blindly(self):
        self.run_mock.side_effect = subprocess.TimeoutExpired('flatpak', 5)
        with self.assertRaisesRegex(ValueError, 'já está aberto'):
            tv_apps.launch({}, 'greenlight')
        self.Popen_mock.assert_not_called()


class TestAppImages(unittest.TestCase):
    def test_fritchii_executavel_vira_app_e_lichii_ausente_nao(self):
        import os, tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp, patch('core.tv_apps.shutil.which', return_value=None):
            home = Path(tmp)
            (home / 'AppImages').mkdir()
            app = home / 'AppImages/fritchii.appimage'
            app.write_text('')
            self.assertNotIn('fritchii', tv_apps.entries({}, home))  # sem permissão de execução
            os.chmod(app, 0o755)
            apps = tv_apps.entries({}, home)
            self.assertEqual(apps['fritchii']['comando'], [str(app)])
            self.assertNotIn('lichii', apps)
