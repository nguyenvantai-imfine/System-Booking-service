import importlib
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEST_JWT_SECRET = "unit-test-only-jwt-secret-with-adequate-length"


def load_service_module(service_name, module_name):
    for imported_module in list(sys.modules):
        if imported_module == "src" or imported_module.startswith("src."):
            del sys.modules[imported_module]
    for path in list(sys.path):
        normalized_path = os.path.normcase(os.path.abspath(path or os.getcwd()))
        if normalized_path.startswith(
            os.path.normcase(os.path.join(PROJECT_ROOT, "services"))
        ):
            sys.path.remove(path)
    service_path = os.path.join(PROJECT_ROOT, "services", service_name)
    sys.path.insert(0, service_path)
    os.chdir(service_path)
    module = importlib.import_module(module_name)
    config = importlib.import_module("src.core.config")
    config.settings.JWT_SECRET_KEY = TEST_JWT_SECRET
    return module


class TestLegacyNumericBearerFallback(unittest.TestCase):
    def _credentials(self, token):
        return HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

    def _token(self, user_id, role):
        return jwt.encode(
            {
                "sub": str(user_id),
                "role": role,
                "type": "access",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
            TEST_JWT_SECRET,
            algorithm="HS256",
        )

    def test_hotel_rejects_numeric_bearer_and_accepts_signed_jwt(self):
        dependencies = load_service_module(
            "hotel-service",
            "src.api.dependencies",
        )
        with self.assertRaises(HTTPException) as raised:
            dependencies.get_current_partner_id(self._credentials("17"))
        self.assertEqual(raised.exception.status_code, 401)

        partner = dependencies.get_current_partner_id(
            self._credentials(self._token(17, "PARTNER"))
        )
        self.assertEqual(int(partner), 17)

    def test_payment_rejects_numeric_bearer_and_accepts_signed_jwt(self):
        dependencies = load_service_module(
            "payment-service",
            "src.api.dependencies",
        )
        with self.assertRaises(HTTPException) as raised:
            dependencies.get_current_user_payload(self._credentials("17"))
        self.assertEqual(raised.exception.status_code, 401)

        payload = dependencies.get_current_user_payload(
            self._credentials(self._token(17, "CUSTOMER"))
        )
        self.assertEqual(payload["sub"], "17")

    def test_hotel_and_payment_fail_closed_without_jwt_configuration(self):
        for service_name in ("hotel-service", "payment-service"):
            with self.subTest(service=service_name):
                module_name = (
                    "src.api.dependencies"
                )
                dependencies = load_service_module(service_name, module_name)
                config = importlib.import_module("src.core.config")
                config.settings.JWT_SECRET_KEY = ""
                function = (
                    dependencies.get_current_partner_id
                    if service_name == "hotel-service"
                    else dependencies.get_current_user_payload
                )
                with self.assertRaises(HTTPException) as raised:
                    function(self._credentials("17"))
                self.assertEqual(raised.exception.status_code, 503)

    def test_user_and_booking_token_helpers_fail_without_jwt_configuration(self):
        user_security = load_service_module(
            "user-service",
            "src.core.security",
        )
        config = importlib.import_module("src.core.config")
        config.settings.JWT_SECRET_KEY = ""
        with self.assertRaisesRegex(RuntimeError, "JWT_SECRET_KEY"):
            user_security.create_access_token({"sub": "17"})

        booking_security = load_service_module(
            "booking-service",
            "src.core.security",
        )
        config = importlib.import_module("src.core.config")
        config.settings.JWT_SECRET_KEY = ""
        with self.assertRaisesRegex(ValueError, "JWT_SECRET_KEY"):
            booking_security.decode_token("not-a-token")


if __name__ == "__main__":
    unittest.main()
