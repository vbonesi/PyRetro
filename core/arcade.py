"""Dependências de ROMs de fliperama (FinalBurn Neo): clones precisam do zip "pai" e, às vezes, de BIOS.

O DAT do FBNeo (em `BIOS/RetroArch/fbneo/`) diz, para cada jogo, `romof="pai"`: o zip do pai (ou de uma
BIOS como `neogeo`) precisa estar junto. O zip do próprio jogo não basta. Aqui só se calcula a cadeia; quem
baixa e quem remove usa o resultado (core/heavy_roms.py e gui/server.py).
"""
import re
from pathlib import Path

DAT_GLOBS = ('*Arcade only*.dat', '*Neogeo only*.dat')
GAME = re.compile(r'<game\s+([^>]*)>')
ATTR = re.compile(r'(\w+)="([^"]*)"')


def dat_dir(cfg):
    return Path(cfg['pc']['roms_root']).expanduser().parent / 'BIOS' / 'RetroArch' / 'fbneo'


def load_dat(folder):
    """{nome do jogo: romof} dos DATs de fliperama da pasta (vazio se não houver DAT)."""
    parents = {}
    folder = Path(folder)
    for pattern in DAT_GLOBS:
        for path in sorted(folder.glob(pattern)):
            try:
                text = path.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            for match in GAME.finditer(text):
                attrs = dict(ATTR.findall(match.group(1)))
                if attrs.get('name'):
                    parents[attrs['name']] = attrs.get('romof') or ''
    return parents


def load_titles(folder):
    """{nome do jogo: título completo} (`<description>` do DAT do FBNeo), vazio se não houver DAT.
    Ex.: kof97 -> "The King of Fighters '97 (NGM-2320)"."""
    import xml.etree.ElementTree as ET
    titles = {}
    for pattern in DAT_GLOBS:
        for path in sorted(Path(folder).glob(pattern)):
            try:
                root = ET.parse(path).getroot()
            except (OSError, ET.ParseError):
                continue
            for game in root.iter('game'):
                name, description = game.get('name'), (game.findtext('description') or '').strip()
                if name and description:
                    titles[name] = description
    return titles


def chain(name, parents):
    """Conjuntos necessários além do próprio: pai, avô, BIOS… em ordem. Ciclo ou profundidade absurda para."""
    out, current = [], parents.get(name, '')
    while current and current not in out and current != name and len(out) < 8:
        out.append(current)
        current = parents.get(current, '')
    return out


def required_zips(zip_name, parents):
    """Nomes de arquivo (`pai.zip`...) que acompanham `zip_name`."""
    return [f'{n}.zip' for n in chain(Path(zip_name).stem, parents)]


def dependents(zip_name, local_zips, parents):
    """Dos zips presentes no PC, quais dependem de `zip_name` (para não apagar um pai ainda usado)."""
    stem = Path(zip_name).stem
    return sorted(z for z in local_zips if z != zip_name and stem in chain(Path(z).stem, parents))
