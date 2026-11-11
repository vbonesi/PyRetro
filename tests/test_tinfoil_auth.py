import json
import stat
import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from pathlib import Path

from core import tinfoil_auth as ta

CLIENTE = {"installed": {"client_id": "cid.apps.example", "client_secret": "segredo-falso",
                         "auth_uri": "https://auth.example/o", "token_uri": "https://tok.example/t"}}


class TinfoilAuthTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.cli = self.dir / "client.json"
        self.cli.write_text(json.dumps(CLIENTE))

    def tearDown(self):
        self.tmp.cleanup()

    def test_cliente_invalido(self):
        (self.dir / "x.json").write_text('{"installed": {}}')
        with self.assertRaises(ValueError):
            ta.ler_cliente(self.dir / "x.json")
        with self.assertRaises(ValueError):
            ta.ler_cliente(self.dir / "nao-existe.json")

    def test_url_de_autorizacao(self):
        url = ta.url_de_autorizacao(CLIENTE["installed"], "http://127.0.0.1:1", ta.ESCOPOS["readonly"], "st", "ch")
        self.assertTrue(url.startswith("https://auth.example/o?"))
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(q["scope"], ["https://www.googleapis.com/auth/drive.readonly"])
        self.assertEqual(q["access_type"], ["offline"])
        self.assertEqual(q["code_challenge_method"], ["S256"])
        self.assertNotIn("client_secret", q)

    def test_troca_de_codigo(self):
        vistos = {}

        def post(url, dados):
            vistos.update(url=url, dados=dados)
            return {"access_token": "a", "refresh_token": "r"}
        r = ta.trocar_codigo(CLIENTE["installed"], "COD", "http://127.0.0.1:9", "ver", post)
        self.assertEqual(vistos["url"], "https://tok.example/t")
        self.assertEqual(vistos["dados"]["grant_type"], "authorization_code")
        self.assertEqual(vistos["dados"]["code_verifier"], "ver")
        self.assertEqual(r["refresh_token"], "r")

    def test_formato_gravado_e_permissao(self):
        out = self.dir / "sd" / "tinfoil"
        ta.gravar(out, self.cli.read_text(), {"access_token": "a", "refresh_token": "r", "expires_in": 3599})
        self.assertEqual(json.loads((out / "gdrive.token").read_text()), {"access_token": "a", "refresh_token": "r"})
        self.assertEqual(json.loads((out / "credentials.json").read_text()), CLIENTE)
        for n in ("gdrive.token", "credentials.json"):
            self.assertEqual(stat.S_IMODE((out / n).stat().st_mode), 0o600)

    def test_sem_refresh_token_nao_grava(self):
        out = self.dir / "o"
        with self.assertRaises(OSError):
            ta.gravar(out, "{}", {"access_token": "a"})
        self.assertFalse(out.exists())

    def test_login_completo_simulado(self):
        def abrir(redirect):  # simula o navegador voltando ao 127.0.0.1 com o state certo
            def volta():
                st = self.estado["state"]
                urllib.request.urlopen(f"{redirect}/?code=COD&state={st}", timeout=10).read()
            threading.Thread(target=volta).start()

        # captura o state gerado interceptando secrets.token_urlsafe(24)
        self.estado = {}
        real = ta.secrets.token_urlsafe

        def spy(n=None):
            v = real(n)
            if n == 24:
                self.estado["state"] = v
            return v
        ta.secrets.token_urlsafe = spy
        try:
            out = self.dir / "saida"
            ta.login(self.cli, out, abrir=abrir, timeout=20,
                     post=lambda u, d: {"access_token": "a", "refresh_token": "r"} if d["code"] == "COD" else {})
        finally:
            ta.secrets.token_urlsafe = real
        self.assertEqual(json.loads((out / "gdrive.token").read_text())["refresh_token"], "r")

    def test_state_errado_recusa(self):
        def abrir(redirect):
            threading.Thread(target=lambda: urllib.request.urlopen(f"{redirect}/?code=C&state=outro", timeout=10).read()).start()
        with self.assertRaises(OSError):
            ta.login(self.cli, self.dir / "s", abrir=abrir, timeout=20, post=lambda u, d: {})
        self.assertFalse((self.dir / "s").exists())


if __name__ == "__main__":
    unittest.main()
