import json
import logging
import urllib.request
import pika
from src.core.config import settings

logger = logging.getLogger(__name__)

def publish_notification_event(queue_name: str, payload: dict):
    """
    Bắn message vào RabbitMQ queue.
    Nếu RabbitMQ không kết nối được (chạy local chưa bật RabbitMQ),
    tự động fallback gửi qua REST API của Notification Service.
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
                delivery_mode=2, # make message persistent
                content_type="application/json",
            )
        )
        connection.close()
        published = True
        print(f">>> [RABBITMQ PUBLISHED] Bắn tin nhắn thành công vào queue: {queue_name}")
    except Exception as e:
        logger.warning(f"RabbitMQ publish skipped/failed ({e}). Triggering Notification API directly...")

    # Fallback trực tiếp nếu RabbitMQ chưa bật
    if not published and settings.NOTIFICATION_SERVICE_URL:
        try:
            loai_map = {
                "notification.booking.confirmed": "BOOKING_CONFIRMED",
                "notification.payment.success": "PAYMENT_SUCCESS",
                "notification.booking.cancelled": "BOOKING_CANCELLED",
            }
            loai_thong_bao = loai_map.get(queue_name, "SYSTEM")
            email = payload.get("email") or payload.get("nguoi_nhan")
            if not email:
                khach_o = payload.get("khach_o")
                if isinstance(khach_o, dict):
                    email = khach_o.get("email")

            data = json.dumps({
                "loai_thong_bao": loai_thong_bao,
                "nguoi_nhan": email or "customer@hotel.com",
                "kenh_gui": "EMAIL",
                "id_tai_khoan": payload.get("id_tai_khoan"),
                "ma_booking": payload.get("ma_booking"),
                "du_lieu": payload,
            }, ensure_ascii=False).encode("utf-8")

            url = f"{settings.NOTIFICATION_SERVICE_URL}/notifications/internal-send"
            from src.core.correlation import get_correlation_id
            cid = get_correlation_id() or payload.get("correlation_id") or ""
            req_headers = {
                "Content-Type": "application/json",
                "X-Internal-Secret": getattr(settings, "INTERNAL_SERVICE_SECRET", "booking_internal_secret_key_2026"),
            }
            if cid:
                req_headers["X-Correlation-ID"] = cid
            req = urllib.request.Request(url, data=data, headers=req_headers)
            with urllib.request.urlopen(req, timeout=3) as res:
                if res.status in (200, 201):
                    print(f">>> [NOTIFICATION FALLBACK API] Gửi thông báo trực tiếp thành công cho {email}!")
        except Exception as fallback_err:
            logger.warning(f"Notification fallback API also failed: {fallback_err}")
