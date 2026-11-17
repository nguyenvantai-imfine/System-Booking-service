import hashlib
import json
import logging
import urllib.request
import pika
from src.core.config import settings

logger = logging.getLogger(__name__)


def _close_connection(connection):
    if connection is not None and connection.is_open:
        try:
            connection.close()
        except Exception as exc:
            logger.warning("Broker connection close failed; error_type=%s", type(exc).__name__)

def publish_payment_event(queue_name: str, payload: dict):
    """
    Bắn message thanh toán thành công vào RabbitMQ queue.
    Nếu RabbitMQ chưa bật, tự động fallback gửi trực tiếp qua REST API Notification Service.
    """
    notification_types = {
        "notification.payment.success": "PAYMENT_SUCCESS",
    }

    from src.core.correlation import get_correlation_id
    cid = get_correlation_id() or payload.get("correlation_id") or ""
    if cid:
        payload["correlation_id"] = cid

    event_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    event_key = hashlib.sha256(queue_name.encode("utf-8") + b"\0" + event_body).hexdigest()
    published = False
    connection = None
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
        channel.confirm_delivery()
        channel.basic_publish(
            mandatory=True,
            exchange="",
            routing_key=queue_name,
            body=message_body.encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                correlation_id=cid if cid else None,
                headers={"X-Correlation-ID": cid} if cid else None,
            )
        )
        connection.close()
        published = True
        logger.info(
            "Payment event published; queue=%s correlation_id=%s",
            queue_name,
            cid or "UNKNOWN",
        )
    except Exception as e:
        logger.warning(f"RabbitMQ publish skipped/failed ({e}). Triggering Notification API directly...")
    finally:
        _close_connection(connection)

    # Fallback trực tiếp nếu RabbitMQ chưa bật
    if not published and settings.NOTIFICATION_SERVICE_URL:
        notification_type = notification_types.get(queue_name)
        if notification_type is None:
            logger.error(
                "No success notification fallback is defined for queue=%s.",
                queue_name,
            )
            return

        recipient = payload.get("email") or payload.get("nguoi_nhan")
        if not isinstance(recipient, str) or not recipient.strip():
            logger.error(
                "Payment notification fallback has no valid recipient; queue=%s.",
                queue_name,
            )
            return

        try:
            data = json.dumps({
                "loai_thong_bao": notification_type,
                "id_tai_khoan": payload.get("id_tai_khoan"),
                "nguoi_nhan": recipient.strip(),
                "kenh_gui": "EMAIL",
                "ma_booking": payload.get("ma_booking"),
                "du_lieu": payload,
            }, ensure_ascii=False).encode("utf-8")

            url = f"{settings.NOTIFICATION_SERVICE_URL}/notifications/internal-send"
            req_headers = {
                "Content-Type": "application/json",
                "X-Internal-Secret": settings.INTERNAL_SERVICE_SECRET,
                "X-Notification-Event-Key": event_key,
            }
            if cid:
                req_headers["X-Correlation-ID"] = cid
            req = urllib.request.Request(url, data=data, headers=req_headers)
            with urllib.request.urlopen(req, timeout=3) as res:
                if res.status in (200, 201):
                    logger.info(
                        "Payment notification fallback accepted; "
                        "queue=%s correlation_id=%s",
                        queue_name,
                        cid or "UNKNOWN",
                    )
        except Exception as fallback_err:
            logger.warning(f"Payment notification fallback API failed: {fallback_err}")

def publish_otp_event(queue_name: str, payload: dict):
    """
    Bắn sự kiện tạo OTP vào RabbitMQ queue (mặc định notification.otp.generated).
    Nếu RabbitMQ chưa bật hoặc gặp lỗi, fallback gửi trực tiếp qua REST API Notification Service và ghi log cảnh báo.
    """
    from src.core.correlation import get_correlation_id
    cid = get_correlation_id() or payload.get("correlation_id") or ""
    if cid:
        payload["correlation_id"] = cid

    event_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    event_key = hashlib.sha256(queue_name.encode("utf-8") + b"\0" + event_body).hexdigest()
    published = False
    connection = None
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
        channel.confirm_delivery()
        channel.basic_publish(
            mandatory=True,
            exchange="",
            routing_key=queue_name,
            body=message_body.encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                correlation_id=cid if cid else None,
                headers={"X-Correlation-ID": cid} if cid else None,
            )
        )
        connection.close()
        published = True
        print(f"[CORRELATION_ID: {cid}] >>> [PAYMENT RABBITMQ] Da ban su kien OTP vao queue: {queue_name}")
    except Exception as e:
        logger.warning(f"RabbitMQ OTP publish skipped/failed ({e}). Triggering Notification API directly...")
        print(f">>> [PAYMENT RABBITMQ WARNING] Khong the ket noi RabbitMQ ({e}), chuyen sang fallback REST.")
    finally:
        _close_connection(connection)

    # Fallback trực tiếp qua REST Notification Service
    if not published and settings.NOTIFICATION_SERVICE_URL:
        try:
            email_dest = payload.get("email")
            data = json.dumps({
                "loai_thong_bao": "OTP_VERIFICATION",
                "id_tai_khoan": payload.get("id_tai_khoan"),
                "nguoi_nhan": email_dest,
                "kenh_gui": "EMAIL",
                "ma_booking": payload.get("ma_booking"),
                "du_lieu": {
                    "otp_code": payload.get("otp_code"),
                    "ma_giao_dich_gateway": payload.get("ma_giao_dich_gateway"),
                    "expires_in_seconds": payload.get("expires_in_seconds", 180),
                    "message": f"Mã OTP xác thực thanh toán của bạn là: {payload.get('otp_code')} (Hiệu lực trong {payload.get('expires_in_seconds', 180)} giây).",
                },
            }, ensure_ascii=False).encode("utf-8")

            url = f"{settings.NOTIFICATION_SERVICE_URL}/notifications/internal-send"
            req_headers = {
                "Content-Type": "application/json",
                "X-Internal-Secret": settings.INTERNAL_SERVICE_SECRET,
                "X-Notification-Event-Key": event_key,
            }
            if cid:
                req_headers["X-Correlation-ID"] = cid
            req = urllib.request.Request(url, data=data, headers=req_headers)
            with urllib.request.urlopen(req, timeout=3) as res:
                if res.status in (200, 201):
                    print(f"[CORRELATION_ID: {cid}] >>> [PAYMENT NOTIFICATION FALLBACK] Gui ma OTP truc tiep qua REST API thanh cong!")
        except Exception as fallback_err:
            logger.warning(f"Payment OTP notification fallback API failed: {fallback_err}")
