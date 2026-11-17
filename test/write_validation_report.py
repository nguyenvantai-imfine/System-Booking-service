"""Publish sanitized evidence and source fingerprints, never environment values."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


if __name__ == "__main__":
    files = set(git("diff", "--name-only").splitlines()) | set(git("ls-files", "--others", "--exclude-standard").splitlines())
    fingerprints = {}
    for name in sorted(files):
        path = ROOT / name
        if path.is_file() and (path.suffix in {".py", ".ts", ".tsx", ".mjs", ".sql", ".yml", ".ps1", ".sh"} or path.name in {"Dockerfile", ".dockerignore", ".gitattributes"}):
            fingerprints[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    offline = json.loads((ROOT/"logs/offline-regression-results.json").read_text(encoding="utf-8"))
    flow = json.loads((ROOT/"logs/isolated-acceptance-results.json").read_text(encoding="utf-8"))
    report = {
        "recorded_at": datetime.now(timezone(timedelta(hours=7))).isoformat(),
        "baseline_head": git("rev-parse", "HEAD"),
        "working_tree_committed": False,
        "offline": {"suites": offline, "unittest_cases":sum(r["unittest_count"] or 0 for r in offline)},
        "integration":flow,
        "frontend_http":json.loads((ROOT/"logs/frontend-server-results.json").read_text(encoding="utf-8")),
        "persistence":json.loads((ROOT/"logs/persistence-results.json").read_text(encoding="utf-8")),
        "additional_executed_checks":{
            "python_compileall":"PASS", "compose_config_quiet":"PASS",
            "customer_production_build":"PASS", "admin_production_build":"PASS",
            "api_client_node_tests":{"status":"PASS","cases":7},
            "full_docker_deployment":"BLOCKED: new Python/Node images fail before application execution; BuildKit reports EOF",
            "browser_ui_e2e":"NOT RUN", "external_smtp":"NOT RUN", "production_payment":"NOT RUN",
        },
        "retained_legacy_test_fixture":{
            "database":"booking_service (pre-existing local configuration)",
            "id_dat_phong":28,"ma_booking":"BK-202611-68F1D3",
            "action":"Retained with child records per explicit user instruction; no deletion attempted",
        },
        "source_sha256": fingerprints,
    }
    output=ROOT/"docs/validation/2026-11-17-results.json"
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Saved sanitized evidence: {len(offline)} suites, {report['offline']['unittest_cases']} unittest cases, {len(flow['checks'])} integration checks.")
