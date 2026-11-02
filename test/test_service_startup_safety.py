import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import SQLAlchemyError
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def activate_service(service_name):
    for module_name in list(sys.modules):
        if module_name == "src" or module_name.startswith("src."):
            del sys.modules[module_name]
    for path in list(sys.path):
        normalized_path = os.path.normcase(os.path.abspath(path or os.getcwd()))
        services_root = os.path.normcase(os.path.join(PROJECT_ROOT, "services"))
        gateway_root = os.path.normcase(os.path.join(PROJECT_ROOT, "gateway"))
        if normalized_path.startswith(services_root) or normalized_path.startswith(
            gateway_root
        ):
            sys.path.remove(path)
    service_path = os.path.join(PROJECT_ROOT, "services", service_name)
    sys.path.insert(0, service_path)
    os.chdir(service_path)


class TestRoomStartupSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        activate_service("room-service")
        from src.core.database import Base
        from src.main import app, lifespan, verify_room_schema

        cls.app = app
        cls.base = Base
        cls.lifespan = staticmethod(lifespan)
        cls.verify_schema = staticmethod(verify_room_schema)

    def test_startup_checks_database_without_creating_schema(self):
        connection = MagicMock()
        with (
            patch("src.main.engine.connect") as connect,
            patch("src.main.verify_room_schema") as verify_schema,
            patch("src.core.database.Base.metadata.create_all") as create_all,
        ):
            connect.return_value.__enter__.return_value = connection
            asyncio.run(self._run_lifespan())

        connection.execute.assert_called_once()
        verify_schema.assert_called_once_with(connection)
        create_all.assert_not_called()

    def test_startup_fails_when_database_is_unavailable(self):
        with patch("src.main.engine.connect", side_effect=SQLAlchemyError("offline")):
            with self.assertRaises(SQLAlchemyError):
                asyncio.run(self._run_lifespan())

    def test_room_schema_readiness_detects_missing_tables_without_creating_them(self):
        from sqlalchemy import create_engine, inspect
        from sqlalchemy.pool import StaticPool

        schema_engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        try:
            with schema_engine.connect() as connection:
                with self.assertRaisesRegex(RuntimeError, "missing required tables"):
                    self.verify_schema(connection)
                self.assertEqual(inspect(connection).get_table_names(), [])
        finally:
            schema_engine.dispose()

    def test_room_schema_readiness_accepts_initialized_schema(self):
        from sqlalchemy import create_engine
        from sqlalchemy.pool import StaticPool

        schema_engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        try:
            self.base.metadata.create_all(schema_engine)
            with schema_engine.connect() as connection:
                self.verify_schema(connection)
        finally:
            schema_engine.dispose()

    async def _run_lifespan(self):
        async with self.lifespan(self.app):
            pass


class TestNotificationStartupSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        activate_service("notification-service")
        from src.core.database import Base
        from src.core.rabbitmq_consumer import RabbitMQConsumer, rabbitmq_consumer
        from src.main import app, lifespan, verify_notification_schema

        cls.app = app
        cls.base = Base
        cls.lifespan = staticmethod(lifespan)
        cls.verify_schema = staticmethod(verify_notification_schema)
        cls.consumer = rabbitmq_consumer
        cls.consumer_class = RabbitMQConsumer

    def test_startup_checks_database_before_starting_consumer(self):
        connection = MagicMock()
        with (
            patch("src.main.engine.connect") as connect,
            patch("src.main.verify_notification_schema") as verify_schema,
            patch("src.main.rabbitmq_consumer.start") as start,
            patch("src.main.rabbitmq_consumer.stop") as stop,
        ):
            connect.return_value.__enter__.return_value = connection
            asyncio.run(self._run_lifespan())

        connection.execute.assert_called_once()
        verify_schema.assert_called_once_with(connection)
        start.assert_called_once()
        stop.assert_called_once()

    def test_startup_does_not_start_consumer_when_database_is_unavailable(self):
        with (
            patch("src.main.engine.connect", side_effect=SQLAlchemyError("offline")),
            patch("src.main.rabbitmq_consumer.start") as start,
        ):
            with self.assertRaises(SQLAlchemyError):
                asyncio.run(self._run_lifespan())
        start.assert_not_called()

    def test_health_is_degraded_when_database_or_broker_is_unavailable(self):
        self.consumer.connection = None
        with patch(
            "src.main.engine.connect",
            side_effect=SQLAlchemyError("offline"),
        ):
            client = TestClient(self.app)
            response = client.get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")
        self.assertFalse(response.json()["database_connected"])
        self.assertFalse(response.json()["rabbitmq_connected"])

    def test_schema_readiness_accepts_the_orm_schema(self):
        from sqlalchemy import create_engine
        from sqlalchemy.pool import StaticPool

        schema_engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        try:
            self.base.metadata.create_all(schema_engine)
            with schema_engine.connect() as connection:
                self.verify_schema(connection)
        finally:
            schema_engine.dispose()

    def test_schema_readiness_supports_dialects_without_unique_constraint_reflection(self):
        inspector = MagicMock()
        inspector.get_table_names.return_value = [
            "thong_bao",
            "noi_dung_thong_bao",
        ]
        inspector.get_columns.side_effect = [
            [{"name": "event_key"}, {"name": "is_read"}]
        ]
        inspector.get_indexes.side_effect = [
            [
                {
                    "unique": True,
                    "column_names": ["event_key"],
                    "dialect_options": {"mssql_where": "[event_key] IS NOT NULL"},
                }
            ],
            [{"unique": True, "column_names": ["id_thong_bao"]}],
        ]
        inspector.get_unique_constraints.side_effect = NotImplementedError

        with patch("src.main.inspect", return_value=inspector):
            self.verify_schema(MagicMock())

    def test_broker_reconnect_uses_capped_backoff_without_sleeping_in_tests(self):
        import pika

        consumer = self.consumer_class()
        consumer.is_running = True
        delays = []

        def wait_and_stop(delay):
            delays.append(delay)
            if len(delays) == 7:
                consumer.is_running = False

        with (
            patch.object(
                consumer,
                "_connect",
                side_effect=pika.exceptions.AMQPConnectionError("offline"),
            ),
            patch.object(consumer._stop_event, "wait", side_effect=wait_and_stop),
        ):
            consumer._run_loop()

        self.assertEqual(delays, [1, 2, 4, 8, 16, 32, 60])

    def test_stop_closes_connection_on_its_owner_thread(self):
        consumer = self.consumer_class()
        connection = MagicMock()
        connection.is_open = True
        worker = MagicMock()
        worker.is_alive.return_value = False
        consumer.connection = connection
        consumer.thread = worker
        consumer.is_running = True

        consumer.stop()

        self.assertFalse(consumer.is_running)
        self.assertTrue(consumer._stop_event.is_set())
        connection.add_callback_threadsafe.assert_called_once_with(
            connection.close
        )
        connection.close.assert_not_called()
        worker.join.assert_called_once_with(timeout=10)

    async def _run_lifespan(self):
        async with self.lifespan(self.app):
            pass


if __name__ == "__main__":
    unittest.main()
