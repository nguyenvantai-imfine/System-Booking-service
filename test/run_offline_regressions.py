"""Run reviewed offline suites in separate interpreters (no live DB fixtures)."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SUITES = [
    "test_admin_booking_confirmation.py",
    "test_notification_transport_identity.py",
    "test_legacy_auth_fallback.py", "test_service_config_defaults.py",
    "test_service_startup_safety.py", "test_room_regression.py",
    "test_notification_safety.py", "test_payment_notification_contract.py",
    "test_gateway_routing_p21_p22.py", "test_available_rooms_p11.py",
    "test_admin_revenue_stats_p34.py", "test_notification_schema_migration.py",
    "test_cors_p07.py", "test_stabilization_security.py",
    "test_room_price_trust_p12.py",
]

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    results = []
    (ROOT/"logs").mkdir(exist_ok=True)
    for suite in SUITES:
        env = {**os.environ, "PYTHONWARNINGS":"ignore", "PYTHONIOENCODING":"utf-8"}
        arguments = (["-m", "unittest", "discover", "-s", "test", "-p", suite]
                     if "unittest.TestCase" in (ROOT/"test"/suite).read_text(encoding="utf-8")
                     else [str(ROOT/"test"/suite)])
        result = subprocess.run([sys.executable, *arguments], cwd=ROOT,
                                env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        output = result.stdout + result.stderr
        (ROOT/"logs"/suite.replace(".py",".log")).write_text(output, encoding="utf-8")
        count = re.search(r"Ran (\d+) tests?", output)
        status = "PASS" if result.returncode == 0 else "FAIL"
        results.append({"suite":suite,"status":status,"unittest_count":int(count[1]) if count else None})
        print(f"{status}: {suite}", flush=True)
        if result.returncode:
            print(output[-1800:])
    (ROOT/"logs/offline-regression-results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    raise SystemExit(int(any(r["status"] != "PASS" for r in results)))
