"""Publisher fallback must retain the exact consumer wire-event identity."""
import hashlib
import json
import unittest
from unittest.mock import MagicMock, patch
from test_legacy_auth_fallback import load_service_module


class TransportIdentityTests(unittest.TestCase):
    def test_broker_and_rest_share_identity_for_booking_payment_and_otp(self):
        for service, function, queue in (
            ("booking-service", "publish_notification_event", "notification.booking.confirmed"),
            ("payment-service", "publish_payment_event", "notification.payment.success"),
            ("payment-service", "publish_otp_event", "notification.otp.generated"),
        ):
            with self.subTest(service=service, function=function):
                module = load_service_module(service, "src.core.publisher")
                module.settings.NOTIFICATION_SERVICE_URL = "http://notification.test/api/v1"
                payload = {"email":"test@example.com","ma_booking":"TRANSPORT-TEST","id_tai_khoan":17,"otp_code":"123456"}
                response = MagicMock()
                response.__enter__.return_value.status = 201
                with patch("pika.BlockingConnection", side_effect=ConnectionError("offline")), patch("urllib.request.urlopen", return_value=response) as send:
                    getattr(module,function)(queue,payload)
                request = send.call_args.args[0]
                expected = hashlib.sha256(queue.encode()+b"\0"+json.dumps(payload,ensure_ascii=False,default=str).encode()).hexdigest()
                self.assertEqual(request.get_header("X-notification-event-key"),expected)
                self.assertEqual(json.loads(request.data)["id_tai_khoan"],17)


if __name__ == "__main__":
    unittest.main()
