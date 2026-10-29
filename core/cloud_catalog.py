"""Dependências do DAT local; nenhuma ROM/BIOS é enviada."""
import json
import re
import xml.etree.ElementTree as ET
from core import arcade,cloud

def publish_arcade(cfg,storage):
    if not cfg.get('pc',{}).get('roms_root'):return
    parents=arcade.load_dat(arcade.dat_dir(cfg))
    if not parents:return
    safe=lambda value:isinstance(value,str) and (value=='' or bool(re.fullmatch(r'[A-Za-z0-9_-]+',value)))
    names={}
    folder=arcade.dat_dir(cfg)
    for pattern in arcade.DAT_GLOBS:
        for path in sorted(folder.glob(pattern)):
            try:
                root=ET.parse(path).getroot()
            except (OSError,ET.ParseError):
                continue
            for game in root.iter('game'):
                name=game.get('name','');description=game.findtext('description','').strip()
                if name in parents and safe(name) and description and len(description)<=512:
                    names[name]=description
    data={'schema':1,'parents':{k:v for k,v in parents.items() if k and safe(k) and safe(v)},'names':names}
    try:previous=json.loads(storage.get('catalog/arcade.json'))
    except cloud.NotFound:previous=None
    if previous!=data:storage.put('catalog/arcade.json',json.dumps(data,sort_keys=True).encode(),overwrite=True)
