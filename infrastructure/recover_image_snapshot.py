"""Rebuild saved base layers into a new local snapshot; never delete volumes/tags.

Usage: python infrastructure/recover_image_snapshot.py IMAGE SLUG
Only needed for the verified Docker Desktop unpacked-snapshot corruption.
Normal clean hosts should pull official images and use the normal build path.
"""
import io,json,re,subprocess,sys,tarfile
from pathlib import Path
image,slug=sys.argv[1:]
if not re.fullmatch(r'[a-z0-9-]+',slug):raise SystemExit('Invalid artifact slug')
Path('logs').mkdir(exist_ok=True)
archive=Path(f'logs/v4-{slug}-image.tar');rootfs=Path(f'logs/v4-{slug}-rootfs.tar')
subprocess.run(['docker','image','save','--output',str(archive),image],check=True)
files={}
with tarfile.open(archive) as saved:
    manifest=json.load(saved.extractfile('manifest.json'))[0]
    config=json.load(saved.extractfile(manifest['Config']))['config']
    for layer in manifest['Layers']:
        with tarfile.open(fileobj=saved.extractfile(layer),mode='r:*') as content:
            for member in content:
                name=member.name.removeprefix('./')
                if '/.wh.' in name or name.startswith('.wh.'):
                    if Path(name).name == '.wh..wh..opq':
                        parent=str(Path(name).parent).replace('\\','/')
                        for old in list(files):
                            if old.startswith(parent+'/'):files.pop(old)
                        continue
                    target=str(Path(name).with_name(Path(name).name.removeprefix('.wh.'))).replace('\\','/')
                    for old in list(files):
                        if old==target or old.startswith(target+'/'):files.pop(old)
                    continue
                files[name]=(member,content.extractfile(member).read() if member.isfile() else None)
    with tarfile.open(rootfs,'w') as output:
        for member,data in files.values():output.addfile(member,io.BytesIO(data) if data is not None else None)
args=['docker','import']
for value in config.get('Env',[]):args+=['--change','ENV '+value]
for key in ['Cmd','Entrypoint']:
    if config.get(key):args+=['--change',key.upper()+' '+json.dumps(config[key])]
if config.get('WorkingDir'):args+=['--change','WORKDIR '+config['WorkingDir']]
if config.get('User'):args+=['--change','USER '+config['User']]
args+=[str(rootfs),'luxestay-v4-recovered-'+slug]
subprocess.run(args,check=True)
print('Reconstructed exact saved image layers in a new snapshot; original image tag untouched.')
