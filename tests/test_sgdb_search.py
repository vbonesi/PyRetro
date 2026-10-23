"""Busca manual de capas no SteamGridDB: grades em paralelo, na ordem da busca."""
import io
import json
import unittest
from unittest.mock import patch

from core import library as lm


class TestSearchSteamGridDB(unittest.TestCase):
    def test_parallel_grids_keep_order_limit_and_skip_failures(self):
        def fake_urlopen(request, timeout):
            url = request.full_url
            if "/search/autocomplete/" in url:
                data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 3, "name": "C"}]
            elif url.endswith("/game/2?dimensions=600x900"):
                raise OSError("tempo esgotado")
            else:
                n = url.split("/game/")[1].split("?")[0]
                data = [{"url": f"https://x/{n}-{i}.png"} for i in range(5)]
            return io.BytesIO(json.dumps({"data": data}).encode())
        with patch.object(lm.urllib.request, "urlopen", side_effect=fake_urlopen):
            out = lm.search_covers_steamgriddb("termo", "chave", por_jogo=2)
        self.assertEqual(out, [{"nome": "A", "url": "https://x/1-0.png"}, {"nome": "A", "url": "https://x/1-1.png"},
                               {"nome": "C", "url": "https://x/3-0.png"}, {"nome": "C", "url": "https://x/3-1.png"}])
