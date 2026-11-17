"""Restart only isolated infrastructure and compare SQL rows / durable queues."""
import json
import subprocess
import time

import httpx
from run_isolated_acceptance import CONFIG, ROOT, connect

COMPOSE = ["docker", "compose", "--env-file", str(ROOT/".env.acceptance.local"), "-p", "luxestay-acceptance"]


def snapshot():
    data = {}
    for name in ("hotel", "user", "room", "booking", "payment", "notification"):
        with connect(f"{name}_service") as db:
            tables = [row[0] for row in db.execute("SELECT name FROM sys.tables WHERE is_ms_shipped=0")]
            data[name] = {table: db.execute(f"SELECT COUNT_BIG(*) FROM [{table.replace(']', ']]')}]").fetchone()[0] for table in tables}
    response = httpx.get("http://127.0.0.1:15674/api/queues", auth=(CONFIG["RABBITMQ_USER"],CONFIG["RABBITMQ_PASSWORD"]),timeout=5)
    response.raise_for_status()
    data["durable_queues"] = sorted(q["name"] for q in response.json() if q["durable"])
    return data


if __name__ == "__main__":
    if CONFIG.get("MSSQL_PORT") != "11433":
        raise SystemExit("Refusing non-acceptance configuration")
    for service in ("sqlserver", "rabbitmq"):
        project = subprocess.check_output(["docker","inspect","--format",'{{index .Config.Labels "com.docker.compose.project"}}',f"luxestay-acceptance-{service}-1"],text=True).strip()
        if project != "luxestay-acceptance":
            raise SystemExit("Container project mismatch")
    before = snapshot()
    subprocess.run([*COMPOSE,"restart","sqlserver","rabbitmq"],check=True)
    after = None
    deadline = time.monotonic()+90
    while time.monotonic() < deadline:
        try:
            after = snapshot()
            break
        except Exception:
            time.sleep(2)
    passed = before == after
    (ROOT/"logs/persistence-results.json").write_text(json.dumps({"status":"PASS" if passed else "FAIL","before":before,"after":after},indent=2),encoding="utf-8")
    print(f"{'PASS' if passed else 'FAIL'}: all six database row counts and durable queue names survive isolated infrastructure restart")
    raise SystemExit(0 if passed else 1)
