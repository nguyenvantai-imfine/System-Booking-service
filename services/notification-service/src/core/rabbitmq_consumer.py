import json
import logging
import threading
import time
import pika
from src.core.config import settings

logger = logging.getLogger(__name__)

QUEUES = [
    "notification.booking.confirmed",
    "notification.payment.success",
    "notification.booking.cancelled",
    "notification.otp.generated",
]

class RabbitMQConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.is_running = False
        self.thread = None

    def start(self, on_message_callback):
        """Khởi động consumer lắng nghe trong thread nền"""
        if not settings.RABBITMQ_ENABLED:
            logger.info("RabbitMQ is disabled in configuration.")
            return

        self.on_message_callback = on_message_callback
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("RabbitMQ Consumer background thread started.")

    def stop(self):
        """Dừng consumer"""
        self.is_running = False
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            logger.warning(f"Error closing RabbitMQ connection: {e}")

    def _connect(self):
        credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=30,
        )
        return pika.BlockingConnection(parameters)

    def _run_loop(self):
        while self.is_running:
            try:
                logger.info(f"Connecting to RabbitMQ at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}...")
                self.connection = self._connect()
                self.channel = self.connection.channel()

                # Khai báo các hàng đợi bền vững (durable)
                for q in QUEUES:
                    self.channel.queue_declare(queue=q, durable=True)
                    self.channel.basic_consume(
                        queue=q,
                        on_message_callback=self._handle_delivery,
                        auto_ack=False
                    )

                print(f">>> [RABBITMQ CONSUMER READY] Listening on queues: {', '.join(QUEUES)}")
                self.channel.start_consuming()

            except pika.exceptions.AMQPConnectionError as e:
                logger.warning(f"RabbitMQ connection failed ({e}). Retrying in 10s...")
                print(f">>> [RABBITMQ NOTICE] RabbitMQ broker not reachable at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}. Retrying in 10s...")
                time.sleep(10)
            except Exception as e:
                logger.error(f"Unexpected RabbitMQ Consumer error: {e}. Retrying in 10s...")
                time.sleep(10)

    def _handle_delivery(self, ch, method, properties, body):
        queue_name = method.routing_key
        try:
            payload = json.loads(body.decode("utf-8"))
            cid = getattr(properties, "correlation_id", None) or payload.get("correlation_id") or "UNKNOWN"
            if "correlation_id" not in payload and cid != "UNKNOWN":
                payload["correlation_id"] = cid
            print(f"[CORRELATION_ID: {cid}] >>> [RABBITMQ MESSAGE RECEIVED] Queue: {queue_name}")
            if self.on_message_callback:
                self.on_message_callback(queue_name, payload)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing message from {queue_name}: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

rabbitmq_consumer = RabbitMQConsumer()
