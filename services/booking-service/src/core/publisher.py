import json
import logging
import urllib.request
import urllib.error

import pika

from src.core.config import settings
from src.core.correlation import get_correlation_id


logger = logging.getLogger(__name__)


def publish_notification_event(queue_name: str, payload: dict):
    """
    Gửi sự kiện thông báo qua RabbitMQ.

    Nếu RabbitMQ không hoạt động, thử gửi trực tiếp
    qua REST API của Notification Service.
    """

    published = False
    connection = None

    # =====================================================
    # 1. GỬI MESSAGE QUA RABBITMQ
    # =====================================================

    try:
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER,
            settings.RABBITMQ_PASSWORD,
        )

        parameters = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
            connection_attempts=1,
            retry_delay=1,
            socket_timeout=2,
            heartbeat=30,
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(
            queue=queue_name,
            durable=True,
        )

        # Bật publisher confirmation để kiểm tra việc RabbitMQ
        # xác nhận message đã được nhận.
        channel.confirm_delivery()

        message_body = json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")

        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                content_encoding="utf-8",
            ),
            mandatory=True,
        )

        published = True

        logger.info(
            "RabbitMQ publish thành công. Queue: %s",
            queue_name,
        )

    except Exception as exc:
        logger.warning(
            "RabbitMQ publish thất bại. Queue: %s. Lỗi: %s",
            queue_name,
            exc,
        )

    finally:
        if connection is not None and connection.is_open:
            try:
                connection.close()
            except Exception as exc:
                logger.warning(
                    "Không thể đóng RabbitMQ connection: %s",
                    exc,
                )

    if published:
        return True

    # =====================================================
    # 2. FALLBACK QUA NOTIFICATION SERVICE
    # =====================================================

    notification_url = str(
        settings.NOTIFICATION_SERVICE_URL or ""
    ).strip().rstrip("/")

    if not notification_url:
        logger.warning(
            "Không thể gửi notification fallback: "
            "NOTIFICATION_SERVICE_URL chưa được cấu hình."
        )
        return False

    try:
        loai_map = {
            "notification.booking.confirmed": "BOOKING_CONFIRMED",
            "notification.payment.success": "PAYMENT_SUCCESS",
            "notification.booking.cancelled": "BOOKING_CANCELLED",
        }

        loai_thong_bao = loai_map.get(
            queue_name,
            "SYSTEM",
        )

        email = (
            payload.get("email")
            or payload.get("nguoi_nhan")
        )

        if not email:
            khach_o = payload.get("khach_o")

            if isinstance(khach_o, dict):
                email = khach_o.get("email")

        if not email:
            logger.warning(
                "Không thể gửi notification fallback: "
                "Payload không có email người nhận."
            )
            return False

        notification_data = {
            "loai_thong_bao": loai_thong_bao,
            "nguoi_nhan": email,
            "kenh_gui": "EMAIL",
            "id_tai_khoan": payload.get("id_tai_khoan"),
            "ma_booking": payload.get("ma_booking"),
            "du_lieu": payload,
        }

        data = json.dumps(
            notification_data,
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")

        url = (
            f"{notification_url}/notifications/internal-send"
        )

        correlation_id = (
            get_correlation_id()
            or payload.get("correlation_id")
            or ""
        )

        headers = {
            "Content-Type": "application/json",
        }

        if settings.INTERNAL_SERVICE_SECRET:
            # Header này cần khớp với Notification Service.
            headers["X-Internal-Secret"] = (
                settings.INTERNAL_SERVICE_SECRET
            )

        if correlation_id:
            headers["X-Correlation-ID"] = str(correlation_id)

        request = urllib.request.Request(
            url=url,
            data=data,
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=5,
        ) as response:

            if 200 <= response.status < 300:
                logger.info(
                    "Notification fallback thành công. "
                    "Booking: %s",
                    payload.get("ma_booking"),
                )
                return True

            logger.warning(
                "Notification Service trả về HTTP %s.",
                response.status,
            )

    except urllib.error.HTTPError as exc:
        logger.error(
            "Notification Service từ chối request. HTTP %s.",
            exc.code,
        )

    except urllib.error.URLError as exc:
        logger.error(
            "Không kết nối được Notification Service: %s",
            exc.reason,
        )

    except Exception:
        logger.exception(
            "Lỗi khi gửi notification fallback."
        )

    return False