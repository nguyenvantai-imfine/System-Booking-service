import os
import smtplib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from fastapi import HTTPException

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
NOTIFICATION_SERVICE_DIR = os.path.join(
    PROJECT_ROOT,
    "services",
    "notification-service",
)


def set_active_notification_service():
    for module_name in list(sys.modules):
        if module_name == "src" or module_name.startswith("src."):
            del sys.modules[module_name]
    for path in list(sys.path):
        normalized_path = os.path.normcase(os.path.abspath(path or os.getcwd()))
        service_root = os.path.normcase(os.path.join(PROJECT_ROOT, "services"))
        gateway_root = os.path.normcase(os.path.join(PROJECT_ROOT, "gateway"))
        if normalized_path.startswith(service_root) or normalized_path.startswith(
            gateway_root
        ):
            sys.path.remove(path)
    sys.path.insert(0, NOTIFICATION_SERVICE_DIR)
    os.chdir(NOTIFICATION_SERVICE_DIR)


class TestNotificationSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        set_active_notification_service()
        from src.core.config import settings
        from src.core.database import Base
        from src.main import app
        from src.models import noi_dung_thong_bao, thong_bao

        cls.settings = settings
        cls.base = Base
        cls.app = app
        cls.models = (noi_dung_thong_bao, thong_bao)

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        from src.core.database import get_db

        def override_get_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        self.app.dependency_overrides[get_db] = override_get_db
        self.settings.JWT_SECRET_KEY = "test-jwt-secret"
        self.settings.INTERNAL_SERVICE_SECRET = "test-internal-secret"
        self.settings.MOCK_EMAIL_SEND = True
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        self.engine.dispose()

    def _token(self, role, user_id="12"):
        import jwt

        return jwt.encode(
            {
                "sub": str(user_id),
                "role": role,
                "type": "access",
            },
            self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM,
        )

    def _notification_payload(self, recipient="recipient@example.test"):
        return {
            "loai_thong_bao": "SYSTEM",
            "nguoi_nhan": recipient,
            "kenh_gui": "EMAIL",
            "id_tai_khoan": 999,
            "du_lieu": {"message": "Test notification"},
        }

    def test_manual_send_requires_admin_and_valid_recipient(self):
        url = "/api/v1/notifications/send"
        self.assertEqual(
            self.client.post(url, json=self._notification_payload()).status_code,
            401,
        )
        customer_headers = {
            "Authorization": f"Bearer {self._token('CUSTOMER')}",
        }
        denied = self.client.post(
            url,
            json=self._notification_payload(),
            headers=customer_headers,
        )
        self.assertEqual(denied.status_code, 403)

        admin_headers = {"Authorization": f"Bearer {self._token('ADMIN')}"}
        invalid_email = self.client.post(
            url,
            json=self._notification_payload("not-an-email"),
            headers=admin_headers,
        )
        self.assertEqual(invalid_email.status_code, 422)

        sent = self.client.post(
            url,
            json=self._notification_payload(),
            headers=admin_headers,
        )
        self.assertEqual(sent.status_code, 201)
        self.assertEqual(sent.json()["id_tai_khoan"], 999)

    def test_manual_send_fails_closed_without_configured_jwt_secret(self):
        token = self._token("ADMIN")
        self.settings.JWT_SECRET_KEY = ""
        response = self.client.post(
            "/api/v1/notifications/send",
            json=self._notification_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 503)

    def test_notification_reads_are_scoped_to_authenticated_recipient_account(self):
        created = self.client.post(
            "/api/v1/notifications/send",
            json=self._notification_payload(),
            headers={"Authorization": f"Bearer {self._token('ADMIN')}"},
        )
        self.assertEqual(created.status_code, 201)
        notification_id = created.json()["id_thong_bao"]

        other_user_headers = {
            "Authorization": f"Bearer {self._token('CUSTOMER')}",
        }
        hidden_detail = self.client.get(
            f"/api/v1/notifications/{notification_id}",
            headers=other_user_headers,
        )
        hidden_list = self.client.get(
            "/api/v1/notifications",
            headers=other_user_headers,
        )
        self.assertEqual(hidden_detail.status_code, 404)
        self.assertEqual(hidden_list.json()["total"], 0)

        owner_headers = {
            "Authorization": f"Bearer {self._token('CUSTOMER', user_id='999')}",
        }
        visible_detail = self.client.get(
            f"/api/v1/notifications/{notification_id}",
            headers=owner_headers,
        )
        self.assertEqual(visible_detail.status_code, 200)

    def test_internal_send_requires_configured_secret(self):
        url = "/api/v1/notifications/internal-send"
        unauthorized = self.client.post(
            url,
            json=self._notification_payload(),
        )
        self.assertEqual(unauthorized.status_code, 401)

        accepted = self.client.post(
            url,
            json=self._notification_payload(),
            headers={"X-Internal-Secret": "test-internal-secret"},
        )
        self.assertEqual(accepted.status_code, 201)

    def test_internal_send_fails_closed_without_configured_secret(self):
        self.settings.INTERNAL_SERVICE_SECRET = ""
        response = self.client.post(
            "/api/v1/notifications/internal-send",
            json=self._notification_payload(),
            headers={"X-Internal-Secret": "test-internal-secret"},
        )
        self.assertEqual(response.status_code, 401)

    def test_mock_sender_never_logs_email_content_or_plaintext_otp(self):
        from src.core.email_sender import EmailSender

        otp = "428159"
        with self.assertLogs("src.core.email_sender", level="INFO") as logs:
            success, _ = EmailSender.send_email(
                "customer@example.test",
                f"OTP {otp}",
                f"<p>{otp}</p>",
                otp,
            )
        self.assertTrue(success)
        self.assertNotIn(otp, "\n".join(logs.output))

    def test_otp_content_is_masked_before_database_storage(self):
        from src.schemas.notification_schema import SendNotificationRequest
        from src.services.notification_service import NotificationService

        otp = "915724"
        request = SendNotificationRequest(
            loai_thong_bao="OTP",
            nguoi_nhan="customer@example.test",
            du_lieu={
                "otp_code": otp,
                "ten_khach": "Test Customer",
                "minutes": 3,
                "expires_in": 180,
            },
        )
        db = self.Session()
        notification = NotificationService.send_notification(db, request)
        stored_content = notification.noi_dung
        stored_fields = (
            stored_content.tieu_de,
            stored_content.noi_dung_html,
            stored_content.noi_dung_text,
            stored_content.du_lieu_dinh_kem,
        )
        self.assertTrue(all(otp not in value for value in stored_fields if value))
        self.assertIn("91****", stored_content.noi_dung_html)
        self.assertIn("91****", stored_content.noi_dung_text)
        self.assertIn("91****", stored_content.du_lieu_dinh_kem)
        db.close()

    def test_smtp_success_and_failures_are_reported_without_real_delivery(self):
        from src.core.email_sender import EmailSender

        self.settings.MOCK_EMAIL_SEND = False
        self.settings.SMTP_HOST = "smtp.invalid.test"
        self.settings.SMTP_USER = "smtp-user"
        self.settings.SMTP_PASSWORD = "not-a-real-password"
        self.settings.SMTP_FROM_EMAIL = "sender@example.test"
        self.settings.SMTP_PORT = 587
        self.settings.SMTP_TLS = True

        smtp_client = unittest.mock.MagicMock()
        smtp_client.__enter__.return_value = smtp_client
        with patch("src.core.email_sender.smtplib.SMTP", return_value=smtp_client):
            success, _ = EmailSender.send_email(
                "recipient@example.test",
                "Subject",
                "<p>Message</p>",
            )
        self.assertTrue(success)
        smtp_client.starttls.assert_called_once()
        smtp_client.login.assert_called_once()
        smtp_client.sendmail.assert_called_once()

        for smtp_error in (
            TimeoutError("simulated timeout"),
            smtplib.SMTPRecipientsRefused({"recipient@example.test": (550, b"rejected")}),
        ):
            with self.subTest(error=type(smtp_error).__name__):
                with patch(
                    "src.core.email_sender.smtplib.SMTP",
                    side_effect=smtp_error,
                ):
                    success, message = EmailSender.send_email(
                        "recipient@example.test",
                        "Subject",
                        "<p>Message</p>",
                    )
                self.assertFalse(success)
                if isinstance(smtp_error, smtplib.SMTPRecipientsRefused):
                    self.assertEqual(
                        message,
                        "SMTP recipient rejected permanently.",
                    )
                else:
                    self.assertIn("SMTP send failed", message)

        self.settings.SMTP_PASSWORD = ""
        success, message = EmailSender.send_email(
            "recipient@example.test",
            "Subject",
            "<p>Message</p>",
        )
        self.assertFalse(success)
        self.assertIn("settings are incomplete", message)

    def test_database_failure_before_email_delivery_does_not_send_email(self):
        from src.core.email_sender import email_sender
        from src.schemas.notification_schema import SendNotificationRequest
        from src.services.notification_service import NotificationService

        db = self.Session()
        request = SendNotificationRequest(**self._notification_payload())
        with patch.object(db, "commit", side_effect=SQLAlchemyError("simulated database failure")):
            with patch.object(email_sender, "send_email") as send_email:
                with self.assertRaises(HTTPException):
                    NotificationService.send_notification(db, request)
        send_email.assert_not_called()
        db.close()

    def test_repeated_event_key_is_idempotent_and_failed_event_can_retry(self):
        from src.core.email_sender import email_sender
        from src.schemas.notification_schema import SendNotificationRequest
        from src.services.notification_service import NotificationService
        from src.models.thong_bao import ThongBaoModel

        db = self.Session()
        request = SendNotificationRequest(**self._notification_payload())
        event_key = "a" * 64
        with patch.object(email_sender, "send_email", return_value=(True, "sent")) as send:
            first = NotificationService.send_notification(
                db,
                request,
                event_key=event_key,
            )
            duplicate = NotificationService.send_notification(
                db,
                request,
                event_key=event_key,
            )
        self.assertEqual(first.id_thong_bao, duplicate.id_thong_bao)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(db.query(ThongBaoModel).count(), 1)

        retry_request = SendNotificationRequest(**self._notification_payload("retry@example.test"))
        retry_key = "b" * 64
        with patch.object(
            email_sender,
            "send_email",
            side_effect=[(False, "SMTP send failed."), (True, "sent")],
        ) as send:
            failed = NotificationService.send_notification(
                db,
                retry_request,
                event_key=retry_key,
            )
            retried = NotificationService.send_notification(
                db,
                retry_request,
                event_key=retry_key,
            )
        self.assertEqual(failed.id_thong_bao, retried.id_thong_bao)
        self.assertEqual(retried.trang_thai, "SENT")
        self.assertEqual(send.call_count, 2)
        self.assertEqual(db.query(ThongBaoModel).count(), 2)
        db.close()

    def test_consumer_retries_then_dead_letters_without_logging_payload(self):
        import json
        from src.core.rabbitmq_consumer import (
            DEAD_LETTER_QUEUE,
            RabbitMQConsumer,
        )

        consumer = RabbitMQConsumer()
        consumer.on_message_callback = lambda _queue, _payload: (_ for _ in ()).throw(
            RuntimeError("temporary failure")
        )
        channel = unittest.mock.MagicMock()
        channel.basic_publish.return_value = True
        body = json.dumps({"email": "private@example.test", "otp_code": "773904"}).encode()

        with patch("src.core.rabbitmq_consumer.time.sleep"), self.assertLogs(
            "src.core.rabbitmq_consumer",
            level="WARNING",
        ) as logs:
            for retry_count in range(4):
                method = SimpleNamespace(
                    routing_key="notification.otp.generated",
                    delivery_tag=retry_count + 1,
                )
                properties = SimpleNamespace(
                    headers={"x-notification-retry": retry_count},
                    content_type="application/json",
                    content_encoding="utf-8",
                    correlation_id="test-correlation",
                    message_id=None,
                )
                consumer._handle_delivery(channel, method, properties, body)

        destinations = [
            call.kwargs["routing_key"]
            for call in channel.basic_publish.call_args_list
        ]
        self.assertEqual(destinations[:3], ["notification.otp.generated"] * 3)
        self.assertEqual(destinations[-1], DEAD_LETTER_QUEUE)
        self.assertEqual(channel.basic_ack.call_count, 4)
        self.assertNotIn("private@example.test", "\n".join(logs.output))
        self.assertNotIn("773904", "\n".join(logs.output))

    def test_malformed_message_is_dead_lettered_and_failed_publish_requeues(self):
        from src.core.rabbitmq_consumer import DEAD_LETTER_QUEUE, RabbitMQConsumer

        consumer = RabbitMQConsumer()
        consumer.on_message_callback = lambda _queue, _payload: None
        method = SimpleNamespace(
            routing_key="notification.otp.generated",
            delivery_tag=1,
        )
        properties = SimpleNamespace(headers={})
        body = b"{invalid-json"

        channel = unittest.mock.MagicMock()
        channel.basic_publish.return_value = True
        consumer._handle_delivery(channel, method, properties, body)
        self.assertEqual(
            channel.basic_publish.call_args.kwargs["routing_key"],
            DEAD_LETTER_QUEUE,
        )
        channel.basic_ack.assert_called_once_with(delivery_tag=1)

        failed_channel = unittest.mock.MagicMock()
        failed_channel.basic_publish.return_value = False
        consumer._handle_delivery(failed_channel, method, properties, body)
        failed_channel.basic_nack.assert_called_once_with(
            delivery_tag=1,
            requeue=True,
        )

    def test_permanently_rejected_recipient_is_dead_lettered_without_retry(self):
        import json
        from src.core.email_sender import (
            SMTP_RECIPIENT_REJECTED_PERMANENTLY,
            email_sender,
        )
        from src.core.rabbitmq_consumer import DEAD_LETTER_QUEUE, RabbitMQConsumer
        from src.models.thong_bao import ThongBaoModel
        from src.services import notification_service

        payload = {
            "email": "rejected@example.test",
            "id_tai_khoan": 12,
            "otp_code": "680241",
        }
        body = json.dumps(payload).encode("utf-8")
        db = self.Session()
        consumer = RabbitMQConsumer()
        consumer.on_message_callback = (
            notification_service.NotificationService.handle_message_queue_event
        )
        channel = unittest.mock.MagicMock()
        channel.basic_publish.return_value = True
        method = SimpleNamespace(
            routing_key="notification.otp.generated",
            delivery_tag=1,
        )
        properties = SimpleNamespace(headers={})

        with patch.object(
            notification_service,
            "SessionLocal",
            return_value=db,
        ), patch.object(
            email_sender,
            "send_email",
            return_value=(False, SMTP_RECIPIENT_REJECTED_PERMANENTLY),
        ):
            consumer._handle_delivery(channel, method, properties, body)

        self.assertEqual(
            channel.basic_publish.call_args.kwargs["routing_key"],
            DEAD_LETTER_QUEUE,
        )
        channel.basic_ack.assert_called_once_with(delivery_tag=1)
        failed_notification = db.query(ThongBaoModel).one()
        self.assertEqual(failed_notification.trang_thai, "FAILED")
        db.close()
