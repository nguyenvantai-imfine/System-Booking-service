import hashlib
import json
import logging
import threading
import time
from typing import Any

import pika

from src.core.config import settings

logger = logging.getLogger(__name__)

QUEUES = [
    "notification.booking.confirmed",
    "notification.payment.success",
    "notification.booking.cancelled",
    "notification.otp.generated",
]
DEAD_LETTER_QUEUE = "notification.dead-letter"
MAX_RETRIES = 3
INITIAL_RECONNECT_DELAY_SECONDS = 1
MAX_RECONNECT_DELAY_SECONDS = 60


class PermanentMessageError(Exception):
    """Raised for messages that will not succeed if delivered again."""


class RabbitMQConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.is_running = False
        self.thread = None
        self._stop_event = threading.Event()

    def start(self, on_message_callback):
        """Khởi động consumer lắng nghe trong thread nền."""
        if not settings.RABBITMQ_ENABLED:
            logger.info("RabbitMQ is disabled in configuration.")
            return

        self.on_message_callback = on_message_callback
        self.is_running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("RabbitMQ Consumer background thread started.")

    def stop(self):
        """Dừng consumer."""
        self.is_running = False
        self._stop_event.set()
        connection = self.connection
        if connection and connection.is_open:
            try:
                connection.add_callback_threadsafe(connection.close)
            except Exception as exc:
                logger.warning(
                    "Could not schedule RabbitMQ connection close; error_type=%s",
                    type(exc).__name__,
                )

        consumer_thread = self.thread
        if consumer_thread and consumer_thread is not threading.current_thread():
            consumer_thread.join(timeout=10)
            if consumer_thread.is_alive():
                logger.warning("RabbitMQ consumer thread did not stop before timeout.")

    def _connect(self):
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER,
            settings.RABBITMQ_PASSWORD,
        )
        parameters = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=30,
        )
        return pika.BlockingConnection(parameters)

    def _run_loop(self):
        reconnect_delay = INITIAL_RECONNECT_DELAY_SECONDS
        while self.is_running:
            try:
                self.connection = self._connect()
                reconnect_delay = INITIAL_RECONNECT_DELAY_SECONDS
                self.channel = self.connection.channel()
                self.channel.confirm_delivery()
                self.channel.basic_qos(prefetch_count=1)

                for queue_name in QUEUES:
                    self.channel.queue_declare(
                        queue=queue_name,
                        durable=True,
                    )
                    self.channel.basic_consume(
                        queue=queue_name,
                        on_message_callback=self._handle_delivery,
                        auto_ack=False,
                    )
                self.channel.queue_declare(
                    queue=DEAD_LETTER_QUEUE,
                    durable=True,
                )

                logger.info("RabbitMQ consumer ready; queues=%s", ",".join(QUEUES))
                self.channel.start_consuming()
            except pika.exceptions.AMQPConnectionError as exc:
                logger.warning(
                    "RabbitMQ connection failed; error_type=%s retry_seconds=%s",
                    type(exc).__name__,
                    reconnect_delay,
                )
            except Exception as exc:
                logger.error(
                    "RabbitMQ consumer loop failed; error_type=%s retry_seconds=%s",
                    type(exc).__name__,
                    reconnect_delay,
                )
            if self.is_running:
                self._stop_event.wait(reconnect_delay)
                reconnect_delay = min(
                    reconnect_delay * 2,
                    MAX_RECONNECT_DELAY_SECONDS,
                )

    @staticmethod
    def _message_properties(properties, headers: dict[str, Any]):
        return pika.BasicProperties(
            content_type=getattr(properties, "content_type", None),
            content_encoding=getattr(properties, "content_encoding", None),
            correlation_id=getattr(properties, "correlation_id", None),
            message_id=getattr(properties, "message_id", None),
            delivery_mode=2,
            headers=headers,
        )

    def _publish_and_ack(
        self,
        channel,
        method,
        properties,
        body: bytes,
        target_queue: str,
        headers: dict[str, Any],
    ) -> None:
        confirmed = channel.basic_publish(
            exchange="",
            routing_key=target_queue,
            body=body,
            properties=self._message_properties(properties, headers),
            mandatory=True,
        )
        if confirmed is False:
            raise RuntimeError("RabbitMQ did not confirm the republished message.")
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def _dead_letter(
        self,
        channel,
        method,
        properties,
        body: bytes,
        error_type: str,
    ) -> None:
        headers = dict(getattr(properties, "headers", None) or {})
        headers["x-notification-original-queue"] = method.routing_key
        headers["x-notification-failure-type"] = error_type
        self._publish_and_ack(
            channel,
            method,
            properties,
            body,
            DEAD_LETTER_QUEUE,
            headers,
        )
        logger.error(
            "Notification message moved to dead-letter queue; queue=%s error_type=%s",
            method.routing_key,
            error_type,
        )

    def _handle_delivery(self, channel, method, properties, body):
        queue_name = method.routing_key
        headers = dict(getattr(properties, "headers", None) or {})
        retry_count = headers.get("x-notification-retry", 0)
        if not isinstance(retry_count, int) or retry_count < 0:
            retry_count = MAX_RETRIES

        try:
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise PermanentMessageError("Invalid JSON message.") from exc

            if not isinstance(payload, dict):
                raise PermanentMessageError("Notification event must be a JSON object.")
            if queue_name not in QUEUES:
                raise PermanentMessageError("Unknown notification queue.")
            if not self.on_message_callback:
                raise RuntimeError("Notification callback is not configured.")

            event_key = hashlib.sha256(
                queue_name.encode("utf-8") + b"\0" + body
            ).hexdigest()
            payload["_notification_event_key"] = event_key
            correlation_id = (
                getattr(properties, "correlation_id", None)
                or payload.get("correlation_id")
            )
            if correlation_id and "correlation_id" not in payload:
                payload["correlation_id"] = correlation_id

            self.on_message_callback(queue_name, payload)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except PermanentMessageError as exc:
            try:
                self._dead_letter(
                    channel,
                    method,
                    properties,
                    body,
                    type(exc).__name__,
                )
            except Exception as publish_exc:
                logger.error(
                    "Could not dead-letter notification message; queue=%s error_type=%s",
                    queue_name,
                    type(publish_exc).__name__,
                )
                channel.basic_nack(
                    delivery_tag=method.delivery_tag,
                    requeue=True,
                )
        except (ValueError, TypeError) as exc:
            try:
                self._dead_letter(
                    channel,
                    method,
                    properties,
                    body,
                    type(exc).__name__,
                )
            except Exception as publish_exc:
                logger.error(
                    "Could not dead-letter notification message; queue=%s error_type=%s",
                    queue_name,
                    type(publish_exc).__name__,
                )
                channel.basic_nack(
                    delivery_tag=method.delivery_tag,
                    requeue=True,
                )
        except Exception as exc:
            if retry_count >= MAX_RETRIES:
                try:
                    self._dead_letter(
                        channel,
                        method,
                        properties,
                        body,
                        type(exc).__name__,
                    )
                except Exception as publish_exc:
                    logger.error(
                        "Could not dead-letter notification message; queue=%s error_type=%s",
                        queue_name,
                        type(publish_exc).__name__,
                    )
                    channel.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=True,
                    )
                return

            retry_delay = min(2 ** retry_count, 8)
            time.sleep(retry_delay)
            headers["x-notification-retry"] = retry_count + 1
            try:
                self._publish_and_ack(
                    channel,
                    method,
                    properties,
                    body,
                    queue_name,
                    headers,
                )
                logger.warning(
                    "Notification delivery retry scheduled; queue=%s attempt=%s error_type=%s",
                    queue_name,
                    retry_count + 1,
                    type(exc).__name__,
                )
            except Exception as publish_exc:
                logger.error(
                    "Could not publish notification retry; queue=%s error_type=%s",
                    queue_name,
                    type(publish_exc).__name__,
                )
                channel.basic_nack(
                    delivery_tag=method.delivery_tag,
                    requeue=True,
                )


rabbitmq_consumer = RabbitMQConsumer()
