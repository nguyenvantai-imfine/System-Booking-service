# -*- coding: utf-8 -*-
import sys
import os
import json
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
PAYMENT_SERVICE_DIR = os.path.join(PROJECT_ROOT, "services", "payment-service")

if PAYMENT_SERVICE_DIR not in sys.path:
    sys.path.insert(0, PAYMENT_SERVICE_DIR)

os.chdir(PAYMENT_SERVICE_DIR)

import jwt
from fastapi.testclient import TestClient
from src.main import app
from src.core.config import settings
from src.core.database import SessionLocal
from src.models import ThanhToanModel, GiaoDichOtpModel, TrangThaiThanhToanEnum
import src.services.payment_service as ps_module

def test_payment_reconciliation_and_sync_failure():
    print("=" * 70)
    print("BẮT ĐẦU TEST P1.3 & P1.4: ĐỐI SOÁT SỐ TIỀN & NHẤT QUÁN TRẠNG THÁI GIAO DỊCH")
    print("=" * 70)

    client = TestClient(app)
    token = jwt.encode(
        {"sub": "1", "role": "CUSTOMER", "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    client.headers["Authorization"] = f"Bearer {token}"
    admin_token = jwt.encode(
        {"sub": "1", "role": "ADMIN", "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    db = SessionLocal()

    # Track published RabbitMQ events
    published_events = []
    def mock_publish(event_name, data):
        published_events.append((event_name, data))

    ps_module.publish_payment_event = mock_publish
    ps_module.publish_otp_event = mock_publish

    # =========================================================================
    # CHECK 1: P1.3 - create_payment với số tiền lệch so với Booking Service
    # =========================================================================
    print("\n[TEST P1.3 - 1] Chặn tạo thanh toán khi số tiền không khớp giá trị đơn đặt phòng...")
    test_bk_id_1 = int(str(uuid.uuid4().int)[:6])
    booking_total_actual = 2500000.0
    tampered_amount = 1500000.0

    class MockHTTPResponse:
        def __init__(self, data, status=200):
            self.data = json.dumps(data).encode("utf-8")
            self.status = status
        def read(self):
            return self.data
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    booking_mock_data = {
        "id_dat_phong": test_bk_id_1,
        "ma_booking": f"BK-TEST-{test_bk_id_1}",
        "tong_tien": booking_total_actual,
        "trang_thai": "PENDING",
        "han_giu_cho": "2030-01-01T00:00:00Z",
    }

    def mock_urlopen_for_booking(req, timeout=3.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if f"/bookings/{test_bk_id_1}" in url:
            return MockHTTPResponse(booking_mock_data, status=200)
        raise ConnectionRefusedError("Mock connection refused")

    with patch("urllib.request.urlopen", side_effect=mock_urlopen_for_booking):
        # Gửi số tiền 1,500,000 đ trong khi đơn hàng là 2,500,000 đ
        mismatch_res = client.post("/api/v1/payments/create-payment", json={
            "id_dat_phong": test_bk_id_1,
            "ma_booking": f"BK-TEST-{test_bk_id_1}",
            "so_tien": tampered_amount,
            "phuong_thuc": "VNPAY",
            "ghi_chu": "Thanh toan gia lech",
        })

        assert mismatch_res.status_code == 400, f"Kỳ vọng 400, nhận: {mismatch_res.status_code} ({mismatch_res.text})"
        err_detail = mismatch_res.json().get("detail", "")
        expected_msg = f"Số tiền thanh toán ({Decimal(str(tampered_amount)):,.0f} đ) không khớp với giá trị đơn đặt phòng ({Decimal(str(booking_total_actual)):,.0f} đ)."
        assert expected_msg in err_detail, f"Thông báo lỗi không khớp!\nKỳ vọng: {expected_msg}\nThực tế: {err_detail}"
        print(f" -> [PASS] Số tiền lệch bị từ chối 400: '{err_detail}'")

    # =========================================================================
    # CHECK 2: P1.3 - create_payment với số tiền khớp hoàn toàn
    # =========================================================================
    print("\n[TEST P1.3 - 2] Tạo thanh toán thành công khi số tiền khớp chính xác...")
    with patch("urllib.request.urlopen", side_effect=mock_urlopen_for_booking):
        match_res = client.post("/api/v1/payments/create-payment", json={
            "id_dat_phong": test_bk_id_1,
            "ma_booking": f"BK-TEST-{test_bk_id_1}",
            "so_tien": booking_total_actual,
            "phuong_thuc": "VNPAY",
            "ghi_chu": "Thanh toan dung gia",
        })

        assert match_res.status_code == 201, f"Tạo thanh toán thất bại: {match_res.text}"
        payment_data = match_res.json()
        txn_match = payment_data["ma_giao_dich_gateway"]
        assert payment_data["trang_thai"] == "PENDING"
        assert float(payment_data["so_tien"]) == booking_total_actual
        print(f" -> [PASS] Tạo thành công giao dịch {txn_match} với trạng thái PENDING.")

    # =========================================================================
    # CHECK 3: P1.4 - Xác thực OTP khi Booking Service sập (SYNC_FAILED)
    # =========================================================================
    print("\n[TEST P1.4 - 3] Xác thực OTP khi Booking Service sập: Trạng thái chuyển SYNC_FAILED...")
    # Sinh OTP cho giao dịch
    captured_otps = {}
    def hook_otp(event_name, data):
        if "otp_code" in data and "ma_giao_dich_gateway" in data:
            captured_otps[data["ma_giao_dich_gateway"]] = data["otp_code"]
        published_events.append((event_name, data))
    ps_module.publish_otp_event = hook_otp

    otp_res = client.post("/api/v1/payments/generate-otp", json={
        "ma_giao_dich_gateway": txn_match,
        "email": "customer@example.com",
    })
    assert otp_res.status_code == 200, f"Generate OTP thất bại: {otp_res.text}"
    raw_otp = captured_otps.get(txn_match)
    assert raw_otp, "Không bắt được mã raw_otp qua event!"

    # Giả lập confirm_booking_with_retry thất bại (Booking Service bị tắt đột ngột)
    retry_call_count = 0
    def mock_confirm_fail(id_dat_phong, note, max_retries=3, initial_delay=0.01):
        nonlocal retry_call_count
        retry_call_count += 1
        return False

    orig_confirm = ps_module.PaymentService.confirm_booking_with_retry
    ps_module.PaymentService.confirm_booking_with_retry = staticmethod(mock_confirm_fail)

    published_events.clear()
    try:
        verify_fail_res = client.post("/api/v1/payments/verify-otp", json={
            "ma_giao_dich_gateway": txn_match,
            "otp_code": raw_otp,
        })
        assert verify_fail_res.status_code == 200, f"Verify OTP lỗi: {verify_fail_res.text}"
        res_data = verify_fail_res.json()
        assert res_data["trang_thai"] == "SYNC_FAILED", f"Kỳ vọng SYNC_FAILED, nhận {res_data['trang_thai']}"
        expected_note = "Thanh toán thành công nhưng chưa thể cập nhật Booking Service. Chờ đối soát tự động."
        assert res_data["ghi_chu"] == expected_note, f"Ghi chú sai: {res_data['ghi_chu']}"

        # Kiểm tra DB
        db.expire_all()
        db_txn = db.query(ThanhToanModel).filter(ThanhToanModel.ma_giao_dich_gateway == txn_match).first()
        assert db_txn.trang_thai == "SYNC_FAILED"
        assert db_txn.ghi_chu == expected_note

        # Kiểm tra event notification.payment.sync_failed được bắn
        event_names = [e[0] for e in published_events]
        assert "notification.payment.sync_failed" in event_names, f"Thiếu event sync_failed! Events: {event_names}"
        print(f" -> [PASS] Trạng thái được ghi nhận chính xác: SYNC_FAILED, ghi chú đối soát đầy đủ, event sync_failed đã bắn.")
    finally:
        ps_module.PaymentService.confirm_booking_with_retry = orig_confirm

    # =========================================================================
    # CHECK 4: P1.4 - Xác thực OTP khi Booking Service hoạt động tốt (SUCCESS)
    # =========================================================================
    print("\n[TEST P1.4 - 4] Xác thực OTP khi Booking Service đồng bộ thành công (SUCCESS)...")
    test_bk_id_2 = int(str(uuid.uuid4().int)[:6])
    booking_mock_data_2 = {
        "id_dat_phong": test_bk_id_2,
        "ma_booking": f"BK-TEST-{test_bk_id_2}",
        "tong_tien": 1800000.0,
        "trang_thai": "PENDING",
        "han_giu_cho": "2030-01-01T00:00:00Z",
    }
    def mock_urlopen_2(req, timeout=3.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if f"/bookings/{test_bk_id_2}" in url:
            return MockHTTPResponse(booking_mock_data_2, status=200)
        raise ConnectionRefusedError("Mock connection refused")

    with patch("urllib.request.urlopen", side_effect=mock_urlopen_2):
        create_res_2 = client.post("/api/v1/payments/create-payment", json={
            "id_dat_phong": test_bk_id_2,
            "ma_booking": f"BK-TEST-{test_bk_id_2}",
            "so_tien": 1800000.0,
            "phuong_thuc": "MOMO",
        })
        assert create_res_2.status_code == 201
        txn_success = create_res_2.json()["ma_giao_dich_gateway"]

    otp_res_2 = client.post("/api/v1/payments/generate-otp", json={
        "ma_giao_dich_gateway": txn_success,
        "email": "customer2@example.com",
    })
    raw_otp_2 = captured_otps.get(txn_success)

    # Giả lập confirm_booking_with_retry thành công
    ps_module.PaymentService.confirm_booking_with_retry = staticmethod(lambda id_dp, note, max_retries=3, initial_delay=0.01: True)
    published_events.clear()
    try:
        verify_success_res = client.post("/api/v1/payments/verify-otp", json={
            "ma_giao_dich_gateway": txn_success,
            "otp_code": raw_otp_2,
        })
        assert verify_success_res.status_code == 200
        res_data_2 = verify_success_res.json()
        assert res_data_2["trang_thai"] == "SUCCESS", f"Kỳ vọng SUCCESS, nhận {res_data_2['trang_thai']}"
        event_names = [e[0] for e in published_events]
        assert "notification.payment.success" in event_names, f"Thiếu event payment.success! Events: {event_names}"
        print(f" -> [PASS] Giao dịch xác thực thành công chuyển trạng thái SUCCESS và bắn event payment.success.")
    finally:
        ps_module.PaymentService.confirm_booking_with_retry = orig_confirm

    # =========================================================================
    # CHECK 5: P1.4 - simulate-ipn khi Booking Service lỗi (SYNC_FAILED)
    # =========================================================================
    print("\n[TEST P1.4 - 5] simulate-ipn khi Booking Service lỗi: Trạng thái chuyển SYNC_FAILED...")
    test_bk_id_3 = int(str(uuid.uuid4().int)[:6])
    booking_mock_data_3 = {
        "id_dat_phong": test_bk_id_3,
        "ma_booking": f"BK-TEST-{test_bk_id_3}",
        "tong_tien": 3000000.0,
        "trang_thai": "PENDING",
        "han_giu_cho": "2030-01-01T00:00:00Z",
    }
    def mock_urlopen_3(req, timeout=3.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if f"/bookings/{test_bk_id_3}" in url:
            return MockHTTPResponse(booking_mock_data_3, status=200)
        raise ConnectionRefusedError("Mock connection refused")

    with patch("urllib.request.urlopen", side_effect=mock_urlopen_3):
        create_res_3 = client.post("/api/v1/payments/create-payment", json={
            "id_dat_phong": test_bk_id_3,
            "ma_booking": f"BK-TEST-{test_bk_id_3}",
            "so_tien": 3000000.0,
            "phuong_thuc": "VNPAY",
        })
        assert create_res_3.status_code == 201
        txn_ipn = create_res_3.json()["ma_giao_dich_gateway"]

    # Giả lập confirm_booking_with_retry trả về False
    ps_module.PaymentService.confirm_booking_with_retry = staticmethod(lambda id_dp, note, max_retries=3, initial_delay=0.01: False)
    published_events.clear()
    try:
        ipn_fail_res = client.post("/api/v1/payments/simulate-ipn", json={
            "ma_giao_dich_gateway": txn_ipn,
            "trang_thai": "SUCCESS",
            "note": "IPN callback VNPay",
        })
        assert ipn_fail_res.status_code == 200
        ipn_data = ipn_fail_res.json()
        assert ipn_data["trang_thai"] == "SYNC_FAILED", f"Kỳ vọng SYNC_FAILED, nhận: {ipn_data['trang_thai']}"
        expected_note = "Thanh toán thành công nhưng chưa thể cập nhật Booking Service. Chờ đối soát tự động."
        assert ipn_data["ghi_chu"] == expected_note
        event_names = [e[0] for e in published_events]
        assert "notification.payment.sync_failed" in event_names
        print(f" -> [PASS] IPN khi Booking Service lỗi ghi nhận SYNC_FAILED chính xác.")
    finally:
        ps_module.PaymentService.confirm_booking_with_retry = orig_confirm

    # =========================================================================
    # CHECK 6: P1.4 - simulate-ipn khi Booking Service thành công (SUCCESS)
    # =========================================================================
    print("\n[TEST P1.4 - 6] simulate-ipn khi Booking Service thành công (SUCCESS)...")
    test_bk_id_4 = int(str(uuid.uuid4().int)[:6])
    booking_mock_data_4 = {
        "id_dat_phong": test_bk_id_4,
        "ma_booking": f"BK-TEST-{test_bk_id_4}",
        "tong_tien": 950000.0,
        "trang_thai": "PENDING",
        "han_giu_cho": "2030-01-01T00:00:00Z",
    }
    def mock_urlopen_4(req, timeout=3.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if f"/bookings/{test_bk_id_4}" in url:
            return MockHTTPResponse(booking_mock_data_4, status=200)
        raise ConnectionRefusedError("Mock connection refused")

    with patch("urllib.request.urlopen", side_effect=mock_urlopen_4):
        create_res_4 = client.post("/api/v1/payments/create-payment", json={
            "id_dat_phong": test_bk_id_4,
            "ma_booking": f"BK-TEST-{test_bk_id_4}",
            "so_tien": 950000.0,
            "phuong_thuc": "MOMO",
        })
        assert create_res_4.status_code == 201
        txn_ipn_success = create_res_4.json()["ma_giao_dich_gateway"]

    ps_module.PaymentService.confirm_booking_with_retry = staticmethod(lambda id_dp, note, max_retries=3, initial_delay=0.01: True)
    published_events.clear()
    try:
        ipn_ok_res = client.post("/api/v1/payments/simulate-ipn", json={
            "ma_giao_dich_gateway": txn_ipn_success,
            "trang_thai": "SUCCESS",
            "note": "IPN MOMO sandbox",
        })
        assert ipn_ok_res.status_code == 200
        assert ipn_ok_res.json()["trang_thai"] == "SUCCESS"
        event_names = [e[0] for e in published_events]
        assert "notification.payment.success" in event_names
        print(f" -> [PASS] IPN thành công chuyển trạng thái SUCCESS và publish event.")
    finally:
        ps_module.PaymentService.confirm_booking_with_retry = orig_confirm

    # =========================================================================
    # CHECK 7: GET /api/v1/payments/stats có sync_failed_count
    # =========================================================================
    print("\n[TEST P1.4 - 7] Kiểm tra API thống kê /payments/stats trả về sync_failed_count...")
    client.headers["Authorization"] = f"Bearer {admin_token}"
    stats_res = client.get("/api/v1/payments/stats")
    assert stats_res.status_code == 200, f"Stats error: {stats_res.text}"
    stats_data = stats_res.json()
    assert "sync_failed_count" in stats_data, f"Thiếu sync_failed_count trong stats response: {stats_data}"
    assert stats_data["sync_failed_count"] >= 2, f"sync_failed_count phải >= 2, thực tế: {stats_data['sync_failed_count']}"
    print(f" -> [PASS] Thống kê phản ánh đúng số giao dịch SYNC_FAILED: {stats_data['sync_failed_count']}")

    print("\n" + "=" * 70)
    print(">>> TẤT CẢ 7/7 KIỂM TRA P1.3 & P1.4 ĐÃ HOÀN THÀNH XUẤT SẮC!")
    print("=" * 70)

if __name__ == "__main__":
    test_payment_reconciliation_and_sync_failure()
