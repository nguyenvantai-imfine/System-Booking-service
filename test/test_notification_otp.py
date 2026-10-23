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
    assert "849201" not in saved_noi_dung.noi_dung_html, "Ma OTP ro khong duoc luu truc tiep trong noi dung HTML CSDL!"
    assert "84****" in saved_noi_dung.noi_dung_html or "******" in saved_noi_dung.noi_dung_html, "Ma OTP phai duoc che trong CSDL"
    assert "849201" not in saved_noi_dung.du_lieu_dinh_kem, "Ma OTP ro khong duoc luu trong du_lieu_dinh_kem!"
    print("[PASS] Check 3: OTP is securely masked in database persistent storage.")

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

    # 5. Don dep du lieu test
    db.query(ThongBaoModel).filter(ThongBaoModel.id_thong_bao.in_([notif_id, mq_record.id_thong_bao])).delete(synchronize_session=False)
    db.commit()
    db.close()
    print("==================================================")
    print(">>> ALL NOTIFICATION SERVICE OTP TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_notification_otp()
