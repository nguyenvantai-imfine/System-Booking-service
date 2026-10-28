# -*- coding: utf-8 -*-
import sys
import os
import json
import uuid
from unittest.mock import patch, MagicMock

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
NOTIF_SERVICE_DIR = os.path.join(PROJECT_ROOT, "services", "notification-service")

if NOTIF_SERVICE_DIR not in sys.path:
    sys.path.insert(0, NOTIF_SERVICE_DIR)

os.chdir(NOTIF_SERVICE_DIR)

from fastapi.testclient import TestClient
from src.main import app
from src.core.config import settings
from src.core.database import SessionLocal
from src.core.email_sender import EmailSender

def test_internal_notifications_and_smtp_configuration():
    print("=" * 70)
    print("BẮT ĐẦU TEST P2.4 & P2.5: REST FALLBACK NỘI BỘ VÀ CẤU HÌNH GỬI EMAIL SMTP")
    print("=" * 70)

    client = TestClient(app)

    # =========================================================================
    # CHECK 1: Kiểm tra bảo mật endpoint POST /api/v1/notifications/internal-send
    # =========================================================================
    print("\n[CHECK 1] Kiểm tra xác thực qua X-Internal-Secret tại /internal-send...")
    payload = {
        "loai_thong_bao": "BOOKING_CONFIRMED",
        "nguoi_nhan": "guest.internal@gmail.com",
        "kenh_gui": "EMAIL",
        "ma_booking": "BK-INTERNAL-001",
        "du_lieu": {
            "ten_khach": "Nguyen Van A",
            "ma_booking": "BK-INTERNAL-001",
            "ten_khach_san": "Khach san Bien Xanh",
            "ngay_nhan": "2026-11-01",
            "ngay_tra": "2026-11-03",
            "so_phong": "P.301",
            "tong_tien": 2400000,
        },
    }

    # 1.1 Gọi không có Header X-Internal-Secret -> Phải nhận 403 Forbidden
    res_no_secret = client.post("/api/v1/notifications/internal-send", json=payload)
    assert res_no_secret.status_code == 403, f"Kỳ vọng 403 khi thiếu secret, nhận: {res_no_secret.status_code}"
    print(f" -> [PASS] Không có X-Internal-Secret bị chặn 403: {res_no_secret.json().get('detail')}")

    # 1.2 Gọi với X-Internal-Secret sai -> Phải nhận 403 Forbidden
    res_bad_secret = client.post(
        "/api/v1/notifications/internal-send",
        json=payload,
        headers={"X-Internal-Secret": "sai_secret_roi_123"},
    )
    assert res_bad_secret.status_code == 403, f"Kỳ vọng 403 khi sai secret, nhận: {res_bad_secret.status_code}"
    print(f" -> [PASS] X-Internal-Secret sai bị chặn 403: {res_bad_secret.json().get('detail')}")

    # 1.3 Gọi với X-Internal-Secret đúng -> Thành công 201 Created mà KHÔNG CẦN JWT Token
    res_ok = client.post(
        "/api/v1/notifications/internal-send",
        json=payload,
        headers={
            "X-Internal-Secret": settings.INTERNAL_SERVICE_SECRET,
            "X-Correlation-ID": "cid-test-123456",
        },
    )
    assert res_ok.status_code == 201, f"Kỳ vọng 201 khi đúng secret, nhận: {res_ok.status_code} ({res_ok.text})"
    data_ok = res_ok.json()
    assert data_ok["loai_thong_bao"] == "BOOKING_CONFIRMED"
    assert data_ok["nguoi_nhan"] == "guest.internal@gmail.com"
    assert data_ok["trang_thai"] in ("SENT", "PENDING")
    print(f" -> [PASS] Gửi thông báo nội bộ thành công với 201 Created (ID: {data_ok['id_thong_bao']})")

    # =========================================================================
    # CHECK 2: Kiểm tra REST Fallback từ Booking Service
    # =========================================================================
    import importlib.util
    bk_config_file = os.path.join(PROJECT_ROOT, "services", "booking-service", "src", "core", "config.py")
    spec_bk_cfg = importlib.util.spec_from_file_location("booking_config", bk_config_file)
    bk_cfg = importlib.util.module_from_spec(spec_bk_cfg)
    spec_bk_cfg.loader.exec_module(bk_cfg)

    bk_publisher_file = os.path.join(PROJECT_ROOT, "services", "booking-service", "src", "core", "publisher.py")
    spec_bk = importlib.util.spec_from_file_location("booking_publisher", bk_publisher_file)
    bk_pub = importlib.util.module_from_spec(spec_bk)
    spec_bk.loader.exec_module(bk_pub)
    bk_pub.settings = bk_cfg.settings

    captured_bk_requests = []

    class MockHTTPResponse:
        def __init__(self, status=201):
            self.status = status
        def read(self):
            return b'{"status": "ok"}'
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    def mock_urlopen_bk(req, timeout=3):
        captured_bk_requests.append(req)
        return MockHTTPResponse(201)

    # Giả lập pika kết nối thất bại -> buộc chạy vào nhánh REST Fallback
    with patch("pika.BlockingConnection", side_effect=Exception("RabbitMQ Connection Refused")):
        with patch("urllib.request.urlopen", side_effect=mock_urlopen_bk):
            bk_payload = {
                "id_dat_phong": 901,
                "ma_booking": "BK-FALLBACK-901",
                "email": "customer.bk@example.com",
                "tong_tien": 3500000,
            }
            bk_pub.publish_notification_event("notification.booking.confirmed", bk_payload)

    assert len(captured_bk_requests) == 1, "Booking Service không gọi REST Fallback!"
    req_sent = captured_bk_requests[0]
    assert "/notifications/internal-send" in req_sent.full_url, f"Sai URL fallback: {req_sent.full_url}"
    assert req_sent.headers.get("X-internal-secret") == bk_cfg.settings.INTERNAL_SERVICE_SECRET, "Thiếu header X-Internal-Secret!"
    print(f" -> [PASS] Booking Service fallback gọi đúng: {req_sent.full_url} với X-Internal-Secret.")

    # =========================================================================
    # CHECK 3: Kiểm tra REST Fallback từ Payment Service (Payment & OTP)
    # =========================================================================
    print("\n[CHECK 3] Kiểm tra Payment Service REST Fallback (Payment Success & OTP)...")
    pm_config_file = os.path.join(PROJECT_ROOT, "services", "payment-service", "src", "core", "config.py")
    spec_pm_cfg = importlib.util.spec_from_file_location("payment_config", pm_config_file)
    pm_cfg = importlib.util.module_from_spec(spec_pm_cfg)
    spec_pm_cfg.loader.exec_module(pm_cfg)

    pm_publisher_file = os.path.join(PROJECT_ROOT, "services", "payment-service", "src", "core", "publisher.py")
    spec_pm = importlib.util.spec_from_file_location("payment_publisher", pm_publisher_file)
    pm_pub = importlib.util.module_from_spec(spec_pm)
    spec_pm.loader.exec_module(pm_pub)
    pm_pub.settings = pm_cfg.settings

    captured_pm_requests = []

    def mock_urlopen_pm(req, timeout=3):
        captured_pm_requests.append(req)
        return MockHTTPResponse(201)

    # 3.1 Test fallback cho Payment Event
    with patch("pika.BlockingConnection", side_effect=Exception("RabbitMQ Down")):
        with patch("urllib.request.urlopen", side_effect=mock_urlopen_pm):
            pm_pub.publish_payment_event("notification.payment.success", {
                "ma_booking": "BK-PM-902",
                "email": "customer.pm@example.com",
                "so_tien": 1200000,
            })

    assert len(captured_pm_requests) == 1
    pm_req1 = captured_pm_requests[0]
    assert "/notifications/internal-send" in pm_req1.full_url
    assert pm_req1.headers.get("X-internal-secret") == settings.INTERNAL_SERVICE_SECRET
    print(f" -> [PASS] Payment Success fallback gọi đúng /internal-send kèm X-Internal-Secret.")

    # 3.2 Test fallback cho OTP Event
    captured_pm_requests.clear()
    with patch("pika.BlockingConnection", side_effect=Exception("RabbitMQ Down")):
        with patch("urllib.request.urlopen", side_effect=mock_urlopen_pm):
            pm_pub.publish_otp_event("notification.otp.generated", {
                "ma_booking": "BK-OTP-903",
                "email": "customer.otp@example.com",
                "otp_code": "889900",
                "expires_in_seconds": 180,
            })

    assert len(captured_pm_requests) == 1
    pm_req2 = captured_pm_requests[0]
    assert "/notifications/internal-send" in pm_req2.full_url
    assert pm_req2.headers.get("X-internal-secret") == settings.INTERNAL_SERVICE_SECRET
    print(f" -> [PASS] Payment OTP fallback gọi đúng /internal-send kèm X-Internal-Secret.")

    # =========================================================================
    # CHECK 4: Kiểm tra EmailSender (Mock Mode vs Real SMTP Mode)
    # =========================================================================
    print("\n[CHECK 4] Kiểm tra logic EmailSender: Chế độ Mock vs Real SMTP...")
    # 4.1 Mock Mode (Mặc định)
    settings.USE_MOCK_EMAIL = True
    ok, msg = EmailSender.send_email(
        to_email="test.mock@example.com",
        subject="Thử nghiệm Mock Email",
        html_content="<p>Xin chào</p>",
        text_content="Xin chào",
    )
    assert ok is True
    assert "Simulation/Mock mode" in msg
    print(f" -> [PASS] Chế độ Mock trả về thành công mô phỏng.")

    # 4.2 Real SMTP Mode (Cấu hình USE_MOCK_EMAIL = False, port 587 STARTTLS)
    settings.USE_MOCK_EMAIL = False
    settings.MOCK_EMAIL_SEND = False
    settings.SMTP_HOST = "smtp.mailserver.test"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = "mailer@mailserver.test"
    settings.SMTP_PASSWORD = "secret_smtp_password"
    settings.SMTP_TLS = True

    mock_smtp_instance = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_instance) as mock_smtp_cls:
        ok_real, msg_real = EmailSender.send_email(
            to_email="customer.real@gmail.com",
            subject="Xác nhận đặt phòng thành công",
            html_content="<h1>Kính chào quý khách</h1>",
            text_content="Kính chào quý khách",
        )
        assert ok_real is True
        assert "successfully via SMTP" in msg_real
        mock_smtp_cls.assert_called_once_with("smtp.mailserver.test", 587, timeout=10)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("mailer@mailserver.test", "secret_smtp_password")
        mock_smtp_instance.sendmail.assert_called_once()
        mock_smtp_instance.quit.assert_called_once()
        print(f" -> [PASS] Chế độ Real SMTP 587 STARTTLS hoạt động chuẩn xác (starttls, login, sendmail, quit).")

    # 4.3 Real SMTP Mode (port 465 SSL)
    settings.SMTP_PORT = 465
    mock_ssl_instance = MagicMock()
    with patch("smtplib.SMTP_SSL", return_value=mock_ssl_instance) as mock_ssl_cls:
        ok_ssl, msg_ssl = EmailSender.send_email(
            to_email="customer.ssl@gmail.com",
            subject="Xác thực OTP",
            html_content="<h1>Mã OTP</h1>",
            text_content="Mã OTP",
        )
        assert ok_ssl is True
        mock_ssl_cls.assert_called_once_with("smtp.mailserver.test", 465, timeout=10)
        mock_ssl_instance.login.assert_called_once_with("mailer@mailserver.test", "secret_smtp_password")
        mock_ssl_instance.sendmail.assert_called_once()
        mock_ssl_instance.quit.assert_called_once()
        print(f" -> [PASS] Chế độ Real SMTP 465 SSL hoạt động chuẩn xác (SMTP_SSL, login, sendmail, quit).")

    # Reset về mock mode an toàn sau test
    settings.USE_MOCK_EMAIL = True
    settings.MOCK_EMAIL_SEND = True

    print("\n" + "=" * 70)
    print(">>> TẤT CẢ CÁC KIỂM TRA P2.4 & P2.5 ĐỀU ĐẠT 100%!")
    print("=" * 70)

if __name__ == "__main__":
    test_internal_notifications_and_smtp_configuration()
