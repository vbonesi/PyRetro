"""Modelo de Drive com nomes não únicos: chamadas paralelas não devem criar duplicatas."""
import collections
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import threading
import time
import unittest
import uuid
from core import cloud

class TestParallelCloud(unittest.TestCase):
    def test_shared_parents_and_immutable_paths_are_unique_across_storage_instances(self):
        folders=set();files=collections.defaultdict(list);guard=threading.Lock();active=0;peak=0
        def run(args,**kwargs):
            nonlocal active,peak
            op=args[1];code=0;out=b''
            if op=='mkdir':
                with guard:folders.add(args[2])
            elif op=='lsjson':
                with guard:exists=args[-1] in files
                code=0 if exists else 3;out=json.dumps({'IsDir':False}).encode() if exists else b''
            elif op=='copyto':
                target=args[3];parent=target.rsplit('/',1)[0]
                with guard:
                    self.assertIn(parent,folders);active+=1;peak=max(peak,active)
                time.sleep(.015)
                with guard:files[target].append(Path(args[2]).read_bytes());active-=1
            else:raise AssertionError(op)
            return subprocess.CompletedProcess(args,code,out,b'')
        base='memory:'+str(uuid.uuid4());stores=[cloud.RcloneStorage(base,run=run) for _ in range(3)]
        def put(i):
            try:stores[i%3].put('shared/folder/'+str(i%4),str(i%4).encode())
            except cloud.Exists:pass
        with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(put,range(24)))
        self.assertEqual(len(files),4);self.assertTrue(all(len(v)==1 for v in files.values()))
        self.assertGreater(peak,1,'uploads de caminhos distintos devem continuar paralelos')
