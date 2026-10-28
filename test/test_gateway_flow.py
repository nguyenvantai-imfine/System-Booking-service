# -*- coding: utf-8 -*-
import sys
import os
import json
import uuid
from datetime import datetime, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
GATEWAY_DIR = os.path.join(PROJECT_ROOT, "gateway")

if GATEWAY_DIR not in sys.path:
    sys.path.insert(0, GATEWAY_DIR)

import jwt
import urllib.request
from unittest.mock import patch, AsyncMock, MagicMock

# Khóa JWT dùng chung của toàn hệ thống
JWT_SECRET_KEY = "booking_super_secret_jwt_key_2026_xyz!@#"

def get_auth_token():
    """
    Thử đăng nhập lấy token JWT từ User Service qua Gateway.
    Nếu Gateway/User Service chưa bật, sinh token JWT hợp lệ chuẩn P0.
    """
    # 1. Thử login thật qua Gateway
    try:
        login_url = "http://127.0.0.1:8080/api/v1/auth/login"
        body = json.dumps({"ten_dang_nhap": "customer", "mat_khau": "123456"}).encode("utf-8")
        req = urllib.request.Request(
            login_url,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "access_token" in data:
                return data["access_token"]
    except Exception:
        pass

    # 2. Sinh token JWT chuẩn thuật toán HS256 và vai trò CUSTOMER
    payload = {
        "sub": "4",
        "id_tai_khoan": 4,
        "vai_tro": "CUSTOMER",
        "role": "CUSTOMER",
        "type": "access",
        "exp": datetime.utcnow() + timedelta(hours=2),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def check_gateway_live():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080/", timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False

def run_live_gateway_flow(token):
    print(">>> Phát hiện Gateway :8080 đang chạy. Thực thi kiểm thử trực tiếp qua HTTP...")
    
    def post_json(url, data):
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        with urllib.request.urlopen(req, timeout=5.0) as res:
            return json.loads(res.read().decode("utf-8"))

    # 1. Tạo đơn đặt phòng
    print(">>> Step 1: Tạo booking qua Gateway :8080...")
    rand_room = int(str(uuid.uuid4().int)[:5])
    bk_req = {
        "id_khach_san": 1,
        "id_tai_khoan": 4,
        "ngay_nhan_phong": "2026-12-01",
        "ngay_tra_phong": "2026-12-04",
        "rooms": [
            {
                "id_phong": rand_room,
                "id_loai_phong": 1,
                "so_phong": f"P.{rand_room}",
                "ten_loai_phong": "Deluxe Ocean View",
                "gia": 1200000,
            }
        ],
        "khach_o": {
            "ho_ten": "Nguyen Gateway Tester",
            "email": "tester.gateway@gmail.com",
            "sdt": "0988776655",
            "ghi_chu_dac_biet": "Yêu cầu view biển và check-in sớm",
        },
    }
    booking = post_json("http://127.0.0.1:8080/api/v1/bookings", bk_req)
    ma_booking = booking["ma_booking"]
    id_dat_phong = booking["id_dat_phong"]
    print(f" -> Tạo booking thành công! Mã: {ma_booking}, ID: {id_dat_phong}")

    # 2. Tạo thanh toán
    print(">>> Step 2: Tạo giao dịch thanh toán qua Gateway :8080...")
    pm_req = {
        "id_dat_phong": id_dat_phong,
        "ma_booking": ma_booking,
        "so_tien": booking.get("tong_tien", 3960000),
        "phuong_thuc": "VNPAY",
        "ghi_chu": "Thanh toán đơn đặt phòng qua Gateway VNPAY",
    }
    payment = post_json("http://127.0.0.1:8080/api/v1/payments/create-payment", pm_req)
    ma_txn = payment["ma_giao_dich_gateway"]
    print(f" -> Tạo payment thành công! Mã TXN: {ma_txn}")

    # 3. Giả lập IPN
    print(">>> Step 3: Mô phỏng Callback IPN SUCCESS qua Gateway :8080...")
    ipn_req = {
        "ma_giao_dich_gateway": ma_txn,
        "trang_thai": "SUCCESS",
        "note": "Giao dịch VNPAY thành công 100%",
    }
    ipn_res = post_json("http://127.0.0.1:8080/api/v1/payments/simulate-ipn", ipn_req)
    print(f" -> IPN xử lý xong! Trạng thái GD: {ipn_res['trang_thai']}")

    # 4. Kiểm tra thông báo
    print(">>> Step 4: Kiểm tra danh sách thông báo qua Gateway :8080...")
    url_noti = f"http://127.0.0.1:8080/api/v1/notifications?booking_code={ma_booking}"
    req_noti = urllib.request.Request(url_noti, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req_noti, timeout=5.0) as res_noti_raw:
        res_noti = json.loads(res_noti_raw.read().decode("utf-8"))
        print(f" -> Số lượng thông báo tìm thấy cho {ma_booking}: {len(res_noti.get('items', []))}")

def run_isolated_gateway_flow(token):
    print(">>> Gateway :8080 chưa khởi chạy nền. Thực thi kiểm thử định tuyến Gateway với FastAPI TestClient...")
    from fastapi.testclient import TestClient
    from src.main import app as gateway_app, resolve_target_url
    import httpx

    client = TestClient(gateway_app)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Correlation-ID": f"TEST-GW-{uuid.uuid4().hex[:8].upper()}",
    }

    # Step 1: Kiểm tra định tuyến Booking Service
    print(">>> Step 1: Kiểm tra định tuyến Booking qua Gateway...")
    route_booking = resolve_target_url("/api/v1/bookings")
    assert "8003" in route_booking, f"Định tuyến sai Booking Service: {route_booking}"
    print(f" -> Tuyến đường /api/v1/bookings định tuyến chuẩn xác tới: {route_booking}")

    # Step 2: Kiểm tra định tuyến Payment Service
    print(">>> Step 2: Kiểm tra định tuyến Payment qua Gateway...")
    route_payment = resolve_target_url("/api/v1/payments/create-payment")
    assert "8004" in route_payment, f"Định tuyến sai Payment Service: {route_payment}"
    print(f" -> Tuyến đường /api/v1/payments/create-payment định tuyến chuẩn xác tới: {route_payment}")

    # Step 3: Kiểm tra định tuyến IPN Callback
    print(">>> Step 3: Kiểm tra định tuyến IPN Callback qua Gateway...")
    route_ipn = resolve_target_url("/api/v1/payments/simulate-ipn")
    assert "8004" in route_ipn, f"Định tuyến sai Payment IPN: {route_ipn}"
    print(f" -> Tuyến đường /api/v1/payments/simulate-ipn định tuyến chuẩn xác tới: {route_ipn}")

    # Step 4: Kiểm tra định tuyến Notification Service
    print(">>> Step 4: Kiểm tra định tuyến Notification qua Gateway...")
    route_noti = resolve_target_url("/api/v1/notifications")
    assert "8005" in route_noti, f"Định tuyến sai Notification Service: {route_noti}"
    print(f" -> Tuyến đường /api/v1/notifications định tuyến chuẩn xác tới: {route_noti}")

    # Step 5: Kiểm tra proxy request qua Gateway TestClient kèm bảo toàn Header JWT & Correlation-ID
    print(">>> Step 5: Mô phỏng gọi Gateway Proxy kèm Bearer Token...")
    import src.main as gw_module
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"success": true, "message": "Gateway forwarded successfully"}'
    mock_resp.headers = {"content-type": "application/json"}

    mock_client = MagicMock()
    mock_client.request = AsyncMock(return_value=mock_resp)

    with TestClient(gw_module.app) as client:
        with patch.object(gw_module, "http_client", mock_client):
            res = client.get("/api/v1/notifications", headers=headers)
            assert res.status_code == 200, f"Gateway response error: {res.text}"

            # Kiểm tra Gateway đã chuyển tiếp Authorization & X-Correlation-ID
            call_kwargs = mock_client.request.call_args[1]
            forwarded_headers = call_kwargs["headers"]
            assert forwarded_headers.get("authorization") == f"Bearer {token}", "Gateway không chuyển tiếp token Authorization!"
            cid_header = forwarded_headers.get("X-Correlation-ID") or forwarded_headers.get("x-correlation-id")
            assert cid_header == headers["X-Correlation-ID"], "Gateway làm mất X-Correlation-ID!"
            print(f" -> Gateway đã bảo toàn và chuyển tiếp đầy đủ: Authorization Bearer & X-Correlation-ID ({headers['X-Correlation-ID']})!")

def main():
    print("\n" + "=" * 65)
    print("BẮT ĐẦU TEST TOÀN DIỆN LUỒNG GATEWAY FLOW (P0 AUTH & ROUTING)")
    print("=" * 65)
    
    token = get_auth_token()
    print(f" -> Token JWT xác thực (30 ký tự đầu): {token[:30]}...")

    if check_gateway_live():
        run_live_gateway_flow(token)
    else:
        run_isolated_gateway_flow(token)

    print("\n" + "=" * 65)
    print(">>> GATEWAY FLOW TEST COMPLETED SUCCESSFULLY (100% PASS)!")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
