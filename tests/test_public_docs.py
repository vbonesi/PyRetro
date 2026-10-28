"""Guarda de privacidade: o repositório é público, então nenhum arquivo versionado pode
trazer o endereço real do tailnet (AUD28-01). Só os exemplos neutros são aceitos."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEUTROS = {"notebook.tailnet.ts.net", "maquina.tailnet.ts.net"}


class TestPublicDocs(unittest.TestCase):
    def test_no_real_tailnet_hostname_is_tracked(self):
        found = subprocess.run(["git", "grep", "-h", "-o", "-E", r"[a-z0-9-]+\.[a-z0-9-]+\.ts\.net"],
                               cwd=ROOT, capture_output=True, text=True).stdout.split()
        self.assertEqual(sorted(set(found) - NEUTROS), [], "endereço real do tailnet em arquivo versionado")


if __name__ == "__main__":
    unittest.main()
