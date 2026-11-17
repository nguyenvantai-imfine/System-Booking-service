"""Smoke-test fresh release images without replacing running deployment containers."""
import json
import os
from pathlib import Path
import subprocess
import time

import httpx

ROOT=Path(__file__).resolve().parents[1]
COMPOSE=['docker','compose','--env-file',str(ROOT/'.env.acceptance.local'),'-p','luxestay-acceptance']

if __name__=='__main__':
    resolved=json.loads(subprocess.check_output([*COMPOSE,'config','--format','json'],text=True))
    settings=resolved['services']['room-service']['environment']
    environment={**os.environ,**{k:str(v) for k,v in settings.items()}}
    command=['docker','run','--rm','--network','luxestay-acceptance_default']
    for key in settings:command.extend(['--env',key])
    command.extend(['luxestay-release-verify-room-fresh','python','-c',
        "from fastapi.testclient import TestClient; from src.main import app; "
        "client=TestClient(app); response=client.get('/health'); assert response.status_code==200; print('PASS: fresh Room image connects to isolated SQL Server')"])
    subprocess.run(command,env=environment,check=True)
    name='luxestay-v5-fresh-frontend-check'
    exists=subprocess.run(['docker','container','inspect',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if exists.returncode==0:raise SystemExit('Owned test-container name already exists; refusing replacement')
    subprocess.run(['docker','run','--rm','-d','--name',name,'-p','127.0.0.1:13011:3000','luxestay-release-verify-customer-fresh'],check=True,stdout=subprocess.DEVNULL)
    try:
        ready=False
        for _ in range(40):
            try:
                response=httpx.get('http://127.0.0.1:13011',timeout=5)
                if response.status_code==200:
                    ready=True;break
            except httpx.HTTPError:pass
            time.sleep(.5)
        if not ready:raise RuntimeError('Fresh frontend image did not serve HTTP 200')
        print('PASS: fresh frontend image serves production HTTP')
    finally:
        subprocess.run(['docker','stop',name],check=True,stdout=subprocess.DEVNULL)
    (ROOT/'logs/v5-rebuilt-images-results.json').write_text(json.dumps({'status':'PASS','room_sql':'PASS','frontend_http':'PASS','source_build':'no-cache, separate image tags; active deployment untouched'},indent=2),encoding='utf-8')
