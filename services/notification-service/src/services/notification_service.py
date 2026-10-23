import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.models.thong_bao import ThongBaoModel
from src.models.noi_dung_thong_bao import NoiDungThongBaoModel
from src.schemas.notification_schema import SendNotificationRequest
from src.core.templates import (
    render_booking_confirmed_email,
    render_booking_cancelled_email,
    render_otp_email,
)
from src.core.email_sender import email_sender
from src.core.database import SessionLocal

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_notification(db: Session, req: SendNotificationRequest) -> ThongBaoModel:
        """Tạo và gửi thông báo (qua Email hoặc kênh khác)"""
        loai = req.loai_thong_bao.upper()
        du_lieu = req.du_lieu or {}
        if req.ma_booking and "ma_booking" not in du_lieu:
            du_lieu["ma_booking"] = req.ma_booking

        # 1. Render Template theo loại thông báo
        if loai in ("BOOKING_CONFIRMED", "PAYMENT_SUCCESS"):
            subject, html_content, text_content = render_booking_confirmed_email(du_lieu)
        elif loai == "BOOKING_CANCELLED":
            subject, html_content, text_content = render_booking_cancelled_email(du_lieu)
        elif loai in ("OTP", "OTP_VERIFICATION", "NOTIFICATION.OTP.GENERATED"):
            loai = "OTP"
            subject, html_content, text_content = render_otp_email(du_lieu)
        else:
            subject = f"Thông báo từ hệ thống đặt phòng: {loai}"
            html_content = f"<p>{du_lieu.get('message', 'Thông báo từ hệ thống')}</p>"
            text_content = du_lieu.get("message", "Thông báo từ hệ thống")

        # 2. Tạo bản ghi ThongBao trong DB
        thong_bao = ThongBaoModel(
            id_tai_khoan=req.id_tai_khoan,
            loai_thong_bao=loai,
            kenh_gui=req.kenh_gui,
            nguoi_nhan=req.nguoi_nhan,
            trang_thai="PENDING",
            ma_booking=req.ma_booking or du_lieu.get("ma_booking"),
            ngay_tao=datetime.utcnow(),
        )
        db.add(thong_bao)
        db.flush()

        # 3. Tạo bản ghi NoiDungThongBao (Che mã OTP trước khi lưu trữ lâu dài trong CSDL)
        saved_html = html_content
        saved_text = text_content
        saved_du_lieu = dict(du_lieu)

        if loai == "OTP":
            otp_val = str(du_lieu.get("otp_code", ""))
            if otp_val:
                masked_otp = f"{otp_val[:2]}****" if len(otp_val) >= 2 else "******"
                saved_html = saved_html.replace(otp_val, masked_otp)
                if saved_text:
                    saved_text = saved_text.replace(otp_val, masked_otp)
                saved_du_lieu["otp_code"] = masked_otp

        noi_dung = NoiDungThongBaoModel(
            id_thong_bao=thong_bao.id_thong_bao,
            tieu_de=subject,
            noi_dung_html=saved_html,
            noi_dung_text=saved_text,
            du_lieu_dinh_kem=json.dumps(saved_du_lieu, ensure_ascii=False),
        )
        db.add(noi_dung)

        # 4. Gửi email
        if req.kenh_gui.upper() == "EMAIL":
            success, msg = email_sender.send_email(
                to_email=req.nguoi_nhan,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )
            if success:
                thong_bao.trang_thai = "SENT"
                thong_bao.ngay_gui = datetime.utcnow()
            else:
                thong_bao.trang_thai = "FAILED"
                thong_bao.ghi_chu_loi = msg
        else:
            thong_bao.trang_thai = "SENT"
            thong_bao.ngay_gui = datetime.utcnow()

        db.commit()
        db.refresh(thong_bao)
        return thong_bao

    @classmethod
    def send_otp_notification(cls, db: Session, payload: Dict[str, Any]) -> ThongBaoModel:
        """Hàm chuyên biệt xử lý sự kiện gửi email OTP"""
        email = payload.get("email") or payload.get("nguoi_nhan") or "customer@hotel.com"
        req = SendNotificationRequest(
            loai_thong_bao="OTP",
            nguoi_nhan=email,
            kenh_gui="EMAIL",
            id_tai_khoan=payload.get("id_tai_khoan"),
            ma_booking=payload.get("ma_booking"),
            du_lieu=payload,
        )
        return cls.send_notification(db, req)

    @classmethod
    def handle_message_queue_event(cls, queue_name: str, payload: Dict[str, Any]):
        """Xử lý sự kiện từ RabbitMQ Consumer trong thread nền"""
        db = SessionLocal()
        try:
            loai_map = {
                "notification.booking.confirmed": "BOOKING_CONFIRMED",
                "notification.payment.success": "PAYMENT_SUCCESS",
                "notification.booking.cancelled": "BOOKING_CANCELLED",
                "notification.otp.generated": "OTP",
            }
            loai_thong_bao = loai_map.get(queue_name, "SYSTEM")

            email = payload.get("email") or payload.get("nguoi_nhan")
            if not email:
                khach_o = payload.get("khach_o")
                if isinstance(khach_o, dict):
                    email = khach_o.get("email")

            if not email:
                email = "customer@hotel.com" # Fallback email mặc định

            req = SendNotificationRequest(
                loai_thong_bao=loai_thong_bao,
                nguoi_nhan=email,
                kenh_gui="EMAIL",
                id_tai_khoan=payload.get("id_tai_khoan"),
                ma_booking=payload.get("ma_booking"),
                du_lieu=payload,
            )
            cls.send_notification(db, req)
            cid = payload.get("correlation_id") or "UNKNOWN"
            print(f"[CORRELATION_ID: {cid}] >>> [NOTIFICATION SERVICE] Notification processed and sent to {email}!")
        except Exception as e:
            logger.error(f"Error handling MQ event {queue_name}: {e}")
            print(f">>> [NOTIFICATION SERVICE ERROR]: {e}")
        finally:
            db.close()

    @staticmethod
    def get_notifications(
        db: Session,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        recipient: Optional[str] = None,
        booking_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 15,
    ) -> tuple[list[ThongBaoModel], int]:
        query = db.query(ThongBaoModel)
        if status and status.upper() != "ALL":
            query = query.filter(ThongBaoModel.trang_thai == status.upper())
        if notification_type and notification_type.upper() != "ALL":
            query = query.filter(ThongBaoModel.loai_thong_bao == notification_type.upper())
        if recipient:
            query = query.filter(ThongBaoModel.nguoi_nhan.like(f"%{recipient.strip()}%"))
        if booking_code:
            query = query.filter(ThongBaoModel.ma_booking.like(f"%{booking_code.strip()}%"))

        total = query.count()
        items = (
            query.order_by(desc(ThongBaoModel.id_thong_bao))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get_notification_by_id(db: Session, id_thong_bao: int) -> Optional[ThongBaoModel]:
        return db.query(ThongBaoModel).filter(ThongBaoModel.id_thong_bao == id_thong_bao).first()

    @staticmethod
    def get_stats(db: Session) -> Dict[str, int]:
        total = db.query(func.count(ThongBaoModel.id_thong_bao)).scalar() or 0
        sent = db.query(func.count(ThongBaoModel.id_thong_bao)).filter(ThongBaoModel.trang_thai == "SENT").scalar() or 0
        failed = db.query(func.count(ThongBaoModel.id_thong_bao)).filter(ThongBaoModel.trang_thai == "FAILED").scalar() or 0
        pending = db.query(func.count(ThongBaoModel.id_thong_bao)).filter(ThongBaoModel.trang_thai == "PENDING").scalar() or 0
        return {
            "total_notifications": total,
            "sent_count": sent,
            "failed_count": failed,
            "pending_count": pending,
        }
