#!/usr/bin/env python3
"""Gera core/texturas_fontes.json a partir da planilha comunitária "Texture Packs
Archive" (.xlsx, mantida por Sad Origami; links para gbatemp.net,
forums.ppsspp.org etc.). É só um índice de onde achar o pacote: nada é baixado
aqui nem pelo PyRetro, o usuário abre a página, baixa e instala pela importação
local da aba Texturas.

Ficam de fora: pacotes pagos (Patreon/Ko-fi ou restrição "Paywall"), espelhos
TeraBox (muitos são cópias de pacotes pagos) e sistemas sem suporte a texturas
no PyRetro (N64, Dreamcast, Switch, Vita).

Uso: python3 -I tools/gerar_fontes_texturas.py "~/Downloads/Texture Packs Archive.xlsx"
Lê o .xlsx com a biblioteca padrão (zip + XML), sem openpyxl."""
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

SAIDA = Path(__file__).resolve().parent.parent / "core" / "texturas_fontes.json"
ABAS = {"PSOne": "PS1", "PS2": "PS2", "PSP": "PSP", "GC": "GC", "Wii": "WII", "3DS": "3DS"}
PAGOS = ("patreon.com", "ko-fi.com", "buymeacoffee.com")
RESTRICAO_PAGA = ("paywall", "join patreon", "buymeacoffee")
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
_R_ID = "{%s}id" % _NS["r"]
_SERIAIS = {
    "PS1": re.compile(r"\b([A-Z]{4})-?(\d{5})\b"), "PS2": re.compile(r"\b([A-Z]{4})-?(\d{5})\b"),
    "PSP": re.compile(r"\b([A-Z]{4})-?(\d{5})\b"),
}


def _textos(el) -> str:
    return "".join(t.text or "" for t in el.iter("{%s}t" % _NS["m"]))


def ler_abas(xlsx: Path) -> dict:
    """{aba: [ {coluna: (texto, link)} por linha ]}, com o link do hyperlink da célula."""
    z = zipfile.ZipFile(xlsx)
    ss = [_textos(si) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS)]
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    abas = {}
    for sh in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", _NS):
        caminho = "xl/" + rels[sh.get(_R_ID)].lstrip("/").removeprefix("xl/")
        x = ET.fromstring(z.read(caminho))
        links = {}
        try:
            alvos = {r.get("Id"): r.get("Target") for r in ET.fromstring(
                z.read(caminho.replace("worksheets/", "worksheets/_rels/") + ".rels"))}
            for h in x.iter("{%s}hyperlink" % _NS["m"]):
                links[h.get("ref")] = alvos.get(h.get(_R_ID))
        except KeyError:
            pass
        linhas = []
        for row in x.iter("{%s}row" % _NS["m"]):
            celulas = {}
            for c in row.findall("m:c", _NS):
                v = c.find("m:v", _NS)
                if v is not None:
                    texto = ss[int(v.text)] if c.get("t") == "s" else v.text
                elif c.find("m:is", _NS) is not None:
                    texto = _textos(c.find("m:is", _NS))
                else:
                    texto = ""
                ref = c.get("r")
                link = links.get(ref)
                f = c.find("m:f", _NS)
                if not link and f is not None and f.text:
                    m = re.search(r'HYPERLINK\("([^"]+)"', f.text)
                    link = m.group(1) if m else None
                celulas[re.sub(r"\d", "", ref)] = ((texto or "").strip(), link)
            linhas.append(celulas)
        abas[sh.get("name")] = linhas
    return abas


def _limpo(v: str) -> str:
    return "" if v in ("N/A", "None", "-", "✖") else v


def fontes(abas: dict) -> list[dict]:
    out, vistos = [], set()
    for aba, sistema in ABAS.items():
        linhas = abas.get(aba) or []
        if not linhas:
            continue
        col = {texto.strip(): c for c, (texto, _) in linhas[0].items() if texto}
        pega = lambda cel, nome: cel.get(col.get(nome, "?"), ("", None))
        for cel in linhas[1:]:
            nome = pega(cel, "Game Title")[0].strip()
            url = pega(cel, "Download")[1] or ""
            restricao = _limpo(pega(cel, "Restriction")[0])
            if not nome or not url.startswith("https://"):
                continue
            dominio = urlparse(url).netloc.lower().removeprefix("www.")
            if dominio.endswith(PAGOS) or restricao.lower() in RESTRICAO_PAGA:
                continue
            serial = ""
            if sistema in _SERIAIS:
                m = _SERIAIS[sistema].search(pega(cel, "Serial Number")[0].upper())
                serial = f"{m.group(1)}-{m.group(2)}" if m and sistema != "PSP" else (m.group(1) + m.group(2) if m else "")
            chave = (sistema, nome.lower(), url)
            if chave in vistos:
                continue
            vistos.add(chave)
            out.append({
                "sistema": sistema, "nome": nome, "url": url, "site": dominio, "serial": serial,
                "restricao": restricao, "regiao": _limpo(pega(cel, "Region")[0]),
                "tamanho": _limpo(pega(cel, "Size")[0]), "autor": _limpo(pega(cel, "Pack Author")[0]),
                "tipo": _limpo(pega(cel, "Type")[0]), "status": _limpo(pega(cel, "Status")[0]),
            })
    out.sort(key=lambda f: (f["sistema"], f["nome"].lower()))
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    lista = fontes(ler_abas(Path(sys.argv[1]).expanduser()))
    SAIDA.write_text(json.dumps({"origem": "Texture Packs Archive (planilha comunitária)",
                                 "fontes": lista}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    por = {}
    for f in lista:
        por[f["sistema"]] = por.get(f["sistema"], 0) + 1
    print(f"{len(lista)} fontes gravadas em {SAIDA}: {por}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
