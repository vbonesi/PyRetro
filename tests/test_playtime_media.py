"""Tempo/mídia com acervo e arquivos sintéticos; nenhum emulador real."""
import json
import struct
import zlib
from pathlib import Path
import subprocess
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import Mock, patch

from core import play, playtime, recent, tv_media, library
from test_api import BaseAPI
import server as srv

def png_chunk(kind, data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))

PNG = b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+png_chunk(b'IDAT',zlib.compress(b'\0\x80\xe0\xc0\xff'))+png_chunk(b'IEND',b'')


class TestPlaytime(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'time.json'

    def test_concurrent_sessions_and_duplicate_retry(self):
        threads = [threading.Thread(target=playtime.record, args=(self.path,'pc:a',60), kwargs={'event':str(i)}) for i in range(12)]
        for t in threads: t.start()
        for t in threads: t.join()
        playtime.record(self.path,'pc:a',60,event='2')
        data = playtime.public(playtime.load(self.path)['pc:a'])
        self.assertEqual(data, {'seconds':720,'sessions':12,'manualSeconds':720,'automaticSeconds':0})
        playtime.record(self.path,'pc:a',30,source='emulator')
        self.assertEqual(playtime.load(self.path)['pc:a']['automaticSeconds'],30)

    def test_corrupt_ledger_and_invalid_duration_are_preserved(self):
        self.path.write_text('{"games":[]}'); before=self.path.read_bytes()
        for seconds in (0, -1, True, float('nan'), float('inf'), 366*86400, '30', 60):
            with self.assertRaises(ValueError): playtime.record(self.path,'pc:a',seconds)
            self.assertEqual(self.path.read_bytes(),before)

    def test_old_offline_event_is_not_counted_again_after_many_sessions(self):
        for event in range(105):playtime.record(self.path,'pc:a',1,event=str(event))
        playtime.record(self.path,'pc:a',1,event='0')
        self.assertEqual(playtime.load(self.path)['pc:a']['seconds'],105)

    def test_process_completion_records_once_without_http_poll(self):
        process=Mock();process.poll.return_value=0;record=Mock()
        session=play.Sessions(record=record)
        session.process=process;session.started=100;session.state={'status':'running','session':1}
        with patch.object(play.time,'monotonic',return_value=160), patch.object(play.time,'sleep'), patch.object(play,'restore_tv_focus') as focus:
            session._watch(process)
            session.status();session.status()
        record.assert_called_once();self.assertEqual(record.call_args.args[1],60)
        focus.assert_called_once()

    def test_record_error_does_not_leave_process_running(self):
        session=play.Sessions(record=Mock(side_effect=OSError('disco indisponível')))
        session.process=Mock();session.process.poll.return_value=0;session.started=0
        with patch.object(play,'restore_tv_focus'):
            self.assertEqual(session.status()['status'],'finished')
            self.assertIn('disco indisponível',session.status()['timeError'])


class TestMedia(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    @unittest.skipUnless(shutil.which('identify'),'ImageMagick necessário para validar logos')
    def test_import_logo_and_invalid_replacement_preserve_previous(self):
        media=tv_media.install(self.root,'pc:game','logo',PNG)
        path=tv_media.folder(self.root,'pc:game')/'logo.png';before=path.read_bytes()
        self.assertTrue(media['logo'].startswith('/tv-media/'))
        for data in (b'',b'<svg/>',b'\x89PNG\r\n\x1a\ninvalid'):
            with self.assertRaises(ValueError):tv_media.install(self.root,'pc:game','logo',data)
            self.assertEqual(path.read_bytes(),before)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'ffmpeg/ffprobe necessários para validar vídeo real')
    def test_video_is_probed_and_only_old_variant_is_removed(self):
        video=self.root/'tiny.webm'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=black:s=16x16:d=0.2','-c:v','libvpx','-y',str(video)],check=True)
        media=tv_media.install(self.root,'pc:game','video',video.read_bytes())
        self.assertIn('video.webm',media['video'])
        path=tv_media.folder(self.root,'pc:game')/'video.webm';before=path.read_bytes()
        with self.assertRaises(ValueError):tv_media.install(self.root,'pc:game','video',b'\x1aE\xdf\xa3invalid')
        self.assertEqual(path.read_bytes(),before)

    def test_traversal_symlinks_and_oversized_upload_refused(self):
        for digest,name in (('../outside','video.mp4'),('a'*64,'../outside'),('a'*64,'library.json')):
            with self.assertRaises(ValueError):tv_media.resolve(self.root,digest,name)
        folder=tv_media.folder(self.root,'pc:link');folder.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):tv_media.install(self.root,'pc:link','logo',PNG)
        with patch.object(tv_media,'MAX_BYTES',2),self.assertRaises(ValueError):tv_media.install(self.root,'pc:large','logo',PNG)


