"""Testes de core/capas_emuladores.py: symlinks de capa por destino, sem tocar
no que já existe, e leitura do serial de uma ISO de PS2 montada na mão."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import capas_emuladores as ce


def _iso_ps2(path: Path, boot: str) -> None:
    """ISO 9660 mínima: PVD no setor 16, raiz no setor 20, SYSTEM.CNF no setor 21."""
    cnf = f"BOOT2 = cdrom0:\\{boot};1\nVER = 1.00\n".encode()
    nome = b"SYSTEM.CNF;1"
    rec = bytearray(33 + len(nome))
    rec[0] = len(rec)
    rec[2:6] = struct.pack("<I", 21)
    rec[10:14] = struct.pack("<I", len(cnf))
    rec[32] = len(nome)
    rec[33:] = nome
    data = bytearray(22 * 2048)
    pvd = bytearray(2048)
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[158:162] = struct.pack("<I", 20)
    pvd[166:170] = struct.pack("<I", 2048)
    data[16 * 2048:17 * 2048] = pvd
    data[20 * 2048:20 * 2048 + len(rec)] = rec
    data[21 * 2048:21 * 2048 + len(cnf)] = cnf
    path.write_bytes(bytes(data))


class CapasEmuladoresTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.d = Path(self._tmp.name)
        self.cfg = {
            "pc": {"roms_root": str(self.d / "ROMs"), "capas_root": str(self.d / "Capas")},
            "systems": {},
            "heavy_systems": {"PS2": {"exts": ["iso"], "capas": "Sony - PlayStation 2"},
                              "NGC": {"exts": ["iso"], "capas": "Nintendo - GameCube"}},
        }
        (self.d / "ROMs/PS2").mkdir(parents=True)
        self.capas = self.d / "Capas/Sony - PlayStation 2/Named_Boxarts"
        self.capas.mkdir(parents=True)
        (self.capas / "Jogo A.png").write_bytes(b"png")

    def test_serial_ps2_le_o_system_cnf(self):
        iso = self.d / "x.iso"
        _iso_ps2(iso, "SLUS_210.65")
        self.assertEqual(ce.serial_ps2(iso), "SLUS-21065")
        self.assertIsNone(ce.serial_ps2(self.d / "naoexiste.iso"))
        (self.d / "lixo.iso").write_bytes(b"\0" * 40000)
        self.assertIsNone(ce.serial_ps2(self.d / "lixo.iso"))

    def test_link_por_rom_e_por_serial_guardando_capa_baixada(self):
        _iso_ps2(self.d / "ROMs/PS2/Jogo A.iso", "SLUS_210.65")
        (self.d / "ROMs/PS2/Sem Capa.iso").write_bytes(b"x")
        pasta = self.d / "covers"
        pasta.mkdir()
        (pasta / "SLUS-21065.jpg").write_bytes(b"baixada")
        r = ce._por_rom(self.cfg, "PS2", pasta, "PCSX2", True, ce.serial_ps2)
        self.assertTrue((pasta / "Jogo A.png").is_symlink())
        self.assertTrue((pasta / "SLUS-21065.png").is_symlink())
        self.assertEqual((pasta / "_baixadas_pelo_emulador/SLUS-21065.jpg").read_bytes(), b"baixada")
        self.assertFalse((pasta / "SLUS-21065.jpg").exists())
        self.assertIn("sem capa", [x["estado"] for x in r])
        # segunda rodada não muda nada
        r2 = ce._por_rom(self.cfg, "PS2", pasta, "PCSX2", True, ce.serial_ps2)
        self.assertNotIn("criado", [x["estado"] for x in r2])

    def test_simulacao_nao_cria_nada(self):
        (self.d / "ROMs/PS2/Jogo A.iso").write_bytes(b"x")
        pasta = self.d / "covers"
        r = ce._por_rom(self.cfg, "PS2", pasta, "DuckStation", False)
        self.assertEqual(r[0]["estado"], "a criar")
        self.assertFalse(pasta.exists())

    def test_nao_sobrescreve_arquivo_real_de_outra_origem(self):
        pasta = self.d / "covers"
        pasta.mkdir()
        (pasta / "Jogo A.png").write_bytes(b"do usuario")
        (self.d / "ROMs/PS2/Jogo A.iso").write_bytes(b"x")
        r = ce._por_rom(self.cfg, "PS2", pasta, "DuckStation", True)
        self.assertEqual(r[0]["estado"], "pulado")
        self.assertEqual((pasta / "Jogo A.png").read_bytes(), b"do usuario")

    def test_dolphin_so_png_com_id_do_cabecalho(self):
        (self.d / "ROMs/NGC").mkdir()
        cap = self.d / "Capas/Nintendo - GameCube/Named_Boxarts"
        cap.mkdir(parents=True)
        (cap / "Metroid.png").write_bytes(b"png")
        (self.d / "ROMs/NGC/Metroid.iso").write_bytes(b"G2MP01" + b"\0" * 100)
        pasta = self.d / "gc"
        r = ce.plano_dolphin(self.cfg, True, pasta)
        self.assertEqual(r[0]["estado"], "criado")
        self.assertTrue((pasta / "G2MP01.png").is_symlink())


if __name__ == "__main__":
    unittest.main()
