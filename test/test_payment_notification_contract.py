import os
import sys
import unittest
from unittest.mock import patch

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
PAYMENT_SERVICE_DIR = os.path.join(
    PROJECT_ROOT,
    "services",
    "payment-service",
)


def activate_payment_service():
    for module_name in list(sys.modules):
        if module_name == "src" or module_name.startswith("src."):
            del sys.modules[module_name]
    for path in list(sys.path):
        normalized_path = os.path.normcase(os.path.abspath(path or os.getcwd()))
        if normalized_path.startswith(
            os.path.normcase(os.path.join(PROJECT_ROOT, "services"))
        ):
            sys.path.remove(path)
    sys.path.insert(0, PAYMENT_SERVICE_DIR)
    os.chdir(PAYMENT_SERVICE_DIR)


class TestPaymentNotificationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        activate_payment_service()
        from src.core import publisher

        cls.publisher = publisher

    def setUp(self):
        self.publisher.settings.NOTIFICATION_SERVICE_URL = (
            "http://notification-service.test/api/v1"
        )
        self.publisher.settings.INTERNAL_SERVICE_SECRET = (
            "payment-notification-test-secret"
        )

    def test_sync_failed_event_never_uses_success_email_fallback(self):
        with patch(
            "pika.BlockingConnection",
            side_effect=OSError("broker unavailable"),
        ), patch("urllib.request.urlopen") as urlopen:
            self.publisher.publish_payment_event(
                "notification.payment.sync_failed",
                {
                    "email": "customer@example.test",
                    "ma_booking": "BK-SYNC-FAILED",
                },
            )
        urlopen.assert_not_called()

    def test_missing_recipient_never_uses_demo_email_fallback(self):
        with patch(
            "pika.BlockingConnection",
            side_effect=OSError("broker unavailable"),
        ), patch("urllib.request.urlopen") as urlopen:
            self.publisher.publish_payment_event(
                "notification.payment.success",
                {"ma_booking": "BK-MISSING-EMAIL"},
            )
        urlopen.assert_not_called()

    def test_payment_success_fallback_preserves_real_recipient_and_contract(self):
        captured_requests = []

        class FakeResponse:
            status = 201

            def __enter__(self):
                return self

            def __exit__(self, _exc_type, _exc, _traceback):
                return None

        def fake_urlopen(request, timeout):
            captured_requests.append((request, timeout))
            return FakeResponse()

        with patch(
            "pika.BlockingConnection",
            side_effect=OSError("broker unavailable"),
        ), patch("urllib.request.urlopen", side_effect=fake_urlopen):
            with self.assertLogs(self.publisher.__name__, level="WARNING") as logs:
                self.publisher.publish_payment_event(
                    "notification.payment.success",
                    {
                        "email": "verified@example.test",
                        "ma_booking": "BK-PAYMENT-SUCCESS",
                    },
                )

        self.assertEqual(len(captured_requests), 1)
        self.assertFalse(
            any("fallback API failed" in message for message in logs.output)
        )
        request, timeout = captured_requests[0]
        self.assertEqual(timeout, 3)
        self.assertTrue(request.full_url.endswith("/notifications/internal-send"))
        self.assertEqual(
            request.headers.get("X-internal-secret"),
            "payment-notification-test-secret",
        )
        import json

        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["loai_thong_bao"], "PAYMENT_SUCCESS")
        self.assertEqual(body["nguoi_nhan"], "verified@example.test")


if __name__ == "__main__":
    unittest.main()
