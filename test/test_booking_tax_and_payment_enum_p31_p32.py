# -*- coding: utf-8 -*-
"""
Test Suite for Task P3.1 & P3.2:
- Đồng bộ thuế/phí (VAT 10%) giữa Frontend và Backend Booking & Payment
- Chuẩn hóa Enum phương thức thanh toán (VNPAY, MOMO, CREDIT_CARD, CASH)
"""
import sys
import os
import json
import random
import unittest
import jwt
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BOOKING_SERVICE_DIR = os.path.join(PROJECT_ROOT, "services", "booking-service")
PAYMENT_SERVICE_DIR = os.path.join(PROJECT_ROOT, "services", "payment-service")

JWT_SECRET = "booking_super_secret_jwt_key_2026_xyz!@#"
JWT_ALGO = "HS256"

def make_token(user_id: int, role: str = "CUSTOMER") -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": "customer@example.com",
        "type": "access",
        "exp": datetime.utcnow() + timedelta(hours=2),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def unload_src_modules():
    for mod in list(sys.modules.keys()):
        if mod == "src" or mod.startswith("src."):
            del sys.modules[mod]

def set_active_service(service_path: str):
    unload_src_modules()
    for p in list(sys.path):
        if "services" in p or "gateway" in p:
            try:
                sys.path.remove(p)
            except ValueError:
                pass
    sys.path.insert(0, service_path)
    os.chdir(service_path)

