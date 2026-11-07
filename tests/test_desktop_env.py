import subprocess
import unittest
from types import SimpleNamespace

from core.desktop_env import session_env


class SessionEnvTest(unittest.TestCase):
    def test_takes_the_current_display_from_the_user_manager(self):
        # O servidor sobe antes do Plasma: sem a tela da sessão o RetroArch fechava em 2 s.
        out = ('WAYLAND_DISPLAY=wayland-1\nDISPLAY=:1\nXDG_SESSION_TYPE=wayland\n'
               'PATH=/outro\nLS_COLORS=$\'x=y\'\n')
        calls = []

        def run(cmd, **kw):
            calls.append(cmd)
            return SimpleNamespace(stdout=out)
        env = session_env({'PATH': '/usr/bin', 'HOME': '/home/u'}, run=run)
        self.assertEqual(calls, [['systemctl', '--user', 'show-environment']])
        self.assertEqual(env['WAYLAND_DISPLAY'], 'wayland-1')
        self.assertEqual(env['DISPLAY'], ':1')
        self.assertEqual(env['PATH'], '/usr/bin')  # só as variáveis da sessão gráfica mudam
        self.assertNotIn('LS_COLORS', env)

    def test_failure_keeps_the_process_environment(self):
        def run(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, 5)
        self.assertEqual(session_env({'A': '1'}, run=run), {'A': '1'})


if __name__ == '__main__':
    unittest.main()
