"""Formatos e caminhos de saves; regras puras independentes do transporte."""
from pathlib import PurePosixPath
import re

GROUPS={'retro-saves','retro-states','retro-runtime','psp-saves','psp-states','3ds-saves'}


def accepted(group, relative):
    if group not in GROUPS or not isinstance(relative, str) or not relative or len(relative) > 1024:
        return False
    parts = relative.split('/')
    if (relative.startswith('/') or '\\' in relative or ':' in relative or '\0' in relative or
            any(p in ('', '.', '..') or p.startswith('.pyretro-') for p in parts)):
        return False
    if group == 'retro-saves':
        return PurePosixPath(relative).suffix.lower() in {'.srm','.sav','.rtc','.sra','.eep','.fla','.mcr','.mcd','.dat','.dsv','.nv','.nvm','.mem','.fs'}
    if group == 'retro-states':
        return bool(re.search(r'\.state(?:\d+|\.auto)?(?:\.png)?$', relative, re.I))
    if group == 'retro-runtime':
        return relative.lower().endswith('.lrtl')
    if group == 'psp-saves':
        return bool(re.fullmatch(r'[A-Z]{4}\d{5}[^/]*(/[^/]+)+', relative))
    if group == 'psp-states':
        return bool(re.fullmatch(r'[A-Z]{4}\d{5}[^/]*\.(ppst|jpg|png)', relative, re.I))
    return bool(re.fullmatch(r'Nintendo 3DS/[0-9a-f]{32}/[0-9a-f]{32}/(?:title/[0-9a-f]{8}/[0-9a-f]{8}/data|extdata/[0-9a-f]{8}/[0-9a-f]{8})/.+', relative, re.I))