class TestTimeMediaHTTP(BaseAPI):
    def setUp(self):
        self.game=library._blank_game('Tempo teste','Steam');self.gravar_biblioteca([self.game])
        srv.PLAYTIME_PATH.unlink(missing_ok=True)
        self.key=recent.pc_key(self.game['id'])

    def test_manual_duration_is_idempotent_and_home_exposes_totals(self):
        before=self.lib_path.read_bytes();body={'key':self.key,'minutes':30,'event':'android-test'}
        self.assertEqual(self.pedir('/api/tv/playtime',body)[1]['seconds'],1800)
        self.assertEqual(self.pedir('/api/tv/playtime',body)[1]['seconds'],1800)
        home=self.pedir('/api/tv/home')[1]
        self.assertEqual(home['mostPlayed'][0]['key'],self.key)
        self.assertEqual(home['mostPlayed'][0]['playtime']['sessions'],1)
        self.assertEqual(self.lib_path.read_bytes(),before)
        self.assertNotIn('_events',self.pedir('/api/tv/playtime')[1][self.key])
        for minutes in (0,True,-1,1441,'30'):
            self.assertEqual(self.pedir('/api/tv/playtime',{'key':self.key,'minutes':minutes})[0],400)
        self.assertEqual(self.pedir('/api/tv/playtime',{'key':'pc:unknown','minutes':1})[0],400)

    @unittest.skipUnless(shutil.which('identify'),'ImageMagick necessário para validar logos')
    def test_media_upload_csrf_and_range_stream(self):
        before=self.lib_path.read_bytes();url=self.url+'/api/tv/media?key='+urllib.parse.quote(self.key)+'&kind=logo'
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(urllib.request.Request(url,data=PNG),timeout=10)
        self.assertEqual(error.exception.code,403);error.exception.close()
        request=urllib.request.Request(url,data=PNG,headers={'X-PyRetro-CSRF':self.csrf_token})
        with urllib.request.urlopen(request,timeout=10) as response:media=json.load(response)
        with urllib.request.urlopen(urllib.request.Request(self.url+media['logo'],headers={'Range':'bytes=0-7'}),timeout=10) as response:
            self.assertEqual(response.status,206);self.assertEqual(response.read(),b'\x89PNG\r\n\x1a\n')
            self.assertTrue(response.headers['Content-Range'].startswith('bytes 0-7/'))
        self.assertEqual(self.lib_path.read_bytes(),before)
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(urllib.request.Request(self.url+media['logo'],headers={'Range':'bytes=999999-'}),timeout=10)
        self.assertEqual(error.exception.code,416);error.exception.close()

    def test_offline_progress_revalidates_cascade_in_write_transaction(self):
        self.game.update(iniciado=True,finalizado=True,platinado=True);self.gravar_biblioteca([self.game]);before=self.lib_path.read_bytes()
        body={'id':self.game['id'],'campos':{'iniciado':False,'finalizado':False,'platinado':False},'expected':{'iniciado':True,'finalizado':False,'platinado':False}}
        self.assertEqual(self.pedir('/api/library/edit',body)[0],409)
        self.assertEqual(self.lib_path.read_bytes(),before)
        body['expected']={'iniciado':True,'finalizado':True,'platinado':True}
        self.assertEqual(self.pedir('/api/library/edit',body)[0],200)
        self.assertEqual(self.pedir('/api/library/edit',body)[0],200,'retry já aplicado deve ser aceito')

    def test_offline_rating_is_compared_like_progress(self):
        self.game.update(nota=7.5);self.gravar_biblioteca([self.game]);before=self.lib_path.read_bytes()
        body={'id':self.game['id'],'campos':{'nota':9},'expected':{'nota':None}}
        self.assertEqual(self.pedir('/api/library/edit',body)[0],409,'nota mudou no notebook: preserva a do celular')
        self.assertEqual(self.lib_path.read_bytes(),before)
        self.assertEqual(self.pedir('/api/library/edit',{**body,'expected':{'nota':True}})[0],400)
        body['expected']={'nota':7.5}
        self.assertEqual(self.pedir('/api/library/edit',body)[0],200)
        self.assertEqual(self.pedir('/api/library/edit',body)[0],200,'retry já aplicado deve ser aceito')
        self.assertEqual(self.pedir('/api/library/edit',{'id':self.game['id'],'campos':{'nota':None},'expected':{'nota':9}})[0],200)
