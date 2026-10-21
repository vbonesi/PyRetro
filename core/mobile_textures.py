"""Arquivos enviados e pacotes portáteis de texturas; nunca escreve no acervo."""
from pathlib import Path
import re
import secrets
import tempfile
import zipfile
from core import texturas

MAX_BYTES = 12 * 1024**3
ROOT = Path(__file__).resolve().parent.parent / 'cache/mobile-textures'


def upload(stream, length, filename):
    suffix = Path(filename).suffix.lower() if isinstance(filename,str) else ''
    if suffix not in texturas.EXTENSOES or not 0 < length <= MAX_BYTES:
        raise ValueError('use ZIP/7z/RAR de até 12 GB')
    ROOT.mkdir(parents=True,exist_ok=True)
    token = secrets.token_hex(16); path = ROOT/(token+suffix)
    try:
        with path.open('xb') as output:
            remaining=length
            while remaining:
                data=stream.read(min(1024*1024,remaining))
                if not data:raise ValueError('envio interrompido')
                output.write(data);remaining-=len(data)
        return token+suffix
    except Exception:
        path.unlink(missing_ok=True);raise


def uploaded(token):
    if not isinstance(token,str) or not re.fullmatch(r'[0-9a-f]{32}\.(zip|7z|rar)',token):
        raise ValueError('envio inválido')
    path=ROOT/token
    if path.is_symlink() or not path.is_file():raise ValueError('arquivo enviado não encontrado')
    return path


def bundle(token):
    if not re.fullmatch(r'[0-9a-f]{32}',token or ''):raise ValueError('pacote inválido')
    path=ROOT/(token+'.zip')
    if path.is_symlink() or not path.is_file():raise ValueError('pacote não encontrado')
    return path


def prepare(body, emit):
    if body.get('id'):
        package=texturas.achar_pacote(body['id'])
        if package['sistema']!='PSP':raise ValueError('catálogo portátil disponível para PSP')
        archive=texturas.baixar(package,emit)
        system,game_id=package['sistema'],package['id_jogo']
    else:
        system=body.get('sistema');game_id=str(body.get('id_jogo','')).upper()
        if system not in ('PSP','3DS') or not texturas._CEL_ID[system].fullmatch(game_id):
            raise ValueError('informe PSP e ID do disco, ou 3DS e title ID de 16 hexadecimais')
        archive=uploaded(body.get('upload'))
    ROOT.mkdir(parents=True,exist_ok=True);token=secrets.token_hex(16);output=ROOT/(token+'.zip')
    try:
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='.prepare-') as temp:
            extracted=Path(temp);emit({'type':'progress','status':'extraindo no notebook'})
            texturas.validar_arquivo(archive)
            texturas.extrair(archive,extracted)
            root=texturas._achar_raiz(extracted,game_id)
            paths=[];total=0
            for path in sorted(root.rglob('*')):
                if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):raise ValueError('atalho inseguro no pacote')
                if path.is_file() and path.suffix.lower() in ('.png','.dds','.ktx','.ktx2','.ini','.txt'):
                    total+=path.stat().st_size;paths.append(path)
                    if total>MAX_BYTES or len(paths)>50000:raise ValueError('pacote extraído grande demais')
            if not paths:raise ValueError('nenhuma textura/configuração encontrada')
            emit({'type':'progress','status':'preparando download portátil'})
            with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as target:
                for path in paths:target.write(path,path.relative_to(root).as_posix())
        emit({'type':'done','result':{'url':'/api/mobile/textures/bundle/'+token,'sistema':system,'id_jogo':game_id,'files':len(paths)}})
    except Exception:
        output.unlink(missing_ok=True);raise
