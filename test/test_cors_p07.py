import os
import sys
import unittest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SERVICES = [
    ("Gateway", os.path.join(PROJECT_ROOT, "gateway")),
    ("User Service", os.path.join(PROJECT_ROOT, "services", "user-service")),
    ("Hotel Service", os.path.join(PROJECT_ROOT, "services", "hotel-service")),
    ("Room Service", os.path.join(PROJECT_ROOT, "services", "room-service")),
    ("Booking Service", os.path.join(PROJECT_ROOT, "services", "booking-service")),
    ("Payment Service", os.path.join(PROJECT_ROOT, "services", "payment-service")),
    ("Notification Service", os.path.join(PROJECT_ROOT, "services", "notification-service")),
]

def load_service_app(service_dir: str):
    # Unload any previously loaded src modules
    for mod in list(sys.modules.keys()):
        if mod == "src" or mod.startswith("src."):
            del sys.modules[mod]

    # Put service_dir first on sys.path
    if service_dir in sys.path:
        sys.path.remove(service_dir)
    sys.path.insert(0, service_dir)

    import importlib
    main_mod = importlib.import_module("src.main")
    config_mod = importlib.import_module("src.core.config")
    return main_mod.app, config_mod.settings

class TestCorsConfiguration(unittest.TestCase):

    def test_cors_origins_parsing(self):
        """Kiểm tra parser chuỗi phân tách bằng dấu phẩy và JSON string cho CORS_ORIGINS"""
        from pydantic_settings import BaseSettings
        from pydantic import field_validator
        from typing import List, Union

        class DummyConfig(BaseSettings):
            CORS_ORIGINS: List[str] = ["http://localhost:3000"]

            @field_validator("CORS_ORIGINS", mode="before")
            @classmethod
            def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
                if isinstance(v, str):
                    v = v.strip()
                    if v.startswith("[") and v.endswith("]"):
                        import json
                        try:
                            return json.loads(v)
                        except Exception:
                            pass
                    return [i.strip() for i in v.split(",") if i.strip()]
                return v

        # Test comma-separated string
        c1 = DummyConfig(CORS_ORIGINS="http://localhost:3000,http://localhost:3001,https://domain.com")
        self.assertEqual(c1.CORS_ORIGINS, ["http://localhost:3000", "http://localhost:3001", "https://domain.com"])

        # Test JSON string
        c2 = DummyConfig(CORS_ORIGINS='["http://localhost:3000", "http://localhost:3001"]')
        self.assertEqual(c2.CORS_ORIGINS, ["http://localhost:3000", "http://localhost:3001"])

        # Test list input
        c3 = DummyConfig(CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"])
        self.assertEqual(c3.CORS_ORIGINS, ["http://localhost:3000", "http://localhost:3001"])

    def test_services_cors_behavior(self):
        """Kiểm tra cấu hình CORS thực tế trên Gateway và 6 Backend Services"""
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ]
        evil_origin = "http://evil-site.com"

        for service_name, service_dir in SERVICES:
            with self.subTest(service=service_name):
                print(f"\n[TESTING CORS] {service_name} at {service_dir}")
                app, settings = load_service_app(service_dir)

                # 1. Kiểm tra CORS_ORIGINS trong settings
                self.assertTrue(hasattr(settings, "CORS_ORIGINS"), f"{service_name} settings missing CORS_ORIGINS")
                self.assertIsInstance(settings.CORS_ORIGINS, list)
                for origin in allowed_origins:
                    self.assertIn(origin, settings.CORS_ORIGINS, f"{origin} not in {service_name} CORS_ORIGINS")

                client = TestClient(app)

                # 2. Test preflight OPTIONS request từ allowed origin 1 (Customer Web)
                headers_preflight_1 = {
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Authorization,Content-Type",
                }
                res_preflight_1 = client.options("/", headers=headers_preflight_1)
                self.assertEqual(res_preflight_1.headers.get("access-control-allow-origin"), "http://localhost:3000")
                self.assertEqual(res_preflight_1.headers.get("access-control-allow-credentials"), "true")

                # 3. Test preflight OPTIONS request từ allowed origin 2 (Admin Web)
                headers_preflight_2 = {
                    "Origin": "http://localhost:3001",
                    "Access-Control-Request-Method": "POST",
                }
                res_preflight_2 = client.options("/", headers=headers_preflight_2)
                self.assertEqual(res_preflight_2.headers.get("access-control-allow-origin"), "http://localhost:3001")
                self.assertEqual(res_preflight_2.headers.get("access-control-allow-credentials"), "true")

                # 4. Test preflight OPTIONS request từ EVIL ORIGIN -> Phải bị chặn
                headers_preflight_evil = {
                    "Origin": evil_origin,
                    "Access-Control-Request-Method": "GET",
                }
                res_preflight_evil = client.options("/", headers=headers_preflight_evil)
                # Khi bị chặn, FastAPI/Starlette CORSMiddleware KHÔNG trả về access-control-allow-origin
                self.assertIsNone(
                    res_preflight_evil.headers.get("access-control-allow-origin"),
                    f"CORS security breach! {service_name} allowed evil origin!"
                )

                # 5. Test GET request thực tế từ allowed origin
                headers_get_allowed = {"Origin": "http://localhost:3000"}
                res_get_allowed = client.get("/", headers=headers_get_allowed)
                self.assertEqual(res_get_allowed.headers.get("access-control-allow-origin"), "http://localhost:3000")
                self.assertEqual(res_get_allowed.headers.get("access-control-allow-credentials"), "true")

                # 6. Test GET request thực tế từ EVIL origin
                headers_get_evil = {"Origin": evil_origin}
                res_get_evil = client.get("/", headers=headers_get_evil)
                self.assertIsNone(
                    res_get_evil.headers.get("access-control-allow-origin"),
                    f"CORS security breach! {service_name} allowed evil origin on GET!"
                )
                print(f"  -> {service_name} CORS tests PASSED.")

if __name__ == "__main__":
    unittest.main()
