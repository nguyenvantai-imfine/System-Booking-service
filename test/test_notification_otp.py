# -*- coding: utf-8 -*-
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
NOTIF_SERVICE_DIR = os.path.join(PROJECT_ROOT, "services", "notification-service")
PAYMENT_SERVICE_DIR = os.path.join(PROJECT_ROOT, "services", "payment-service")

if NOTIF_SERVICE_DIR not in sys.path:
    sys.path.insert(0, NOTIF_SERVICE_DIR)

os.chdir(NOTIF_SERVICE_DIR)

from fastapi.testclient import TestClient
from src.main import app as notif_app
from src.core.database import SessionLocal
from src.models.thong_bao import ThongBaoModel
from src.models.noi_dung_thong_bao import NoiDungThongBaoModel
from src.core.templates import render_otp_email
from src.services.notification_service import NotificationService

def test_notification_otp():
    print(">>> [TEST START] Checking Notification Service OTP Email...")
    client = TestClient(notif_app)
    import jwt
    from src.core.config import settings
    token = jwt.encode(
        {"sub": "1", "role": "CUSTOMER", "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    client.headers["Authorization"] = f"Bearer {token}"

    # 1. Test template render_otp_email
    test_payload = {
        "email": "customer@hotel.com",
        "otp_code": "849201",
        "ma_giao_dich_gateway": "VNPAY-20261023-TEST",
        "ma_booking": "BK-202610-TEST",
        "expires_in_seconds": 180,
    }
    subject, html_content, text_content = render_otp_email(test_payload)
    assert "849201" in subject, "Subject phai chua ma OTP"
    assert "849201" in html_content, "HTML email phai chua ma OTP 6 chu so"
    assert "3 phút" in html_content or "180 giây" in html_content, "HTML phai canh bao het han"
    assert "chia sẻ mã" in html_content and "KHÔNG" in html_content, "HTML phai co huong dan bao mat"
    print("[PASS] Check 1: render_otp_email renders elegant HTML, large OTP & security warnings.")

    # 2. Test REST endpoint /api/v1/notifications/send with loai_thong_bao='OTP'
    send_res = client.post("/api/v1/notifications/send", json={
        "loai_thong_bao": "OTP",
        "nguoi_nhan": "customer_otp@test.com",
        "kenh_gui": "EMAIL",
        "ma_booking": "BK-202610-TEST",
        "du_lieu": test_payload
    })
    assert send_res.status_code == 201, f"Loi send OTP notification: {send_res.text}"
    sent_data = send_res.json()
    assert sent_data["loai_thong_bao"] == "OTP"
    assert sent_data["trang_thai"] == "SENT"
    notif_id = sent_data["id_thong_bao"]
    print(f"[PASS] Check 2: REST /send successfully created OTP notification ID {notif_id}.")

    # 3. Kiem tra DB: khong luu ma OTP ro trong CSDL (phai duoc che)
    db = SessionLocal()
    saved_noi_dung = db.query(NoiDungThongBaoModel).filter(NoiDungThongBaoModel.id_thong_bao == notif_id).first()
    assert saved_noi_dung is not None
    assert "849201" not in saved_noi_dung.tieu_de, "Ma OTP ro khong duoc luu trong tieu de CSDL!"
    assert "849201" not in saved_noi_dung.noi_dung_html, "Ma OTP ro khong duoc luu truc tiep trong noi dung HTML CSDL!"
    assert "84****" in saved_noi_dung.noi_dung_html or "******" in saved_noi_dung.noi_dung_html, "Ma OTP phai duoc che trong CSDL"
    assert "849201" not in saved_noi_dung.du_lieu_dinh_kem, "Ma OTP ro khong duoc luu trong du_lieu_dinh_kem!"
    print("[PASS] Check 3: OTP is securely masked in database persistent storage (tieu_de, html, du_lieu).")

    # 4. Test MQ Event Handler: notification.otp.generated
    mq_payload = {
        "email": "mq_user@test.com",
        "otp_code": "339911",
        "ma_giao_dich_gateway": "MOMO-20261023-MQ",
        "ma_booking": "BK-202610-MQ",
        "expires_in_seconds": 180,
    }
    NotificationService.handle_message_queue_event("notification.otp.generated", mq_payload)

    mq_record = (
        db.query(ThongBaoModel)
        .filter(ThongBaoModel.nguoi_nhan == "mq_user@test.com")
        .order_by(ThongBaoModel.id_thong_bao.desc())
        .first()
    )
    assert mq_record is not None
    assert mq_record.loai_thong_bao == "OTP"
    assert mq_record.trang_thai == "SENT"
    print(f"[PASS] Check 4: RabbitMQ event notification.otp.generated processed, created notification ID {mq_record.id_thong_bao}.")

    # 5. Kiem tra chong XSS trong cac template email
    from src.core.templates import render_booking_confirmed_email, render_booking_cancelled_email
    xss_payload = {
        "ten_khach": "<script>alert(1)</script>",
        "ten_khach_san": "Hotel <b>Bold</b>",
        "dia_chi": "<img src=x onerror=alert(2)>",
        "ma_booking": "BK-XSS<tag>",
        "danh_sach_phong": [{"so_phong": "P101<script>", "ten_loai_phong": "Deluxe<img>"}]
    }
    _, xss_html, _ = render_booking_confirmed_email(xss_payload)
    assert "<script>alert(1)</script>" not in xss_html, "HTML chua chuoi chua escape script!"
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in xss_html, "HTML phai escape &lt;script&gt;!"
    assert "&lt;img src=x onerror=alert(2)&gt;" in xss_html
    print("[PASS] Check 5: HTML email templates properly escape dynamic variables against XSS.")

    # 6. Don dep du lieu test
    db.query(ThongBaoModel).filter(ThongBaoModel.id_thong_bao.in_([notif_id, mq_record.id_thong_bao])).delete(synchronize_session=False)
    db.commit()
    db.close()
    print("==================================================")
    print(">>> ALL NOTIFICATION SERVICE TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_notification_otp()
