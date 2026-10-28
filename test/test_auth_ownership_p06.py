# -*- coding: utf-8 -*-
import sys
import os
import unittest
import jwt
from datetime import datetime, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

JWT_SECRET = "booking_super_secret_jwt_key_2026_xyz!@#"
JWT_ALGO = "HS256"

def make_token(user_id: int, role: str, email: str = "test@example.com", token_type: str = "access") -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "type": token_type,
        "exp": datetime.utcnow() + timedelta(hours=2),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def unload_src_modules():
    for mod in list(sys.modules.keys()):
        if mod == "src" or mod.startswith("src."):
            del sys.modules[mod]


def run_tests():
    print("=" * 60)
    print("RUNNING P0.6 AUTH & OWNERSHIP ACCEPTANCE TESTS")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. PAYMENT SERVICE TESTS
    # -------------------------------------------------------------
    print("\n--- 1. Testing Payment Service Auth & Role ---")
    unload_src_modules()
    payment_dir = os.path.join(PROJECT_ROOT, "services", "payment-service")
    if payment_dir not in sys.path:
        sys.path.insert(0, payment_dir)
    os.chdir(payment_dir)

    from fastapi.testclient import TestClient
    from src.main import app as payment_app

    client_pay = TestClient(payment_app)

    # Test 1.1: GET /payments without token -> 401
    res = client_pay.get("/api/v1/payments")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
    print("[PASS] 1.1 Unauthenticated GET /payments returns 401 Unauthorized")

    # Test 1.2: GET /payments/stats without token -> 401
    res = client_pay.get("/api/v1/payments/stats")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
    print("[PASS] 1.2 Unauthenticated GET /payments/stats returns 401 Unauthorized")

    # Test 1.3: POST /payments/create-payment without token -> 401
    res = client_pay.post("/api/v1/payments/create-payment", json={})
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
    print("[PASS] 1.3 Unauthenticated POST /payments/create-payment returns 401 Unauthorized")

    # Test 1.4: Regular CUSTOMER GET /payments -> 403 Forbidden
    cust_token = make_token(user_id=10, role="CUSTOMER")
    res = client_pay.get("/api/v1/payments", headers={"Authorization": f"Bearer {cust_token}"})
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    print("[PASS] 1.4 Customer GET /payments returns 403 Forbidden")

    # Test 1.5: Regular CUSTOMER GET /payments/stats -> 403 Forbidden
    res = client_pay.get("/api/v1/payments/stats", headers={"Authorization": f"Bearer {cust_token}"})
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    print("[PASS] 1.5 Customer GET /payments/stats returns 403 Forbidden")

    # Test 1.6: ADMIN GET /payments/stats -> 200 OK
    admin_token = make_token(user_id=1, role="ADMIN")
    res = client_pay.get("/api/v1/payments/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    print("[PASS] 1.6 Admin GET /payments/stats returns 200 OK")

    # -------------------------------------------------------------
    # 2. BOOKING SERVICE TESTS
    # -------------------------------------------------------------
    print("\n--- 2. Testing Booking Service Auth & Ownership ---")
    unload_src_modules()
    booking_dir = os.path.join(PROJECT_ROOT, "services", "booking-service")
    if payment_dir in sys.path:
        sys.path.remove(payment_dir)
    if booking_dir not in sys.path:
        sys.path.insert(0, booking_dir)
    os.chdir(booking_dir)

    # Use SQLite in-memory with StaticPool for isolated unit testing
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.orm import sessionmaker
    from src.core.database import Base, get_db
    from src.main import app as booking_app
    from src.models import DatPhongModel, ChiTietDatPhongModel, TrangThaiBookingEnum

    test_booking_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_booking_engine)
    Base.metadata.create_all(bind=test_booking_engine)

    def override_booking_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    booking_app.dependency_overrides[get_db] = override_booking_get_db
    client_bk = TestClient(booking_app)

    # Test 2.1: POST /bookings without token -> 401 Unauthorized
    res = client_bk.post("/api/v1/bookings", json={})
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
    print("[PASS] 2.1 Unauthenticated POST /bookings returns 401 Unauthorized")

    # Seed bookings directly into test DB
    seed_db = TestingSession()
    bk1 = DatPhongModel(
        ma_booking="BK-USER-10-TEST",
        id_tai_khoan=10,
        id_khach_san=1,
        ngay_nhan_phong=datetime.utcnow() + timedelta(days=2),
        ngay_tra_phong=datetime.utcnow() + timedelta(days=4),
        tong_tien=1500000.0,
        trang_thai=TrangThaiBookingEnum.PENDING_PAYMENT.value,
        han_giu_cho=datetime.utcnow() + timedelta(minutes=15),
    )
    bk2 = DatPhongModel(
        ma_booking="BK-USER-20-TEST",
        id_tai_khoan=20,
        id_khach_san=1,
        ngay_nhan_phong=datetime.utcnow() + timedelta(days=2),
        ngay_tra_phong=datetime.utcnow() + timedelta(days=4),
        tong_tien=2500000.0,
        trang_thai=TrangThaiBookingEnum.PENDING_PAYMENT.value,
        han_giu_cho=datetime.utcnow() + timedelta(minutes=15),
    )
    seed_db.add_all([bk1, bk2])
    seed_db.commit()
    seed_db.refresh(bk1)
    seed_db.refresh(bk2)
    bk1_id = bk1.id_dat_phong
    bk2_id = bk2.id_dat_phong
    seed_db.close()

    user10_token = make_token(user_id=10, role="CUSTOMER")
    user20_token = make_token(user_id=20, role="CUSTOMER")

    # Test 2.2: User 10 accessing User 10's booking -> 200 OK
    res = client_bk.get(f"/api/v1/bookings/{bk1_id}", headers={"Authorization": f"Bearer {user10_token}"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    assert res.json()["id_tai_khoan"] == 10
    print("[PASS] 2.2 User 10 viewing own booking returns 200 OK")

    # Test 2.3: User 10 accessing User 20's booking -> 403 Forbidden
    res = client_bk.get(f"/api/v1/bookings/{bk2_id}", headers={"Authorization": f"Bearer {user10_token}"})
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    print("[PASS] 2.3 User 10 viewing User 20's booking returns 403 Forbidden")

    # Test 2.4: User 10 attempting to cancel User 20's booking -> 403 Forbidden
    res = client_bk.patch(f"/api/v1/bookings/{bk2_id}/cancel", headers={"Authorization": f"Bearer {user10_token}"})
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    print("[PASS] 2.4 User 10 cancelling User 20's booking returns 403 Forbidden")

    # Test 2.5: ADMIN viewing User 20's booking -> 200 OK
    res = client_bk.get(f"/api/v1/bookings/{bk2_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    print("[PASS] 2.5 Admin viewing User 20's booking returns 200 OK")

    # Test 2.6: GET /bookings filters by current_user_id for customer
    res = client_bk.get("/api/v1/bookings", headers={"Authorization": f"Bearer {user10_token}"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    items = res.json()["items"]
    assert len(items) == 1 and items[0]["id_tai_khoan"] == 10, f"Customer list returned unexpected: {items}"
    print("[PASS] 2.6 Customer GET /bookings only returns bookings belonging to customer")

    # Test 2.7: GET /bookings returns all for admin
    res = client_bk.get("/api/v1/bookings", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    items = res.json()["items"]
    assert len(items) >= 2, f"Admin list should return all bookings: {items}"
    print("[PASS] 2.7 Admin GET /bookings returns all bookings")

    # -------------------------------------------------------------
    # 3. HOTEL SERVICE OWNERSHIP TESTS
    # -------------------------------------------------------------
    print("\n--- 3. Testing Hotel Service Ownership Check ---")
    unload_src_modules()
    hotel_dir = os.path.join(PROJECT_ROOT, "services", "hotel-service")
    if booking_dir in sys.path:
        sys.path.remove(booking_dir)
    if hotel_dir not in sys.path:
        sys.path.insert(0, hotel_dir)
    os.chdir(hotel_dir)

    from src.models import KhachSanModel
    from src.services.hotel_service import _check_ownership
    from src.api.dependencies import PartnerUser
    from fastapi import HTTPException

    fake_hotel = KhachSanModel(id_khach_san=101, id_tai_khoan=50)

    # Test 3.1: True owner PartnerUser(50, role='PARTNER') -> Allowed
    try:
        _check_ownership(fake_hotel, PartnerUser(50, role="PARTNER"))
        print("[PASS] 3.1 Hotel owner (id=50) passed ownership check")
    except Exception as e:
        assert False, f"Expected ownership pass, got {e}"

    # Test 3.2: Other partner PartnerUser(51, role='PARTNER') -> 403 Forbidden
    try:
        _check_ownership(fake_hotel, PartnerUser(51, role="PARTNER"))
        assert False, "Expected 403 for different partner, but was allowed!"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403, got {e.status_code}"
        print("[PASS] 3.2 Different partner (id=51) rejected with 403 Forbidden")

    # Test 3.3: Partner 1 (old hardcoded bypass) is now rejected if not owner!
    try:
        _check_ownership(fake_hotel, PartnerUser(1, role="PARTNER"))
        assert False, "Expected 403 for Partner 1 on another partner's hotel!"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403, got {e.status_code}"
        print("[PASS] 3.3 Old bypass partner_id=1 correctly rejected with 403 Forbidden if not ADMIN")

    # Test 3.4: Admin PartnerUser(99, role='ADMIN') -> Allowed
    try:
        _check_ownership(fake_hotel, PartnerUser(99, role="ADMIN"))
        print("[PASS] 3.4 Admin (role=ADMIN) passed ownership check regardless of ID")
    except Exception as e:
        assert False, f"Expected admin pass, got {e}"

    # -------------------------------------------------------------
    # 4. ROOM SERVICE OWNERSHIP TESTS
    # -------------------------------------------------------------
    print("\n--- 4. Testing Room Service Ownership Check ---")
    unload_src_modules()
    room_dir = os.path.join(PROJECT_ROOT, "services", "room-service")
    if hotel_dir in sys.path:
        sys.path.remove(hotel_dir)
    if room_dir not in sys.path:
        sys.path.insert(0, room_dir)
    os.chdir(room_dir)

    from src.api.v1.dependencies import check_hotel_ownership

    # Test 4.1: Admin user payload -> Allowed
    admin_user = {"sub": "99", "role": "ADMIN"}
    try:
        check_hotel_ownership(hotel_id=101, user=admin_user)
        print("[PASS] 4.1 Room check_hotel_ownership: Admin allowed")
    except Exception as e:
        assert False, f"Expected admin pass, got {e}"

    # Test 4.2: Partner with conflicting hotel_id in token -> 403 Forbidden
    partner_user = {"sub": "50", "role": "PARTNER", "hotel_id": 999}
    try:
        check_hotel_ownership(hotel_id=101, user=partner_user)
        assert False, "Expected 403 when partner hotel_id does not match"
    except HTTPException as e:
        assert e.status_code == 403, f"Expected 403, got {e.status_code}"
        print("[PASS] 4.2 Room check_hotel_ownership: Partner with mismatched hotel_id rejected with 403")

    print("\n" + "=" * 60)
    print(">>> ALL P0.6 ACCEPTANCE TESTS PASSED SUCCESSFULLY! (16/16 Checks)")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
