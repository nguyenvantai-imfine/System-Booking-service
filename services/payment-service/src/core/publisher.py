import json
import logging
import urllib.request
import pika
from src.core.config import settings

logger = logging.getLogger(__name__)

def publish_payment_event(queue_name: str, payload: dict):
    """
    Bắn message thanh toán thành công vào RabbitMQ queue.
    Nếu RabbitMQ chưa bật, tự động fallback gửi trực tiếp qua REST API Notification Service.
    """
    published = False
    try:
        credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
            connection_attempts=1,
            retry_delay=1,
            socket_timeout=2,
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)

        message_body = json.dumps(payload, ensure_ascii=False)
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=message_body.encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            )
        )
        connection.close()
        published = True
        print(f">>> [PAYMENT RABBITMQ] Đã bắn sự kiện thanh toán vào queue: {queue_name}")
    except Exception as e:
        logger.warning(f"RabbitMQ publish skipped/failed ({e}). Triggering Notification API directly...")

    # Fallback trực tiếp nếu RabbitMQ chưa bật
    if not published and settings.NOTIFICATION_SERVICE_URL:
        try:
            data = json.dumps({
                "loai_thong_bao": "PAYMENT_SUCCESS",
                "nguoi_nhan": payload.get("email") or "customer@hotel.com",
                "kenh_gui": "EMAIL",
                "ma_booking": payload.get("ma_booking"),
                "du_lieu": payload,
            }, ensure_ascii=False).encode("utf-8")

            url = f"{settings.NOTIFICATION_SERVICE_URL}/notifications/send"
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as res:
                if res.status in (200, 201):
                    print(f">>> [PAYMENT NOTIFICATION FALLBACK] Gửi email xác nhận thanh toán trực tiếp thành công!")
        except Exception as fallback_err:
            logger.warning(f"Payment notification fallback API failed: {fallback_err}")
