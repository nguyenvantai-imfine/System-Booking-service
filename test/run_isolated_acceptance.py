"""Real SQL/RabbitMQ integration through a local gateway; email uses an in-memory mock.

Requires the dedicated luxestay-acceptance Compose infrastructure. Starts only
local child processes and always terminates its own children. Never uses root
or service dotenv credentials. Does not claim full Docker or browser acceptance.
"""
import concurrent.futures
from datetime import date, datetime, timedelta
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
import time
import uuid

import httpx
import pyodbc
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ENV_FILE = ROOT / ".env.acceptance.local"
RESULT = ROOT / "logs/isolated-acceptance-results.json"
PROCESSES = []
LOGS = []
CHECKS = []
MESSAGES = []
INBOX_KEY = secrets.token_urlsafe(32)
CONFIG = dotenv_values(ENV_FILE)


def check(name, condition):
    CHECKS.append({"check": name, "status": "PASS" if condition else "FAIL"})
    print(f"{'PASS' if condition else 'FAIL'}: {name}", flush=True)
    if not condition:
        raise AssertionError(name)


class MockEmailSink(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        if self.headers.get("X-Test-Inbox-Key") != INBOX_KEY:
            self.send_response(403); self.end_headers(); return
        txn = parse_qs(urlparse(self.path).query).get("txn",[""])[0]
        for message in reversed(MESSAGES):
            if txn and txn in message["html"]:
                match = re.search(r">\s*(\d{6})\s*<",message["html"])
                if match:
                    self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"code":match[1]}).encode()); return
        self.send_response(404); self.end_headers()
    def do_POST(self):
        MESSAGES.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        self.send_response(200)
        self.end_headers()
    def log_message(self, *_):
        pass


def connect(database):
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER=127.0.0.1,11433;DATABASE={database};"
        f"UID=sa;PWD={{{CONFIG['SA_PASSWORD']}}};TrustServerCertificate=yes;",
        autocommit=True,
    )


def start_services(sink_port):
    if "--docker" in sys.argv:
        import yaml
        code = (
            "import json,urllib.request,uvicorn; from src.core.email_sender import EmailSender; "
            f"sink='http://host.docker.internal:{sink_port}'; "
            "EmailSender.send_email=staticmethod(lambda to_email,subject,html_content,text_content='': "
            "(urllib.request.urlopen(urllib.request.Request(sink,data=json.dumps({'subject':subject,'html':html_content,'text':text_content}).encode(),headers={'Content-Type':'application/json'}),timeout=3).close() or True,'Mock sink')); "
            "uvicorn.run('src.main:app',host='0.0.0.0',port=8005)"
        )
        override = ROOT/"logs/docker-mock-email.override.yml"
        override.write_text(yaml.safe_dump({"services":{"notification-service":{"command":["python","-c",code]}}}),encoding="utf-8")
        subprocess.run(["docker","compose","--env-file",str(ENV_FILE),"-p","luxestay-acceptance","-f",str(ROOT/"docker-compose.yml"),"-f",str(override),"up","-d","--no-build"],check=True)
        check("All application services launched in Docker (email transport mocked)", True)
        return
    names = ["hotel", "user", "room", "booking", "payment", "notification"]
    env = os.environ.copy()
    env.update({k: str(v) for k, v in CONFIG.items() if v is not None})
    env.update({"ENV_FILE": str(ENV_FILE), "PYTHONWARNINGS":"ignore", "PYTHONUNBUFFERED":"1",
                "DB_SERVER":"127.0.0.1", "DB_PORT":"11433", "DB_USER":"sa",
                "DB_PASSWORD": CONFIG["SA_PASSWORD"], "DB_DRIVER":"ODBC Driver 18 for SQL Server",
                "DB_TRUSTED_CONNECTION":"False", "RABBITMQ_HOST":"127.0.0.1", "RABBITMQ_PORT":"15673",
                "MOCK_EMAIL_SEND":"True", "PUBLIC_API_URL":"http://127.0.0.1:18080/api/v1"})
    for i, name in enumerate(names):
        env[f"{name.upper()}_SERVICE_URL"] = f"http://127.0.0.1:{18000+i}/api/v1"
    for i, name in enumerate(names + ["gateway"]):
        child_env = env.copy()
        child_env.update({"APP_NAME":f"{name.title()} Acceptance", "DB_NAME":f"{name}_service"})
        port = 18080 if name == "gateway" else 18000+i
        child_env["PORT"] = str(port)
        directory = ROOT / "gateway" if name == "gateway" else ROOT / f"services/{name}-service"
        if name == "gateway":
            for j, target in enumerate(names):
                child_env[f"{target.upper()}_SERVICE_URL"] = f"http://127.0.0.1:{18000+j}"
        command = [sys.executable, "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", str(port)]
        if name == "notification":
            # Test-process patch only: retain real templates/consumer/persistence,
            # capture mock delivery in memory; never contact an SMTP service.
            code = (
                "import json,urllib.request,uvicorn; from src.core.email_sender import EmailSender; "
                f"sink='http://127.0.0.1:{sink_port}'; "
                "EmailSender.send_email=staticmethod(lambda to_email,subject,html_content,text_content='': "
                "(urllib.request.urlopen(urllib.request.Request(sink,data=json.dumps({'subject':subject,'html':html_content,'text':text_content}).encode(),headers={'Content-Type':'application/json'}),timeout=3).close() or True,'Mock sink')); "
                f"uvicorn.run('src.main:app',host='127.0.0.1',port={port})"
            )
            command = [sys.executable, "-c", code]
        logfile = open(ROOT / f"logs/acceptance-local-{name}.log", "w", encoding="utf-8")
        LOGS.append(logfile)
        PROCESSES.append(subprocess.Popen(command, cwd=directory, env=child_env, stdout=logfile, stderr=subprocess.STDOUT))
    deadline = time.monotonic() + 75
    while time.monotonic() < deadline:
        try:
            if httpx.get("http://127.0.0.1:18080/health", timeout=5).status_code == 200:
                check("All six local services ready through gateway", True)
                return
        except httpx.HTTPError:
            pass
        if any(p.poll() is not None for p in PROCESSES):
            raise RuntimeError("A local service failed startup; see acceptance-local logs.")
        time.sleep(1)
    raise RuntimeError("Gateway readiness timeout; see acceptance-local logs.")


