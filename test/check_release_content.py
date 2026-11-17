"""Read-only release content gate. Prints locations, never sensitive values."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]
def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.DEVNULL)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--staged',action='store_true')
    args=parser.parse_args()
    if args.staged:
        names=git('diff','--cached','--name-only','-z').decode().split('\0')
    else:
        names=(git('diff','--name-only','-z')+git('ls-files','--others','--exclude-standard','-z')).decode().split('\0')
    names=sorted(set(filter(None,names)))
    sensitive=[]
    for envfile in [ROOT/'.env',ROOT/'.env.acceptance.local',*ROOT.glob('services/*/.env')]:
        if envfile.is_file():
            for key,value in dotenv_values(envfile).items():
                if value and len(value)>=16 and any(part in key.upper() for part in ('PASSWORD','SECRET','TOKEN','PRIVATE_KEY')):
                    sensitive.append((key,value))
    findings=[]
    for name in names:
        path=Path(name)
        if any(part in {'logs','node_modules','.next','.git','.aws'} for part in path.parts) or (path.name.startswith('.env') and not path.name.endswith('.example')):
            findings.append({'file':name,'reason':'excluded environment/runtime artifact'})
            continue
        blob=git('show',':'+name) if args.staged else (ROOT/name).read_bytes()
        text=blob.decode('utf-8',errors='replace')
        for key,value in sensitive:
            if value in text:
                findings.append({'file':name,'reason':'configured sensitive value: '+key})
        if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}',text):
            findings.append({'file':name,'reason':'private key or provider-token pattern'})
        if name.startswith('services/') and '/src/' in name and '_COMPATIBILITY_JWT_SECRETS' in text:
            findings.append({'file':name,'reason':'JWT compatibility fallback'})
    print(json.dumps({'mode':'staged' if args.staged else 'working-tree','files':len(names),'status':'FAIL' if findings else 'PASS','findings':findings},indent=2))
    raise SystemExit(1 if findings else 0)
