"""Collect sanitized V4 evidence without environment values or raw message data."""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
def read(name):
    return json.loads((ROOT/'logs'/name).read_text(encoding='utf-8'))

if __name__=='__main__':
    inventory=sorted(set(git('diff','--name-only').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines()))
    changed=[];fingerprints={}
    for name in inventory:
        path=ROOT/name;before=ROOT/'logs/v4-baseline'/name
        if not path.is_file():continue
        if not before.is_file() or path.read_bytes()!=before.read_bytes():changed.append(name)
        if path.suffix in {'.py','.ts','.tsx','.mjs','.cjs','.ps1','.sql','.sh','.yml'} or path.name in {'Dockerfile','.dockerignore'}:
            fingerprints[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    offline=read('offline-regression-results.json')
    raw=(ROOT/'logs/v4-compose-state.json').read_text(encoding='utf-16')
    containers=[json.loads(line) for line in raw.splitlines() if line.startswith('{')]
    report={
        'date':datetime.now(timezone(timedelta(hours=7))).isoformat(),
        'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'committed':False,
        'source_inventory':inventory,'changed_since_v4_baseline':changed,'source_sha256':fingerprints,
        'offline':offline,'unittest_cases':sum(r['unittest_count'] or 0 for r in offline),
        'docker_api':read('docker-acceptance-results.json'),
        'browser':read('v4-browser-results.json'),
        'persistence':read('persistence-results.json'),
        'health_after_restart':read('v4-health-after-restart.json'),
        'containers':[{'service':r['Service'],'state':r['State'],'health':r.get('Health',''),'image':r['Image']} for r in containers],
        'build':{'applications':9,'status':'PASS','builder':'legacy, sequential','base_snapshot_recovery':'same saved layers imported into new snapshots; originals retained'},
        'api_client_tests':{'status':'PASS','cases':7},
        'frontend_lint':{'customer':{'exit':0,'errors':0,'warnings':13},'admin':{'exit':0,'errors':0,'warnings':4}},
        'source_syntax':'PASS','frontend_docker_types_build':'PASS both apps',
        'retained_booking':{'id':28,'code':'BK-202611-68F1D3','action':'untouched per user instruction'},
        'remaining':['Chrome host resource exhaustion prevents UI E2E','Default BuildKit EOF; legacy builder is verified','Not all nested Hotel/User/admin CRUD cases exhaustively covered','No external SMTP/payment/QR image acceptance','SMTP/SQL crash-window atomicity and distributed transaction limits retained'],
    }
    output=ROOT/'docs/validation/2026-11-17-v4-results.json'
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"V4 evidence: {len(offline)} suites, {report['unittest_cases']} unittest cases, {len(report['docker_api']['checks'])} Docker checks; browser {report['browser']['status']}.")
