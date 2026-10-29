import unittest.mock
import tempfile
import tomllib
import unittest
from pathlib import Path

from core import firstrun

EXAMPLE = Path(__file__).resolve().parent.parent / 'config.example.toml'
ALL = {app for _n, app, _r in firstrun.PROGRAMS}


class FirstRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / 'home'
        self.home.mkdir()
        self.config = Path(self.tmp.name) / 'config.toml'
        # Acervo dentro do diretório temporário: o modelo usa ~/Games/PyRetro, então simula o HOME.
        self.patch = unittest.mock.patch.object(firstrun, 'STORAGE_SECTION',
            firstrun.STORAGE_SECTION.replace('~/Games/PyRetro', str(self.home / 'Games/PyRetro')))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def status(self, **kw):
        kw.setdefault('flatpaks', ALL); kw.setdefault('remotes', set()); kw.setdefault('which', lambda _n: '/bin/x')
        return firstrun.status(self.config, EXAMPLE, home=self.home, **kw)

    def test_sem_configuracao_o_status_pede_o_assistente_e_nada_e_criado(self):
        result = self.status()
        steps = {s['id']: s for s in result['steps']}
        self.assertFalse(result['ready'])
        self.assertEqual(steps['config']['state'], 'missing')
        self.assertTrue(steps['config']['fixable'] and steps['folders']['fixable'])
        self.assertFalse(self.config.exists())
        self.assertFalse((self.home / 'Games').exists())

    def test_apply_cria_configuracao_valida_privada_e_pastas_vazias(self):
        done = firstrun.apply(self.config, EXAMPLE)
        self.assertIn('config', done['created'])
        cfg = tomllib.loads(self.config.read_text(encoding='utf-8'))
        self.assertEqual(cfg['storage']['games_root'], str(self.home / 'Games/PyRetro'))
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)
        self.assertTrue((self.home / 'Games/PyRetro/ROMs').is_dir())
        self.assertTrue((self.home / 'Games/PyRetro/Saves/saves').is_dir())
        self.assertTrue(self.status()['ready'])

    def test_apply_repetido_nao_sobrescreve_nem_apaga_nada(self):
        firstrun.apply(self.config, EXAMPLE)
        self.config.write_text(self.config.read_text(encoding='utf-8') + '\n# minha anotação\n', encoding='utf-8')
        rom = self.home / 'Games/PyRetro/ROMs/GBA/jogo.gba'
        rom.parent.mkdir(parents=True); rom.write_bytes(b'rom')
        before = self.config.read_bytes()
        self.assertEqual(firstrun.apply(self.config, EXAMPLE), {'created': []})
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(rom.read_bytes(), b'rom')

    def test_emuladores_ausentes_sao_nomeados_e_o_pyretro_nao_instala(self):
        firstrun.apply(self.config, EXAMPLE)
        step = {s['id']: s for s in self.status(flatpaks=ALL - {'net.pcsx2.PCSX2', 'com.valvesoftware.Steam'})['steps']}['programs']
        self.assertEqual(step['state'], 'missing')
        self.assertIn('PCSX2', step['detail']); self.assertIn('Opcionais ausentes: Steam', step['detail'])
        self.assertIn('setup', step['detail']); self.assertFalse(step['fixable'])

    def test_so_loja_ausente_e_opcional(self):
        firstrun.apply(self.config, EXAMPLE)
        (self.home / 'AppImages').mkdir(); (self.home / 'AppImages/DuckStation-x64.AppImage').write_bytes(b'')
        step = {s['id']: s for s in self.status(flatpaks=ALL - {'org.freedesktop.fake', 'com.heroicgameslauncher.hgl'})['steps']}['programs']
        self.assertEqual(step['state'], 'optional')

    def test_nuvem_so_cobra_quando_configurada(self):
        firstrun.apply(self.config, EXAMPLE)
        cloud = {s['id']: s for s in self.status()['steps']}['cloud']
        self.assertEqual(cloud['state'], 'optional')
        self.config.write_text(self.config.read_text(encoding='utf-8') + '\n[cloud]\nremote = "drive:PyRetro"\n', encoding='utf-8')
        self.assertEqual({s['id']: s for s in self.status()['steps']}['cloud']['state'], 'missing')
        self.assertEqual({s['id']: s for s in self.status(remotes={'drive'})['steps']}['cloud']['state'], 'ok')


if __name__ == '__main__':
    unittest.main()
