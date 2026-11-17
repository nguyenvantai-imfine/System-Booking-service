"""Sanitized final acceptance evidence; post-push receipt is intentionally local."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
def git(*arguments):
    return subprocess.check_output(['git',*arguments],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
def read(name):
    return json.loads((ROOT/'logs'/name).read_text(encoding='utf-8'))

if __name__=='__main__':
    names=sorted(set(git('diff','HEAD','--name-only').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines()))
    source={}
    for name in names:
        path=ROOT/name
        if path.is_file() and (path.suffix in {'.py','.ts','.tsx','.mjs','.cjs','.sql','.sh','.ps1','.yml'} or path.name in {'Dockerfile','.dockerignore','.gitattributes'}):
            source[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    raw=(ROOT/'logs/v5-compose-state.json').read_text(encoding='utf-16')
    containers=[json.loads(line) for line in raw.splitlines() if line.startswith('{')]
    offline=read('offline-regression-results.json');api=read('docker-acceptance-results.json');browser=read('v4-browser-results.json')
    assert all(row['status']=='PASS' for row in offline)
    assert api['error'] is None and all(row['status']=='PASS' for row in api['checks'])
    assert browser['status']=='PASS' and read('v5-rebuilt-images-results.json')['status']=='PASS'
    assert all(row['Health']=='healthy' for row in containers if row['Service']!='db-init')
    result={
        'recorded_at':datetime.now(timezone(timedelta(hours=7))).isoformat(),
        'baseline_head':git('rev-parse','HEAD'),'remote_baseline':git('rev-parse','origin/main'),
        'branch':git('branch','--show-current'),'release_authorization':'User V5: normal commit/push main after successful gate; no tag/force push',
        'files':names,'source_sha256':source,
        'offline':offline,'unittest_cases':sum(row['unittest_count'] or 0 for row in offline),
        'api_client':{'status':'PASS','cases':7},'frontend_typechecks':'PASS both',
        'frontend_lint':{'errors':0,'customer_warnings':13,'admin_warnings':4},
        'docker_api':api,'browser':browser,
        'docker_runtime':{'status':'PASS','containers':[{'service':r['Service'],'state':r['State'],'health':r['Health']} for r in containers]},
        'rebuild':{'status':'PASS on supported recovered-base/legacy-builder host','applications':9,'separate_tags':'luxestay-release-verify-*','fresh_smoke':read('v5-rebuilt-images-results.json'),'clean_linux_buildkit':'NOT RUN'},
        'persistence':read('persistence-results.json'),'health_after_restart':read('v5-health-after-restart.json'),
        'content_gate':'Working and staged exact-value/pattern scan; enforced before commit',
        'retained_booking':{'id':28,'code':'BK-202611-68F1D3','action':'preserved; no original-database writes performed in V5'},
        'limits':['Images/fonts/media blocked during UI QA; external QR graphics not validated','Admin page navigation is not exhaustive CRUD acceptance','No real SMTP or production payment','SMTP/SQL crash-window and SYNC_FAILED limits retained','Default BuildKit/clean host not certified; supported legacy path verified'],
        'git_receipt':'Final commit, remote equality and clean-tree status recorded after push in logs/v5-release-receipt.json and final answer',
    }
    output=ROOT/'docs/validation/2026-11-17-v5-results.json'
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"PASS: V5 evidence saved; {result['unittest_cases']} unit cases, {len(api['checks'])} Docker groups, browser PASS.")
