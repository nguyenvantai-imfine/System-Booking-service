# -*- coding: utf-8 -*-
import sys
import os
import uuid
import concurrent.futures
from datetime import datetime, timedelta, date

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BOOKING_SERVICE_DIR = os.path.join(PROJECT_ROOT, "services", "booking-service")

if BOOKING_SERVICE_DIR not in sys.path:
    sys.path.insert(0, BOOKING_SERVICE_DIR)

os.chdir(BOOKING_SERVICE_DIR)

from fastapi.testclient import TestClient
from src.main import app
from src.core.database import SessionLocal
from src.models import DatPhongModel, ChiTietDatPhongModel, TrangThaiBookingEnum

def test_overbooking_and_concurrency_protection():
    client = TestClient(app)
    db = SessionLocal()

    print("\n" + "=" * 65)
    print("BẮT ĐẦU TEST CƠ CHẾ CHỐNG OVERBOOKING & CONCURRENCY TRONG BOOKING-SERVICE")
    print("=" * 65)

    unique_room_id = int(str(uuid.uuid4().int)[:6])
    print(f"\n[Thông tin test] Sử dụng mã phòng thử nghiệm: id_phong = {unique_room_id}")

    # -------------------------------------------------------------
    # 1. Test Tạo đơn bình thường (Ngày 2026-11-10 đến 2026-11-15)
    # -------------------------------------------------------------
    print("\n[Test 1] Tạo đơn đặt phòng đầu tiên (10/11 -> 15/11)")
    payload_1 = {
        "id_khach_san": 1,
        "ngay_nhan_phong": "2026-11-10",
        "ngay_tra_phong": "2026-11-15",
        "rooms": [
            {
                "id_phong": unique_room_id,
                "id_loai_phong": 1,
                "so_phong": f"P{unique_room_id}",
                "ten_loai_phong": "Deluxe Room",
                "gia": 1200000,
            }
        ],
        "khach_o": {
            "ho_ten": "Nguyen Van A",
            "email": "khachA@example.com",
            "sdt": "0912345678",
            "ghi_chu_dac_biet": "Check-in sớm nếu có thể",
        },
    }
    res1 = client.post("/api/v1/bookings", json=payload_1)
    assert res1.status_code == 201, f"Lỗi tạo booking 1: {res1.text}"
    bk1_data = res1.json()
    bk1_code = bk1_data["ma_booking"]
    print(f" -> Đặt phòng 1 thành công: ma_booking={bk1_code}, trang_thai={bk1_data['trang_thai']}")

    # -------------------------------------------------------------
    # 2. Test Chặn giao thoa ngày tuần tự
    # -------------------------------------------------------------
    print("\n[Test 2] Kiểm tra chặn giao thoa ngày tuần tự")
    # Trường hợp A: Giao thoa giữa kỳ (12/11 -> 14/11)
    payload_overlap_mid = dict(payload_1)
    payload_overlap_mid["ngay_nhan_phong"] = "2026-11-12"
    payload_overlap_mid["ngay_tra_phong"] = "2026-11-14"
    res_overlap_mid = client.post("/api/v1/bookings", json=payload_overlap_mid)
    assert res_overlap_mid.status_code == 409, f"Kỳ vọng 409, nhận: {res_overlap_mid.status_code}"
    print(f" -> Giao thoa giữa kỳ (12-14) bị từ chối 409: {res_overlap_mid.json().get('detail')}")

    # Trường hợp B: Giao thoa đầu kỳ (08/11 -> 12/11)
    payload_overlap_start = dict(payload_1)
    payload_overlap_start["ngay_nhan_phong"] = "2026-11-08"
    payload_overlap_start["ngay_tra_phong"] = "2026-11-12"
    res_overlap_start = client.post("/api/v1/bookings", json=payload_overlap_start)
    assert res_overlap_start.status_code == 409
    print(f" -> Giao thoa đầu kỳ (08-12) bị từ chối 409: {res_overlap_start.json().get('detail')}")

    # Trường hợp C: Giao thoa cuối kỳ (14/11 -> 18/11)
    payload_overlap_end = dict(payload_1)
    payload_overlap_end["ngay_nhan_phong"] = "2026-11-14"
    payload_overlap_end["ngay_tra_phong"] = "2026-11-18"
    res_overlap_end = client.post("/api/v1/bookings", json=payload_overlap_end)
    assert res_overlap_end.status_code == 409
    print(f" -> Giao thoa cuối kỳ (14-18) bị từ chối 409: {res_overlap_end.json().get('detail')}")

    # Trường hợp D: Không giao thoa (CheckOut đơn cũ = CheckIn đơn mới: 15/11 -> 20/11) -> Thành công!
    payload_adjacent = dict(payload_1)
    payload_adjacent["ngay_nhan_phong"] = "2026-11-15"
    payload_adjacent["ngay_tra_phong"] = "2026-11-20"
    res_adjacent = client.post("/api/v1/bookings", json=payload_adjacent)
    assert res_adjacent.status_code == 201, f"Lỗi ngày liền kề: {res_adjacent.text}"
    print(f" -> Ngày liền kề hợp lệ (15/11 -> 20/11) thành công: {res_adjacent.json()['ma_booking']}")
    print("[PASS] Test 2: Logic điều kiện giao thoa ngày CheckIn < CheckOut_old AND CheckOut > CheckIn_old chuẩn xác.")

    # -------------------------------------------------------------
    # 3. Test ĐỒNG THỜI (Race Condition Test với sp_getapplock):
    # Hai thread cùng gửi request đặt cùng một phòng vào cùng ngày tại cùng 1 tích tắc
    # -------------------------------------------------------------
    concurrent_room_id = int(str(uuid.uuid4().int)[:6])
    print(f"\n[Test 3] Kiểm tra RACE CONDITION: 2 request ĐỒNG THỜI đặt phòng #{concurrent_room_id}")

    conc_payload_a = {
        "id_khach_san": 1,
        "ngay_nhan_phong": "2026-12-01",
        "ngay_tra_phong": "2026-12-05",
        "rooms": [
            {
                "id_phong": concurrent_room_id,
                "id_loai_phong": 2,
                "so_phong": f"P{concurrent_room_id}",
                "ten_loai_phong": "Executive Suite",
                "gia": 2500000,
            }
        ],
        "khach_o": {
            "ho_ten": "Khach A Dong Thoi",
            "email": "khachA@concurrent.com",
            "sdt": "0988888881",
        },
    }
    conc_payload_b = {
        "id_khach_san": 1,
        "ngay_nhan_phong": "2026-12-03",  # Giao thoa với đơn A (12/01 -> 12/05)
        "ngay_tra_phong": "2026-12-07",
        "rooms": [
            {
                "id_phong": concurrent_room_id,
                "id_loai_phong": 2,
                "so_phong": f"P{concurrent_room_id}",
                "ten_loai_phong": "Executive Suite",
                "gia": 2500000,
            }
        ],
        "khach_o": {
            "ho_ten": "Khach B Dong Thoi",
            "email": "khachB@concurrent.com",
            "sdt": "0988888882",
        },
    }

    def send_booking(payload):
        c = TestClient(app)
        return c.post("/api/v1/bookings", json=payload)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(send_booking, conc_payload_a)
        f2 = executor.submit(send_booking, conc_payload_b)
        results = [f1.result(), f2.result()]

    status_codes = sorted([r.status_code for r in results])
    print(f" -> Kết quả 2 request đồng thời: Status codes = {status_codes}")
    assert status_codes == [201, 409], f"Kỳ vọng đúng 1 request 201 và 1 request 409, nhận: {status_codes}"

    # Kiểm tra DB: chỉ có duy nhất 1 booking được tạo cho khoảng thời gian này
    db.expire_all()
    active_bookings = (
        db.query(ChiTietDatPhongModel)
        .join(DatPhongModel, ChiTietDatPhongModel.id_dat_phong == DatPhongModel.id_dat_phong)
        .filter(
            ChiTietDatPhongModel.id_phong == concurrent_room_id,
            DatPhongModel.trang_thai == TrangThaiBookingEnum.PENDING_PAYMENT.value,
        )
        .all()
    )
    assert len(active_bookings) == 1, f"Bị overbooking! Số đơn trong DB: {len(active_bookings)}"
    print("[PASS] Test 3: Cơ chế khóa sp_getapplock tuần tự hóa thành công, loại bỏ 100% Race Condition.")

    # -------------------------------------------------------------
    # 4. Test Giải phóng đơn hết hạn giữ chỗ (Hold Release)
    # -------------------------------------------------------------
    print("\n[Test 4] Kiểm tra tự động nhả phòng khi quá hạn 15 phút giữ chỗ")
    expired_room_id = int(str(uuid.uuid4().int)[:6])
    
    # Tạo đơn đặt phòng
    res_exp = client.post("/api/v1/bookings", json={
        "id_khach_san": 1,
        "ngay_nhan_phong": "2026-12-10",
        "ngay_tra_phong": "2026-12-15",
        "rooms": [{
            "id_phong": expired_room_id,
            "id_loai_phong": 1,
            "so_phong": f"P{expired_room_id}",
            "ten_loai_phong": "Standard",
            "gia": 900000,
        }],
        "khach_o": {"ho_ten": "Khach Het Han", "email": "hethan@test.com", "sdt": "0900000000"},
    })
    assert res_exp.status_code == 201
    exp_bk_id = res_exp.json()["id_dat_phong"]

    # Giả lập lùi thời hạn han_giu_cho về quá khứ 20 phút trước
    db_exp_booking = db.query(DatPhongModel).filter(DatPhongModel.id_dat_phong == exp_bk_id).first()
    db_exp_booking.han_giu_cho = datetime.utcnow() - timedelta(minutes=20)
    db.commit()
    print(f" -> Đã chỉnh han_giu_cho của đơn #{exp_bk_id} về quá khứ 20 phút trước.")

    # Khách khác đặt lại đúng phòng và ngày đó -> Hệ thống phải tự nhả đơn cũ và cho phép đặt thành công!
    res_rebook = client.post("/api/v1/bookings", json={
        "id_khach_san": 1,
        "ngay_nhan_phong": "2026-12-10",
        "ngay_tra_phong": "2026-12-15",
        "rooms": [{
            "id_phong": expired_room_id,
            "id_loai_phong": 1,
            "so_phong": f"P{expired_room_id}",
            "ten_loai_phong": "Standard",
            "gia": 900000,
        }],
        "khach_o": {"ho_ten": "Khach Dat Lai", "email": "datlai@test.com", "sdt": "0911111111"},
    })
    assert res_rebook.status_code == 201, f"Lỗi đặt lại phòng đã hết hạn giữ chỗ: {res_rebook.text}"
    
    # Kiểm tra đơn cũ đã chuyển sang CANCELLED
    db.refresh(db_exp_booking)
    assert db_exp_booking.trang_thai == TrangThaiBookingEnum.CANCELLED.value
    print(f" -> Đơn cũ #{exp_bk_id} đã tự động chuyển sang CANCELLED, phòng được nhả và đơn mới được tạo thành công!")
    print("[PASS] Test 4: Giải phóng đơn hết hạn giữ chỗ hoạt động hoàn hảo.")

    db.close()
    print("\n" + "=" * 65)
    print(">>> TẤT CẢ 4 BÀI TEST CHỐNG OVERBOOKING ĐỀU ĐẠT 100%! <<<")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    test_overbooking_and_concurrency_protection()
