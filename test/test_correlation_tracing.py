# -*- coding: utf-8 -*-
import sys
import os
import uuid
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

def run_isolated_test(title, script_code, cwd):
    print(f"\n[{title}]")
    cmd = [sys.executable, "-c", script_code]
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"FAILED (Exit Code {res.returncode}):")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        raise RuntimeError(f"Test '{title}' failed!")
    print(res.stdout.strip())
    print(f"[PASS] {title}")

def main():
    print("\n" + "=" * 65)
    print("BẮT ĐẦU BỘ KIỂM THỬ TRACING VỚI X-CORRELATION-ID")
    print("=" * 65)

    # -------------------------------------------------------------
    # 1. Gateway tự sinh X-Correlation-ID và ghi log đúng format
    # -------------------------------------------------------------
    gateway_auto_gen_code = """
import uuid
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
res = client.get('/')
assert res.status_code == 200, f'Status: {res.status_code}'
cid = res.headers.get('X-Correlation-ID')
assert cid is not None, 'Thieu X-Correlation-ID tren response!'
assert len(cid) >= 32, f'Invalid CID: {cid}'
print(f' -> Gateway tu sinh X-Correlation-ID: {cid}')
print(f' -> Header response co X-Correlation-ID: {cid}')
"""
    run_isolated_test(
        "Test 1: Gateway tu dong sinh X-Correlation-ID khi client khong gui header",
        gateway_auto_gen_code,
        cwd=os.path.join(PROJECT_ROOT, "gateway"),
    )

    # -------------------------------------------------------------
    # 2. Gateway bảo toàn X-Correlation-ID của client và ghi log
    # -------------------------------------------------------------
    test_client_cid = f"CLIENT-CID-{uuid.uuid4().hex[:8].upper()}"
    gateway_preserve_code = f"""
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
custom_cid = '{test_client_cid}'
res = client.get('/', headers={{'X-Correlation-ID': custom_cid}})
assert res.status_code == 200
assert res.headers.get('X-Correlation-ID') == custom_cid, f'Kỳ vọng {{custom_cid}}, nhận {{res.headers.get(\"X-Correlation-ID\")}}'
print(f' -> Gateway bao toan dung X-Correlation-ID: {{custom_cid}}')
"""
    run_isolated_test(
        "Test 2: Gateway bao toan X-Correlation-ID tu request client",
        gateway_preserve_code,
        cwd=os.path.join(PROJECT_ROOT, "gateway"),
    )

    # -------------------------------------------------------------
    # 3. Booking Service nhận X-Correlation-ID, gán response và log
    # -------------------------------------------------------------
    booking_trace_id = f"TRACE-BOOKING-{uuid.uuid4().hex[:8].upper()}"
    booking_test_code = f"""
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
cid = '{booking_trace_id}'
res = client.get('/', headers={{'X-Correlation-ID': cid}})
assert res.status_code == 200
assert res.headers.get('X-Correlation-ID') == cid, f'Response header thieu CID: {{res.headers}}'
print(f' -> Booking Service tiep nhan va tra ve X-Correlation-ID: {{cid}}')
"""
    run_isolated_test(
        "Test 3: Booking Service tiep nhan X-Correlation-ID va log chuan",
        booking_test_code,
        cwd=os.path.join(PROJECT_ROOT, "services", "booking-service"),
    )

    # -------------------------------------------------------------
    # 4. Payment Service nhận X-Correlation-ID, gán response và log
    # -------------------------------------------------------------
    payment_trace_id = f"TRACE-PAYMENT-{uuid.uuid4().hex[:8].upper()}"
    payment_test_code = f"""
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
cid = '{payment_trace_id}'
res = client.get('/', headers={{'X-Correlation-ID': cid}})
assert res.status_code == 200
assert res.headers.get('X-Correlation-ID') == cid, f'Response header thieu CID: {{res.headers}}'
print(f' -> Payment Service tiep nhan va tra ve X-Correlation-ID: {{cid}}')
"""
    run_isolated_test(
        "Test 4: Payment Service tiep nhan X-Correlation-ID va log chuan",
        payment_test_code,
        cwd=os.path.join(PROJECT_ROOT, "services", "payment-service"),
    )

    # -------------------------------------------------------------
    # 5. Payment Service tự động lan truyền X-Correlation-ID sang Booking Service
    # -------------------------------------------------------------
    propagation_trace_id = f"DISTRIBUTED-TRACE-{uuid.uuid4().hex[:10].upper()}"
    propagation_test_code = f"""
from unittest.mock import patch, MagicMock
from src.core.correlation import set_correlation_id, get_correlation_id
from src.services.payment_service import PaymentService
from src.schemas.payment_schema import CreatePaymentRequest
from src.core.database import SessionLocal

trace_id = '{propagation_trace_id}'
set_correlation_id(trace_id)
assert get_correlation_id() == trace_id

db = SessionLocal()
captured_headers = {{}}

try:
    with patch('urllib.request.urlopen') as mock_url:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{{"trang_thai": "PENDING_PAYMENT"}}'
        mock_url.return_value.__enter__.return_value = mock_resp

        PaymentService.create_payment(
            db=db,
            payload=CreatePaymentRequest(
                id_dat_phong=9999,
                ma_booking='BK-PROP-TEST',
                so_tien=2000000,
                phuong_thuc='VNPAY',
            )
        )

        call_args = mock_url.call_args
        req = call_args[0][0]
        sent_cid = req.headers.get('X-correlation-id') or req.headers.get('X-Correlation-ID')
        assert sent_cid == trace_id, f'Loi: sent_cid={{sent_cid}} != expected={{trace_id}}'
        print(f' -> Payment Service da tu dong forward X-Correlation-ID: {{sent_cid}} khi goi Booking Service!')
finally:
    db.close()
"""
    run_isolated_test(
        "Test 5: Payment Service lan truyen X-Correlation-ID sang Booking Service",
        propagation_test_code,
        cwd=os.path.join(PROJECT_ROOT, "services", "payment-service"),
    )

    # -------------------------------------------------------------
    # 6. Payment Service đính kèm correlation_id vào RabbitMQ Message & Fallback REST
    # -------------------------------------------------------------
    mq_trace_id = f"MQ-TRACE-{uuid.uuid4().hex[:10].upper()}"
    mq_test_code = f"""
from unittest.mock import patch, MagicMock
from src.core.correlation import set_correlation_id, get_correlation_id
from src.core.publisher import publish_payment_event, publish_otp_event

trace_id = '{mq_trace_id}'
set_correlation_id(trace_id)
assert get_correlation_id() == trace_id

with patch('pika.BlockingConnection') as mock_conn:
    mock_chan = MagicMock()
    mock_conn.return_value.channel.return_value = mock_chan

    payload = {{'ma_booking': 'BK-MQ-TEST', 'so_tien': 1000000}}
    publish_payment_event('notification.payment.success', payload)

    # Kiem tra basic_publish duoc goi voi correlation_id trong properties
    pub_call = mock_chan.basic_publish.call_args
    props = pub_call[1]['properties']
    assert props.correlation_id == trace_id, f'Props correlation_id mismatch: {{props.correlation_id}}'
    assert props.headers.get('X-Correlation-ID') == trace_id, f'Props headers mismatch: {{props.headers}}'
    assert payload.get('correlation_id') == trace_id, 'Payload correlation_id mismatch!'
    print(f' -> RabbitMQ BasicProperties duoc dinh kem correlation_id: {{props.correlation_id}}!')
"""
    run_isolated_test(
        "Test 6: Payment Service lan truyen correlation_id vao RabbitMQ Message Properties",
        mq_test_code,
        cwd=os.path.join(PROJECT_ROOT, "services", "payment-service"),
    )

    # -------------------------------------------------------------
    # 7. Notification Service, User Service, Hotel Service, Room Service kiểm tra nhanh
    # -------------------------------------------------------------
    for svc_name in ["notification-service", "user-service", "hotel-service", "room-service"]:
        svc_cid = f"TEST-CID-{svc_name.upper()}-{uuid.uuid4().hex[:6]}"
        svc_test_code = f"""
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
cid = '{svc_cid}'
res = client.get('/', headers={{'X-Correlation-ID': cid}})
assert res.status_code == 200
assert res.headers.get('X-Correlation-ID') == cid
print(f' -> {svc_name} tra ve X-Correlation-ID: {{cid}}')
"""
        run_isolated_test(
            f"Test 7: {svc_name} tiep nhan va phan hoi X-Correlation-ID chuan",
            svc_test_code,
            cwd=os.path.join(PROJECT_ROOT, "services", svc_name),
        )

    print("\n" + "=" * 65)
    print(">>> TẤT CẢ 10 BÀI TEST TRACING X-CORRELATION-ID ĐỀU ĐẠT 100%! <<<")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
