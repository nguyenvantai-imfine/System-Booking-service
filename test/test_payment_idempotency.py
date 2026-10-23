# -*- coding: utf-8 -*-
import sys
import os
import uuid
import concurrent.futures

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

from fastapi.testclient import TestClient
from src.main import app
from src.core.database import SessionLocal
from src.models import ThanhToanModel, GiaoDichOtpModel, TrangThaiThanhToanEnum

def test_payment_idempotency_and_double_payment_prevention():
    client = TestClient(app)
    db = SessionLocal()

    print("\n" + "=" * 60)
    print("BẮT ĐẦU TEST CHỐNG THANH TOÁN TRÙNG & IDEMPOTENCY TRONG PAYMENT-SERVICE")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. Test Idempotency: Gửi 2 lần create-payment cùng X-Idempotency-Key
    # -------------------------------------------------------------
    idem_key = f"IDEM-{uuid.uuid4().hex[:12].upper()}"
    test_booking_id = int(str(uuid.uuid4().int)[:6])
    test_booking_code = f"BK-TEST-{test_booking_id}"
    amount = 2500000.0

    print(f"\n[Test 1] Gửi 2 lần create-payment cùng X-Idempotency-Key: {idem_key}")
    headers = {"X-Idempotency-Key": idem_key}
    payload = {
        "id_dat_phong": test_booking_id,
        "ma_booking": test_booking_code,
        "so_tien": amount,
        "phuong_thuc": "VNPAY",
        "ghi_chu": "Test idempotency lần 1",
    }

    # Request lần 1
    res1 = client.post("/api/v1/payments/create-payment", json=payload, headers=headers)
    assert res1.status_code == 201, f"Lần 1 thất bại: {res1.text}"
    data1 = res1.json()
    txn1 = data1["ma_giao_dich_gateway"]
    id_tt1 = data1["id_thanh_toan"]
    assert data1["idempotency_key"] == idem_key, "idempotency_key không được lưu đúng!"
    print(f" -> Lần 1 thành công: id_thanh_toan={id_tt1}, ma_giao_dich_gateway={txn1}")

    # Request lần 2 (cùng key, cùng payload)
    res2 = client.post("/api/v1/payments/create-payment", json=payload, headers=headers)
    assert res2.status_code in [200, 201], f"Lần 2 thất bại: {res2.text}"
    data2 = res2.json()
    txn2 = data2["ma_giao_dich_gateway"]
    id_tt2 = data2["id_thanh_toan"]
    print(f" -> Lần 2 trả về: id_thanh_toan={id_tt2}, ma_giao_dich_gateway={txn2}")

    assert id_tt1 == id_tt2, "Idempotency thất bại: tạo ra 2 bản ghi khác nhau!"
    assert txn1 == txn2, "Idempotency thất bại: ma_giao_dich_gateway không trùng khớp!"

    # Kiểm tra trực tiếp trong DB: chỉ có duy nhất 1 bản ghi mang key này
    count_records = (
        db.query(ThanhToanModel)
        .filter(ThanhToanModel.idempotency_key == idem_key)
        .count()
    )
    assert count_records == 1, f"DB tồn tại {count_records} bản ghi mang cùng key {idem_key}!"
    print(f"[PASS] Test 1: Gửi 2 lần cùng X-Idempotency-Key chỉ tạo đúng 1 bản ghi duy nhất trong DB.")

    # -------------------------------------------------------------
    # 2. Test Idempotency Conflict: Cùng X-Idempotency-Key nhưng khác số tiền hoặc id_dat_phong
    # -------------------------------------------------------------
    print(f"\n[Test 2] Kiểm tra xung đột Idempotency (cùng key nhưng khác số tiền / booking)")
    # Khác số tiền
    conflict_payload_amount = {
        "id_dat_phong": test_booking_id,
        "ma_booking": test_booking_code,
        "so_tien": amount + 500000,  # Sai số tiền
        "phuong_thuc": "VNPAY",
    }
    res_conflict_amt = client.post("/api/v1/payments/create-payment", json=conflict_payload_amount, headers=headers)
    assert res_conflict_amt.status_code == 409, f"Kỳ vọng 409 Conflict, nhận: {res_conflict_amt.status_code} ({res_conflict_amt.text})"
    print(f" -> Sai số tiền nhận đúng 409: {res_conflict_amt.json().get('detail')}")

    # Khác id_dat_phong
    conflict_payload_id = {
        "id_dat_phong": test_booking_id + 1,  # Sai id_dat_phong
        "ma_booking": f"BK-TEST-{test_booking_id + 1}",
        "so_tien": amount,
        "phuong_thuc": "VNPAY",
    }
    res_conflict_id = client.post("/api/v1/payments/create-payment", json=conflict_payload_id, headers=headers)
    assert res_conflict_id.status_code == 409, f"Kỳ vọng 409 Conflict, nhận: {res_conflict_id.status_code} ({res_conflict_id.text})"
    print(f" -> Sai id_dat_phong nhận đúng 409: {res_conflict_id.json().get('detail')}")
    print("[PASS] Test 2: Cùng key nhưng khác số tiền hoặc đơn đặt phòng bị từ chối 409 Conflict chính xác.")

    # -------------------------------------------------------------
    # 3. Test Cho phép nhiều bản ghi NULL idempotency_key (Filtered Unique Index)
    # -------------------------------------------------------------
    print(f"\n[Test 3] Kiểm tra Filtered Unique Index cho phép nhiều giao dịch không có X-Idempotency-Key")
    null_bk_1 = int(str(uuid.uuid4().int)[:6])
    null_bk_2 = int(str(uuid.uuid4().int)[:6])
    res_null1 = client.post("/api/v1/payments/create-payment", json={
        "id_dat_phong": null_bk_1,
        "ma_booking": f"BK-TEST-{null_bk_1}",
        "so_tien": 1000000,
        "phuong_thuc": "MOMO",
    })
    res_null2 = client.post("/api/v1/payments/create-payment", json={
        "id_dat_phong": null_bk_2,
        "ma_booking": f"BK-TEST-{null_bk_2}",
        "so_tien": 1500000,
        "phuong_thuc": "VNPAY",
    })
    assert res_null1.status_code == 201, f"Lỗi tạo null1: {res_null1.text}"
    assert res_null2.status_code == 201, f"Lỗi tạo null2: {res_null2.text}"
    print("[PASS] Test 3: SQL Server Filtered Unique Index hoạt động chuẩn, cho phép nhiều NULL.")

    # -------------------------------------------------------------
    # 4. Test Chặn thanh toán đúp trong simulate-ipn
    # -------------------------------------------------------------
    print(f"\n[Test 4] Kiểm tra chống thanh toán đúp trong simulate-ipn")
    test_ipn_booking_id = int(str(uuid.uuid4().int)[:6])
    res_ipn_create = client.post("/api/v1/payments/create-payment", json={
        "id_dat_phong": test_ipn_booking_id,
        "ma_booking": f"BK-IPN-{test_ipn_booking_id}",
        "so_tien": 3000000,
        "phuong_thuc": "VNPAY",
    })
    assert res_ipn_create.status_code == 201
    ipn_gateway_txn = res_ipn_create.json()["ma_giao_dich_gateway"]

    # Gọi IPN lần 1 -> SUCCESS
    ipn_res1 = client.post("/api/v1/payments/simulate-ipn", json={
        "ma_giao_dich_gateway": ipn_gateway_txn,
        "trang_thai": "SUCCESS",
        "note": "IPN Callback lần 1",
    })
    assert ipn_res1.status_code == 200
    assert ipn_res1.json()["trang_thai"] == "SUCCESS"
    print(f" -> simulate-ipn lần 1 thành công: trạng thái chuyển sang SUCCESS.")

    # Gọi IPN lần 2 trên cùng giao dịch -> Nhận 400
    ipn_res2 = client.post("/api/v1/payments/simulate-ipn", json={
        "ma_giao_dich_gateway": ipn_gateway_txn,
        "trang_thai": "SUCCESS",
        "note": "IPN Callback lần 2",
    })
    assert ipn_res2.status_code == 400, f"Kỳ vọng 400, nhận: {ipn_res2.status_code} ({ipn_res2.text})"
    assert "đã được thanh toán thành công trước đó" in ipn_res2.json().get("detail", "")
    print(f" -> simulate-ipn lần 2 bị chặn với HTTP 400: '{ipn_res2.json().get('detail')}'")
    print("[PASS] Test 4: Chặn thanh toán đúp qua simulate-ipn thành công.")

    # -------------------------------------------------------------
    # 5. Test Validation: Chặn tạo thanh toán mới cho đơn đã thanh toán SUCCESS
    # -------------------------------------------------------------
    print(f"\n[Test 5] Kiểm tra validation chặn tạo thanh toán mới cho đơn đã thanh toán thành công")
    res_duplicate_order = client.post("/api/v1/payments/create-payment", json={
        "id_dat_phong": test_ipn_booking_id,  # Đơn đã SUCCESS ở Test 4
        "ma_booking": f"BK-IPN-{test_ipn_booking_id}",
        "so_tien": 3000000,
        "phuong_thuc": "VNPAY",
    })
    assert res_duplicate_order.status_code == 400, f"Kỳ vọng 400, nhận: {res_duplicate_order.status_code} ({res_duplicate_order.text})"
    assert "đã được thanh toán thành công trước đó" in res_duplicate_order.json().get("detail", "")
    print(f" -> Từ chối tạo thanh toán với HTTP 400: '{res_duplicate_order.json().get('detail')}'")
    print("[PASS] Test 5: Không cho tạo thanh toán mới cho đơn đã thanh toán thành công.")

    # -------------------------------------------------------------
    # 6. Test Chặn thanh toán đúp trong verify-otp
    # -------------------------------------------------------------
    print(f"\n[Test 6] Kiểm tra chống thanh toán đúp trong verify-otp")
    test_otp_bk_id = int(str(uuid.uuid4().int)[:6])
    res_otp_payment = client.post("/api/v1/payments/create-payment", json={
        "id_dat_phong": test_otp_bk_id,
        "ma_booking": f"BK-OTP-{test_otp_bk_id}",
        "so_tien": 1800000,
        "phuong_thuc": "VNPAY",
    })
    assert res_otp_payment.status_code == 201
    otp_gateway_txn = res_otp_payment.json()["ma_giao_dich_gateway"]

    # Sinh mã OTP
    gen_otp_res = client.post("/api/v1/payments/generate-otp", json={
        "ma_giao_dich_gateway": otp_gateway_txn,
        "email": "customer.test@gmail.com",
    })
    assert gen_otp_res.status_code == 200

    # Lấy OTP thực tế từ DB
    otp_db = (
        db.query(GiaoDichOtpModel)
        .filter(GiaoDichOtpModel.ma_giao_dich_gateway == otp_gateway_txn)
        .order_by(GiaoDichOtpModel.id_otp.desc())
        .first()
    )
    assert otp_db is not None
    valid_code = otp_db.otp_code

    # Verify lần 1 -> Thành công
    v_res1 = client.post("/api/v1/payments/verify-otp", json={
        "ma_giao_dich_gateway": otp_gateway_txn,
        "otp_code": valid_code,
    })
    assert v_res1.status_code == 200
    assert v_res1.json()["trang_thai"] == "SUCCESS"
    print(f" -> verify-otp lần 1 thành công: giao dịch chuyển sang SUCCESS.")

    # Verify lần 2 -> Bị chặn với HTTP 400
    v_res2 = client.post("/api/v1/payments/verify-otp", json={
        "ma_giao_dich_gateway": otp_gateway_txn,
        "otp_code": valid_code,
    })
    assert v_res2.status_code == 400, f"Kỳ vọng 400, nhận: {v_res2.status_code} ({v_res2.text})"
    assert "đã được thanh toán thành công trước đó" in v_res2.json().get("detail", "")
    print(f" -> verify-otp lần 2 bị chặn với HTTP 400: '{v_res2.json().get('detail')}'")
    print("[PASS] Test 6: Chặn gọi verify-otp đúp tuần tự thành công.")

    # -------------------------------------------------------------
    # 7. Test Đồng thời: 2 request verify-otp cùng lúc -> 1 request thành công, 1 nhận 400
    # -------------------------------------------------------------
    print(f"\n[Test 7] Kiểm tra gọi verify-otp hai lần ĐỒNG THỜI (Concurrency Locking)")
    test_concurrent_bk_id = int(str(uuid.uuid4().int)[:6])
    res_conc_payment = client.post("/api/v1/payments/create-payment", json={
        "id_dat_phong": test_concurrent_bk_id,
        "ma_booking": f"BK-CONC-{test_concurrent_bk_id}",
        "so_tien": 4200000,
        "phuong_thuc": "VNPAY",
    })
    assert res_conc_payment.status_code == 201
    conc_gateway_txn = res_conc_payment.json()["ma_giao_dich_gateway"]

    # Sinh mã OTP
    client.post("/api/v1/payments/generate-otp", json={
        "ma_giao_dich_gateway": conc_gateway_txn,
        "email": "concurrent.test@gmail.com",
    })

    # Lấy OTP từ DB
    db.expire_all()
    conc_otp = (
        db.query(GiaoDichOtpModel)
        .filter(GiaoDichOtpModel.ma_giao_dich_gateway == conc_gateway_txn)
        .order_by(GiaoDichOtpModel.id_otp.desc())
        .first()
    )
    assert conc_otp is not None
    conc_code = conc_otp.otp_code

    def send_verify():
        # Mỗi thread tạo client riêng để độc lập session
        c = TestClient(app)
        return c.post("/api/v1/payments/verify-otp", json={
            "ma_giao_dich_gateway": conc_gateway_txn,
            "otp_code": conc_code,
        })

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(send_verify)
        f2 = executor.submit(send_verify)
        res_list = [f1.result(), f2.result()]

    status_codes = sorted([r.status_code for r in res_list])
    print(f" -> Kết quả 2 request đồng thời: Status codes = {status_codes}")

    assert status_codes == [200, 400], f"Kỳ vọng 1 request 200 và 1 request 400, nhận: {status_codes}"
    
    # Tìm request thất bại để kiểm tra message
    failed_res = next(r for r in res_list if r.status_code == 400)
    assert "đã được thanh toán thành công trước đó" in failed_res.json().get("detail", "")
    print(f" -> Request thất bại nhận đúng thông báo: '{failed_res.json().get('detail')}'")
    print("[PASS] Test 7: Gọi verify-otp đồng thời chỉ đúng 1 request thành công, request còn lại nhận HTTP 400.")

    db.close()
    print("\n" + "=" * 60)
    print(">>> TẤT CẢ CÁC BÀI TEST CHỐNG THANH TOÁN TRÙNG ĐỀU ĐẠT 100%! <<<")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    test_payment_idempotency_and_double_payment_prevention()
