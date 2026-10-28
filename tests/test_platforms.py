"""Manifesto único de ícones de plataforma: arquivos gerados em dia, sem alias repetido e com contraste."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_platform_icons as bpi  # noqa: E402


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


class TestPlatforms(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(bpi.MANIFEST.read_text(encoding="utf-8"))

    def test_generated_files_are_up_to_date(self):
        js, kt = bpi.render()
        self.assertEqual(bpi.JS.read_text(encoding="utf-8"), js, "rode tools/build_platform_icons.py")
        self.assertEqual(bpi.KT.read_text(encoding="utf-8"), kt, "rode tools/build_platform_icons.py")

    def test_ids_and_aliases_do_not_collide(self):
        owner = {}
        for p in self.data["platforms"]:
            for name in [p["id"], p["name"], *p["aliases"]]:
                key = "".join(c for c in name.lower() if c.isalnum())
                self.assertEqual(owner.setdefault(key, p["id"]), p["id"], f"{name} pertence a duas plataformas")

    def test_white_label_has_enough_contrast(self):
        for p in [self.data["fallback"], *self.data["platforms"]]:
            ratio = 1.05 / (luminance(p["color"]) + 0.05)
            self.assertGreaterEqual(ratio, 4.5, f'{p["id"]} {p["color"]} contraste {ratio:.2f}')
            self.assertLessEqual(len(p["short"]), 6)

    def test_every_rom_system_and_library_platform_has_an_icon(self):
        known = {a for p in self.data["platforms"] for a in p["aliases"]}
        from core import play
        for code in play.SYSTEMS:
            self.assertIn(code, known | {"NSW"}, code)
        for name in ["Nintendo Switch", "Epic Games Store", "Steam", "GOG", "Xbox One", "Xbox Series S", "Amazon Games",
                     "Android", "PlayStation 4", "Xbox 360", "Xbox", "PlayStation 3", "Sony - PlayStation", "iOS",
                     "Sony - PlayStation 2", "Sony - PSP"]:
            self.assertIn(name, known | {p["name"] for p in self.data["platforms"]}, name)


if __name__ == "__main__":
    unittest.main()
