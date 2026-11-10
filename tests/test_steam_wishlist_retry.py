"""Wishlist da Steam: novas tentativas em 429/rede e progresso (10/11/2026)."""
import io
import json
import unittest
import urllib.error
from unittest import mock

from core import library as L


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _json(obj):
    return _Resp(json.dumps(obj).encode())


def _http(code, retry_after=None):
    headers = {"Retry-After": retry_after} if retry_after else {}
    return urllib.error.HTTPError("u", code, "x", headers, None)


class TestSteamRetry(unittest.TestCase):
    def setUp(self):
        self.esperas = []
        p = mock.patch.object(L, "_sleep", self.esperas.append)
        p.start(); self.addCleanup(p.stop)

    def test_429_tenta_de_novo_e_respeita_retry_after(self):
        respostas = [_http(429, "30"), _json({"ok": 1})]
        with mock.patch.object(L.urllib.request, "urlopen", side_effect=respostas):
            self.assertEqual(L._steam_get_json("https://x.invalid/", 5), {"ok": 1})
        self.assertEqual(self.esperas, [30])

    def test_falha_de_rede_tenta_de_novo(self):
        respostas = [urllib.error.URLError("caiu"), TimeoutError(), _json([1])]
        with mock.patch.object(L.urllib.request, "urlopen", side_effect=respostas):
            self.assertEqual(L._steam_get_json("https://x.invalid/", 5), [1])
        self.assertEqual(len(self.esperas), 2)

    def test_404_nao_repete(self):
        with mock.patch.object(L.urllib.request, "urlopen", side_effect=[_http(404)]) as u:
            with self.assertRaises(urllib.error.HTTPError):
                L._steam_get_json("https://x.invalid/", 5)
        self.assertEqual(u.call_count, 1)

    def test_desiste_depois_das_tentativas(self):
        n = len(L._STEAM_RETRY_WAITS) + 1
        with mock.patch.object(L.urllib.request, "urlopen", side_effect=[_http(429)] * n):
            with self.assertRaises(urllib.error.HTTPError):
                L._steam_get_json("https://x.invalid/", 5)

    def test_wishlist_com_429_no_meio_completa_e_avisa_progresso(self):
        def detalhe(appid, nome):
            return _json({str(appid): {"success": True, "data": {"name": nome, "type": "game", "genres": []}}})
        respostas = [
            _json({"response": {"items": [{"appid": 1}, {"appid": 2}]}}),
            detalhe(1, "Um"), _http(429), detalhe(2, "Dois"),
        ]
        progresso = []
        with mock.patch.object(L.urllib.request, "urlopen", side_effect=respostas), \
                mock.patch.object(L, "find_cover_steam_cdn", return_value=None):
            r = L.read_steam_wishlist({"steamid64": "1"}, progress=lambda f, t: progresso.append((f, t)))
        self.assertEqual([j["nome"] for j in r], ["Um", "Dois"])
        self.assertEqual(progresso, [(0, 2), (1, 2), (2, 2)])

    def test_falha_persistente_ainda_cancela(self):
        n = len(L._STEAM_RETRY_WAITS) + 1
        respostas = [_json({"response": {"items": [{"appid": 1}]}})] + [_http(503)] * n
        with mock.patch.object(L.urllib.request, "urlopen", side_effect=respostas):
            with self.assertRaisesRegex(RuntimeError, "sincronização cancelada"):
                L.read_steam_wishlist({"steamid64": "1"})


if __name__ == "__main__":
    unittest.main()
