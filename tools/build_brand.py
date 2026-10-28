#!/usr/bin/env python3
"""Gera os ativos da marca PyRetro (assets/brand/) a partir do símbolo em docs/design/.

Não instala nada: só cria arquivos para revisão. Trocar o favicon, o ícone do modo TV, o atalho do
Steam e o ícone do Android é uma etapa separada, depois da aprovação do Victor.
Requer rsvg-convert e ImageMagick (magick)."""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs/design/pyretro-logo-proposta.svg'
OUT = ROOT / 'assets/brand'
SIZES = (16, 24, 32, 48, 64, 128, 192, 256, 512)
MINT, BASE = '#81E1CA', '#11212E'
SMALL_SIZES = (16, 24)  # o play se perde abaixo de 32 px: nesses tamanhos vale a variante sem ele


TRIANGLE = '<path d="M46 33L66 43L46 53Z" fill="#11212E"/>'


def mono(svg, color):
    """Versão de uma cor só: sem fundo, e o play vira um furo de verdade no símbolo (evenodd),
    para funcionar sobre qualquer superfície."""
    text = svg.replace(f'<rect width="108" height="108" rx="25" fill="{BASE}"/>', '').replace(TRIANGLE, '')
    text = text.replace('Z" fill="#81E1CA"/>', 'ZM46 33L66 43L46 53Z" fill-rule="evenodd" fill="#81E1CA"/>')
    return text.replace(f'fill="{MINT}"', f'fill="{color}"')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'png').mkdir(exist_ok=True)
    svg = SOURCE.read_text(encoding='utf-8')
    shutil.copyfile(SOURCE, OUT / 'pyretro.svg')
    (OUT / 'pyretro-mono-escuro.svg').write_text(mono(svg, BASE), encoding='utf-8')
    (OUT / 'pyretro-mono-claro.svg').write_text(mono(svg, '#EDF4FD'), encoding='utf-8')
    small = svg.replace(TRIANGLE, '')
    (OUT / 'pyretro-pequeno.svg').write_text(small, encoding='utf-8')
    for size in SIZES:
        source = OUT / 'pyretro-pequeno.svg' if size in SMALL_SIZES else SOURCE
        subprocess.run(['rsvg-convert', '-w', str(size), '-h', str(size), str(source), '-o', str(OUT / 'png' / f'pyretro-{size}.png')], check=True)
    subprocess.run(['magick', *[str(OUT / 'png' / f'pyretro-{s}.png') for s in (16, 32, 48)], str(OUT / 'favicon.ico')], check=True)
    # folha de conferência: todos os tamanhos lado a lado, sobre fundo claro e escuro
    cells = []
    for background in ('#FFFFFF', '#0B1220'):
        row = OUT / f'.row-{background[1:]}.png'
        subprocess.run(['magick', '-background', background, '-gravity', 'center', *sum([[str(OUT / 'png' / f'pyretro-{s}.png'), '-extent', f'{s + 24}x{max(SIZES[:7]) + 24}'] for s in SIZES[:7]], []), '+append', str(row)], check=True)
        cells.append(row)
    subprocess.run(['magick', *map(str, cells), '-append', str(OUT / 'folha-de-tamanhos.png')], check=True)
    for row in cells:
        row.unlink()


if __name__ == '__main__':
    main()