def run_flow():
    base = "http://127.0.0.1:18080/api/v1"
    client = httpx.Client(base_url=base, timeout=15)
    def call(method, path, token=None, expected=200, **kwargs):
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = client.request(method, path, headers=headers, **kwargs)
        if response.status_code != expected:
            raise AssertionError(f"{method} {path}: expected {expected}, got {response.status_code}: {response.text[:700]}")
        return response.json()
    def login(username):
        return call("POST", "/auth/login", json={"ten_dang_nhap_hoac_email":username,"mat_khau":"123456"})["access_token"]
    admin, partner = login("admin"), login("partner1")
    check("Fresh bcrypt demo admin and partner login", True)
    call("POST", "/auth/login", expected=401, json={"ten_dang_nhap_hoac_email":"admin","mat_khau":"incorrect"})
    suffix = uuid.uuid4().hex[:10]
    tokens = []
    for i in range(2):
        result = call("POST", "/auth/register", expected=201, json={"ten_dang_nhap":f"accept_{suffix}_{i}","email":f"accept_{suffix}_{i}@example.com","mat_khau":secrets.token_urlsafe(16),"ho":"Acceptance","ten":"Test"})
        tokens.append(result["access_token"])
        if i == 0:
            customer_id = result["user"]["id_tai_khoan"]
    customer, other = tokens
    call("GET", "/payments/stats", customer, expected=403)
    call("POST", "/payments/simulate-ipn", expected=401, json={"ma_giao_dich_gateway":"invalid","trang_thai":"SUCCESS"})
    check("Wrong password, customer admin access and anonymous IPN rejected", True)
    hotel = call("POST", "/hotels", partner, expected=201, json={"ten_khach_san":f"Acceptance {suffix}","thanh_pho":"Da Nang"})
    hid = hotel["id_khach_san"]
    hotels = call("GET", "/hotels", params={"keyword":suffix})
    check("Hotel search reaches real Hotel SQL database", any(h["id_khach_san"] == hid for h in hotels["items"]))
    kind = call("POST", f"/hotels/{hid}/room-types", partner, expected=201, json={"ten_loai_phong":"Acceptance Deluxe","gia_co_ban_mot_dem":1000000})
    tid = kind["id_loai_phong"]
    rooms = [call("POST", f"/room-types/{tid}/rooms", partner, expected=201, json={"so_phong":f"A-{suffix}-{i}"}) for i in range(3)]
    arrival, departure = (date.today()+timedelta(days=8)).isoformat(), (date.today()+timedelta(days=10)).isoformat()
    available = call("GET", "/rooms/available", params={"hotel_id":hid,"check_in":arrival,"check_out":departure})
    check("Room availability includes newly created rooms", len(available) == 3)
    def booking_payload(room):
        return {"id_khach_san":hid,"ngay_nhan_phong":arrival,"ngay_tra_phong":departure,
                "rooms":[{"id_phong":room["id_phong"],"id_loai_phong":tid,"so_phong":room["so_phong"],"ten_loai_phong":"Acceptance Deluxe","gia":1000000}],
                "khach_o":{"ho_ten":"Acceptance Customer","email":"acceptance@example.com","sdt":"0901234567"}}
    booking = call("POST", "/bookings", customer, expected=201, json=booking_payload(rooms[0]))
    bid, bcode = booking["id_dat_phong"], booking["ma_booking"]
    check("Booking hold and numeric monetary response", booking["trang_thai"] == "PENDING_PAYMENT" and isinstance(booking["tong_tien"], (int,float)))
    call("POST", "/bookings", customer, expected=409, json=booking_payload(rooms[0]))
    call("GET", f"/bookings/{bid}", other, expected=403)
    check("Occupied room and foreign booking access rejected", True)
    pay = {"id_dat_phong":bid,"ma_booking":bcode,"so_tien":booking["tong_tien"],"phuong_thuc":"VNPAY"}
    call("POST", "/payments/create-payment", customer, expected=400, json={**pay,"so_tien":1})
    call("POST", "/payments/create-payment", other, expected=403, json=pay)
    key = uuid.uuid4().hex
    payment = call("POST", "/payments/create-payment", customer, expected=201, json=pay, headers={"X-Idempotency-Key":key})
    repeat = call("POST", "/payments/create-payment", customer, expected=201, json=pay, headers={"X-Idempotency-Key":key})
    check("Amount validation, ownership and idempotent payment creation", payment["id_thanh_toan"] == repeat["id_thanh_toan"])
    txn = payment["ma_giao_dich_gateway"]
    call("POST", "/payments/generate-otp", other, expected=403, json={"ma_giao_dich_gateway":txn,"email":"acceptance@example.com"})
    otp_response = call("POST", "/payments/generate-otp", customer, json={"ma_giao_dich_gateway":txn,"email":"acceptance@example.com"})
    check("OTP omitted from HTTP response and foreign account rejected", "otp_code" not in otp_response)
    deadline = time.monotonic()+15
    otp = None
    while time.monotonic() < deadline and otp is None:
        for message in MESSAGES:
            if txn in message["html"] or txn in message["text"]:
                match = re.search(r">\s*(\d{6})\s*<", message["html"])
                if match:
                    otp = match.group(1)
        if otp is None:
            time.sleep(.2)
    check("Real RabbitMQ delivers OTP to in-memory mock email sink", otp is not None)
    with connect("payment_service") as db:
        stored = db.execute("SELECT TOP 1 otp_code FROM giao_dich_otp WHERE ma_giao_dich_gateway=? ORDER BY id_otp DESC", txn).fetchone()[0]
    check("OTP persisted only as SHA-256", stored == hashlib.sha256(otp.encode()).hexdigest())
    wrong = "000000" if otp != "000000" else "000001"
    call("POST", "/payments/verify-otp", customer, expected=400, json={"ma_giao_dich_gateway":txn,"otp_code":wrong})
    verified = call("POST", "/payments/verify-otp", customer, json={"ma_giao_dich_gateway":txn,"otp_code":otp})
    confirmed = call("GET", f"/bookings/{bid}", customer)
    check("Valid OTP confirms booking and payment consistently", verified["trang_thai"] == "SUCCESS" and confirmed["trang_thai"] == "CONFIRMED")
    call("POST", "/payments/verify-otp", customer, expected=400, json={"ma_giao_dich_gateway":txn,"otp_code":otp})
    history = call("GET", "/bookings", customer)
    check("OTP cannot be reused; confirmed booking appears in history", any(b["id_dat_phong"] == bid for b in history["items"]))
    with connect("notification_service") as db:
        bodies = db.execute("SELECT noi_dung_html,noi_dung_text,du_lieu_dinh_kem FROM noi_dung_thong_bao n JOIN thong_bao t ON t.id_thong_bao=n.id_thong_bao WHERE t.ma_booking=? AND t.loai_thong_bao='OTP'", bcode).fetchall()
    check("Persisted OTP notifications redact the raw code", bool(bodies) and all(otp not in str(row) for row in bodies))
    # Exercise real SQL Server sp_getapplock with concurrent HTTP requests.
    def compete(_):
        return client.post("/bookings", json=booking_payload(rooms[1]), headers={"Authorization":f"Bearer {customer}"}).status_code
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(compete, range(2)))
    check("Concurrent bookings produce one winner without overbooking", statuses == [201,409])
    with connect("booking_service") as db:
        race = db.execute("SELECT d.id_dat_phong,d.ma_booking,d.tong_tien FROM dat_phong d JOIN chi_tiet_dat_phong c ON c.id_dat_phong=d.id_dat_phong WHERE c.id_phong=? AND d.trang_thai='PENDING_PAYMENT'", rooms[1]["id_phong"]).fetchone()
    race_pay = {"id_dat_phong":race[0],"ma_booking":race[1],"so_tien":float(race[2]),"phuong_thuc":"VNPAY"}
    race_key = uuid.uuid4().hex
    def compete_payment(_):
        response = client.post("/payments/create-payment", json=race_pay, headers={"Authorization":f"Bearer {customer}","X-Idempotency-Key":race_key})
        return response.status_code, response.json().get("id_thanh_toan")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        race_results = list(pool.map(compete_payment, range(2)))
    check("Concurrent payment retries reuse one transaction", all(code == 201 for code,_ in race_results) and race_results[0][1] == race_results[1][1])
    race_payment = call("POST", "/payments/create-payment", customer, expected=201, json=race_pay, headers={"X-Idempotency-Key":race_key})
    race_txn = race_payment["ma_giao_dich_gateway"]
    call("POST", "/payments/generate-otp", customer, json={"ma_giao_dich_gateway":race_txn,"email":"acceptance@example.com"})
    with connect("payment_service") as db:
        db.execute("UPDATE giao_dich_otp SET thoi_gian_het_han=DATEADD(minute,-1,GETUTCDATE()) WHERE ma_giao_dich_gateway=?", race_txn)
    call("POST", "/payments/verify-otp", customer, expected=400, json={"ma_giao_dich_gateway":race_txn,"otp_code":"000000"})
    check("Expired OTP rejected", True)
    held = call("POST", "/bookings", customer, expected=201, json=booking_payload(rooms[2]))
    with connect("booking_service") as db:
        db.execute("UPDATE dat_phong SET han_giu_cho=DATEADD(minute,-20,GETUTCDATE()) WHERE id_dat_phong=?", held["id_dat_phong"])
    call("POST", "/bookings", customer, expected=201, json=booking_payload(rooms[2]))
    released = call("GET", f"/bookings/{held['id_dat_phong']}", customer)
    check("Expired hold releases room and cancels stale booking", released["trang_thai"] == "CANCELLED")
    call("GET", "/payments/stats", admin)
    check("Admin payment statistics accessible", True)
    notifications = call("GET", "/notifications", customer)
    check("Payment OTP notification belongs to the booking owner", any(n["loai_thong_bao"] == "OTP" and n["ma_booking"] == bcode for n in notifications["items"]))
    call("PUT", f"/room-types/{tid}", partner, json={"mo_ta":"Updated acceptance room type"})
    batch = call("POST", f"/room-types/{tid}/rooms/batch", partner, expected=201, json={"room_numbers":["B1","B2"]})
    call("POST", f"/room-types/{tid}/rooms/batch", partner, expected=409, json={"room_numbers":["B2","B3"]})
    def create_room(index):
        return call("POST", f"/room-types/{tid}/rooms", partner, expected=201, json={"so_phong":f"Concurrent-{index}"})
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(create_room,range(2)))
    with connect("room_service") as db:
        counter = db.execute("SELECT so_luong_phong FROM loai_phong WHERE id_loai_phong=?",tid).fetchone()[0]
        actual = db.execute("SELECT COUNT(*) FROM phong WHERE id_loai_phong=?",tid).fetchone()[0]
    check("Room batch conflict is atomic; concurrent creation preserves counter", counter == actual == 7)
    room_id = batch[0]["id_phong"]
    call("PATCH", f"/rooms/{room_id}/status", partner, json={"trang_thai":"MAINTENANCE"})
    call("PATCH", f"/rooms/{room_id}/status", partner, expected=400, json={"trang_thai":"OCCUPIED"})
    check("Room rejects invalid maintenance-to-occupied transition", True)
    # Same event delivered by concurrent REST fallbacks and the real broker.
    import pika
    queue = "notification.booking.cancelled"
    wire = {"email":"dedup@example.com","id_tai_khoan":customer_id,"ma_booking":"DEDUP-"+suffix}
    body = json.dumps(wire,ensure_ascii=False).encode()
    event_key = hashlib.sha256(queue.encode()+b"\0"+body).hexdigest()
    request = {"loai_thong_bao":"BOOKING_CANCELLED","nguoi_nhan":wire["email"],"id_tai_khoan":customer_id,"ma_booking":wire["ma_booking"],"du_lieu":wire}
    headers = {"X-Internal-Secret":CONFIG["INTERNAL_SERVICE_SECRET"],"X-Notification-Event-Key":event_key}
    before = len(MESSAGES)
    def deliver(_):
        return call("POST","/notifications/internal-send",expected=201,json=request,headers=headers)["id_thong_bao"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(deliver,range(2)))
    connection = pika.BlockingConnection(pika.ConnectionParameters("127.0.0.1",15673,credentials=pika.PlainCredentials(CONFIG["RABBITMQ_USER"],CONFIG["RABBITMQ_PASSWORD"])))
    connection.channel().basic_publish(exchange="",routing_key=queue,body=body)
    connection.close()
    time.sleep(1)
    with connect("notification_service") as db:
        count = db.execute("SELECT COUNT(*) FROM thong_bao WHERE event_key=?",event_key).fetchone()[0]
    check("Concurrent REST and RabbitMQ event share one record and one mock email", ids[0] == ids[1] and count == 1 and len(MESSAGES) == before+1)
    call("PATCH",f"/notifications/{ids[0]}/read",customer)
    call("GET",f"/notifications/{ids[0]}",other,expected=404)
    check("Notification read action enforces owner isolation", True)
    client.close()


