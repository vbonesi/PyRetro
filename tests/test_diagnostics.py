import json
import tempfile
import unittest
from unittest.mock import patch

from core import diagnostics
from test_api import BaseAPI


class TestDiagnostics(unittest.TestCase):
    def test_allowlist_does_not_leak_configuration_or_exception(self):
        with tempfile.TemporaryDirectory(prefix='private-user-') as root:
            cfg = {'pc': {'roms_root': root, 'saves_root': '/private/account/save',
                          'states_root': '\x00private', 'backups_root': root},
                   'token': 'SECRET_TOKEN', 'host': '192.0.2.77', 'library': ['PRIVATE_GAME']}
            report = diagnostics.report(cfg, 'PRIVATE_GAME', which=lambda _: '/private/bin/executable')
            text = json.dumps(report)
            for secret in (root, '/private', 'SECRET_TOKEN', '192.0.2.77', 'PRIVATE_GAME'):
                self.assertNotIn(secret, text)
            self.assertEqual(report['play_state'], 'unknown')
            self.assertEqual(report['checks'][0]['status'], 'present')
            self.assertEqual(report['checks'][1]['status'], 'missing')

    def test_missing_programs_have_action_and_no_process_runs(self):
        with patch('subprocess.run', side_effect=AssertionError('must not run')):
            result = diagnostics.report({}, 'idle', which=lambda _: None)
        self.assertTrue(all(c['action'] for c in result['checks']))


class TestDiagnosticRoute(BaseAPI):
    def test_report_contains_no_fixture_paths_or_inventory(self):
        status, report = self.pedir('/api/diagnostics')
        self.assertEqual(status, 200)
        self.assertEqual(report['application'], 'PyRetro')
        self.assertNotIn(str(self.raiz), json.dumps(report))
        self.assertNotIn('Chrono Trigger', json.dumps(report))
