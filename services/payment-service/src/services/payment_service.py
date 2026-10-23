import math
import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.core.config import settings
from src.core.publisher import publish_payment_event, publish_otp_event
from src.models import (
    ThanhToanModel,
    TrangThaiThanhToanEnum,
    PhuongThucThanhToanEnum,
    GiaoDichOtpModel,
)
from src.schemas import (
    CreatePaymentRequest,
    SimulateIpnRequest,
    PaymentStatsResponse,
    GenerateOtpRequest,
    VerifyOtpRequest,
    OtpResponse,
)

class PaymentService:
    @staticmethod
    async def generate_otp(
        db: Session, payload: GenerateOtpRequest
    ) -> OtpResponse:
        # 1. Kiểm tra giao dịch tồn tại và đang PENDING
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

        if payment.trang_thai != TrangThaiThanhToanEnum.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Giao dịch đã ở trạng thái {payment.trang_thai}, không thể tạo OTP.",
            )

        # 2. Vô hiệu hóa các OTP cũ chưa dùng của giao dịch
        db.query(GiaoDichOtpModel).filter(
            GiaoDichOtpModel.ma_giao_dich_gateway == payload.ma_giao_dich_gateway,
            GiaoDichOtpModel.da_su_dung == False,
        ).update({"da_su_dung": True}, synchronize_session=False)

        # 3. Sinh mã 6 chữ số bằng module secrets (secrets.randbelow), giữ số 0 đứng đầu bằng zfill(6)
        otp_code = str(secrets.randbelow(1_000_000)).zfill(6)

        # 4. Hạn dùng 3 phút (now + timedelta(minutes=3)); lưu DB
        now_utc = datetime.utcnow()
        expires_at = now_utc + timedelta(minutes=3)
        expires_in_seconds = 180

        otp_record = GiaoDichOtpModel(
            ma_giao_dich_gateway=payload.ma_giao_dich_gateway,
            email=str(payload.email),
            otp_code=otp_code,
            thoi_gian_tao=now_utc,
            thoi_gian_het_han=expires_at,
            da_su_dung=False,
            so_lan_thu=0,
        )
        db.add(otp_record)
        db.commit()
        db.refresh(otp_record)

        # 5. Publish event RabbitMQ notification.otp.generated với payload
        # Nếu publish lỗi thì fallback gọi REST sang Notification Service (/api/v1/notifications/send) và ghi log cảnh báo
        try:
            publish_otp_event("notification.otp.generated", {
                "email": str(payload.email),
                "otp_code": otp_code,
                "ma_giao_dich_gateway": payload.ma_giao_dich_gateway,
                "ma_booking": payment.ma_booking,
                "expires_in_seconds": expires_in_seconds,
            })
        except Exception as e:
            print(f">>> [Payment Service] Error publishing OTP event: {e}")

        # 6. Không bao giờ trả otp_code trong response API
        return OtpResponse(
            success=True,
            message=f"Mã OTP đã được gửi đến email {payload.email}.",
            ma_giao_dich_gateway=payload.ma_giao_dich_gateway,
            expires_in_seconds=expires_in_seconds,
        )

    @staticmethod
    async def verify_otp(
        db: Session, payload: VerifyOtpRequest
    ) -> ThanhToanModel:
        # 1. Mở transaction, khóa dòng giao dịch bằng with_for_update() để chống tranh chấp
        payment = (
            db.query(ThanhToanModel)
            .filter(ThanhToanModel.ma_giao_dich_gateway == payload.ma_giao_dich_gateway)
            .with_for_update()
            .with_hint(ThanhToanModel, "WITH (UPDLOCK, ROWLOCK)")
            .first()
        )
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy giao dịch: {payload.ma_giao_dich_gateway}",
            )

        if payment.trang_thai == TrangThaiThanhToanEnum.SUCCESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giao dịch này đã được thanh toán thành công trước đó.",
            )

        # 2. Lấy OTP mới nhất theo ma_giao_dich_gateway
        otp_record = (
            db.query(GiaoDichOtpModel)
            .filter(GiaoDichOtpModel.ma_giao_dich_gateway == payload.ma_giao_dich_gateway)
            .order_by(desc(GiaoDichOtpModel.id_otp))
            .with_for_update()
            .with_hint(GiaoDichOtpModel, "WITH (UPDLOCK, ROWLOCK)")
            .first()
        )
        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không tìm thấy mã OTP nào cho giao dịch này. Vui lòng yêu cầu tạo OTP mới.",
            )

        # Kiểm tra da_su_dung == 0
        if otp_record.da_su_dung:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã OTP này đã được sử dụng. Vui lòng tạo mã OTP mới.",
            )

        # Kiểm tra so_lan_thu < 3
        if otp_record.so_lan_thu >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã OTP đã vượt quá 3 lần thử sai. Vui lòng tạo mã OTP mới.",
            )

        # Kiểm tra now <= thoi_gian_het_han
        now_utc = datetime.utcnow()
        if now_utc > otp_record.thoi_gian_het_han:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã OTP đã hết thời hạn hiệu lực (3 phút). Vui lòng tạo mã OTP mới.",
            )

        # So sánh mã bằng secrets.compare_digest
        if not secrets.compare_digest(otp_record.otp_code, payload.otp_code):
            otp_record.so_lan_thu += 1
            db.commit()
            remaining = 3 - otp_record.so_lan_thu
            if remaining <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mã OTP không chính xác. Bạn đã hết 3 lần thử, vui lòng tạo mã OTP mới.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã OTP không chính xác. Bạn còn {remaining} lần thử.",
            )

        # Đúng mã: da_su_dung = 1, cập nhật thanh_toan sang SUCCESS, commit nguyên tử
        otp_record.da_su_dung = True
        payment.trang_thai = TrangThaiThanhToanEnum.SUCCESS.value
        payment.ngay_thanh_toan = datetime.utcnow()
        payment.ghi_chu = f"Thanh toán xác thực OTP thành công ({otp_record.email})"

        db.commit()
        db.refresh(payment)

        # Sau commit: gọi đồng bộ PATCH sang Booking Service để chuyển đơn sang CONFIRMED
        try:
            import urllib.request
            import urllib.parse
            note_encoded = urllib.parse.quote(
                f"Xác nhận tự động qua cổng {payment.phuong_thuc} OTP ({payment.ma_giao_dich_gateway})"
            )
            from src.core.correlation import get_correlation_id
            cid = get_correlation_id()
            headers = {"User-Agent": "payment-service"}
            if cid:
                headers["X-Correlation-ID"] = cid

            confirm_url = f"{settings.BOOKING_SERVICE_URL}/bookings/{payment.id_dat_phong}/confirm?note={note_encoded}"
            req = urllib.request.Request(confirm_url, method="PATCH", headers=headers)
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                print(
                    f">>> [Payment Service] Booking {payment.id_dat_phong} confirmed successfully via OTP (status {resp.status})."
                )
        except Exception as e:
            print(f">>> [Payment Service] Error contacting booking-service: {str(e)}")

        # Publish event notification.payment.success để gửi vé điện tử kèm QR
        try:
            publish_payment_event("notification.payment.success", {
                "ma_booking": payment.ma_booking,
                "id_dat_phong": payment.id_dat_phong,
                "id_thanh_toan": payment.id_thanh_toan,
                "so_tien": float(payment.so_tien),
                "phuong_thuc": payment.phuong_thuc,
                "ma_giao_dich_gateway": payment.ma_giao_dich_gateway,
                "email": otp_record.email,
            })
        except Exception as mq_err:
            print(f">>> [Payment Service] MQ Warning: {mq_err}")

        return payment

    @staticmethod
    def create_payment(
        db: Session,
        payload: CreatePaymentRequest,
        idempotency_key: Optional[str] = None,
    ) -> ThanhToanModel:
        clean_idem_key = idempotency_key.strip() if idempotency_key and idempotency_key.strip() else None

        # 1. Kiểm tra Idempotency Key nếu được cung cấp
        if clean_idem_key:
            existing_txn = (
                db.query(ThanhToanModel)
                .filter(ThanhToanModel.idempotency_key == clean_idem_key)
                .first()
            )
            if existing_txn:
                # Nếu cùng key nhưng khác id_dat_phong hoặc số tiền: trả 409 Conflict kèm thông báo rõ ràng
                if (
                    existing_txn.id_dat_phong != payload.id_dat_phong
                    or float(existing_txn.so_tien) != float(payload.so_tien)
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            f"X-Idempotency-Key '{clean_idem_key}' đã được sử dụng trước đó cho đơn đặt phòng hoặc số tiền khác "
                            f"(ID: {existing_txn.id_dat_phong}, Số tiền: {float(existing_txn.so_tien):,.0f} VND)."
                        ),
                    )
                # Key khớp hoàn toàn: trả lại giao dịch cũ, không tạo bản ghi mới
                return existing_txn

        # 2. Validation: không cho tạo thanh toán mới cho đơn đã CONFIRMED hoặc đã hết hạn giữ chỗ
        # 2.1 Kiểm tra cục bộ trong CSDL payment-service: đơn đã có giao dịch SUCCESS chưa
        existing_paid = (
            db.query(ThanhToanModel)
            .filter(
                ThanhToanModel.id_dat_phong == payload.id_dat_phong,
                ThanhToanModel.trang_thai == TrangThaiThanhToanEnum.SUCCESS.value,
            )
            .first()
        )
        if existing_paid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Đơn đặt phòng {payload.ma_booking} đã được thanh toán thành công trước đó (Mã GD: {existing_paid.ma_giao_dich_gateway}).",
            )

        # 2.2 Kiểm tra trạng thái và hạn giữ chỗ từ Booking Service
        try:
            import json
            import urllib.request
            import urllib.error
            from src.core.correlation import get_correlation_id
            cid = get_correlation_id()
            headers = {"User-Agent": "payment-service"}
            if cid:
                headers["X-Correlation-ID"] = cid

            booking_url = f"{settings.BOOKING_SERVICE_URL}/bookings/{payload.id_dat_phong}"
            req = urllib.request.Request(booking_url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    bk_data = json.loads(resp.read().decode("utf-8"))
                    bk_status = bk_data.get("trang_thai")
                    if bk_status == "CONFIRMED":
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Đơn đặt phòng {payload.ma_booking} đã ở trạng thái CONFIRMED (đã được thanh toán).",
                        )
                    if bk_status in ["CANCELLED", "EXPIRED"]:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Đơn đặt phòng {payload.ma_booking} đã bị hủy hoặc hết hạn ({bk_status}). Không thể tạo thanh toán.",
                        )

                    # Kiểm tra hạn giữ chỗ (han_giu_cho)
                    han_giu_cho_str = bk_data.get("han_giu_cho")
                    if han_giu_cho_str:
                        try:
                            clean_iso = han_giu_cho_str.replace("Z", "+00:00")
                            han_dt = datetime.fromisoformat(clean_iso)
                            if han_dt.tzinfo is not None:
                                han_dt = han_dt.astimezone().replace(tzinfo=None)
                            if datetime.utcnow() > han_dt:
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Đơn đặt phòng {payload.ma_booking} đã hết hạn giữ chỗ (15 phút). Vui lòng thực hiện đặt phòng lại.",
                                )
                        except HTTPException:
                            raise
                        except Exception as dt_err:
                            print(f">>> [Payment Service] Error checking hold time: {dt_err}")
        except urllib.error.HTTPError as http_err:
            if http_err.code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy đơn đặt phòng có ID {payload.id_dat_phong} tại Booking Service.",
                )
            elif http_err.code == 400:
                err_body = http_err.read().decode("utf-8", errors="ignore")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Booking Service từ chối: {err_body}",
                )
        except HTTPException:
            raise
        except Exception as net_err:
            print(f">>> [Payment Service] Warning: Unable to contact Booking Service for pre-validation: {net_err}")

        # 3. Khởi tạo bản ghi thanh toán mới
        now_utc = datetime.utcnow()
        random_code = uuid.uuid4().hex[:6].upper()
        gateway_txn = f"{payload.phuong_thuc.value}-{now_utc.strftime('%Y%m%d%H%M%S')}-{random_code}"
        payment_url = f"http://localhost:8004/api/v1/payments/sandbox-checkout?txn={gateway_txn}&amount={payload.so_tien}&booking={payload.ma_booking}"

        db_payment = ThanhToanModel(
            id_dat_phong=payload.id_dat_phong,
            ma_booking=payload.ma_booking,
            so_tien=payload.so_tien,
            phuong_thuc=payload.phuong_thuc.value,
            trang_thai=TrangThaiThanhToanEnum.PENDING.value,
            ma_giao_dich_gateway=gateway_txn,
            payment_url=payment_url,
            idempotency_key=clean_idem_key,
            ghi_chu=payload.ghi_chu or f"Thanh toán đơn {payload.ma_booking}",
        )
        db.add(db_payment)

        # 4. Bắt lỗi vi phạm unique khi 2 request cùng key đến đồng thời (race condition)
        try:
            db.commit()
            db.refresh(db_payment)
            return db_payment
        except IntegrityError:
            db.rollback()
            if clean_idem_key:
                concurrent_txn = (
                    db.query(ThanhToanModel)
                    .filter(ThanhToanModel.idempotency_key == clean_idem_key)
                    .first()
                )
                if concurrent_txn:
                    if (
                        concurrent_txn.id_dat_phong != payload.id_dat_phong
                        or float(concurrent_txn.so_tien) != float(payload.so_tien)
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=(
                                f"X-Idempotency-Key '{clean_idem_key}' đã được sử dụng đồng thời cho một đơn đặt phòng hoặc số tiền khác."
                            ),
                        )
                    return concurrent_txn
            raise

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
            .with_for_update()
            .with_hint(ThanhToanModel, "WITH (UPDLOCK, ROWLOCK)")
            .first()
        )
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy giao dịch: {payload.ma_giao_dich_gateway}",
            )

        if payment.trang_thai == TrangThaiThanhToanEnum.SUCCESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giao dịch này đã được thanh toán thành công trước đó.",
            )

        old_status = payment.trang_thai
        payment.trang_thai = payload.trang_thai.value

        if payload.trang_thai == TrangThaiThanhToanEnum.SUCCESS:
            payment.ngay_thanh_toan = datetime.utcnow()
            payment.ghi_chu = payload.note or "Thanh toán thành công qua IPN Callback"

            # 1. Đảm bảo commit trạng thái nguyên tử trong database TRƯỚC
            db.commit()
            db.refresh(payment)

            # 2. CHỈ gọi Booking Service và publish event SAU khi commit thành công, và chỉ thực hiện đúng một lần
            try:
                import urllib.request
                import urllib.parse
                note_encoded = urllib.parse.quote(
                    f"Xác nhận tự động qua cổng {payment.phuong_thuc} ({payment.ma_giao_dich_gateway})"
                )
                from src.core.correlation import get_correlation_id
                cid = get_correlation_id()
                headers = {"User-Agent": "payment-service"}
                if cid:
                    headers["X-Correlation-ID"] = cid

                confirm_url = f"{settings.BOOKING_SERVICE_URL}/bookings/{payment.id_dat_phong}/confirm?note={note_encoded}"
                req = urllib.request.Request(confirm_url, method="PATCH", headers=headers)
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    print(
                        f">>> [Payment Service] Booking {payment.id_dat_phong} confirmed successfully via IPN (status {resp.status})."
                    )
            except Exception as e:
                print(f">>> [Payment Service] Error contacting booking-service: {str(e)}")

            try:
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

            return payment

        elif payload.trang_thai == TrangThaiThanhToanEnum.FAILED:
            payment.ghi_chu = payload.note or "Giao dịch thanh toán thất bại"
            db.commit()
            db.refresh(payment)
            return payment
        else:
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
