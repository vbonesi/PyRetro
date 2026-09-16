"""Regressões de concorrência nos arquivos compartilhados da GUI/CLI."""
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "gui"))
import server as srv
from core import library as library_mod


class TestJobsDaBiblioteca(unittest.TestCase):
    def test_dois_adds_concorrentes_nao_perdem_o_primeiro(self):
        """Reproduz o lost update de 12/09 de forma determinística."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            library_path = root / "library.json"
            library_mod.save_library(library_path, {"games": []})
            cfg = {"pc": {"library_root": str(root)}}
            primeiro_no_save = threading.Event()
            liberar_primeiro = threading.Event()
            original_save = library_mod.save_library
            chamadas = {"n": 0}
            chamadas_lock = threading.Lock()

            def save_lento(path, library):
                with chamadas_lock:
                    chamadas["n"] += 1
                    primeira = chamadas["n"] == 1
                if primeira:
                    primeiro_no_save.set()
                    self.assertTrue(liberar_primeiro.wait(5), "teste não liberou o primeiro job")
                original_save(path, library)

            emit = lambda _event: None
            with mock.patch.object(srv, "load_config", return_value=cfg), \
                 mock.patch.object(library_mod, "save_library", side_effect=save_lento):
                t1 = threading.Thread(
                    target=srv.run_library_add_job,
                    args=(emit, "Jogo A", "PC", "manual", True))
                t1.start()
                self.assertTrue(primeiro_no_save.wait(5), "primeiro job não chegou ao save")

                t2 = threading.Thread(
                    target=srv.run_library_add_job,
                    args=(emit, "Jogo B", "PC", "manual", True))
                t2.start()
                time.sleep(0.1)
                self.assertTrue(t2.is_alive(), "segundo job não esperou o lock")
                liberar_primeiro.set()
                t1.join(5)
                t2.join(5)

            self.assertFalse(t1.is_alive() or t2.is_alive(), "job ficou preso")
            nomes = {g["nome"] for g in json.loads(library_path.read_text())["games"]}
            self.assertEqual(nomes, {"Jogo A", "Jogo B"})


class TestRegistryAtomico(unittest.TestCase):
    def test_save_registry_troca_o_arquivo_inteiro(self):
        with tempfile.TemporaryDirectory() as d:
            original = srv.REGISTRY_PATH
            try:
                srv.REGISTRY_PATH = Path(d) / "cache" / "covers_registry.json"
                srv.save_registry({"SFC": {"Jogo": {"status": "manual"}}})
                self.assertEqual(json.loads(srv.REGISTRY_PATH.read_text())["SFC"]["Jogo"]["status"],
                                 "manual")
                self.assertFalse(srv.REGISTRY_PATH.with_name("covers_registry.json.tmp").exists())
            finally:
                srv.REGISTRY_PATH = original


if __name__ == "__main__":
    unittest.main()
