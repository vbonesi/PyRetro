#!/usr/bin/env python3
"""Gera a partir de assets/platforms/manifest.json os dados de ícones de plataforma usados pela
web/modo TV (gui/static/platforms.js) e pelo Android (PlatformData.kt). Rode depois de editar o
manifesto; tests/test_platforms.py confere que os arquivos gerados estão em dia."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'assets/platforms/manifest.json'
JS = ROOT / 'gui/static/platforms.js'
KT = ROOT / 'android/app/src/main/java/com/pyretro/app/PlatformData.kt'
HEADER = 'Gerado por tools/build_platform_icons.py a partir de assets/platforms/manifest.json; não edite.'


def render():
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    items = [data['fallback'], *data['platforms']]
    js = f'// {HEADER}\nconst PLATAFORMAS = {json.dumps(data, ensure_ascii=False, indent=1)};\n'
    rows = ',\n'.join(
        f'    PlatformInfo({json.dumps(p["id"])},{json.dumps(p["name"], ensure_ascii=False)},{json.dumps(p["short"], ensure_ascii=False)},'
        f'0xFF{p["color"][1:].upper()}.toInt(),listOf({",".join(json.dumps(a, ensure_ascii=False) for a in p.get("aliases", []))}))' for p in items)
    kt = (f'package com.pyretro.app\n\n// {HEADER}\n'
          'data class PlatformInfo(val id:String,val name:String,val short:String,val color:Int,val aliases:List<String>)\n\n'
          f'object PlatformData {{\n    val all=listOf(\n{rows}\n    )\n}}\n')
    return js, kt


def main():
    js, kt = render()
    JS.write_text(js, encoding='utf-8'); KT.write_text(kt, encoding='utf-8')


if __name__ == '__main__':
    main()