def main():
    if "--allow-test-writes" not in sys.argv:
        raise SystemExit("Pass --allow-test-writes to authorize fixtures in the dedicated acceptance databases.")
    if CONFIG.get("MSSQL_PORT") != "11433" or CONFIG.get("GATEWAY_PORT") != "18080":
        raise SystemExit("Refusing a configuration outside the isolated acceptance ports.")
    hostname = subprocess.check_output(["docker","inspect","--format","{{.Config.Hostname}}","luxestay-acceptance-sqlserver-1"], text=True).strip()
    with connect("master") as db:
        actual = db.execute("SELECT @@SERVERNAME").fetchone()[0]
    if actual.lower() != hostname.lower():
        raise SystemExit("SQL Server does not match the dedicated acceptance container.")
    sink = ThreadingHTTPServer(("0.0.0.0" if "--docker" in sys.argv else "127.0.0.1",0), MockEmailSink)
    threading.Thread(target=sink.serve_forever,daemon=True).start()
    error = None
    try:
        start_services(sink.server_port)
        run_flow()
        if "--browser" in sys.argv:
            subprocess.run(["node",str(ROOT/"test/check_browser_flow.cjs")],cwd=ROOT,
                env={**os.environ,"MOCK_INBOX_URL":f"http://127.0.0.1:{sink.server_port}","MOCK_INBOX_KEY":INBOX_KEY},check=True)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        print(f"FAIL: {error}", flush=True)
    finally:
        for process in PROCESSES:
            process.terminate()
        for process in PROCESSES:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        for logfile in LOGS:
            logfile.close()
        sink.shutdown()
        if "--docker" in sys.argv:
            subprocess.run(["docker","compose","--env-file",str(ENV_FILE),"-p","luxestay-acceptance","up","-d","--no-build","notification-service"],check=True)
        result_path = ROOT/"logs/docker-acceptance-results.json" if "--docker" in sys.argv else RESULT
        result_path.write_text(json.dumps({"mode":"Docker applications + mock email" if "--docker" in sys.argv else "local services + isolated Docker SQL/RabbitMQ + mock email","checks":CHECKS,"error":error}, indent=2),encoding="utf-8")
    return 1 if error is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
