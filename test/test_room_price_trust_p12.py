# -*- coding: utf-8 -*-
import sys
import os
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

JWT_SECRET = os.environ.setdefault("JWT_SECRET_KEY", __import__("secrets").token_urlsafe(48))
JWT_ALGO = "HS256"

def make_token(user_id: int, role: str = "CUSTOMER") -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": "user@example.com",
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
            sys.path.remove(p)
    sys.path.insert(0, service_path)
    os.chdir(service_path)

class TestRoomPriceTrustP12(unittest.TestCase):

    def setUp(self):
        set_active_service(BOOKING_SERVICE_DIR)
        from fastapi.testclient import TestClient
        from src.main import app
        self.client = TestClient(app)
        self.auth_headers = {"Authorization": f"Bearer {make_token(10, 'CUSTOMER')}"}
        # Unit tests must never inherit a developer SQL Server connection.
        from sqlalchemy import create_engine, event
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from src.core.database import Base, get_db
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(self.engine, "before_cursor_execute", retval=True)
        def emulate_application_lock(connection, cursor, statement, parameters, context, executemany):
            # Real sp_getapplock concurrency is covered by run_isolated_acceptance.
            if "sp_getapplock" in statement:
                return "SELECT 0", ()
            return statement, parameters
        Base.metadata.create_all(self.engine)
        sessions = sessionmaker(bind=self.engine)
        def isolated_db():
            with sessions() as db:
                yield db
        app.dependency_overrides[get_db] = isolated_db
        self.addCleanup(app.dependency_overrides.clear)
        self.addCleanup(self.engine.dispose)

    def test_price_tampering_rejected(self):
        """Tiêu chí nghiệm thu 1: Cố tình gửi gia: 1000 trong khi giá niêm yết là 1.500.000đ -> Bị từ chối 400"""
        payload = {
            "id_khach_san": 1,
            "ngay_nhan_phong": "2026-11-20",
            "ngay_tra_phong": "2026-11-22",
            "rooms": [
                {
                    "id_phong": 101,
                    "id_loai_phong": 1,
                    "so_phong": "P.101",
                    "ten_loai_phong": "Deluxe Ocean View",
                    "gia": 1000.0,  # Gian lận giá: 1,000đ thay vì 1,500,000đ
                }
            ],
            "khach_o": {
                "ho_ten": "Hacker Attack",
                "email": "hacker@evil.com",
                "sdt": "0988888888",
            },
        }

        # Mock Room Service trả về giá niêm yết thực tế là 1,500,000đ
        mock_room_resp = MagicMock()
        mock_room_resp.status_code = 200
        mock_room_resp.json.return_value = {
            "id_phong": 101,
            "id_khach_san": 1,
            "id_loai_phong": 1,
            "so_phong": "P.101",
            "trang_thai": "AVAILABLE",
            "loai_phong": {
                "id_loai_phong": 1,
                "ten_loai_phong": "Deluxe Ocean View",
                "gia_co_ban_mot_dem": 1500000.0,
            },
        }

        with patch("httpx.Client.get", return_value=mock_room_resp):
            res = self.client.post("/api/v1/bookings", json=payload, headers=self.auth_headers)
            self.assertEqual(res.status_code, 409)
            self.assertIn("Gia phong", res.json()["detail"])
            print("[PASS] 1. Price tampering is rejected with 409 Conflict.")

    def test_valid_price_accepted_and_recalculated(self):
        """Tiêu chí nghiệm thu 2: Giá hợp lệ được tạo thành công, tong_tien tính theo giá niêm yết x số đêm"""
        import random
        rand_room = random.randint(20000, 99999)
        payload = {
            "id_khach_san": 1,
            "ngay_nhan_phong": "2026-11-20",
            "ngay_tra_phong": "2026-11-23",  # 3 đêm
            "rooms": [
                {
                    "id_phong": rand_room,
                    "id_loai_phong": 1,
                    "so_phong": f"P.{rand_room}",
                    "ten_loai_phong": "Deluxe Ocean View",
                    "gia": 1500000.0,
                }
            ],
            "khach_o": {
                "ho_ten": "Khách Hàng Thật",
                "email": "customer@gmail.com",
                "sdt": "0912345678",
            },
        }

        mock_room_resp = MagicMock()
        mock_room_resp.status_code = 200
        mock_room_resp.json.return_value = {
            "id_phong": rand_room,
            "id_khach_san": 1,
            "id_loai_phong": 1,
            "so_phong": f"P.{rand_room}",
            "trang_thai": "AVAILABLE",
            "loai_phong": {
                "id_loai_phong": 1,
                "ten_loai_phong": "Deluxe Ocean View",
                "gia_co_ban_mot_dem": 1500000.0,
            },
        }

        # Mock release_expired_holds và conflict check để test độc lập logic tính tiền
        from src.services.booking_service import BookingService
        with patch("httpx.Client.get", return_value=mock_room_resp), \
             patch.object(BookingService, "release_expired_holds", return_value=0):
            res = self.client.post("/api/v1/bookings", json=payload, headers=self.auth_headers)
            self.assertEqual(res.status_code, 201)
            data = res.json()
            # 3 đêm x 1,500,000đ = 4,500,000đ, Thuế 10% = 450,000đ, Tổng = 4,950,000đ
            self.assertEqual(data["tien_phong"], 4500000.0)
            self.assertEqual(data["thue_phi"], 450000.0)
            self.assertEqual(data["tong_tien"], 4950000.0)
            self.assertEqual(data["chi_tiet"][0]["gia_tai_thoi_diem_dat"], 1500000.0)
            print("[PASS] 2. Giá niêm yết 1,500,000đ được áp dụng, tính thuế VAT 10% (450,000đ), tổng tiền 4,950,000đ.")

    def test_nonexistent_room_rejected(self):
        """Phòng không tồn tại trên Room Service (404) -> Từ chối 404"""
        payload = {
            "id_khach_san": 1,
            "ngay_nhan_phong": "2026-11-20",
            "ngay_tra_phong": "2026-11-22",
            "rooms": [
                {
                    "id_phong": 99999,
                    "id_loai_phong": 1,
                    "gia": 1000000.0,
                }
            ],
            "khach_o": {
                "ho_ten": "Test User",
                "email": "test@example.com",
                "sdt": "0912345678",
            },
        }

        mock_room_resp = MagicMock()
        mock_room_resp.status_code = 404

        with patch("httpx.Client.get", return_value=mock_room_resp):
            res = self.client.post("/api/v1/bookings", json=payload, headers=self.auth_headers)
            self.assertEqual(res.status_code, 404)
            self.assertIn("99999", res.json()["detail"])
            print("[PASS] 3. Phòng không tồn tại trả về lỗi 404 Not Found rõ ràng.")

    def test_wrong_hotel_room_rejected(self):
        """Phòng thuộc khách sạn khác (id_khach_san=2 != 1) -> Từ chối 400"""
        payload = {
            "id_khach_san": 1,
            "ngay_nhan_phong": "2026-11-20",
            "ngay_tra_phong": "2026-11-22",
            "rooms": [
                {
                    "id_phong": 201,
                    "id_loai_phong": 2,
                    "gia": 1200000.0,
                }
            ],
            "khach_o": {
                "ho_ten": "Test User",
                "email": "test@example.com",
                "sdt": "0912345678",
            },
        }

        mock_room_resp = MagicMock()
        mock_room_resp.status_code = 200
        mock_room_resp.json.return_value = {
            "id_phong": 201,
            "id_khach_san": 2,  # Khách sạn 2 chứ không phải 1
            "id_loai_phong": 2,
            "trang_thai": "AVAILABLE",
            "loai_phong": {"gia_co_ban_mot_dem": 1200000.0},
        }

        with patch("httpx.Client.get", return_value=mock_room_resp):
            res = self.client.post("/api/v1/bookings", json=payload, headers=self.auth_headers)
            self.assertEqual(res.status_code, 400)
            self.assertIn("khach san ID 1", res.json()["detail"])
            print("[PASS] 4. Phòng thuộc khách sạn khác bị từ chối 400 Bad Request.")

    def test_unavailable_room_status_rejected(self):
        """Phòng có trạng thái OCCUPIED / MAINTENANCE -> Từ chối 400"""
        payload = {
            "id_khach_san": 1,
            "ngay_nhan_phong": "2026-11-20",
            "ngay_tra_phong": "2026-11-22",
            "rooms": [
                {
                    "id_phong": 103,
                    "id_loai_phong": 1,
                    "gia": 1000000.0,
                }
            ],
            "khach_o": {
                "ho_ten": "Test User",
                "email": "test@example.com",
                "sdt": "0912345678",
            },
        }

        mock_room_resp = MagicMock()
        mock_room_resp.status_code = 200
        mock_room_resp.json.return_value = {
            "id_phong": 103,
            "id_khach_san": 1,
            "id_loai_phong": 1,
            "trang_thai": "OCCUPIED",  # Phòng đang có khách ở
            "loai_phong": {"gia_co_ban_mot_dem": 1000000.0},
        }

        with patch("httpx.Client.get", return_value=mock_room_resp):
            res = self.client.post("/api/v1/bookings", json=payload, headers=self.auth_headers)
            self.assertEqual(res.status_code, 400)
            self.assertIn("OCCUPIED", res.json()["detail"])
            print("[PASS] 5. Phòng đang OCCUPIED bị từ chối 400 Bad Request.")

    def test_room_service_offline_fails_closed(self):
        """An unavailable authoritative price service must not create a booking."""
        import random
        rand_room_fb = random.randint(20000, 99999)
        payload = {
            "id_khach_san": 1,
            "ngay_nhan_phong": "2026-11-25",
            "ngay_tra_phong": "2026-11-27",  # 2 đêm
            "rooms": [
                {
                    "id_phong": rand_room_fb,
                    "id_loai_phong": 1,
                    "so_phong": f"P.{rand_room_fb}",
                    "ten_loai_phong": "Standard Room",
                    "gia": 800000.0,
                }
            ],
            "khach_o": {
                "ho_ten": "Khách Test Fallback",
                "email": "fallback@example.com",
                "sdt": "0912345678",
            },
        }

        from src.services.booking_service import BookingService
        with patch("httpx.Client.get", side_effect=Exception("Connection refused")), \
             patch("urllib.request.urlopen", side_effect=Exception("Connection refused")), \
             patch.object(BookingService, "release_expired_holds", return_value=0):
            res = self.client.post("/api/v1/bookings", json=payload, headers=self.auth_headers)
            self.assertEqual(res.status_code, 503)
            from sqlalchemy import text
            with self.engine.connect() as connection:
                self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM dat_phong")).scalar(), 0)

if __name__ == "__main__":
    unittest.main()
