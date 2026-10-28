# -*- coding: utf-8 -*-
import sys
import os
import re
from unittest.mock import patch, MagicMock

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

os.chdir(GATEWAY_DIR)

from fastapi.testclient import TestClient
from src.main import app, resolve_target_url
from src.core.config import settings

def test_gateway_routing_and_frontend_unification():
    print("=" * 70)
    print("BẮT ĐẦU TEST P2.1 & P2.2: HỢP NHẤT FRONTEND QUA GATEWAY & SỬA LỖI ĐỊNH TUYẾN")
    print("=" * 70)

    # =========================================================================
    # CHECK 1: Kiểm tra resolve_target_url trực tiếp với tất cả các tuyến đường
    # =========================================================================
    print("\n[CHECK 1] Kiểm tra định tuyến chính xác trong resolve_target_url...")

    # 1.1 Route /api/v1/room-types phải trỏ về ROOM_SERVICE_URL
    r1 = resolve_target_url("/api/v1/room-types")
    expected_r1 = f"{settings.ROOM_SERVICE_URL}/api/v1/room-types"
    assert r1 == expected_r1, f"Sai định tuyến /room-types! Nhận: {r1}, Kỳ vọng: {expected_r1}"
    print(f" -> [PASS] /api/v1/room-types => {r1}")

    r1_sub = resolve_target_url("/api/v1/room-types/10")
    expected_r1_sub = f"{settings.ROOM_SERVICE_URL}/api/v1/room-types/10"
    assert r1_sub == expected_r1_sub, f"Sai định tuyến /room-types/10! Nhận: {r1_sub}"
    print(f" -> [PASS] /api/v1/room-types/10 => {r1_sub}")

    # 1.2 Route /api/v1/hotels/{id}/rooms phải trỏ về ROOM_SERVICE_URL (không phải HOTEL_SERVICE_URL)
    r2 = resolve_target_url("/api/v1/hotels/1/rooms")
    expected_r2 = f"{settings.ROOM_SERVICE_URL}/api/v1/hotels/1/rooms"
    assert r2 == expected_r2, f"Sai định tuyến /hotels/1/rooms! Nhận: {r2}, Kỳ vọng: {expected_r2}"
    print(f" -> [PASS] /api/v1/hotels/1/rooms => {r2} (Room Service)")

    # 1.3 Route /api/v1/hotels/{id}/room-types phải trỏ về ROOM_SERVICE_URL
    r3 = resolve_target_url("/api/v1/hotels/1/room-types")
    expected_r3 = f"{settings.ROOM_SERVICE_URL}/api/v1/hotels/1/room-types"
    assert r3 == expected_r3, f"Sai định tuyến /hotels/1/room-types! Nhận: {r3}, Kỳ vọng: {expected_r3}"
    print(f" -> [PASS] /api/v1/hotels/1/room-types => {r3} (Room Service)")

    r3_sub = resolve_target_url("/api/v1/hotels/99/room-types/5")
    expected_r3_sub = f"{settings.ROOM_SERVICE_URL}/api/v1/hotels/99/room-types/5"
    assert r3_sub == expected_r3_sub, f"Sai định tuyến /hotels/99/room-types/5! Nhận: {r3_sub}"
    print(f" -> [PASS] /api/v1/hotels/99/room-types/5 => {r3_sub} (Room Service)")

    # 1.4 Route /api/v1/hotels/... thông thường vẫn phải trỏ về HOTEL_SERVICE_URL
    r4 = resolve_target_url("/api/v1/hotels")
    expected_r4 = f"{settings.HOTEL_SERVICE_URL}/api/v1/hotels"
    assert r4 == expected_r4, f"Sai định tuyến /hotels! Nhận: {r4}, Kỳ vọng: {expected_r4}"
    print(f" -> [PASS] /api/v1/hotels => {r4} (Hotel Service)")

    r4_id = resolve_target_url("/api/v1/hotels/1")
    expected_r4_id = f"{settings.HOTEL_SERVICE_URL}/api/v1/hotels/1"
    assert r4_id == expected_r4_id, f"Sai định tuyến /hotels/1! Nhận: {r4_id}, Kỳ vọng: {expected_r4_id}"
    print(f" -> [PASS] /api/v1/hotels/1 => {r4_id} (Hotel Service)")

    # 1.5 Các route microservices khác vẫn được bảo toàn
    assert resolve_target_url("/api/v1/rooms/available") == f"{settings.ROOM_SERVICE_URL}/api/v1/rooms/available"
    assert resolve_target_url("/api/v1/auth/login") == f"{settings.USER_SERVICE_URL}/api/v1/auth/login"
    assert resolve_target_url("/api/v1/users/me") == f"{settings.USER_SERVICE_URL}/api/v1/users/me"
    assert resolve_target_url("/api/v1/admin/users") == f"{settings.USER_SERVICE_URL}/api/v1/admin/users"
    assert resolve_target_url("/api/v1/bookings") == f"{settings.BOOKING_SERVICE_URL}/api/v1/bookings"
    assert resolve_target_url("/api/v1/payments") == f"{settings.PAYMENT_SERVICE_URL}/api/v1/payments"
    assert resolve_target_url("/api/v1/notifications") == f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/notifications"
    assert resolve_target_url("/api/v1/invalid-service/xyz") is None
    print(" -> [PASS] Tất cả các tuyến microservices khác (auth, users, admin, bookings, payments, notifications) hoạt động chuẩn.")

    # =========================================================================
    # CHECK 2: Proxy HTTP Request qua Gateway Client
    # =========================================================================
    print("\n[CHECK 2] Kiểm tra chuyển tiếp HTTP Request qua Gateway Proxy...")
    client = TestClient(app)

    captured_proxy_calls = []

    async def mock_proxy_request(method, url, headers=None, content=None):
        captured_proxy_calls.append({"method": method, "url": str(url), "headers": headers})
        import httpx
        return httpx.Response(
            status_code=200,
            json={"status": "mock_forwarded_ok", "target_url": str(url)},
            headers={"content-type": "application/json"},
        )

    import src.main as gw_main
    mock_http_client = MagicMock()
    mock_http_client.request = mock_proxy_request
    gw_main.http_client = mock_http_client

    # Test GET /api/v1/room-types qua Gateway
    captured_proxy_calls.clear()
    res1 = client.get("/api/v1/room-types")
    assert res1.status_code == 200
    assert len(captured_proxy_calls) == 1
    assert captured_proxy_calls[0]["url"] == f"{settings.ROOM_SERVICE_URL}/api/v1/room-types"
    print(f" -> [PASS] GET /api/v1/room-types -> Chuyển tiếp tới: {captured_proxy_calls[0]['url']}")

    # Test GET /api/v1/hotels/1/rooms qua Gateway
    captured_proxy_calls.clear()
    res2 = client.get("/api/v1/hotels/1/rooms?page=1&page_size=20")
    assert res2.status_code == 200
    assert len(captured_proxy_calls) == 1
    assert captured_proxy_calls[0]["url"] == f"{settings.ROOM_SERVICE_URL}/api/v1/hotels/1/rooms?page=1&page_size=20"
    print(f" -> [PASS] GET /api/v1/hotels/1/rooms -> Chuyển tiếp tới: {captured_proxy_calls[0]['url']}")

    # Test GET /api/v1/hotels/1/room-types qua Gateway
    captured_proxy_calls.clear()
    res3 = client.get("/api/v1/hotels/1/room-types")
    assert res3.status_code == 200
    assert len(captured_proxy_calls) == 1
    assert captured_proxy_calls[0]["url"] == f"{settings.ROOM_SERVICE_URL}/api/v1/hotels/1/room-types"
    print(f" -> [PASS] GET /api/v1/hotels/1/room-types -> Chuyển tiếp tới: {captured_proxy_calls[0]['url']}")

    # Test GET /api/v1/hotels/1 (thông tin khách sạn) qua Gateway -> Vẫn về HOTEL_SERVICE_URL
    captured_proxy_calls.clear()
    res4 = client.get("/api/v1/hotels/1")
    assert res4.status_code == 200
    assert len(captured_proxy_calls) == 1
    assert captured_proxy_calls[0]["url"] == f"{settings.HOTEL_SERVICE_URL}/api/v1/hotels/1"
    print(f" -> [PASS] GET /api/v1/hotels/1 -> Chuyển tiếp tới: {captured_proxy_calls[0]['url']}")

    # =========================================================================
    # CHECK 3: Cấu hình Frontend cấu hình Gateway 8080
    # =========================================================================
    print("\n[CHECK 3] Kiểm tra cấu hình Frontend trỏ 100% về Gateway :8080...")
    # Kiểm tra customer-web lib/api.ts
    cw_api_path = os.path.join(PROJECT_ROOT, "front-end", "apps", "customer-web", "src", "lib", "api.ts")
    with open(cw_api_path, "r", encoding="utf-8") as f:
        cw_content = f.read()
    assert 'process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8080/api/v1"' in cw_content
    assert 'gatewayUrl: GATEWAY_API_BASE_URL' in cw_content
    print(" -> [PASS] customer-web/src/lib/api.ts đã cấu hình GATEWAY_API_BASE_URL (http://localhost:8080/api/v1).")

    # Kiểm tra admin-dashboard lib/api.ts
    ad_api_path = os.path.join(PROJECT_ROOT, "front-end", "apps", "admin-dashboard", "src", "lib", "api.ts")
    with open(ad_api_path, "r", encoding="utf-8") as f:
        ad_content = f.read()
    assert 'process.env.NEXT_PUBLIC_GATEWAY_URL' in ad_content
    assert '"http://localhost:8080/api/v1"' in ad_content
    assert 'gatewayUrl: GATEWAY_API_BASE_URL' in ad_content
    print(" -> [PASS] admin-dashboard/src/lib/api.ts đã cấu hình GATEWAY_API_BASE_URL (http://localhost:8080/api/v1).")

    # Kiểm tra .env.example của 2 app
    cw_env_path = os.path.join(PROJECT_ROOT, "front-end", "apps", "customer-web", ".env.example")
    with open(cw_env_path, "r", encoding="utf-8") as f:
        cw_env = f.read()
    assert "NEXT_PUBLIC_GATEWAY_URL=http://localhost:8080/api/v1" in cw_env
    print(" -> [PASS] customer-web/.env.example chứa NEXT_PUBLIC_GATEWAY_URL=http://localhost:8080/api/v1.")

    ad_env_path = os.path.join(PROJECT_ROOT, "front-end", "apps", "admin-dashboard", ".env.example")
    with open(ad_env_path, "r", encoding="utf-8") as f:
        ad_env = f.read()
    assert "NEXT_PUBLIC_GATEWAY_URL=http://localhost:8080/api/v1" in ad_env
    print(" -> [PASS] admin-dashboard/.env.example chứa NEXT_PUBLIC_GATEWAY_URL=http://localhost:8080/api/v1.")

    # Kiểm tra @repo/api-client
    client_pkg_path = os.path.join(PROJECT_ROOT, "front-end", "packages", "api-client", "src", "index.ts")
    with open(client_pkg_path, "r", encoding="utf-8") as f:
        client_pkg = f.read()
    assert "const base = this.gatewayUrl || customBaseUrl || this.baseUrl;" in client_pkg
    print(" -> [PASS] @repo/api-client ưu tiên gatewayUrl cho toàn bộ request.")

    print("\n" + "=" * 70)
    print(">>> TẤT CẢ CÁC KIỂM TRA P2.1 & P2.2 ĐỀU ĐẠT 100%!")
    print("=" * 70)

if __name__ == "__main__":
    test_gateway_routing_and_frontend_unification()
