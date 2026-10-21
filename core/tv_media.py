"""Logos e vídeos escolhidos pelo usuário, separados do acervo e sem buscas aproximadas."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from core import library

MAX_BYTES = 64 * 1024 * 1024


def folder(root, key):
    path = Path(root) / hashlib.sha256(key.encode()).hexdigest()
    if path.is_symlink():
        raise ValueError('pasta de mídia inválida')
    return path


def describe(root, key):
    path = folder(root, key)
    result = {}
    for kind, names in (('logo', ('logo.png',)), ('video', ('video.mp4', 'video.webm'))):
        for name in names:
            asset = path / name
            if asset.is_file() and not asset.is_symlink():
                result[kind] = f'/tv-media/{path.name}/{name}?v={asset.stat().st_mtime_ns}'
                break
    return result


def resolve(root, digest, name):
    if not re.fullmatch(r'[0-9a-f]{64}', digest) or name not in ('logo.png', 'video.mp4', 'video.webm'):
        raise ValueError('mídia inválida')
    path = Path(root) / digest / name
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('mídia inválida')
    return path


def install(root, key, kind, data):
    if not data or len(data) > MAX_BYTES:
        raise ValueError('arquivo vazio ou maior que 64 MB')
    dest = folder(root, key); dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest, prefix='.import-') as tmp:
        temporary = Path(tmp)
        if kind == 'logo':
            if not (data.startswith(b'\x89PNG\r\n\x1a\n') or data.startswith(b'\xff\xd8\xff') or data[:4] == b'RIFF' and data[8:12] == b'WEBP'):
                raise ValueError('use uma imagem PNG, JPEG ou WebP')
            result = temporary / 'logo.png'
            if not library.gravar_png(data, result):
                raise ValueError('imagem inválida')
            try:
                image = subprocess.run(['identify','-format','%w %h',str(result)], capture_output=True,text=True,timeout=10,check=True)
                width,height = map(int,image.stdout.split())
                if not 0 < width <= 8192 or not 0 < height <= 8192: raise ValueError('imagem grande demais')
            except (OSError,subprocess.SubprocessError,ValueError):
                raise ValueError('imagem inválida ou maior que 8192 pixels') from None
            result.replace(dest / 'logo.png')
        elif kind == 'video':
            suffix = '.mp4' if data[4:8] == b'ftyp' else '.webm' if data.startswith(b'\x1aE\xdf\xa3') else None
            if not suffix:
                raise ValueError('use vídeo MP4 ou WebM')
            result = temporary / ('video' + suffix); result.write_bytes(data)
            try:
                probe = subprocess.run(['ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-show_entries',
                                        'stream=codec_type,width,height', '-of', 'json', str(result)],
                                       capture_output=True, text=True, timeout=15, check=True)
                streams = json.loads(probe.stdout).get('streams', [])
                if not any(s.get('codec_type') == 'video' and 0 < s.get('width', 0) <= 7680 and 0 < s.get('height', 0) <= 4320 for s in streams):
                    raise ValueError('vídeo sem imagem válida')
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
                raise ValueError('não foi possível validar o vídeo; confira o ffprobe') from None
            result.replace(dest / result.name)
            # Só remove a variante anterior desta prévia, nunca ROMs/capas do acervo.
            for other in (dest / 'video.mp4', dest / 'video.webm'):
                if other.name != result.name:
                    other.unlink(missing_ok=True)
        else:
            raise ValueError('tipo de mídia inválido')
    return describe(root, key)
