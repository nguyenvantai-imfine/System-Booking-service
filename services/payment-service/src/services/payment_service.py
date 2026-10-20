import math
import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from src.core.config import settings
from src.models import (
    ThanhToanModel,
    TrangThaiThanhToanEnum,
    PhuongThucThanhToanEnum,
)
from src.schemas import (
    CreatePaymentRequest,
    SimulateIpnRequest,
    PaymentStatsResponse,
)

class PaymentService:
    @staticmethod
    def create_payment(
        db: Session, payload: CreatePaymentRequest
    ) -> ThanhToanModel:
        now_utc = datetime.utcnow()
        # Sinh mã giao dịch cổng thanh toán: VNPAY-YYYYMMDDHHMMSS-XXXX
        random_code = uuid.uuid4().hex[:6].upper()
        gateway_txn = f"{payload.phuong_thuc.value}-{now_utc.strftime('%Y%m%d%H%M%S')}-{random_code}"

        # URL thanh toán Sandbox giả lập
        payment_url = f"http://localhost:8004/api/v1/payments/sandbox-checkout?txn={gateway_txn}&amount={payload.so_tien}&booking={payload.ma_booking}"

        db_payment = ThanhToanModel(
            id_dat_phong=payload.id_dat_phong,
            ma_booking=payload.ma_booking,
            so_tien=payload.so_tien,
            phuong_thuc=payload.phuong_thuc.value,
            trang_thai=TrangThaiThanhToanEnum.PENDING.value,
            ma_giao_dich_gateway=gateway_txn,
            payment_url=payment_url,
            ghi_chu=payload.ghi_chu or f"Thanh toán đơn {payload.ma_booking}",
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment

    @staticmethod
    async def simulate_ipn(
        db: Session, payload: SimulateIpnRequest
    ) -> ThanhToanModel:
        """
        Mô phỏng IPN Callback từ cổng thanh toán.
        Nếu SUCCESS: Tự động phát tín hiệu sang Booking Service để xác nhận đơn (CONFIRMED).
        """
        payment = (
            db.query(ThanhToanModel)
            .filter(ThanhToanModel.ma_giao_dich_gateway == payload.ma_giao_dich_gateway)
            .first()
        )
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy giao dịch: {payload.ma_giao_dich_gateway}",
            )

        old_status = payment.trang_thai
        payment.trang_thai = payload.trang_thai.value

        if payload.trang_thai == TrangThaiThanhToanEnum.SUCCESS:
            payment.ngay_thanh_toan = datetime.utcnow()
            payment.ghi_chu = payload.note or "Thanh toán thành công qua IPN Callback"

            # Gọi webhook sang Booking Service để xác nhận đơn
            try:
                import urllib.request
                import urllib.parse
                note_encoded = urllib.parse.quote(
                    f"Xác nhận tự động qua cổng {payment.phuong_thuc} ({payment.ma_giao_dich_gateway})"
                )
                confirm_url = f"{settings.BOOKING_SERVICE_URL}/bookings/{payment.id_dat_phong}/confirm?note={note_encoded}"
                req = urllib.request.Request(confirm_url, method="PATCH")
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    print(
                        f">>> [Payment Service] Booking {payment.id_dat_phong} confirmed successfully via IPN (status {resp.status})."
                    )
            except Exception as e:
                print(f">>> [Payment Service] Error contacting booking-service: {str(e)}")

            # Bắn sự kiện thanh toán thành công qua RabbitMQ / Notification Service
            try:
                from src.core.publisher import publish_payment_event
                publish_payment_event("notification.payment.success", {
                    "ma_booking": payment.ma_booking,
                    "id_dat_phong": payment.id_dat_phong,
                    "id_thanh_toan": payment.id_thanh_toan,
                    "so_tien": float(payment.so_tien),
                    "phuong_thuc": payment.phuong_thuc,
                    "ma_giao_dich_gateway": payment.ma_giao_dich_gateway,
                })
            except Exception as mq_err:
                print(f">>> [Payment Service] MQ Warning: {mq_err}")

        elif payload.trang_thai == TrangThaiThanhToanEnum.FAILED:
            payment.ghi_chu = payload.note or "Giao dịch thanh toán thất bại"

        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def get_payments(
        db: Session,
        status_filter: Optional[str] = None,
        method_filter: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ThanhToanModel], int, int]:
        query = db.query(ThanhToanModel)

        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(ThanhToanModel.trang_thai == status_filter.upper())

        if method_filter and method_filter.upper() != "ALL":
            query = query.filter(ThanhToanModel.phuong_thuc == method_filter.upper())

        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.filter(
                (ThanhToanModel.ma_booking.ilike(kw))
                | (ThanhToanModel.ma_giao_dich_gateway.ilike(kw))
            )

        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        items = (
            query.order_by(desc(ThanhToanModel.id_thanh_toan))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total, total_pages

    @staticmethod
    def get_stats(db: Session) -> PaymentStatsResponse:
        total_rev = (
            db.query(func.coalesce(func.sum(ThanhToanModel.so_tien), 0))
            .filter(ThanhToanModel.trang_thai == TrangThaiThanhToanEnum.SUCCESS.value)
            .scalar()
        )

        total_tx = db.query(func.count(ThanhToanModel.id_thanh_toan)).scalar() or 0
        success_count = (
            db.query(func.count(ThanhToanModel.id_thanh_toan))
            .filter(ThanhToanModel.trang_thai == TrangThaiThanhToanEnum.SUCCESS.value)
            .scalar()
            or 0
        )
        pending_count = (
            db.query(func.count(ThanhToanModel.id_thanh_toan))
            .filter(ThanhToanModel.trang_thai == TrangThaiThanhToanEnum.PENDING.value)
            .scalar()
            or 0
        )
        failed_count = (
            db.query(func.count(ThanhToanModel.id_thanh_toan))
            .filter(ThanhToanModel.trang_thai == TrangThaiThanhToanEnum.FAILED.value)
            .scalar()
            or 0
        )

        return PaymentStatsResponse(
            total_revenue=float(total_rev),
            total_transactions=total_tx,
            success_count=success_count,
            pending_count=pending_count,
            failed_count=failed_count,
        )

    @staticmethod
    def seed_default_payments(db: Session) -> None:
        try:
            count = db.query(ThanhToanModel).count()
            if count == 0:
                print(">>> [Payment Service] Seeding default sample payment...")
                sample = ThanhToanModel(
                    id_dat_phong=1,
                    ma_booking="BK-202610-8912",
                    so_tien=3750000,
                    phuong_thuc=PhuongThucThanhToanEnum.VNPAY.value,
                    trang_thai=TrangThaiThanhToanEnum.SUCCESS.value,
                    ma_giao_dich_gateway="VNPAY-20261020-001",
                    payment_url="http://localhost:8004/api/v1/payments/sandbox-checkout?txn=VNPAY-20261020-001",
                    ngay_tao=datetime.utcnow(),
                    ngay_thanh_toan=datetime.utcnow(),
                    ghi_chu="Thanh toán đơn BK-202610-8912 qua VNPay Sandbox",
                )
                db.add(sample)
                db.commit()
                print(">>> [Payment Service] Seeded default payment successfully.")
        except Exception as e:
            db.rollback()
            print(">>> [Payment Service] Seed warning:", str(e))
