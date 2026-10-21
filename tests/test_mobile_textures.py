"""Texturas portáteis e upload com arquivos sintéticos, sem download externo."""
import io
import json
from pathlib import Path
import tempfile
import shutil
import subprocess
import unittest
import urllib.request
import zipfile
from unittest.mock import patch
from core import mobile_textures as mt, texturas
from test_api import BaseAPI


def archive(entries):
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w') as target:
        for name,data in entries.items():target.writestr(name,data)
    return output.getvalue()


class TestMobileTextures(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.patch=patch.object(mt,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)

    def test_uploaded_local_package_preserves_structure_and_only_exports_textures(self):
        data=archive({'ULUS10000/sub/a.png':b'png','ULUS10000/textures.ini':b'[options]','ULUS10000/game.iso':b'rom'})
        token=mt.upload(io.BytesIO(data),len(data),'arquivo.zip');events=[]
        mt.prepare({'upload':token,'sistema':'PSP','id_jogo':'ULUS10000'},events.append)
        result=events[-1]['result'];bundle=mt.bundle(result['url'].split('/')[-1])
        with zipfile.ZipFile(bundle) as output:
            self.assertEqual(set(output.namelist()),{'sub/a.png','textures.ini'})
            self.assertEqual(output.read('sub/a.png'),b'png')
        self.assertTrue(mt.uploaded(token).is_file(),'upload precisa servir também à interface PC')

    def test_invalid_ids_paths_truncated_upload_and_archive_traversal(self):
        for token in ('../outside.zip','a'*32+'.txt',None):
            with self.assertRaises(ValueError):mt.uploaded(token)
        with self.assertRaises(ValueError):mt.upload(io.BytesIO(b'x'),2,'a.zip')
        self.assertEqual(list(self.root.iterdir()),[])
        data=archive({'../outside.png':b'x'});token=mt.upload(io.BytesIO(data),len(data),'a.zip')
        with self.assertRaises(texturas.TexturaErro):mt.prepare({'upload':token,'sistema':'3DS','id_jogo':'0004000000000001'},lambda _:None)
        self.assertFalse((self.root.parent/'outside.png').exists())
        with self.assertRaises(ValueError):mt.prepare({'upload':token,'sistema':'PSP','id_jogo':'../bad'},lambda _:None)
        with patch.object(mt,'MAX_BYTES',1),self.assertRaises(ValueError):mt.upload(io.BytesIO(data),len(data),'a.zip')

    def test_archive_symlink_is_rejected_before_extraction(self):
        file=self.root/'link.zip'
        with zipfile.ZipFile(file,'w') as target:
            link=zipfile.ZipInfo('link');link.create_system=3;link.external_attr=0o120777<<16;target.writestr(link,'../outside')
        with self.assertRaises(texturas.TexturaErro):texturas.extrair(file,self.root/'out')
        self.assertFalse((self.root/'out').exists())

    @unittest.skipUnless(shutil.which('7z'),'7z necessário para conferir formatos 7z/RAR')
    def test_real_7z_listing_is_validated_before_extraction(self):
        (self.root/'a.png').write_bytes(b'texture')
        subprocess.run(['7z','a',str(self.root/'pack.7z'),'a.png'],cwd=self.root,check=True,capture_output=True)
        texturas.extrair(self.root/'pack.7z',self.root/'out')
        self.assertEqual((self.root/'out/a.png').read_bytes(),b'texture')

    @unittest.skipUnless(shutil.which('7z'),'7z necessário para conferir links em 7z')
    def test_real_7z_unix_symlink_is_rejected_before_extraction(self):
        (self.root/'link').symlink_to('../outside')
        subprocess.run(['7z','a','-snl',str(self.root/'link.7z'),'link'],cwd=self.root,check=True,capture_output=True)
        with self.assertRaises(texturas.TexturaErro):texturas.extrair(self.root/'link.7z',self.root/'out')
        self.assertFalse((self.root/'out').exists())


class TestMobileTextureHTTP(BaseAPI):
    def setUp(self):
        self.patch=patch.object(mt,'ROOT',self.raiz/'portable');self.patch.start();self.addCleanup(self.patch.stop)

    def test_raw_upload_then_prepare_and_fetch_bundle(self):
        data=archive({'0004000000000001/a.png':b'texture'})
        req=urllib.request.Request(self.url+'/api/texturas/upload?filename=teste.zip',data=data,headers={'X-PyRetro-CSRF':self.csrf_token})
        with urllib.request.urlopen(req,timeout=10) as response:token=json.load(response)['upload']
        status,response=self.pedir('/api/mobile/textures/prepare',{'upload':token,'sistema':'3DS','id_jogo':'0004000000000001'})
        self.assertEqual(status,200)
        events=[]
        with urllib.request.urlopen(self.url+'/api/fetch/stream?job='+response['job'],timeout=20) as stream:
            for line in stream:
                if line.startswith(b'data:'):events.append(json.loads(line[5:]))
        done=next(event['result'] for event in events if event.get('type')=='done')
        with urllib.request.urlopen(self.url+done['url'],timeout=10) as response:
            self.assertEqual(response.headers['Content-Type'],'application/zip')
            with zipfile.ZipFile(io.BytesIO(response.read())) as result:self.assertEqual(result.read('a.png'),b'texture')
