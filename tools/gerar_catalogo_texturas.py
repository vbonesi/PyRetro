#!/usr/bin/env python3
"""Gera core/texturas_catalogo.json a partir da listagem pública do item
"pcsx2-hd-texture-packs" do Internet Archive (nome, tamanho e SHA-1 de cada
pacote vêm do próprio archive.org; nada é baixado aqui). Só entram arquivos
com serial no nome, no formato "Título (REGIÃO) [SLUS-21065] ... .rar/.zip/.7z".
Os pacotes de outros consoles são acrescentados à mão no JSON (campo "sistema")."""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# (item do archive.org, sistema). Só entram itens com download liberado: os pacotes
# de Dolphin do item "nintendo-gamecube-roms" respondem 401 (bloqueados), os de 3DS
# e PS1 não têm fonte verificável (pesquisa de 16/10/2026).
ITENS = [("pcsx2-hd-texture-packs", "PS2"), ("ppsspp-hd-texture-packs", "PSP")]
SAIDA = Path(__file__).resolve().parent.parent / "core" / "texturas_catalogo.json"
_SERIAL = re.compile(r"\[([A-Z]{4}-?\d{5})\]")


def main() -> int:
    manual = []
    if SAIDA.is_file():
        manual = [e for e in json.loads(SAIDA.read_text())["pacotes"] if e.get("origem") != "archive.org"]
    pacotes = []
    for item, sistema in ITENS:
        with urllib.request.urlopen(f"https://archive.org/metadata/{item}", timeout=60) as r:
            meta = json.load(r)
        for f in meta["files"]:
            nome = f["name"]
            m = _SERIAL.search(nome)
            if not m or not nome.lower().endswith((".rar", ".zip", ".7z")):
                continue
            titulo = re.sub(r"\s*\[.*$", "", nome).strip()
            pacotes.append({
                "id": f"{sistema.lower()}-{m.group(1).lower()}",
                "sistema": sistema,
                "id_jogo": m.group(1),
                "nome": titulo,
                "arquivo": nome,
                "url": f"https://archive.org/download/{item}/" + urllib.parse.quote(nome),
                "tamanho": int(f["size"]),
                "sha1": f["sha1"],
                "origem": "archive.org",
            })
    # Serial repetido (edições "Definitive", títulos alternativos): o id passa a
    # carregar o nome do arquivo, senão dois pacotes disputariam o mesmo id.
    from collections import Counter
    repetidos = {k for k, v in Counter(p["id"] for p in pacotes).items() if v > 1}
    for p in pacotes:
        if p["id"] in repetidos:
            sufixo = re.sub(r"[^a-z0-9]+", "-", Path(p["arquivo"]).stem.lower()).strip("-")
            p["id"] = f"{p['id']}-{sufixo}"
    pacotes.sort(key=lambda p: p["nome"].lower())
    SAIDA.write_text(json.dumps({"pacotes": pacotes + manual}, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(pacotes)} pacotes gravados em {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
