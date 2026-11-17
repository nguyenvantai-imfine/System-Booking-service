"""Offline regressions: no SQL Server, broker or SMTP writes."""
import asyncio
import importlib
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from test_legacy_auth_fallback import load_service_module, TEST_JWT_SECRET


class StabilizationSecurityTests(unittest.TestCase):
    def test_sandbox_rejects_script_injection_and_anonymous_ipn(self):
        from fastapi.testclient import TestClient
        module = load_service_module("payment-service", "src.main")
        client = TestClient(module.app)
        response = client.get("/api/v1/payments/sandbox-checkout", params={"txn":"valid-txn", "booking":"<script>alert(1)</script>"})
        self.assertEqual(response.status_code, 422)
        response = client.post("/api/v1/payments/simulate-ipn", json={"ma_giao_dich_gateway":"valid-txn", "trang_thai":"SUCCESS"})
        self.assertEqual(response.status_code, 401)

    def test_health_checks_report_database_outages(self):
        from fastapi.testclient import TestClient
        for name in ("hotel", "user", "room", "booking", "payment"):
            with self.subTest(service=name):
                module = load_service_module(f"{name}-service", "src.main")
                database = importlib.import_module("src.core.database")
                with patch.object(database.engine, "connect", side_effect=RuntimeError("offline")):
                    response = TestClient(module.app).get("/health")
                self.assertEqual(response.status_code, 503)
                self.assertFalse(response.json()["database_connected"])

    def test_all_services_reject_tokens_signed_with_another_key(self):
        token = jwt.encode({"sub": "1", "role": "ADMIN", "type": "access"}, "untrusted-test-signing-key-with-32-characters", algorithm="HS256")
        for name in ("user", "hotel", "room", "booking", "payment", "notification"):
            with self.subTest(service=name):
                security = load_service_module(f"{name}-service", "src.core.security")
                with self.assertRaises((jwt.PyJWTError, ValueError, HTTPException)):
                    if name == "notification":
                        security.require_admin(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
                    else:
                        security.decode_token(token)

    def test_bcrypt_only_passwords_and_new_sql_seed_hash(self):
        security = load_service_module("user-service", "src.core.security")
        self.assertFalse(security.verify_password("legacy", "legacy"))
        self.assertFalse(security.verify_password("bad", "$2b$invalid"))
        hashed = security.hash_password("test-password")
        self.assertTrue(security.verify_password("test-password", hashed))
        self.assertFalse(security.verify_password("wrong", hashed))

    def test_dotenv_resolution_does_not_depend_on_working_directory(self):
        for name in ("user", "hotel", "room", "booking", "payment", "notification"):
            config = load_service_module(f"{name}-service", "src.core.config")
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("ENV_FILE", None)
                expected = str(Path(config.__file__).resolve().parents[2] / ".env")
                original = os.getcwd()
                try:
                    with tempfile.TemporaryDirectory() as directory:
                        os.chdir(directory)
                        Path(".env").write_text("DB_NAME=wrong_database\n")
                        self.assertEqual(config._resolve_env_file(), expected)
                        os.chdir(original)
                finally:
                    os.chdir(original)
                with patch.dict(os.environ, {"ENV_FILE": "relative.env"}):
                    with self.assertRaises(ValueError):
                        config._resolve_env_file()

    def test_payment_confirmation_sends_internal_authentication(self):
        service = load_service_module("payment-service", "src.services.payment_service")
        service.settings.INTERNAL_SERVICE_SECRET = "offline-test-internal-secret"
        with patch("httpx.Client") as client:
            client.return_value.__enter__.return_value.patch.return_value.status_code = 200
            self.assertTrue(service.PaymentService.confirm_booking_with_retry(17, "test"))
            headers = client.return_value.__enter__.return_value.patch.call_args.kwargs["headers"]
            self.assertEqual(headers["X-Internal-Service-Secret"], service.settings.INTERNAL_SERVICE_SECRET)

    def test_payment_creation_fails_closed_when_booking_is_offline(self):
        module = load_service_module("payment-service", "src.services.payment_service")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        payload = SimpleNamespace(id_dat_phong=17, ma_booking="OFFLINE-TEST", so_tien=100)
        with patch("urllib.request.urlopen", side_effect=ConnectionError("offline")):
            with self.assertRaises(HTTPException) as error:
                module.PaymentService.create_payment(db, payload)
        self.assertEqual(error.exception.status_code, 503)
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_payment_otp_rejects_another_booking_owner(self):
        module = load_service_module("payment-service", "src.api.v1.endpoints.payments")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value.id_dat_phong = 17
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"id_tai_khoan": 99}'
        with patch("urllib.request.urlopen", return_value=response):
            with self.assertRaises(HTTPException) as error:
                module.authorize_transaction(db, "test-txn", {"sub": "1", "role": "CUSTOMER"})
        self.assertEqual(error.exception.status_code, 403)

    def test_payment_startup_fails_on_short_otp_column_without_schema_writes(self):
        module = load_service_module("payment-service", "src.main")
        inspector = MagicMock()
        inspector.get_table_names.return_value = list(module.Base.metadata.tables)
        inspector.get_columns.return_value = [{"name":"otp_code", "type": SimpleNamespace(length=6)}]
        connection = MagicMock()
        with patch.object(module, "inspect", return_value=inspector):
            with self.assertRaisesRegex(RuntimeError, "migration"):
                module.verify_payment_schema(connection)
        connection.execute.assert_not_called()

    def test_payment_startup_propagates_database_failure(self):
        module = load_service_module("payment-service", "src.main")
        async def run():
            async with module.lifespan(module.app):
                pass
        with patch.object(module.engine, "connect", side_effect=RuntimeError("offline")):
            with self.assertRaisesRegex(RuntimeError, "offline"):
                asyncio.run(run())

    def test_valid_otp_keeps_sync_failure_explicit_and_sends_no_success_event(self):
        from datetime import datetime, timedelta
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        module = load_service_module("payment-service", "src.services.payment_service")
        models = importlib.import_module("src.models")
        database = importlib.import_module("src.core.database")
        engine = create_engine("sqlite://")
        database.Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        try:
            payment = models.ThanhToanModel(id_dat_phong=17, ma_booking="UNIT-SYNC", so_tien=100,
                phuong_thuc="VNPAY", trang_thai="PENDING", ma_giao_dich_gateway="UNIT-SYNC-TXN")
            otp = models.GiaoDichOtpModel(ma_giao_dich_gateway="UNIT-SYNC-TXN", email="unit@example.com",
                otp_code=module.hash_otp("123456"), thoi_gian_het_han=datetime.utcnow()+timedelta(minutes=3))
            db.add_all([payment,otp]); db.commit()
            request = importlib.import_module("src.schemas.payment_schema").VerifyOtpRequest(
                ma_giao_dich_gateway="UNIT-SYNC-TXN", otp_code="123456")
            with patch.object(module.PaymentService,"confirm_booking_with_retry",return_value=False), patch.object(module,"publish_payment_event") as publish:
                result = asyncio.run(module.PaymentService.verify_otp(db,request))
            self.assertEqual(result.trang_thai,"SYNC_FAILED")
            self.assertTrue(otp.da_su_dung)
            self.assertEqual(publish.call_args.args[0],"notification.payment.sync_failed")
        finally:
            db.close(); engine.dispose()


if __name__ == "__main__":
    unittest.main()
