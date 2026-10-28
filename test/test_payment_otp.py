# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
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
from src.models import ThanhToanModel, GiaoDichOtpModel

def test_otp_flow():
    client = TestClient(app)
    import jwt
    from src.core.config import settings
    token = jwt.encode({"sub": "1", "role": "CUSTOMER", "type": "access"}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    client.headers["Authorization"] = f"Bearer {token}"

    # 1. Kiem tra OpenAPI schema
    openapi = client.get('/openapi.json').json()
    paths = openapi.get('paths', {})
    assert '/api/v1/payments/generate-otp' in paths, 'Thieu endpoint generate-otp'
    assert '/api/v1/payments/verify-otp' in paths, 'Thieu endpoint verify-otp'
    print("[PASS] Check 1: OpenAPI schema contains both /generate-otp and /verify-otp.")

    # 2. Tao payment moi
    create_res = client.post('/api/v1/payments/create-payment', json={
        'id_dat_phong': 999,
        'ma_booking': 'BK-TEST-OTP-999',
        'so_tien': 1200000,
        'phuong_thuc': 'VNPAY',
        'ghi_chu': 'Test OTP Flow'
    })
    assert create_res.status_code == 201, f'Loi tao payment: {create_res.text}'
    payment_data = create_res.json()
    gateway_txn = payment_data['ma_giao_dich_gateway']
    print(f"[PASS] Check 2: Created payment {gateway_txn} with status PENDING.")

    # Hook publish_otp_event để bắt mã raw_otp 6 chữ số gửi qua event
    captured_otps = {}
    import src.services.payment_service as ps_module
    orig_publish_otp = ps_module.publish_otp_event

    def hook_publish_otp(event_name, data):
        if "otp_code" in data and "ma_giao_dich_gateway" in data:
            captured_otps[data["ma_giao_dich_gateway"]] = data["otp_code"]
        try:
            orig_publish_otp(event_name, data)
        except Exception:
            pass

    ps_module.publish_otp_event = hook_publish_otp

    # 3. Goi generate-otp
    gen_res = client.post('/api/v1/payments/generate-otp', json={
        'ma_giao_dich_gateway': gateway_txn,
        'email': 'customer@test.com'
    })
    assert gen_res.status_code == 200, f'Loi generate-otp: {gen_res.text}'
    gen_data = gen_res.json()
    assert gen_data['success'] is True
    assert 'otp_code' not in gen_data, 'Lo otp_code trong response API!'
    assert gen_data['expires_in_seconds'] == 180
    print("[PASS] Check 3: generate-otp succeeded, otp_code hidden from response.")

    # 4. Kiem tra DB & lay otp_code thuc te
    db = SessionLocal()
    otp_record = (
        db.query(GiaoDichOtpModel)
        .filter(GiaoDichOtpModel.ma_giao_dich_gateway == gateway_txn)
        .order_by(GiaoDichOtpModel.id_otp.desc())
        .first()
    )
    assert otp_record is not None
    assert len(otp_record.otp_code) == 64, f"DB OTP phai la SHA-256 hash 64 ky tu, thuc te: {len(otp_record.otp_code)}"
    real_otp = captured_otps.get(gateway_txn)
    assert real_otp is not None and len(real_otp) == 6
    import hashlib
    assert otp_record.otp_code == hashlib.sha256(real_otp.encode('utf-8')).hexdigest()
    print(f"[PASS] Check 4: Stored OTP in DB is SHA-256 hash (64 hex): {otp_record.otp_code[:12]}... Matches raw OTP: {real_otp}")

    # 5. Kiem tra validate pattern (khong dung 6 so)
    for bad_code in ['12345', '1234567', 'abcdef', '12a456']:
        invalid_pattern_res = client.post('/api/v1/payments/verify-otp', json={
            'ma_giao_dich_gateway': gateway_txn,
            'otp_code': bad_code
        })
        assert invalid_pattern_res.status_code == 422, f'Pattern validation did not catch {bad_code}'
    print("[PASS] Check 5: Pattern validation strictly enforces 6 digits (422).")

    # 6. Thu sai ma (lan 1)
    wrong_code = '000000' if real_otp != '000000' else '111111'
    wrong_code_res = client.post('/api/v1/payments/verify-otp', json={
        'ma_giao_dich_gateway': gateway_txn,
        'otp_code': wrong_code
    })
    assert wrong_code_res.status_code == 400
    assert '2' in wrong_code_res.json()['detail']
    print(f"[PASS] Check 6: Wrong OTP rejected (400), remaining attempts notified: {wrong_code_res.json()['detail']}")

    # 7. Nhap dung ma
    orig_confirm = ps_module.PaymentService.confirm_booking_with_retry
    ps_module.PaymentService.confirm_booking_with_retry = staticmethod(lambda id_dp, note, max_retries=3, initial_delay=0.2: True)
    try:
        correct_res = client.post('/api/v1/payments/verify-otp', json={
            'ma_giao_dich_gateway': gateway_txn,
            'otp_code': real_otp
        })
        assert correct_res.status_code == 200, f'Loi verify-otp dung: {correct_res.text}'
        assert correct_res.json()['trang_thai'] == 'SUCCESS'
        print("[PASS] Check 7: Correct OTP verified successfully, payment status -> SUCCESS.")
    finally:
        ps_module.PaymentService.confirm_booking_with_retry = orig_confirm

    # 8. Thu dung lai ma lan 2
    reuse_res = client.post('/api/v1/payments/verify-otp', json={
        'ma_giao_dich_gateway': gateway_txn,
        'otp_code': real_otp
    })
    assert reuse_res.status_code == 400
    print(f"[PASS] Check 8: Reusing OTP rejected with 400: {reuse_res.json()['detail']}")

    # 9. Kiem tra OTP het han
    create_exp_res = client.post('/api/v1/payments/create-payment', json={
        'id_dat_phong': 1000,
        'ma_booking': 'BK-TEST-EXP-1000',
        'so_tien': 500000,
        'phuong_thuc': 'MOMO'
    })
    exp_txn = create_exp_res.json()['ma_giao_dich_gateway']
    client.post('/api/v1/payments/generate-otp', json={'ma_giao_dich_gateway': exp_txn, 'email': 'exp@test.com'})
    db.query(GiaoDichOtpModel).filter(GiaoDichOtpModel.ma_giao_dich_gateway == exp_txn).update({
        'thoi_gian_het_han': datetime.utcnow() - timedelta(minutes=1)
    })
    db.commit()

    exp_otp = captured_otps.get(exp_txn, "123456")
    exp_verify_res = client.post('/api/v1/payments/verify-otp', json={
        'ma_giao_dich_gateway': exp_txn,
        'otp_code': exp_otp
    })
    assert exp_verify_res.status_code == 400
    print(f"[PASS] Check 9: Expired OTP rejected with 400: {exp_verify_res.json()['detail']}")

    # 10. Kiem tra thu sai qua 3 lan
    create_max_res = client.post('/api/v1/payments/create-payment', json={
        'id_dat_phong': 1001,
        'ma_booking': 'BK-TEST-MAX-1001',
        'so_tien': 700000,
        'phuong_thuc': 'CREDIT_CARD'
    })
    max_txn = create_max_res.json()['ma_giao_dich_gateway']
    client.post('/api/v1/payments/generate-otp', json={'ma_giao_dich_gateway': max_txn, 'email': 'max@test.com'})
    # Thu sai 3 lan
    client.post('/api/v1/payments/verify-otp', json={'ma_giao_dich_gateway': max_txn, 'otp_code': '000000'})
    client.post('/api/v1/payments/verify-otp', json={'ma_giao_dich_gateway': max_txn, 'otp_code': '000000'})
    res_3 = client.post('/api/v1/payments/verify-otp', json={'ma_giao_dich_gateway': max_txn, 'otp_code': '000000'})
    assert res_3.status_code == 400
    # Lan thu 4 khi da qua 3 lan
    res_4 = client.post('/api/v1/payments/verify-otp', json={'ma_giao_dich_gateway': max_txn, 'otp_code': '000000'})
    assert res_4.status_code == 400
    assert 'vượt quá 3 lần' in res_4.json()['detail'] or '3 lần' in res_4.json()['detail']
    print(f"[PASS] Check 10: Exceeding 3 failed attempts blocked (400): {res_4.json()['detail']}")

    # Don dep du lieu test
    all_txns = [gateway_txn, exp_txn, max_txn]
    db.query(GiaoDichOtpModel).filter(GiaoDichOtpModel.ma_giao_dich_gateway.in_(all_txns)).delete(synchronize_session=False)
    db.query(ThanhToanModel).filter(ThanhToanModel.ma_giao_dich_gateway.in_(all_txns)).delete(synchronize_session=False)
    db.commit()
    db.close()
    print("==================================================")
    print(">>> ALL 10 OTP AUTOMATED TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_otp_flow()