class TestBookingTaxAndPaymentEnumP31P32(unittest.TestCase):

    def test_p31_booking_tax_fee_calculation(self):
        """
        P3.1: Kiểm tra tính thuế/phí VAT 10% tại Booking Service
        tien_phong = sum(gia) * nights
        thue_phi = round(tien_phong * 0.10)
        tong_tien = tien_phong + thue_phi
        """
        print("\n" + "=" * 70)
        print("[CHECK 1] Kiểm tra tính thuế VAT 10% và tổng tiền trong Booking Service...")
        print("=" * 70)
        set_active_service(BOOKING_SERVICE_DIR)
        from fastapi.testclient import TestClient
        from src.main import app
        from src.services.booking_service import BookingService

        client = TestClient(app)
        auth_headers = {"Authorization": f"Bearer {make_token(10, 'CUSTOMER')}"}

        rand_room = random.randint(30000, 99999)
        price_per_night = 2500000.0  # 2.500.000 đ
        nights = 2                   # 2 đêm
        expected_room_total = price_per_night * nights   # 5.000.000 đ
        expected_tax = round(expected_room_total * 0.10) # 500.000 đ
        expected_final_total = expected_room_total + expected_tax # 5.500.000 đ

        payload = {
            "id_khach_san": 1,
            "ngay_nhan_phong": "2026-12-01",
            "ngay_tra_phong": "2026-12-03",  # 2 nights
            "rooms": [
                {
                    "id_phong": rand_room,
                    "id_loai_phong": 2,
                    "so_phong": f"P.{rand_room}",
                    "ten_loai_phong": "Executive Suite",
                    "gia": price_per_night,
                }
            ],
            "khach_o": {
                "ho_ten": "Nguyen Van B",
                "email": "nguyenvanb@example.com",
                "sdt": "0987654321",
            },
        }

        mock_room_resp = MagicMock()
        mock_room_resp.status_code = 200
        mock_room_resp.json.return_value = {
            "id_phong": rand_room,
            "id_khach_san": 1,
            "id_loai_phong": 2,
            "so_phong": f"P.{rand_room}",
            "trang_thai": "AVAILABLE",
            "loai_phong": {
                "id_loai_phong": 2,
                "ten_loai_phong": "Executive Suite",
                "gia_co_ban_mot_dem": price_per_night,
            },
        }

        with patch("httpx.Client.get", return_value=mock_room_resp), \
             patch.object(BookingService, "release_expired_holds", return_value=0):
            res = client.post("/api/v1/bookings", json=payload, headers=auth_headers)

        self.assertEqual(res.status_code, 201, f"Tạo đơn thất bại: {res.text}")
        data = res.json()

        self.assertEqual(data["tien_phong"], expected_room_total)
        self.assertEqual(data["thue_phi"], expected_tax)
        self.assertEqual(data["tong_tien"], expected_final_total)
        print(f" -> [PASS] Booking Response chi tiết:")
        print(f"    - Tiền phòng ({nights} đêm x {price_per_night:,.0f} đ): {data['tien_phong']:,.0f} đ")
        print(f"    - Thuế VAT (10%): {data['thue_phi']:,.0f} đ")
        print(f"    - Tổng thanh toán cuối: {data['tong_tien']:,.0f} đ")

    def test_p31_reconciliation_against_payment(self):
        """
        P3.1: Kiểm tra tính nhất quán tiền giữa Booking và Payment Service:
        Payment Service chỉ chấp nhận thanh toán khi số tiền khớp chính xác tong_tien (đã gồm thuế phí),
        và từ chối nếu chỉ gửi tien_phong mà thiếu thuế phí.
        """
        print("\n" + "=" * 70)
        print("[CHECK 2] Kiểm tra đối soát số tiền thuế/phí với Payment Service...")
        print("=" * 70)
        set_active_service(PAYMENT_SERVICE_DIR)
        from fastapi.testclient import TestClient
        from src.main import app

        client = TestClient(app)
        auth_headers = {"Authorization": f"Bearer {make_token(10, 'CUSTOMER')}"}

        # Giả lập đơn booking có tien_phong=2.000.000đ, thue_phi=200.000đ, tong_tien=2.200.000đ
        mock_booking_data = {
            "id_dat_phong": 8888,
            "ma_booking": "BK-202612-TAX01",
            "tien_phong": 2000000.0,
            "thue_phi": 200000.0,
            "tong_tien": 2200000.0,
            "trang_thai": "PENDING_PAYMENT",
            "han_giu_cho": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
        }

        class MockBookingResponse:
            def __init__(self, data):
                self.status = 200
                self._data = data
            def read(self):
                return json.dumps(self._data).encode("utf-8")
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        # 2.1 Gửi thiếu thuế phí (2.000.000đ thay vì 2.200.000đ) -> Bị từ chối 400
        with patch("urllib.request.urlopen", return_value=MockBookingResponse(mock_booking_data)):
            bad_payment_res = client.post(
                "/api/v1/payments/create-payment",
                json={
                    "id_dat_phong": 8888,
                    "ma_booking": "BK-202612-TAX01",
                    "so_tien": 2000000.0,  # Chưa có thuế
                    "phuong_thuc": "VNPAY",
                },
                headers=auth_headers,
            )
        self.assertEqual(bad_payment_res.status_code, 400)
        self.assertIn("không khớp", bad_payment_res.json()["detail"])
        print(f" -> [PASS] Gửi số tiền thiếu thuế phí (2.000.000 đ) bị từ chối 400: {bad_payment_res.json()['detail']}")

        # 2.2 Gửi đúng con số tổng tiền (2.200.000đ) -> Tạo thanh toán thành công 201
        with patch("urllib.request.urlopen", return_value=MockBookingResponse(mock_booking_data)):
            good_payment_res = client.post(
                "/api/v1/payments/create-payment",
                json={
                    "id_dat_phong": 8888,
                    "ma_booking": "BK-202612-TAX01",
                    "so_tien": 2200000.0,  # Đã gồm thuế phí 10%
                    "phuong_thuc": "VNPAY",
                },
                headers=auth_headers,
            )
        self.assertEqual(good_payment_res.status_code, 201)
        self.assertEqual(good_payment_res.json()["so_tien"], 2200000.0)
        print(f" -> [PASS] Gửi số tiền khớp tong_tien (2.200.000 đ) được tạo thanh toán thành công (201 Created).")

    def test_p32_payment_method_enum_standardization(self):
        """
        P3.2: Kiểm tra chuẩn hóa Enum phương thức thanh toán:
        VNPAY, MOMO, CREDIT_CARD, CASH đều được chấp nhận hợp lệ;
        Các giá trị cũ / không hợp lệ (như ATM_CARD, TIEN_MAT, BITCOIN) bị từ chối 422 Unprocessable Entity.
        """
        print("\n" + "=" * 70)
        print("[CHECK 3] Kiểm tra chuẩn hóa Enum phương thức thanh toán...")
        print("=" * 70)
        set_active_service(PAYMENT_SERVICE_DIR)
        from fastapi.testclient import TestClient
        from src.main import app

        client = TestClient(app)
        auth_headers = {"Authorization": f"Bearer {make_token(10, 'CUSTOMER')}"}

        mock_booking_data = {
            "id_dat_phong": 8889,
            "ma_booking": "BK-202612-ENUM01",
            "tong_tien": 1500000.0,
            "trang_thai": "PENDING_PAYMENT",
            "han_giu_cho": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
        }

        class MockBookingResponse:
            def __init__(self, data):
                self.status = 200
                self._data = data
            def read(self):
                return json.dumps(self._data).encode("utf-8")
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        valid_methods = ["VNPAY", "MOMO", "CREDIT_CARD", "CASH"]
        for method in valid_methods:
            with patch("urllib.request.urlopen", return_value=MockBookingResponse(mock_booking_data)):
                res = client.post(
                    "/api/v1/payments/create-payment",
                    json={
                        "id_dat_phong": 8889,
                        "ma_booking": "BK-202612-ENUM01",
                        "so_tien": 1500000.0,
                        "phuong_thuc": method,
                    },
                    headers=auth_headers,
                )
            self.assertEqual(res.status_code, 201, f"Phương thức {method} phải hợp lệ nhưng nhận {res.status_code}")
            self.assertEqual(res.json()["phuong_thuc"], method)
            print(f" -> [PASS] Phương thức chuẩn {method} được chấp nhận hợp lệ (201).")

        # Kiểm tra các giá trị không hợp lệ
        invalid_methods = ["ATM_CARD", "TIEN_MAT", "PAYPAL", "BITCOIN"]
        for invalid in invalid_methods:
            res = client.post(
                "/api/v1/payments/create-payment",
                json={
                    "id_dat_phong": 8889,
                    "ma_booking": "BK-202612-ENUM01",
                    "so_tien": 1500000.0,
                    "phuong_thuc": invalid,
                },
                headers=auth_headers,
            )
            self.assertEqual(res.status_code, 422, f"Phương thức không chuẩn {invalid} phải bị 422")
            print(f" -> [PASS] Phương thức không chuẩn '{invalid}' bị từ chối 422 Unprocessable Entity.")

if __name__ == "__main__":
    unittest.main()
