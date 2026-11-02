import importlib
import os
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_settings(service_name):
    for module_name in list(sys.modules):
        if module_name == "src" or module_name.startswith("src."):
            del sys.modules[module_name]

    service_path = os.path.join(PROJECT_ROOT, "services", service_name)
    sys.path.insert(0, service_path)
    original_directory = os.getcwd()
    try:
        with tempfile.TemporaryDirectory() as isolated_directory:
            os.chdir(isolated_directory)
            try:
                config_module = importlib.import_module("src.core.config")
                return config_module.Settings
            finally:
                os.chdir(original_directory)
    finally:
        sys.path.remove(service_path)


class TestServiceConfigDefaults(unittest.TestCase):
    def test_payment_local_cors_origins_load_from_comma_separated_env(self):
        settings = load_settings("payment-service")
        env_example = os.path.join(
            PROJECT_ROOT,
            "services",
            "payment-service",
            ".env.example",
        )
        loaded = settings(_env_file=env_example)
        self.assertEqual(
            loaded.CORS_ORIGINS,
            [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
            ],
        )

    def test_room_database_password_has_no_hardcoded_fallback(self):
        settings = load_settings("room-service")
        self.assertEqual(settings.model_fields["DB_PASSWORD"].default, "")

    def test_notification_database_password_has_no_hardcoded_fallback(self):
        settings = load_settings("notification-service")
        self.assertEqual(settings.model_fields["DB_PASSWORD"].default, "")

    def test_authentication_secrets_have_no_hardcoded_fallback(self):
        for service_name in (
            "user-service",
            "hotel-service",
            "room-service",
            "booking-service",
            "payment-service",
            "notification-service",
        ):
            with self.subTest(service=service_name):
                settings = load_settings(service_name)
                self.assertEqual(
                    settings.model_fields["JWT_SECRET_KEY"].default,
                    "",
                )

    def test_database_passwords_have_no_hardcoded_fallback(self):
        for service_name in (
            "user-service",
            "hotel-service",
            "room-service",
            "booking-service",
            "payment-service",
            "notification-service",
        ):
            with self.subTest(service=service_name):
                settings = load_settings(service_name)
                self.assertEqual(
                    settings.model_fields["DB_PASSWORD"].default,
                    "",
                )

    def test_local_environment_examples_use_host_urls_and_safe_placeholders(self):
        examples = (
            ".env.example",
            "gateway/.env.example",
            "services/user-service/.env.example",
            "services/hotel-service/.env.example",
            "services/room-service/.env.example",
            "services/booking-service/.env.example",
            "services/payment-service/.env.example",
            "services/notification-service/.env.example",
        )
        forbidden_values = (
            "Password123!",
            "booking_super_secret_jwt_key",
            "change_this_secret_key",
        )
        for relative_path in examples:
            path = os.path.join(PROJECT_ROOT, relative_path)
            with open(path, encoding="utf-8") as example_file:
                contents = example_file.read()
            with self.subTest(path=relative_path):
                for forbidden in forbidden_values:
                    self.assertNotIn(forbidden, contents)

        for service_name in (
            "user-service",
            "hotel-service",
            "room-service",
            "booking-service",
            "payment-service",
            "notification-service",
        ):
            path = os.path.join(
                PROJECT_ROOT,
                "services",
                service_name,
                ".env.example",
            )
            with open(path, encoding="utf-8") as example_file:
                contents = example_file.read()
            with self.subTest(service=service_name):
                self.assertNotIn("=http://hotel-service:", contents)
                self.assertNotIn("=http://booking-service:", contents)
                self.assertNotIn("=http://notification-service:", contents)


if __name__ == "__main__":
    unittest.main()
