# -*- coding: utf-8 -*-
import sys
import os
import unittest
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

class TestAvailableRoomsP11(unittest.TestCase):

    def test_booking_service_get_booked_room_ids_logic(self):
        """Kiểm tra logic lọc giao thoa ngày và trạng thái đơn của BookingService.get_booked_room_ids"""
        booking_dir = os.path.join(PROJECT_ROOT, "services", "booking-service")
        set_active_service(booking_dir)

        from src.services.booking_service import BookingService
        from src.models import DatPhongModel, ChiTietDatPhongModel, TrangThaiBookingEnum

        now_utc = datetime.utcnow()

        mock_db = MagicMock()

        # Case 1: Giả lập trả về phòng 101 và 102
        mock_db.query.return_value.join.return_value.filter.return_value.distinct.return_value.all.return_value = [
            (101,), (102,)
        ]

        booked = BookingService.get_booked_room_ids(
            db=mock_db,
            hotel_id=1,
            check_in=date(2026, 11, 2),
            check_out=date(2026, 11, 4),
        )
        self.assertEqual(booked, [101, 102])

        # Case 2: Không có phòng nào bị trùng
        mock_db.query.return_value.join.return_value.filter.return_value.distinct.return_value.all.return_value = []
        booked_empty = BookingService.get_booked_room_ids(
            db=mock_db,
            hotel_id=1,
            check_in=date(2026, 11, 6),
            check_out=date(2026, 11, 10),
        )
        self.assertEqual(booked_empty, [])

    def test_booking_service_booked_room_ids_endpoint(self):
        """Kiểm tra endpoint GET /api/v1/bookings/booked-room-ids"""
        booking_dir = os.path.join(PROJECT_ROOT, "services", "booking-service")
        set_active_service(booking_dir)

        from fastapi.testclient import TestClient
        from src.main import app as booking_app
        from src.services.booking_service import BookingService

        client = TestClient(booking_app)

        # 1. Test check_in >= check_out -> 400
        res_bad = client.get("/api/v1/bookings/booked-room-ids?hotel_id=1&check_in=2026-11-05&check_out=2026-11-02")
        self.assertEqual(res_bad.status_code, 400)
        self.assertIn("Ngày nhận phòng (check_in) phải trước ngày trả phòng (check_out)", res_bad.json()["detail"])

        # 2. Test mock BookingService.get_booked_room_ids trả về [101]
        with patch.object(BookingService, "get_booked_room_ids", return_value=[101]) as mock_method:
            res_ok = client.get("/api/v1/bookings/booked-room-ids?hotel_id=1&check_in=2026-11-02&check_out=2026-11-04")
            self.assertEqual(res_ok.status_code, 200)
            self.assertEqual(res_ok.json(), [101])
            mock_method.assert_called_once()

    def test_room_service_get_available_rooms_filtering(self):
        """Kiểm tra RoomService.get_available_rooms lọc bỏ phòng đã đặt và xử lý fallback"""
        room_dir = os.path.join(PROJECT_ROOT, "services", "room-service")
        set_active_service(room_dir)

        from src.services.room_service import RoomService
        from src.models import PhongModel, LoaiPhongModel, TrangThaiPhongEnum

        mock_db = MagicMock()

        room_101 = MagicMock(spec=PhongModel)
        room_101.id_phong = 101
        room_101.so_phong = "101"
        room_101.trang_thai = TrangThaiPhongEnum.AVAILABLE.value

        room_102 = MagicMock(spec=PhongModel)
        room_102.id_phong = 102
        room_102.so_phong = "102"
        room_102.trang_thai = TrangThaiPhongEnum.AVAILABLE.value

        # Case 1: Booking Service trả về [101] -> Phòng 101 phải bị lọc bỏ
        with patch("httpx.Client.get") as mock_http_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [101]
            mock_http_get.return_value = mock_resp

            mock_db.query.return_value.join.return_value.options.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [room_102]

            available = RoomService.get_available_rooms(
                db=mock_db,
                hotel_id=1,
                check_in=date(2026, 11, 2),
                check_out=date(2026, 11, 4),
            )
            self.assertEqual(len(available), 1)
            self.assertEqual(available[0].id_phong, 102)

        # Case 2: Khoảng ngày không trùng -> Booking Service trả về [] -> Cả 101 và 102 đều khả dụng
        with patch("httpx.Client.get") as mock_http_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = []
            mock_http_get.return_value = mock_resp

            mock_db.query.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [room_101, room_102]

            available_empty = RoomService.get_available_rooms(
                db=mock_db,
                hotel_id=1,
                check_in=date(2026, 11, 6),
                check_out=date(2026, 11, 10),
            )
            self.assertEqual(len(available_empty), 2)
            self.assertEqual([r.id_phong for r in available_empty], [101, 102])

        # Case 3: Booking Service bị lỗi/timeout -> Không crash, fallback bình thường
        with patch("httpx.Client.get", side_effect=Exception("Connection Refused")):
            mock_db.query.return_value.join.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [room_101, room_102]

            available_fallback = RoomService.get_available_rooms(
                db=mock_db,
                hotel_id=1,
                check_in=date(2026, 11, 2),
                check_out=date(2026, 11, 4),
            )
            self.assertEqual(len(available_fallback), 2)

    def test_room_service_endpoint_available_rooms(self):
        """Kiểm tra endpoint GET /api/v1/rooms/available của Room Service"""
        room_dir = os.path.join(PROJECT_ROOT, "services", "room-service")
        set_active_service(room_dir)

        from fastapi.testclient import TestClient
        from src.main import app as room_app
        from src.services.room_service import RoomService

        client = TestClient(room_app)

        # 1. Invalid date range check_in >= check_out
        res_bad = client.get("/api/v1/rooms/available?hotel_id=1&check_in=2026-11-05&check_out=2026-11-02")
        self.assertEqual(res_bad.status_code, 400)

        # 2. Check call delegation
        with patch.object(RoomService, "get_available_rooms", return_value=[]) as mock_method:
            res = client.get("/api/v1/rooms/available?hotel_id=1&check_in=2026-11-02&check_out=2026-11-04")
            self.assertEqual(res.status_code, 200)
            mock_method.assert_called_once()

    def test_acceptance_criteria_end_to_end(self):
        """
        Nghiệm thu tiêu chuẩn đề bài:
        1. Tạo một đơn đặt phòng cho Phòng #101 từ ngày 2026-11-01 đến 2026-11-05 (CONFIRMED).
        2. Gọi GET /api/v1/rooms/available?hotel_id=1&check_in=2026-11-02&check_out=2026-11-04:
           Phòng #101 không còn xuất hiện trong kết quả trả về.
        3. Gọi kiểm tra khoảng ngày không trùng (ví dụ 2026-11-06 đến 2026-11-10):
           Phòng #101 xuất hiện bình thường.
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # ── 1. Khởi tạo CSDL SQLite giả lập cho Booking Service ──
        booking_dir = os.path.join(PROJECT_ROOT, "services", "booking-service")
        set_active_service(booking_dir)

        from src.core.database import Base as BookingBase
        from src.models import DatPhongModel, ChiTietDatPhongModel, TrangThaiBookingEnum
        from src.services.booking_service import BookingService

        engine_bk = create_engine("sqlite:///:memory:")
        BookingBase.metadata.create_all(engine_bk)
        SessionBooking = sessionmaker(bind=engine_bk)
        db_booking = SessionBooking()

        now_utc = datetime.utcnow()
        bk1 = DatPhongModel(
            ma_booking="BK-202611-TEST101",
            id_tai_khoan=10,
            id_khach_san=1,
            ngay_nhan_phong=date(2026, 11, 1),
            ngay_tra_phong=date(2026, 11, 5),
            tong_tien=5000000,
            trang_thai=TrangThaiBookingEnum.CONFIRMED.value,
            han_giu_cho=now_utc + timedelta(days=1),
        )
        bk1.chi_tiet.append(
            ChiTietDatPhongModel(
                id_phong=101,
                id_loai_phong=1,
                so_phong="101",
                ten_loai_phong="Standard Room",
                gia_tai_thoi_diem_dat=1000000,
            )
        )
        db_booking.add(bk1)
        db_booking.commit()

        # Kiểm tra BookingService trả về phòng 101 khi trùng ngày
        booked_overlap = BookingService.get_booked_room_ids(
            db=db_booking,
            hotel_id=1,
            check_in=date(2026, 11, 2),
            check_out=date(2026, 11, 4),
        )
        self.assertEqual(booked_overlap, [101])

        # Kiểm tra BookingService trả về rỗng khi không trùng ngày
        booked_no_overlap = BookingService.get_booked_room_ids(
            db=db_booking,
            hotel_id=1,
            check_in=date(2026, 11, 6),
            check_out=date(2026, 11, 10),
        )
        self.assertEqual(booked_no_overlap, [])

        # ── 2. Khởi tạo CSDL SQLite giả lập cho Room Service ──
        room_dir = os.path.join(PROJECT_ROOT, "services", "room-service")
        set_active_service(room_dir)

        from src.core.database import Base as RoomBase
        from src.models import PhongModel, LoaiPhongModel, TrangThaiPhongEnum
        from src.services.room_service import RoomService

        engine_rm = create_engine("sqlite:///:memory:")
        RoomBase.metadata.create_all(engine_rm)
        SessionRoom = sessionmaker(bind=engine_rm)
        db_room = SessionRoom()

        loai_phong = LoaiPhongModel(
            id_loai_phong=1,
            id_khach_san=1,
            ten_loai_phong="Standard Room",
            gia_co_ban_mot_dem=1000000,
            suc_chua_nguoi_lon=2,
            suc_chua_tre_em=1,
            so_luong_phong=2,
        )
        db_room.add(loai_phong)
        db_room.commit()

        p101 = PhongModel(
            id_phong=101,
            id_khach_san=1,
            id_loai_phong=1,
            so_phong="101",
            tang=1,
            trang_thai=TrangThaiPhongEnum.AVAILABLE.value,
        )
        p102 = PhongModel(
            id_phong=102,
            id_khach_san=1,
            id_loai_phong=1,
            so_phong="102",
            tang=1,
            trang_thai=TrangThaiPhongEnum.AVAILABLE.value,
        )
        db_room.add_all([p101, p102])
        db_room.commit()

        # ── 3. Test liên thông RoomService gọi BookingService ──
        def mock_booking_http_get(url, **kwargs):
            mock_res = MagicMock()
            mock_res.status_code = 200
            if "check_in=2026-11-02" in url:
                mock_res.json.return_value = booked_overlap  # [101]
            else:
                mock_res.json.return_value = booked_no_overlap  # []
            return mock_res

        with patch("httpx.Client.get", side_effect=mock_booking_http_get):
            # Test khi trùng ngày (2026-11-02 -> 2026-11-04): Phòng 101 KHÔNG xuất hiện
            rooms_overlap = RoomService.get_available_rooms(
                db=db_room,
                hotel_id=1,
                check_in=date(2026, 11, 2),
                check_out=date(2026, 11, 4),
            )
            returned_ids_overlap = [r.id_phong for r in rooms_overlap]
            self.assertNotIn(101, returned_ids_overlap, "Phòng 101 phải bị loại trừ khi trùng ngày đặt!")
            self.assertIn(102, returned_ids_overlap, "Phòng 102 phải khả dụng!")

            # Test khi không trùng ngày (2026-11-06 -> 2026-11-10): Phòng 101 xuất hiện bình thường
            rooms_no_overlap = RoomService.get_available_rooms(
                db=db_room,
                hotel_id=1,
                check_in=date(2026, 11, 6),
                check_out=date(2026, 11, 10),
            )
            returned_ids_no_overlap = [r.id_phong for r in rooms_no_overlap]
            self.assertIn(101, returned_ids_no_overlap, "Phòng 101 phải xuất hiện bình thường khi không trùng ngày!")
            self.assertIn(102, returned_ids_no_overlap, "Phòng 102 phải xuất hiện bình thường!")

        db_booking.close()
        db_room.close()
        print("\n>>> Acceptance Criteria E2E test passed successfully!")

if __name__ == "__main__":
    unittest.main()
